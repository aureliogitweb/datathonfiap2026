"""Modelagem do risco de agravamento de defasagem.

Alvo: defasagem(t+1) < defasagem(t). Treino 2022->2023, teste out-of-time
2023->2024. GroupKFold por RA no tuning — 468 alunos aparecem nas duas
janelas e split ingenuo vazaria individuo entre folds.

Grids deliberadamente pequenos: com 104 eventos no treino, busca ampla
seleciona a combinacao que melhor se ajusta ao ruido da validacao. O
overfit aqui mora no processo de selecao, nao no ajuste.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

try:
    from lightgbm import LGBMClassifier
    from xgboost import XGBClassifier
    BOOSTING = True
except ImportError:
    BOOSTING = False


class BaselineFase(BaseEstimator, ClassifierMixin):
    """Regra trivial: fase ideal <= 1 => risco alto.

    Adversario serio, nao formalidade: AUC univariado 0.694. Se o modelo
    nao superar isso, o fenomeno e estrutural e a recomendacao muda.
    """

    def __init__(self, col: int = 0, corte: float = 1.0):
        self.col, self.corte = col, corte

    def fit(self, X, y):
        Xa = np.asarray(X)
        m = Xa[:, self.col] <= self.corte
        y = np.asarray(y)
        # Probabilidade = taxa observada em cada lado da regra.
        self.p_alto_ = y[m].mean() if m.any() else 0.5
        self.p_baixo_ = y[~m].mean() if (~m).any() else 0.5
        self.classes_ = np.array([0, 1])
        return self

    def predict_proba(self, X):
        Xa = np.asarray(X)
        p = np.where(Xa[:, self.col] <= self.corte, self.p_alto_, self.p_baixo_)
        return np.c_[1 - p, p]

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] > 0.5).astype(int)


def _imputador():
    """Mediana + indicador de ausencia.

    O indicador nao e opcional: iaa_pct tem 3.2% de nulos no treino contra
    25.6% no teste (heranca da limpeza dos zeros sentinela do IAA), e essa
    ausencia carrega sinal.
    """
    return SimpleImputer(strategy="median", add_indicator=True)


def catalogo(seed: int = 42) -> dict[str, tuple]:
    """(pipeline, grid) por modelo. Grids pequenos por decisao."""
    c: dict[str, tuple] = {}

    c["logistica"] = (
        Pipeline([("imp", _imputador()), ("sc", StandardScaler()),
                  # SEM class_weight: reponderar p/ 50/50 destroi a
                  # calibracao (predizia 0.84 onde observava 0.46) e a
                  # probabilidade e requisito do briefing, nao o ranking.
                  ("clf", LogisticRegression(max_iter=2000,
                                             random_state=seed))]),
        {"clf__C": [0.01, 0.05, 0.1, 0.5, 1.0]},
    )

    c["arvore"] = (
        Pipeline([("imp", _imputador()),
                  ("clf", DecisionTreeClassifier(random_state=seed))]),
        {"clf__max_depth": [2, 3, 4], "clf__min_samples_leaf": [20, 40]},
    )

    c["random_forest"] = (
        Pipeline([("imp", _imputador()),
                  ("clf", RandomForestClassifier(n_estimators=400,
                                                 random_state=seed, n_jobs=-1))]),
        {"clf__max_depth": [3, 5], "clf__min_samples_leaf": [10, 20]},
    )

    if BOOSTING:
        # Boosting recebe dados crus: missing e tratado nativamente.
        c["xgboost"] = (
            Pipeline([("clf", XGBClassifier(
                n_estimators=200, learning_rate=0.05, random_state=seed,
                eval_metric="logloss", n_jobs=-1))]),
            {"clf__max_depth": [2, 3], "clf__min_child_weight": [5, 10],
             "clf__reg_lambda": [1.0, 5.0]},
        )
        c["lightgbm"] = (
            Pipeline([("clf", LGBMClassifier(
                n_estimators=200, learning_rate=0.05, random_state=seed,
                verbose=-1, n_jobs=-1))]),
            {"clf__max_depth": [2, 3], "clf__min_child_samples": [20, 40],
             "clf__reg_lambda": [1.0, 5.0]},
        )
    return c


def treinar(X: pd.DataFrame, y: pd.Series, grupos: pd.Series,
            seed: int = 42, n_splits: int = 5) -> dict:
    """Tuning por GroupKFold otimizando PR-AUC. Devolve melhor estimador."""
    cv = GroupKFold(n_splits=n_splits)
    out = {}
    for nome, (pipe, grid) in catalogo(seed).items():
        gs = GridSearchCV(pipe, grid, scoring="average_precision",
                          cv=cv, n_jobs=-1, refit=True)
        gs.fit(X, y, groups=grupos)
        out[nome] = {"modelo": gs.best_estimator_,
                     "params": gs.best_params_,
                     "pr_auc_cv": gs.best_score_}
    # Baseline: fase_ideal_num precisa ser a primeira coluna.
    bl = BaselineFase(col=list(X.columns).index("fase_ideal_num"))
    bl.fit(X.fillna(X.median()), y)
    out["baseline_fase"] = {"modelo": bl, "params": {"regra": "fase_ideal<=1"},
                            "pr_auc_cv": np.nan}
    return out
