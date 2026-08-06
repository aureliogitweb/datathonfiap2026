"""Contratos de integridade do painel.

Falha cedo e alto. Cada violação aqui já custou horas de depuração antes —
o INDE máximo de 8337, por exemplo, passou por toda inspeção de schema e só
apareceu quando olhamos distribuição.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

INDICADORES = ["iaa", "ieg", "ips", "ipp", "ida", "ipv", "ian"]


class ContratoViolado(AssertionError):
    pass


def _check(cond: bool, msg: str, avisos: list[str], estrito: bool) -> None:
    if cond:
        return
    if estrito:
        raise ContratoViolado(msg)
    avisos.append(msg)


def validar_painel(painel: pd.DataFrame, cfg: dict, estrito: bool = True) -> list[str]:
    """Verifica invariantes do painel. Devolve avisos; levanta se estrito."""
    avisos: list[str] = []
    v = cfg["validacao"]

    # Chave
    dup = painel.duplicated(["ra", "ano"]).sum()
    _check(dup == 0, f"{dup} pares (ra, ano) duplicados", avisos, estrito)
    _check(painel["ra"].notna().all(), "RA com nulo", avisos, estrito)

    # Anos esperados
    anos = sorted(painel["ano"].unique())
    _check(anos == sorted(cfg["dados"]["anos"]),
           f"anos inesperados: {anos}", avisos, estrito)

    # Invariante estrutural: defasagem = fase - fase_ideal
    m = painel[["defasagem", "fase_num", "fase_ideal_num"]].dropna()
    viol = int((m["defasagem"] != m["fase_num"] - m["fase_ideal_num"]).sum())
    _check(viol <= v["max_violacoes_defasagem"],
           f"{viol} violacoes de defasagem = fase - fase_ideal "
           f"(tolerado: {v['max_violacoes_defasagem']})", avisos, estrito)

    # Faixas — pega erro de escala e de parser numerico
    lo, hi = v["faixa_indicadores"]
    for c in INDICADORES:
        s = painel[c].dropna()
        if s.empty:
            continue
        fora = int(((s < lo) | (s > hi)).sum())
        _check(fora == 0,
               f"{c}: {fora} valores fora de [{lo}, {hi}] "
               f"(min={s.min():.2f}, max={s.max():.2f})", avisos, estrito)

    lo, hi = v["faixa_inde"]
    s = painel["inde"].dropna()
    fora = int(((s < lo) | (s > hi)).sum())
    _check(fora == 0,
           f"inde: {fora} fora de [{lo}, {hi}] (max={s.max():.2f})",
           avisos, estrito)

    # Cobertura declarada — confere se a coluna some onde deveria
    for col, anos_ok in cfg["dados"]["cobertura_parcial"].items():
        if col not in painel.columns:
            continue
        cob = painel.groupby("ano")[col].count()
        inesperado = [a for a in cob.index if a not in anos_ok and cob[a] > 0]
        _check(not inesperado,
               f"{col}: dado em ano nao declarado {inesperado}", avisos, estrito)

    return avisos


def validar_transicoes(trans: pd.DataFrame, estrito: bool = True) -> list[str]:
    """Invariantes da tabela de transicoes."""
    avisos: list[str] = []

    dup = trans.duplicated(["ra", "ano"]).sum()
    _check(dup == 0, f"{dup} transicoes duplicadas", avisos, estrito)

    # Nada de t+1 alem do que foi trazido de proposito
    permitidas = {"defasagem_t1", "ida_t1", "inde_t1"}
    vazando = {c for c in trans.columns if c.endswith("_t1")} - permitidas
    _check(not vazando, f"colunas de t+1 nao autorizadas: {vazando}", avisos, estrito)

    # Alvo coerente com a definicao
    esperado = (trans["defasagem_t1"] < trans["defasagem"]).astype(int)
    inc = int((trans["alvo_piora"] != esperado).sum())
    _check(inc == 0, f"{inc} alvos inconsistentes", avisos, estrito)

    # Base rate estavel: e o que sustenta o split temporal
    tx = trans.groupby("janela")["alvo_piora"].mean()
    _check(tx.max() - tx.min() < 0.05,
           f"base rate divergente entre janelas: {tx.round(3).to_dict()}",
           avisos, estrito)

    return avisos


def resumo_carga(painel: pd.DataFrame, trans: pd.DataFrame) -> pd.DataFrame:
    """Linha por ano com os numeros que a gente confere toda vez."""
    r = painel.groupby("ano").agg(
        alunos=("ra", "nunique"),
        sem_avaliacao=("sem_avaliacao", "sum"),
        inde_nulo=("inde", lambda s: int(s.isna().sum())),
        defasagem_media=("defasagem", "mean"),
    ).round(2)
    t = trans.groupby("janela").agg(
        transicoes=("ra", "size"),
        eventos=("alvo_piora", "sum"),
        base_rate=("alvo_piora", "mean"),
    ).round(3)
    return r, t
