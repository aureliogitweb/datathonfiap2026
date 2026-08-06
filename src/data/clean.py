"""Limpeza do painel PEDE.

Corrige valores que nao representam o que aparentam. Nao transforma nem
deriva — isso e 6.3. Toda alteracao entra no log de auditoria.

As decisoes aqui sao diferenciadas por indicador e cada uma tem evidencia
no notebook 01. Resumo do porque:

  IAA == 0  -> NaN. Gap de 0 ate 1.7~3.5 na distribuicao (nenhum valor
               intermediario existe) e nao-persistencia entre anos: quem
               zerou em 2022 tem 25% de zero em 2023, contra 21% de quem
               nao zerou. Assinatura de sentinela, nao de medida.
  IEG == 0  -> mantem. Gap menor e engajamento nulo e estado real e
               interpretavel (nao entregou atividade).
  IDA == 0  -> mantem. Distribuicao continua (0, 0.5, 0.7, 0.9): aluno
               pode tirar zero de fato.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TETO = 10.0
INDICADORES = ["iaa", "ieg", "ips", "ipp", "ida", "ipv", "ian"]

# Zeros tratados como ausencia. So IAA — ver docstring.
ZEROS_SENTINELA = ["iaa"]


class LogLimpeza:
    """Registro auditavel. Vira anexo do notebook 01."""

    def __init__(self) -> None:
        self._linhas: list[dict] = []

    def add(self, coluna: str, regra: str, n: int, detalhe: str = "") -> None:
        if n:
            self._linhas.append({"coluna": coluna, "regra": regra,
                                 "n_afetado": n, "detalhe": detalhe})

    def df(self) -> pd.DataFrame:
        return pd.DataFrame(self._linhas or [{"coluna": "-", "regra": "nenhuma",
                                              "n_afetado": 0, "detalhe": ""}])


def tratar_zeros(p: pd.DataFrame, log: LogLimpeza) -> pd.DataFrame:
    """IAA==0 vira NaN, com flag preservando o sinal MNAR."""
    p = p.copy()
    for c in ZEROS_SENTINELA:
        mask = p[c] == 0
        p[f"{c}_nao_respondeu"] = mask.astype(int)
        p.loc[mask, c] = np.nan
        log.add(c, "zero -> NaN (sentinela)", int(mask.sum()),
                "flag _nao_respondeu criada")
    # Zeros mantidos: registra para ninguem achar que passou despercebido.
    for c in ["ieg", "ida"]:
        n = int((p[c] == 0).sum())
        log.add(c, "zero MANTIDO (medida real)", n, "distribuicao continua")
    return p


def truncar_escala(p: pd.DataFrame, log: LogLimpeza) -> pd.DataFrame:
    """Excesso de arredondamento no teto (IAA 10.002, IPV 10.010)."""
    p = p.copy()
    for c in INDICADORES:
        mask = p[c] > TETO
        n = int(mask.sum())
        if n:
            excesso = float(p.loc[mask, c].max() - TETO)
            p.loc[mask, c] = TETO
            log.add(c, f"truncado em {TETO}", n, f"excesso max {excesso:.3f}")
    return p


def recuperar_idade(p: pd.DataFrame, log: LogLimpeza) -> pd.DataFrame:
    """Idade faltante deduzida do proprio painel: idade(t) = idade(t0) + (t-t0).

    Reconstrucao aritmetica, nao imputacao estatistica. 399 nulos, todos
    em 2023, ~91% recuperaveis.
    """
    p = p.copy()
    ref = (p.dropna(subset=["idade"])
             .sort_values("ano")
             .groupby("ra")
             .agg(ano_ref=("ano", "first"), idade_ref=("idade", "first")))
    falta = p["idade"].isna()
    j = p.loc[falta, ["ra", "ano"]].join(ref, on="ra")
    calc = j["idade_ref"] + (j["ano"] - j["ano_ref"])
    p.loc[falta, "idade"] = calc.values
    p["idade_recuperada"] = 0
    p.loc[falta & p["idade"].notna(), "idade_recuperada"] = 1
    log.add("idade", "recuperada por aritmetica no painel",
            int(p["idade_recuperada"].sum()),
            f"restam {int(p['idade'].isna().sum())} sem referencia")
    return p


def consolidar_instituicao(p: pd.DataFrame, log: LogLimpeza) -> pd.DataFrame:
    """2022 e 2023-24 usam taxonomias incompativeis.

    2022: 'Escola Publica', 'Rede Decisao'...
    2023-24: 'Publica', 'Privada - Programa de Apadrinhamento'...
    Nao ha mapeamento fiel. Binario publico/privado e o maximo honesto.
    """
    p = p.copy()
    s = p["instituicao"].fillna("").str.upper()
    p["rede_publica"] = np.where(
        s.str.contains("PÚBLIC|PUBLIC", regex=True), 1,
        np.where(s.str.contains("PRIVAD|DECIS|BOLSIST|JP II"), 0, np.nan))
    log.add("instituicao", "-> binario rede_publica",
            int(p["rede_publica"].notna().sum()),
            f"{int(p['rede_publica'].isna().sum())} nao classificados")
    return p


def derivar_turma(p: pd.DataFrame, log: LogLimpeza) -> pd.DataFrame:
    """Turma tem 120 niveis e semantica que muda por ano. Vira tamanho."""
    p = p.copy()
    # Agrupa por (ano, fase, turma): em 2022 'turma' e so a letra e agrega
    # todas as fases; em 2023-24 ja vem como '1A'. Sem a fase, o tamanho
    # medio sai 54.8 em 2022 contra 12.9 em 2024 — artefato de schema.
    p["tamanho_turma"] = p.groupby(["ano", "fase_num", "turma"])["ra"].transform("size")
    log.add("turma", "-> tamanho_turma (por ano+fase+turma)", len(p),
            "120 niveis descartados")
    return p


def limpar(p: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Pipeline completo. Devolve (painel limpo, log)."""
    log = LogLimpeza()
    p = tratar_zeros(p, log)
    p = truncar_escala(p, log)
    p = recuperar_idade(p, log)
    p = consolidar_instituicao(p, log)
    p = derivar_turma(p, log)
    return p, log.df()
