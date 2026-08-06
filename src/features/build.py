"""Feature engineering.

Regra unica e inegociavel: so entra informacao disponivel no ano t.
A auditoria em auditar_leakage() falha se algo de t+1 escapar.

Fora por decisao (ver notebook 03):
  ian, inde, pedra -> cadeia deterministica do alvo
  ipp             -> nao existe em 2022, quebraria o split temporal
  turma           -> 120 niveis, semantica muda por ano; vira tamanho_turma
"""

from __future__ import annotations

import numpy as np
import pandas as pd

INDICADORES = ["iaa", "ieg", "ips", "ida", "ipv"]

PROIBIDAS = {"ian", "inde", "pedra", "ipp", "defasagem_t1", "ida_t1",
             "inde_t1", "alvo_piora", "alvo_entrada", "delta_defasagem"}

# Grupos nomeados: a selecao final acontece no Passo 7, com validacao.
GRUPOS: dict[str, list[str]] = {
    "estrutural": ["fase_ideal_num", "defasagem", "anos_na_fase",
                   "idade_rel_fase_ideal", "tempo_casa"],
    "desempenho": [f"{c}_pct" for c in INDICADORES],
    "trajetoria": ["d_ida", "d_ieg", "tem_historico"],
    "ausencia":   ["sem_avaliacao", "n_indic_faltantes", "iaa_nao_respondeu"],
    "contexto":   ["rede_publica", "genero_f", "tamanho_turma"],
}


def features(grupos: list[str] | None = None) -> list[str]:
    g = grupos or list(GRUPOS)
    return [f for k in g for f in GRUPOS[k]]


def _pct_intra_ano(p: pd.DataFrame, col: str) -> pd.Series:
    """Percentil dentro do ano. Imune ao drift de escala do IPS."""
    return p.groupby("ano")[col].rank(pct=True)


def adicionar_features(p: pd.DataFrame) -> pd.DataFrame:
    """Deriva features no painel. Tudo em t; nada olha para frente."""
    p = p.sort_values(["ra", "ano"]).copy()
    g = p.groupby("ra")

    # --- desempenho relativo ---
    for c in INDICADORES:
        p[f"{c}_pct"] = _pct_intra_ano(p, c)

    # --- ciclo da regua ---
    # Faixas de fase ideal cobrem 2 anos escolares. Aluno mais velho dentro
    # da propria faixa esta no segundo ano dela -> regua sobe em breve.
    med = p.groupby(["ano", "fase_ideal_num"])["idade"].transform("median")
    p["idade_rel_fase_ideal"] = p["idade"] - med

    # Quantos anos consecutivos na mesma fase da PM (proxy de estagnacao).
    mudou = g["fase_num"].diff().ne(0) | g["fase_num"].diff().isna()
    p["_bloco"] = mudou.groupby(p["ra"]).cumsum()
    p["anos_na_fase"] = p.groupby(["ra", "_bloco"]).cumcount()
    p = p.drop(columns="_bloco")

    # --- trajetoria (so veteranos) ---
    p["tem_historico"] = g["ano"].cumcount().gt(0).astype(int)
    for c in ["ida", "ieg"]:
        p[f"d_{c}"] = g[c].diff()
    p.loc[p["tem_historico"] == 0, ["d_ida", "d_ieg"]] = np.nan

    # --- contexto ---
    p["tempo_casa"] = p["ano"] - p["ano_ingresso"]
    p["genero_f"] = (p["genero"] == "F").astype(int)

    return p


def montar_matriz(trans: pd.DataFrame, grupos: list[str] | None = None):
    """Devolve X, y, grupos_cv (RA) e o recorte para estratificar."""
    cols = features(grupos)
    faltando = [c for c in cols if c not in trans.columns]
    if faltando:
        raise KeyError(f"features ausentes: {faltando}")
    X = trans[cols].copy()
    y = trans["alvo_piora"].astype(int)
    return X, y, trans["ra"], trans["bloco_fase_ideal"]


def diagnosticar_features(X: pd.DataFrame, mask_treino: np.ndarray,
                         min_nunique: int = 2,
                         max_nulo_treino: float = 0.6) -> pd.DataFrame:
    """Detecta features inuteis ou perigosas na janela de treino.

    Motivo: 2022 e o primeiro ano do painel, entao nada que dependa de t-1
    tem variacao la. Feature constante no treino que varia no teste e pior
    que feature fraca — o modelo nao aprende e mesmo assim ela se move.
    """
    linhas = []
    for c in X.columns:
        tr, te = X.loc[mask_treino, c], X.loc[~mask_treino, c]
        nu_tr, nulo_tr = tr.nunique(), tr.isna().mean()
        drift_nulo = abs(te.isna().mean() - nulo_tr)
        if nu_tr < min_nunique:
            veredito = "DEGENERADA (constante no treino)"
        elif nulo_tr > max_nulo_treino:
            veredito = "DEGENERADA (nulos demais no treino)"
        elif drift_nulo > 0.15:
            veredito = "ATENCAO (missingness diverge)"
        else:
            veredito = "ok"
        linhas.append({"feature": c, "nunique_treino": nu_tr,
                       "nulo_treino": round(nulo_tr, 3),
                       "nulo_teste": round(te.isna().mean(), 3),
                       "veredito": veredito})
    return pd.DataFrame(linhas)


def features_utilizaveis(X: pd.DataFrame, mask_treino: np.ndarray) -> list[str]:
    """Colunas que sobrevivem ao diagnostico. ATENCAO passa; DEGENERADA nao."""
    d = diagnosticar_features(X, mask_treino)
    return d.loc[~d["veredito"].str.startswith("DEGENERADA"), "feature"].tolist()


def auditar_leakage(X: pd.DataFrame, trans: pd.DataFrame) -> pd.DataFrame:
    """Falha se alguma feature for proibida ou correlacionar perfeito com o alvo.

    Correlacao ~1 e assinatura de vazamento: foi assim que o IAN se
    denunciaria se tivesse escapado.
    """
    ruins = [c for c in X.columns if c in PROIBIDAS or c.endswith("_t1")]
    if ruins:
        raise ValueError(f"features proibidas na matriz: {ruins}")

    y = trans["alvo_piora"]
    linhas = []
    for c in X.columns:
        s = X[c]
        r = s.corr(y) if s.notna().sum() > 10 else np.nan
        linhas.append({
            "feature": c,
            "grupo": next(k for k, v in GRUPOS.items() if c in v),
            "pct_nulo": round(100 * s.isna().mean(), 1),
            "corr_alvo": round(r, 3) if pd.notna(r) else None,
            "suspeita": "VERIFICAR" if pd.notna(r) and abs(r) > 0.9 else "",
        })
    aud = pd.DataFrame(linhas).sort_values("corr_alvo", key=abs, ascending=False)
    if (aud["suspeita"] == "VERIFICAR").any():
        raise ValueError(f"correlacao suspeita:\n{aud[aud.suspeita != '']}")
    return aud
