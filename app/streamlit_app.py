"""Passos Magicos: risco de agravamento de defasagem.

Carrega o modelo treinado e estima a probabilidade de a defasagem do aluno
piorar no proximo ciclo. Nao treina nada em tempo de execucao.

Deploy: Streamlit Community Cloud. Arquivo principal: app/streamlit_app.py
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st

ART = Path(__file__).parent / "artifacts" / "modelo_risco.joblib"
INDICADORES = ["iaa", "ieg", "ips", "ida", "ipv"]

NOME_ESTRATO = {"inicial": "fase inicial", "avancada": "fase avançada"}

st.set_page_config(page_title="Risco de Defasagem | Passos Mágicos",
                   page_icon="📚", layout="wide")


# --------------------------------------------------------------------------
# Carregamento
# --------------------------------------------------------------------------
@st.cache_resource(show_spinner="Carregando modelo...")
def carregar():
    """Usa cache_resource porque o objeto e imutavel e nao serializavel."""
    if not ART.exists():
        st.error(
            f"**Arquivo do modelo não encontrado em:** `{ART}`\n\n"
            "O arquivo `modelo_risco.joblib` precisa estar na pasta "
            "`app/artifacts/`. Para gerá-lo, execute o notebook "
            "`notebooks/03_modelo_risco.ipynb` até a última célula."
        )
        st.stop()
    try:
        return joblib.load(ART)
    except Exception as erro:
        st.error(
            f"**Não foi possível carregar o modelo.** ({type(erro).__name__})\n\n"
            "A causa mais comum é a versão do scikit-learn instalada ser "
            "diferente daquela usada para gerar o arquivo. Confira as versões "
            "listadas em `requirements.txt` ou execute novamente o notebook "
            "`03_modelo_risco.ipynb` para gerar um arquivo compatível.\n\n"
            f"Mensagem original: {erro}"
        )
        st.stop()


art = carregar()
MODELO, FEATURES = art["modelo"], art["features"]
QUANTIS, FAIXAS = art["quantis"], art["faixas"]
BASE, MET = art["base_rate"], art["metricas"]


# --------------------------------------------------------------------------
# Features derivadas
# --------------------------------------------------------------------------
def nota_para_percentil(nota: float, indicador: str) -> float:
    """Converte nota de 0 a 10 em percentil pela distribuicao de referencia.

    O modelo foi treinado com percentis calculados dentro de cada ano, o que
    protege contra mudancas de escala entre ciclos. O usuario informa a nota
    e a conversao acontece aqui.
    """
    if nota is None or (isinstance(nota, float) and np.isnan(nota)):
        return np.nan
    q = np.asarray(QUANTIS[indicador])
    return float(np.searchsorted(q, nota) / 100.0)


def montar_linha(d: dict) -> pd.DataFrame:
    """Converte os dados informados no formato esperado pelo modelo."""
    fase_ideal = d["fase_ideal"]
    idade_med = art["idade_mediana_por_fase_ideal"].get(float(fase_ideal), np.nan)
    linha = {
        "fase_ideal_num": fase_ideal,
        "defasagem": d["fase"] - fase_ideal,
        "idade_rel_fase_ideal": d["idade"] - idade_med if pd.notna(idade_med) else np.nan,
        "tempo_casa": d["tempo_casa"],
        "iaa_nao_respondeu": int(d.get("iaa") in (None, 0)),
        "rede_publica": d["rede_publica"],
        "genero_f": d["genero_f"],
        "tamanho_turma": d.get("tamanho_turma") or art["tamanho_turma_mediano"],
    }
    for ind in INDICADORES:
        linha[f"{ind}_pct"] = nota_para_percentil(d.get(ind), ind)
    return pd.DataFrame([linha])[FEATURES]


def classificar(p: float, estrato: str) -> tuple[str, str]:
    """Classifica o risco em relacao a media do grupo do aluno.

    Um risco de 20% e grave na fase avancada e esta abaixo da media na fase
    inicial, por isso a comparacao e sempre relativa ao estrato.
    """
    ref = BASE[estrato]
    if p >= 2 * ref:
        return "ALTO", "🔴"
    if p >= ref:
        return "ACIMA DA MÉDIA", "🟠"
    return "DENTRO DO ESPERADO", "🟢"


# --------------------------------------------------------------------------
# Validacao das entradas
# --------------------------------------------------------------------------
def validar(d: dict) -> list[str]:
    """Retorna as mensagens de erro. Lista vazia significa entrada valida."""
    erros = []

    lo, hi = FAIXAS["indicador"]
    for ind in INDICADORES:
        valor = d.get(ind)
        if valor is not None and not (lo <= valor <= hi):
            erros.append(
                f"O indicador {ind.upper()} deve ficar entre {lo:.0f} e "
                f"{hi:.0f}. Valor informado: {valor}."
            )

    f_lo, f_hi = FAIXAS["fase"]
    rotulo = {"fase": "A fase atual", "fase_ideal": "A fase ideal"}
    for campo in ("fase", "fase_ideal"):
        if not (f_lo <= d[campo] <= f_hi):
            erros.append(
                f"{rotulo[campo]} deve ficar entre {f_lo} e {f_hi}. "
                f"Valor informado: {d[campo]}."
            )

    i_lo, i_hi = FAIXAS["idade"]
    if not (i_lo <= d["idade"] <= i_hi):
        erros.append(
            f"A idade deve ficar entre {i_lo} e {i_hi} anos. "
            f"Valor informado: {d['idade']}."
        )

    d_lo, d_hi = FAIXAS["defasagem"]
    diferenca = d["fase"] - d["fase_ideal"]
    if not (d_lo <= diferenca <= d_hi):
        erros.append(
            f"A diferença entre a fase atual ({d['fase']}) e a fase ideal "
            f"({d['fase_ideal']}) resulta em {diferenca:+d}, valor que não "
            f"aparece na base histórica, cujo intervalo observado vai de "
            f"{d_lo} a {d_hi:+d}. Verifique o preenchimento dos dois campos: "
            f"a fase atual é o nível que o aluno cursa na Passos Mágicos e a "
            f"fase ideal é a esperada para o ano escolar dele."
        )

    if d["tempo_casa"] < 0:
        erros.append("O tempo de programa não pode ser negativo.")

    return erros


COLS_CSV = ["ra", "fase", "fase_ideal", "idade", "tempo_casa",
            "rede_publica", "genero_f"]


def validar_csv(df: pd.DataFrame) -> list[str]:
    """Verifica a estrutura do arquivo enviado antes de pontuar."""
    erros = []

    faltando = [c for c in COLS_CSV if c not in df.columns]
    if faltando:
        erros.append(
            "O arquivo não contém as seguintes colunas obrigatórias: "
            f"{', '.join(faltando)}. Baixe o arquivo modelo disponível nesta "
            "página para conferir o formato esperado."
        )
        return erros

    if df.empty:
        erros.append("O arquivo não contém nenhuma linha de dados.")

    if df["ra"].duplicated().any():
        n = int(df["ra"].duplicated().sum())
        erros.append(
            f"O arquivo contém {n} registro(s) de RA repetido(s). "
            "Cada aluno deve aparecer uma única vez."
        )

    for c in ["fase", "fase_ideal", "idade", "tempo_casa"]:
        if not pd.api.types.is_numeric_dtype(df[c]):
            erros.append(
                f"A coluna '{c}' contém valores que não são numéricos. "
                "Verifique se há texto ou células em branco nessa coluna."
            )

    return erros


# --------------------------------------------------------------------------
# Interface
# --------------------------------------------------------------------------
st.title("📚 Risco de Agravamento de Defasagem")
st.caption("Associação Passos Mágicos. Modelo treinado com dados do PEDE 2022 a 2024.")

st.warning(
    "**O que este modelo mede.** A probabilidade de a defasagem do aluno "
    "aumentar no próximo ciclo. Em 98,7% dos casos observados, esse aumento "
    "ocorreu porque o aluno permaneceu na mesma fase enquanto a fase ideal "
    "avançou. Trata-se, portanto, de um descompasso entre o calendário da "
    "Passos Mágicos e o calendário escolar. O resultado não indica "
    "dificuldade de aprendizagem nem falta de esforço do aluno.",
    icon="⚠️",
)

aba1, aba2, aba3 = st.tabs(["📋 Priorização em lote", "👤 Aluno individual",
                            "ℹ️ Sobre o modelo"])

# ---- Priorizacao em lote -------------------------------------------------
with aba1:
    st.subheader("Lista priorizada por risco")
    st.markdown(
        "Envie um arquivo CSV com os dados da turma para receber a lista "
        "ordenada por risco. As colunas obrigatórias são: "
        f"`{'`, `'.join(COLS_CSV)}`. Os indicadores "
        f"(`{'`, `'.join(INDICADORES)}`) são opcionais e, quando ausentes, "
        "o modelo trata o campo como não informado."
    )

    modelo_csv = pd.DataFrame([{
        "ra": "A001", "fase": 3, "fase_ideal": 4, "idade": 13, "tempo_casa": 2,
        "rede_publica": 1, "genero_f": 1, "iaa": 8.5, "ieg": 7.2,
        "ips": 6.8, "ida": 6.1, "ipv": 7.5}])
    st.download_button("⬇️ Baixar arquivo modelo",
                       modelo_csv.to_csv(index=False).encode("utf-8-sig"),
                       "modelo_entrada.csv", "text/csv")

    up = st.file_uploader("Selecione o arquivo CSV", type="csv")
    if up:
        try:
            df = pd.read_csv(up)
        except Exception as erro:
            st.error(
                "**Não foi possível ler o arquivo.** Verifique se ele está no "
                "formato CSV e se as colunas estão separadas por vírgula.\n\n"
                f"Mensagem original: {erro}"
            )
            st.stop()

        erros = validar_csv(df)
        if erros:
            st.error("**O arquivo precisa ser corrigido antes do envio:**\n\n"
                     + "\n".join(f"- {e}" for e in erros))
            st.stop()

        linhas, descartadas = [], []
        for _, r in df.iterrows():
            d = {c: r[c] for c in COLS_CSV if c != "ra"}
            d.update({i: r[i] for i in INDICADORES
                      if i in df.columns and pd.notna(r.get(i))})
            d = {k: (int(v) if k in ("fase", "fase_ideal", "tempo_casa",
                                     "rede_publica", "genero_f") else v)
                 for k, v in d.items()}
            if validar(d):
                descartadas.append(r["ra"])
                continue
            linhas.append((r["ra"], montar_linha(d)))

        if descartadas:
            st.warning(
                f"{len(descartadas)} registro(s) não foram avaliados porque "
                "contêm valores fora das faixas esperadas. "
                f"RA: {', '.join(map(str, descartadas[:10]))}"
                + (" e outros." if len(descartadas) > 10 else "")
            )
        if not linhas:
            st.error("Nenhum registro válido foi encontrado no arquivo.")
            st.stop()

        Xb = pd.concat([x for _, x in linhas], ignore_index=True)
        probs = MODELO.predict_proba(Xb)[:, 1]
        out = pd.DataFrame({
            "RA": [ra for ra, _ in linhas],
            "risco": probs,
            "estrato": np.where(Xb["fase_ideal_num"] <= 1, "inicial", "avancada"),
            "defasagem": Xb["defasagem"].values,
        })
        out["grupo"] = out["estrato"].map(NOME_ESTRATO)
        out["classificacao"] = [classificar(p, e)[0]
                                for p, e in zip(out.risco, out.estrato)]
        out = (out.drop(columns="estrato")
                  .sort_values("risco", ascending=False)
                  .reset_index(drop=True))
        out.insert(0, "prioridade", out.index + 1)

        c1, c2, c3 = st.columns(3)
        c1.metric("Alunos avaliados", len(out))
        c2.metric("Classificados como risco alto",
                  int((out.classificacao == "ALTO").sum()))
        c3.metric("Risco médio da turma", f"{out.risco.mean():.1%}")

        st.info(
            "**Como interpretar a lista.** Compare cada aluno com a média do "
            f"próprio grupo: {BASE['inicial']:.0%} na fase inicial e "
            f"{BASE['avancada']:.0%} na fase avançada. Um aluno com 20% de "
            "risco representa um caso grave na fase avançada, mas está abaixo "
            "da média na fase inicial.",
            icon="💡",
        )
        st.dataframe(
            out.style.format({"risco": "{:.1%}"})
               .background_gradient("Reds", subset=["risco"]),
            use_container_width=True, hide_index=True)
        st.download_button("⬇️ Baixar lista priorizada",
                           out.to_csv(index=False).encode("utf-8-sig"),
                           "priorizacao_risco.csv", "text/csv")

# ---- Consulta individual -------------------------------------------------
with aba2:
    st.subheader("Consulta individual")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Situação escolar**")
        fase = st.number_input("Fase atual na Passos Mágicos", 0, 8, 3,
                               help="Nível que o aluno cursa hoje no programa.")
        fase_ideal = st.number_input("Fase ideal para o ano escolar", 0, 8, 3,
                                     help="Nível esperado para o ano escolar do aluno.")
        idade = st.number_input("Idade", 5, 25, 12)
        tempo_casa = st.number_input("Anos de programa", 0, 15, 2)
    with c2:
        st.markdown("**Indicadores** (use 0 quando não houver avaliação)")
        iaa = st.slider("IAA, autoavaliação", 0.0, 10.0, 8.0, 0.1)
        ieg = st.slider("IEG, engajamento", 0.0, 10.0, 8.0, 0.1)
        ips = st.slider("IPS, aspectos psicossociais", 0.0, 10.0, 7.0, 0.1)
    with c3:
        st.markdown("**Indicadores (continuação)**")
        ida = st.slider("IDA, aprendizagem", 0.0, 10.0, 6.5, 0.1)
        ipv = st.slider("IPV, ponto de virada", 0.0, 10.0, 7.5, 0.1)
        rede = st.selectbox("Rede de ensino", ["Pública", "Privada"])
        genero = st.selectbox("Gênero", ["Feminino", "Masculino"])

    if st.button("Calcular risco", type="primary"):
        d = {"fase": fase, "fase_ideal": fase_ideal, "idade": idade,
             "tempo_casa": tempo_casa, "rede_publica": int(rede == "Pública"),
             "genero_f": int(genero == "Feminino"), "iaa": iaa or None,
             "ieg": ieg, "ips": ips, "ida": ida, "ipv": ipv}
        erros = validar(d)
        if erros:
            st.error("**Corrija os itens abaixo antes de calcular:**\n\n"
                     + "\n".join(f"- {e}" for e in erros))
        else:
            X1 = montar_linha(d)
            p = float(MODELO.predict_proba(X1)[0, 1])
            estrato = "inicial" if fase_ideal <= 1 else "avancada"
            rotulo, emoji = classificar(p, estrato)
            razao = p / BASE[estrato]

            a, b = st.columns([1, 2])
            a.metric("Probabilidade de agravamento", f"{p:.1%}")
            a.metric("Classificação", f"{emoji} {rotulo}")
            b.markdown(
                f"**Leitura do resultado.** Entre 1.000 alunos com esse "
                f"perfil, cerca de **{p*1000:.0f}** tiveram agravamento de "
                f"defasagem no ciclo seguinte.\n\n"
                f"Esse valor equivale a **{razao:.1f} vez(es) a média** do "
                f"grupo de {NOME_ESTRATO[estrato]}, que é de "
                f"{BASE[estrato]:.1%}. A defasagem atual do aluno é de "
                f"**{fase - fase_ideal:+d}** fase(s).\n\n"
                f"O modelo é calibrado, com índice de Brier igual a "
                f"{MET['brier']}, portanto a proporção estimada é confiável. "
                f"Ainda assim, trata-se de uma taxa de grupo e **não de uma "
                f"previsão individual**."
            )
            if abs(fase - fase_ideal) >= 1 and p < BASE[estrato]:
                st.info(
                    "**Por que o risco aparece baixo mesmo com o aluno "
                    "defasado?** Quem já acumulou defasagem tem menos margem "
                    "para piorar, o que reduz a probabilidade estimada. Um "
                    "risco baixo indica estabilidade na situação atual e não "
                    "ausência de necessidade de apoio pedagógico.",
                    icon="⚠️",
                )

# ---- Sobre o modelo ------------------------------------------------------
with aba3:
    st.subheader("Como o modelo foi construído")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PR-AUC (dados de 2024)", MET["pr_auc_teste"])
    c2.metric("PR-AUC na fase avançada", MET["pr_auc_avancada"])
    c3.metric("Regra simples (só fase)", MET["baseline_pr_auc"])
    c4.metric("Índice de Brier", MET["brier"])

    st.markdown(f"""
**Variável prevista.** Agravamento da defasagem entre um ciclo e o seguinte,
definido como `defasagem(t+1) < defasagem(t)`. O evento ocorreu em
{BASE['global']:.1%} das transições observadas na base.

**Validação.** O modelo foi treinado com as transições de 2022 para 2023 e
testado com as transições de 2023 para 2024. Nenhum dado do período de teste
participou do treinamento e nenhum aluno aparece simultaneamente nos dois
lados de uma mesma etapa de validação.

**Algoritmo.** Regressão logística com regularização. A escolha considerou
também Random Forest, XGBoost e LightGBM. A regressão logística foi
selecionada porque produz probabilidades calibradas, requisito para uso em
decisões reais, e porque apresentou melhor desempenho no grupo de fase
avançada, no qual a previsão é mais difícil.

**Fatores mais influentes.** A defasagem atual é o fator de maior peso, por
efeito de piso: alunos próximos do nível ideal têm mais margem para regredir.
Em seguida aparece o IPV, cujo valor elevado reduz em mais da metade a chance
de agravamento.

### Limitações que devem ser observadas

- O modelo mede descompasso de calendário e não desempenho pedagógico.
- A análise considera apenas alunos que permaneceram no programa. A cada ano,
  entre 25% e 30% dos alunos deixam a instituição.
- Não é possível distinguir a não promoção pedagógica da administrativa.
- Os resultados são associativos e não causais, pois a base não possui grupo
  de controle.
- A ferramenta destina-se à priorização de atendimento e não ao diagnóstico
  individual. A decisão sobre cada aluno cabe à equipe pedagógica.
""")

st.divider()
st.caption("Datathon PosTech. Associação Passos Mágicos. "
           "Modelo treinado com dados do PEDE 2022 a 2024.")
