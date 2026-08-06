"""EDA tecnica: propriedades dos dados que decidem a modelagem.

Nao responde as perguntas do briefing (isso e 6.5). Aqui so o que muda
decisao tecnica: drift, colinearidade, shift entre janelas, fluxo do painel.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

# Recuperados por regressao (R2 = 1.000000 em 2024). O dicionario oficial
# lista os componentes mas nao informa a ponderacao.
PESOS_INDE = {"iaa": .10, "ieg": .20, "ips": .10, "ipp": .10,
              "ida": .20, "ipv": .20, "ian": .10}


def coorte_fechada(painel: pd.DataFrame, cols: list[str]) -> pd.Index:
    """Alunos presentes em todos os anos com os indicadores dados."""
    w = painel.pivot_table(index="ra", columns="ano", values=cols)
    return w.dropna().index


def testar_drift(painel: pd.DataFrame, cols: list[str],
                 amp_min: float = 0.5) -> pd.DataFrame:
    """Friedman na coorte fechada + classificacao pelo FORMATO da mudanca.

    A assinatura de drift de instrumento nao e a magnitude, e o padrao em V
    ou pico: cair e voltar. Mudanca real tende a ser monotonica. Por isso
    'defasagem' (-1, -1, 0) e melhora e 'ips' (7.5, 5.0, 7.5) e instrumento,
    apesar de amplitudes parecidas.
    """
    linhas = []
    for c in cols:
        m = painel.pivot_table(index="ra", columns="ano", values=c).dropna()
        if len(m) < 30:
            continue
        anos = sorted(m.columns)
        fr = stats.friedmanchisquare(*[m[a] for a in anos])
        med = m.median()
        amp = float(med.max() - med.min())
        d = np.diff(med.values)
        monotonico = bool(np.all(d >= -1e-9) or np.all(d <= 1e-9))
        if amp < amp_min:
            v = "estavel"
        elif monotonico:
            v = "MUDANCA REAL (monotonica)"
        else:
            v = "DRIFT (padrao em V)"
        linhas.append({"indicador": c, "n": len(m),
                       **{f"med_{a}": round(med[a], 2) for a in anos},
                       "amplitude": round(amp, 2),
                       "p_friedman": fr.pvalue, "veredito": v})
    return pd.DataFrame(linhas)


def recuperar_pesos_inde(painel: pd.DataFrame, ano: int) -> tuple[dict, float]:
    """Regride INDE nos componentes. R2 ~ 1 => coeficientes SAO os pesos."""
    ind = list(PESOS_INDE)
    d = painel[painel["ano"] == ano].dropna(subset=ind + ["inde"])
    A = np.c_[d[ind].values, np.ones(len(d))]
    coef, *_ = np.linalg.lstsq(A, d["inde"].values, rcond=None)
    pred = A @ coef
    y = d["inde"].values
    r2 = 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return dict(zip(ind + ["const"], np.round(coef, 4))), float(r2)


def contribuicao_inde(painel: pd.DataFrame, ano: int) -> pd.DataFrame:
    """Peso x dispersao. Responde a pergunta 8 sem cair na tautologia.

    O que move o INDE nao e o maior peso, e peso x variabilidade: um
    indicador com peso alto e todo mundo no mesmo valor nao move nada.
    """
    d = painel[painel["ano"] == ano]
    r = pd.DataFrame([{"indicador": k, "peso": v, "dp": d[k].std(),
                       "contrib": v * d[k].std()}
                      for k, v in PESOS_INDE.items()])
    r["pct_variancia"] = 100 * r["contrib"] / r["contrib"].sum()
    return r.sort_values("contrib", ascending=False).round(3)


def vif(X: pd.DataFrame) -> pd.DataFrame:
    """VIF via inversa da matriz de correlacao. >5 pede atencao, >10 e grave."""
    Z = X.fillna(X.median())
    Z = (Z - Z.mean()) / Z.std().replace(0, 1)
    v = np.diag(np.linalg.pinv(np.corrcoef(Z.values.T)))
    return (pd.DataFrame({"feature": X.columns, "VIF": np.round(v, 2)})
            .sort_values("VIF", ascending=False))


def covariate_shift(X: pd.DataFrame, mask_treino: np.ndarray) -> pd.DataFrame:
    """KS entre janelas. KS alto = degradacao out-of-time com causa conhecida."""
    linhas = []
    for c in X.columns:
        a, b = X.loc[mask_treino, c].dropna(), X.loc[~mask_treino, c].dropna()
        if a.nunique() < 2 or len(b) < 10:
            continue
        ks = stats.ks_2samp(a, b)
        linhas.append({"feature": c, "media_treino": round(a.mean(), 3),
                       "media_teste": round(b.mean(), 3),
                       "KS": round(ks.statistic, 3), "p": ks.pvalue,
                       "alerta": "SHIFT" if ks.statistic > 0.2 else ""})
    return pd.DataFrame(linhas).sort_values("KS", ascending=False)


def fluxo_painel(painel: pd.DataFrame) -> pd.DataFrame:
    """Entradas, saidas e permanencias. Base do vies de sobrevivencia."""
    anos = sorted(painel["ano"].unique())
    s = {a: set(painel.loc[painel["ano"] == a, "ra"]) for a in anos}
    linhas = []
    for a, b in zip(anos, anos[1:]):
        sai = len(s[a] - s[b])
        linhas.append({"transicao": f"{a}->{b}", "base_inicial": len(s[a]),
                       "permanecem": len(s[a] & s[b]), "saem": sai,
                       "taxa_saida": round(sai / len(s[a]), 3),
                       "entram": len(s[b] - s[a])})
    return pd.DataFrame(linhas)
