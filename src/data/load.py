"""Ingestão e harmonização da base PEDE 2022-2024 (Datathon Passos Mágicos).

Converte as três abas — que têm schemas divergentes — em um painel longo
(uma linha por aluno-ano) e em uma tabela de transições t -> t+1.

Uso:
    from src.data.load import build_panel, build_transitions
    painel = build_panel("data/raw/BASE_PEDE_2024.xlsx")
    trans  = build_transitions(painel)
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

SHEETS = {2022: "PEDE2022", 2023: "PEDE2023", 2024: "PEDE2024"}


def load_config(path: str | Path = "config.yaml") -> dict:
    import yaml
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def salvar(df: pd.DataFrame, destino: str | Path) -> Path:
    """Parquet quando disponivel (preserva tipos); CSV utf-8-sig como fallback."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        alvo = destino.with_suffix(".parquet")
        df.to_parquet(alvo, index=False)
    except (ImportError, ValueError):
        alvo = destino.with_suffix(".csv")
        df.to_csv(alvo, index=False, encoding="utf-8-sig")
    return alvo

# Mapa origem -> nome canônico, por ano. Só entra aqui coluna que existe
# na aba; ausências viram NaN em harmonise() para manter o schema estável.
RENAME = {
    2022: {
        "RA": "ra", "Fase": "fase_raw", "Turma": "turma", "Idade 22": "idade",
        "Gênero": "genero", "Ano ingresso": "ano_ingresso",
        "Instituição de ensino": "instituicao", "INDE 22": "inde",
        "Pedra 22": "pedra", "Cg": "cg", "Cf": "cf", "Ct": "ct", "Nº Av": "n_aval",
        "IAA": "iaa", "IEG": "ieg", "IPS": "ips", "IDA": "ida", "IPV": "ipv",
        "IAN": "ian", "Matem": "nota_mat", "Portug": "nota_por", "Inglês": "nota_ing",
        "Indicado": "indicado_bolsa", "Atingiu PV": "atingiu_pv",
        "Fase ideal": "fase_ideal_raw", "Defas": "defasagem",
        "Rec Psicologia": "rec_psicologia", "Destaque IEG": "destaque_ieg",
        "Destaque IDA": "destaque_ida", "Destaque IPV": "destaque_ipv",
    },
    2023: {
        "RA": "ra", "Fase": "fase_raw", "Turma": "turma", "Idade": "idade",
        "Gênero": "genero", "Ano ingresso": "ano_ingresso",
        "Instituição de ensino": "instituicao", "INDE 2023": "inde",
        "Pedra 2023": "pedra", "Cg": "cg", "Cf": "cf", "Ct": "ct", "Nº Av": "n_aval",
        "IAA": "iaa", "IEG": "ieg", "IPS": "ips", "IPP": "ipp", "IDA": "ida",
        "IPV": "ipv", "IAN": "ian", "Mat": "nota_mat", "Por": "nota_por",
        "Ing": "nota_ing", "Indicado": "indicado_bolsa", "Atingiu PV": "atingiu_pv",
        "Fase Ideal": "fase_ideal_raw", "Defasagem": "defasagem",
        "Rec Psicologia": "rec_psicologia", "Destaque IEG": "destaque_ieg",
        "Destaque IDA": "destaque_ida", "Destaque IPV": "destaque_ipv",
    },
    2024: {
        "RA": "ra", "Fase": "fase_raw", "Turma": "turma", "Idade": "idade",
        "Gênero": "genero", "Ano ingresso": "ano_ingresso",
        "Instituição de ensino": "instituicao", "INDE 2024": "inde",
        "Pedra 2024": "pedra", "Cg": "cg", "Cf": "cf", "Ct": "ct", "Nº Av": "n_aval",
        "IAA": "iaa", "IEG": "ieg", "IPS": "ips", "IPP": "ipp", "IDA": "ida",
        "IPV": "ipv", "IAN": "ian", "Mat": "nota_mat", "Por": "nota_por",
        "Ing": "nota_ing", "Indicado": "indicado_bolsa", "Atingiu PV": "atingiu_pv",
        "Fase Ideal": "fase_ideal_raw", "Defasagem": "defasagem",
        "Rec Psicologia": "rec_psicologia", "Destaque IEG": "destaque_ieg",
        "Destaque IDA": "destaque_ida", "Destaque IPV": "destaque_ipv",
        "Escola": "escola",
    },
}

CANONICAL = [
    "ra", "ano", "fase_num", "fase_raw", "turma", "idade", "genero",
    "ano_ingresso", "instituicao", "inde", "pedra", "cg", "cf", "ct", "n_aval",
    "iaa", "ieg", "ips", "ipp", "ida", "ipv", "ian", "nota_mat", "nota_por",
    "nota_ing", "indicado_bolsa", "atingiu_pv", "fase_ideal_num",
    "fase_ideal_raw", "defasagem", "rec_psicologia", "destaque_ieg",
    "destaque_ida", "destaque_ipv", "escola", "n_indic_faltantes",
    "sem_avaliacao",
]

INDICADORES = ["iaa", "ieg", "ips", "ipp", "ida", "ipv", "ian"]

# 'INCLUIR' aparece em INDE 2024 como marcador administrativo, não como nota.
SENTINELAS_NAO_NUMERICAS = {"INCLUIR", "#DIV/0!", "-", ""}


def _strip_accents(s) -> str:
    """Robusto a NaN/numérico: pandas 3.x mantém NA em astype(str)."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", str(s))
        if not unicodedata.combining(c)
    )


def fase_to_num(value) -> float:
    """'ALFA'->0, 'FASE 3'->3, '1A'->1, 7->7, 'Fase 2 (5º e 6º ano)'->2."""
    if pd.isna(value):
        return np.nan
    if isinstance(value, (int, np.integer)):
        return float(value)
    s = _strip_accents(str(value)).upper().strip()
    if "ALFA" in s:
        return 0.0
    m = re.search(r"(\d)", s)
    return float(m.group(1)) if m else np.nan


def to_numeric(series: pd.Series) -> pd.Series:
    """Numérico tolerante: trata vírgula decimal e sentinelas administrativas."""
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(float)
    s = series.map(_strip_accents).str.strip()
    s = s.where(~s.str.upper().isin(SENTINELAS_NAO_NUMERICAS))
    # Separador de milhar só é removido quando há vírgula decimal na mesma
    # string ("1.234,56"). Sem essa guarda, "8.337" (INDE válido, 3 casas)
    # seria lido como 8337.
    tem_virgula = s.str.contains(",", na=False)
    s = s.mask(tem_virgula,
               s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    return pd.to_numeric(s, errors="coerce")


def norm_genero(series: pd.Series) -> pd.Series:
    """2022 usa Menina/Menino; 2023-24 usam Feminino/Masculino."""
    s = series.map(_strip_accents).str.upper().str.strip()
    return np.where(
        s.str.startswith(("MENINA", "F")), "F",
        np.where(s.str.startswith(("MENINO", "M")), "M", None),
    )


def norm_pedra(series: pd.Series) -> pd.Series:
    """Corrige 'Agata' sem acento (2024) e padroniza capitalização."""
    s = series.map(_strip_accents).str.strip().str.upper()
    mapa = {"QUARTZO": "Quartzo", "AGATA": "Ágata",
            "AMETISTA": "Ametista", "TOPAZIO": "Topázio"}
    return s.map(mapa)


def norm_bool(series: pd.Series) -> pd.Series:
    s = series.map(_strip_accents).str.upper().str.strip()
    return pd.Series(
        np.where(s.str.startswith("SIM"), 1.0,
                 np.where(s.str.startswith("NAO"), 0.0, np.nan)),
        index=series.index,
    )


def harmonise(df: pd.DataFrame, ano: int) -> pd.DataFrame:
    """Aplica renomeação, tipagem e normalizações de um ano."""
    mapa = {k: v for k, v in RENAME[ano].items() if k in df.columns}
    out = df.rename(columns=mapa)[list(mapa.values())].copy()
    out["ano"] = ano

    out["fase_num"] = out["fase_raw"].map(fase_to_num)
    out["fase_ideal_num"] = out["fase_ideal_raw"].map(fase_to_num)

    for col in INDICADORES + ["inde", "nota_mat", "nota_por", "nota_ing",
                              "idade", "cg", "cf", "ct", "n_aval", "defasagem"]:
        if col in out.columns:
            out[col] = to_numeric(out[col])

    if "genero" in out.columns:
        out["genero"] = norm_genero(out["genero"])
    if "pedra" in out.columns:
        out["pedra"] = norm_pedra(out["pedra"])
    for col in ["indicado_bolsa", "atingiu_pv"]:
        if col in out.columns:
            out[col] = norm_bool(out[col])

    # Aluno sem ciclo avaliativo completo. Critério por CONTAGEM, não por
    # "todos nulos": em 2024 o IEG vem preenchido mesmo para quem não tem
    # nenhum outro indicador, então .all() não detectaria esses 102 casos.
    # Categoria própria: NÃO imputar (ver relatório de qualidade).
    aval = [c for c in ["iaa", "ieg", "ips", "ipp", "ida", "ipv"] if c in out.columns]
    out["n_indic_faltantes"] = out[aval].isna().sum(axis=1)
    out["sem_avaliacao"] = (out["n_indic_faltantes"] >= 4).astype(int)

    for col in CANONICAL:
        if col not in out.columns:
            out[col] = np.nan
    return out[CANONICAL]


def resolver_planilha(path: str | Path) -> Path:
    """Aceita o arquivo com qualquer nome, desde que seja o unico .xlsx.

    O nome original da banca tem espacos ("BASE DE DADOS PEDE 2024 -
    DATATHON.xlsx"); downloads e uploads costumam trocar por underscore.
    Em vez de exigir nome exato, procura na mesma pasta.
    """
    path = Path(path)
    if path.exists():
        return path
    pasta = path.parent
    if not pasta.exists():
        raise FileNotFoundError(
            f"Pasta {pasta} nao existe. Crie-a e coloque a planilha PEDE la."
        )
    candidatos = [f for f in pasta.glob("*.xls*") if not f.name.startswith("~$")]
    if len(candidatos) == 1:
        return candidatos[0]
    if not candidatos:
        raise FileNotFoundError(
            f"Nenhuma planilha encontrada em {pasta}/. "
            f"Coloque a base PEDE (.xlsx) nessa pasta."
        )
    raise FileNotFoundError(
        f"Mais de uma planilha em {pasta}/: {[c.name for c in candidatos]}. "
        f"Ajuste paths.raw no config.yaml para o arquivo correto."
    )


def build_panel(path: str | Path) -> pd.DataFrame:
    """Lê as três abas e devolve painel longo (uma linha por aluno-ano)."""
    path = resolver_planilha(path)
    partes = [harmonise(pd.read_excel(path, sheet_name=aba), ano)
              for ano, aba in SHEETS.items()]
    painel = pd.concat(partes, ignore_index=True)
    painel["ra"] = painel["ra"].astype(str).str.strip()

    dup = painel.duplicated(["ra", "ano"]).sum()
    if dup:
        raise ValueError(f"{dup} pares (ra, ano) duplicados — chave não é única.")
    return painel.sort_values(["ra", "ano"]).reset_index(drop=True)


def build_transitions(painel: pd.DataFrame) -> pd.DataFrame:
    """Pares t -> t+1 do mesmo aluno.

    Sufixos: features do ano-base sem sufixo; alvos do ano seguinte com '_t1'.
    Apenas 'defasagem' e 'ida' são trazidos de t+1 — qualquer outra variável
    futura seria vazamento no modelo de risco.
    """
    base = painel.copy()
    fut = painel[["ra", "ano", "defasagem", "ida", "inde"]].copy()
    fut["ano"] = fut["ano"] - 1
    fut = fut.rename(columns={"defasagem": "defasagem_t1", "ida": "ida_t1",
                              "inde": "inde_t1"})

    t = base.merge(fut, on=["ra", "ano"], how="inner")
    t["janela"] = t["ano"].astype(str) + "->" + (t["ano"] + 1).astype(str)
    t["delta_defasagem"] = t["defasagem_t1"] - t["defasagem"]
    t["alvo_piora"] = (t["delta_defasagem"] < 0).astype(int)
    t["alvo_entrada"] = ((t["defasagem"] == 0) & (t["defasagem_t1"] < 0)).astype(int)
    # Bloco pela fase IDEAL (proxy de idade/ano escolar), não pela fase cursada:
    # é a fase ideal que reproduz o gradiente de risco observado na EDA.
    t["bloco_fase_ideal"] = np.where(t["fase_ideal_num"] <= 1, "inicial", "avancada")
    return t


def quality_report(painel: pd.DataFrame) -> pd.DataFrame:
    """Nulos e cardinalidade por coluna e ano — insumo do slide de qualidade."""
    linhas = []
    for ano, g in painel.groupby("ano"):
        for col in g.columns:
            linhas.append({
                "ano": ano, "coluna": col,
                "n_nulos": int(g[col].isna().sum()),
                "pct_nulos": round(100 * g[col].isna().mean(), 1),
                "n_unicos": int(g[col].nunique(dropna=True)),
            })
    return pd.DataFrame(linhas)
