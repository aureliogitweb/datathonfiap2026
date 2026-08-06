"""Avaliacao do modelo de risco.

Metrica primaria: PR-AUC. Com 17.3% de positivos, ROC-AUC infla e da
falsa sensacao de desempenho.

Tudo com IC bootstrap: 104 eventos no treino e 132 no teste produzem
intervalos largos, e diferenca de 0.02 entre modelos nao significa nada.
Reportar ponto sem intervalo aqui seria enganoso.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (average_precision_score, brier_score_loss,
                             roc_auc_score)


def pr_auc_ic(y, p, n_boot: int = 2000, seed: int = 42) -> tuple:
    """PR-AUC com IC95 por bootstrap estratificado."""
    y, p = np.asarray(y), np.asarray(p)
    obs = average_precision_score(y, p)
    rng = np.random.default_rng(seed)
    ipos, ineg = np.where(y == 1)[0], np.where(y == 0)[0]
    vals = []
    for _ in range(n_boot):
        idx = np.r_[rng.choice(ipos, len(ipos), True),
                    rng.choice(ineg, len(ineg), True)]
        vals.append(average_precision_score(y[idx], p[idx]))
    return obs, float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def recall_at_k(y, p, k: int) -> float:
    """Dos k alunos de maior risco, que fracao dos casos reais capturamos?

    E a metrica que a ONG usa: ninguem atende 765 alunos.
    """
    y, p = np.asarray(y), np.asarray(p)
    if y.sum() == 0:
        return np.nan
    top = np.argsort(-p)[:k]
    return float(y[top].sum() / y.sum())


def calibracao(y, p, n_bins: int = 5) -> pd.DataFrame:
    """Predito vs observado por bin. Desvio grande => probabilidade nao confiavel."""
    y, p = np.asarray(y), np.asarray(p)
    q = pd.qcut(pd.Series(p), n_bins, labels=False, duplicates="drop")
    d = pd.DataFrame({"y": y, "p": p, "bin": q})
    g = d.groupby("bin").agg(n=("y", "size"), predito=("p", "mean"),
                             observado=("y", "mean"))
    g["desvio"] = (g["predito"] - g["observado"]).abs()
    return g.round(3)


def avaliar(modelos: dict, X, y, estrato: pd.Series,
            ks: tuple = (50, 100)) -> pd.DataFrame:
    """Tabela comparativa no conjunto de teste."""
    linhas = []
    for nome, info in modelos.items():
        m = info["modelo"]
        Xp = X.fillna(X.median()) if nome == "baseline_fase" else X
        p = m.predict_proba(Xp)[:, 1]
        obs, lo, hi = pr_auc_ic(y, p)
        r = {"modelo": nome, "pr_auc": round(obs, 3),
             "ic95": f"[{lo:.3f}, {hi:.3f}]",
             "roc_auc": round(roc_auc_score(y, p), 3),
             "brier": round(brier_score_loss(y, p), 4)}
        for k in ks:
            r[f"recall@{k}"] = round(recall_at_k(y, p, k), 3)
        # Por estrato: modelo bom no agregado pode ser inutil dentro do grupo.
        for e in sorted(estrato.unique()):
            m_e = (estrato == e).values
            if y[m_e].sum() >= 5:
                r[f"pr_auc_{e}"] = round(
                    average_precision_score(y[m_e], p[m_e]), 3)
        linhas.append(r)
    return pd.DataFrame(linhas).sort_values("pr_auc", ascending=False)


def teste_delong_aprox(y, p1, p2, n_boot: int = 2000, seed: int = 42) -> dict:
    """Diferenca de PR-AUC entre dois modelos, com IC bootstrap pareado.

    Pareado no mesmo reamostrado: e a diferenca que interessa, nao os
    intervalos individuais, que se sobrepoem quase sempre com este n.
    """
    y, p1, p2 = np.asarray(y), np.asarray(p1), np.asarray(p2)
    rng = np.random.default_rng(seed)
    difs = []
    ipos, ineg = np.where(y == 1)[0], np.where(y == 0)[0]
    for _ in range(n_boot):
        idx = np.r_[rng.choice(ipos, len(ipos), True),
                    rng.choice(ineg, len(ineg), True)]
        difs.append(average_precision_score(y[idx], p1[idx])
                    - average_precision_score(y[idx], p2[idx]))
    difs = np.array(difs)
    return {"dif_media": float(difs.mean()),
            "ic95": (float(np.percentile(difs, 2.5)),
                     float(np.percentile(difs, 97.5))),
            "p_aprox": float(2 * min((difs <= 0).mean(), (difs >= 0).mean()))}
