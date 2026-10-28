"""Monthly forecasting: baselines vs. models, temporal back-test (3/6/12-month folds), public `forecast()` API.

Only 24 months exist, so back-test folds are expanding-window and tiny; every result must be read with that caveat:
  fold 3m : train 2024-01..2025-09 -> test 2025-10..12
  fold 6m : train 2024-01..2025-06 -> test 2025-07..12
  fold 12m: train 2024-01..2024-12 -> test 2025-01..12   (the only fold with a full unseen annual cycle)
"""
from __future__ import annotations
import warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

warnings.filterwarnings("ignore")
FOLDS = {"3m": ("2025-09-01", 3), "6m": ("2025-06-01", 6), "12m": ("2024-12-01", 12)}  # last train month, horizon
BASELINES = {"last_value", "ma3", "snaive12", "snaive12_growth"}


# ----------------------------------------------------------------------------- feature helpers
def _fourier(months: pd.DatetimeIndex, K=2) -> pd.DataFrame:
    m = months.month.values / 12.0
    return pd.DataFrame({f"{f}{k}": getattr(np, f)(2 * np.pi * k * m) for k in range(1, K + 1) for f in ("sin", "cos")},
                        index=months)


def _X(cal: pd.DataFrame, months: pd.DatetimeIndex, egypt: bool) -> pd.DataFrame:
    X = _fourier(months)
    X["t"] = cal.loc[months, "t"].values / 12.0
    if egypt:
        c = cal.loc[months]
        X["ramadan"] = c.ramadan_share.values
        X["eid"] = c.eid_days.values / 30.0
        X["working"] = c.working_share.values
    return X


# ----------------------------------------------------------------------------- models: f(train, future_months, cal) -> Series
def m_last(train, fm, cal):
    """Baseline: last observed value held flat."""
    return pd.Series(train.iloc[-1], index=fm)


def m_ma3(train, fm, cal):
    """Baseline: mean of last 3 months."""
    return pd.Series(train.iloc[-3:].mean(), index=fm)


def _lag12(train, fm):
    v = []
    for m in fm:
        src = m - pd.DateOffset(years=1)
        while src not in train.index and src + pd.DateOffset(years=1) <= m and src < train.index.max():
            src += pd.DateOffset(years=1)
        v.append(train.get(src, np.nan))
    return np.array(v, dtype=float)


def m_snaive12(train, fm, cal):
    """Baseline: same calendar month last year (seasonal naive, 12-month lag)."""
    v = _lag12(train, fm)
    return pd.Series(np.where(np.isnan(v), train.iloc[-12:].mean(), v), index=fm)


def m_snaive12_growth(train, fm, cal):
    """Baseline: seasonal naive x recent year-over-year growth (needs >= 15 months, else growth = 1)."""
    k = min(12, len(train) - 12)
    g = 1.0
    if k >= 3:
        recent, prior = train.iloc[-k:].sum(), train.iloc[-k - 12:-12].sum()
        g = recent / prior if prior > 0 else 1.0
    return m_snaive12(train, fm, cal) * float(np.clip(g, 0.5, 2.0))


def _ridge(train, fm, cal, egypt):
    ytr = np.log1p(train.values.astype(float))
    mdl = make_pipeline(StandardScaler(), Ridge(alpha=3.0)).fit(_X(cal, train.index, egypt), ytr)
    return pd.Series(np.expm1(mdl.predict(_X(cal, fm, egypt))), index=fm)


def m_ridge_fourier(train, fm, cal):
    """Model: log-ridge on trend + annual Fourier terms (generic seasonality)."""
    return _ridge(train, fm, cal, egypt=False)


def m_ridge_egypt(train, fm, cal):
    """Model: log-ridge on trend + annual Fourier + Ramadan share + Eid days + working-day share (Egyptian calendar)."""
    return _ridge(train, fm, cal, egypt=True)


MODELS = {"last_value": m_last, "ma3": m_ma3, "snaive12": m_snaive12, "snaive12_growth": m_snaive12_growth,
          "ridge_fourier": m_ridge_fourier, "ridge_egypt": m_ridge_egypt}


# ----------------------------------------------------------------------------- metrics
def _metrics(y, p, train) -> dict:
    e = y - p
    scale = train.diff().abs().mean()  # naive one-step MAE in training data (MASE scale)
    return {"MAE": e.abs().mean(), "RMSE": float(np.sqrt((e ** 2).mean())),
            "MAPE_%": 100 * (e.abs() / y.replace(0, np.nan)).mean(), "WAPE_%": 100 * e.abs().sum() / max(y.abs().sum(), 1e-9),
            "MASE": e.abs().mean() / scale if scale and scale > 0 else np.nan, "Bias_%": 100 * e.sum() / max(y.sum(), 1e-9),
            "MaxAPE_%": 100 * (e.abs() / y.replace(0, np.nan)).max()}


def backtest(df: pd.DataFrame, cal: pd.DataFrame, targets=None):
    targets = targets or list(df.columns)
    rows, preds = [], []
    for tg in targets:
        for fold, (end, h) in FOLDS.items():
            train = df[tg].loc[:end]
            fm = pd.date_range(pd.Timestamp(end) + pd.offsets.MonthBegin(1), periods=h, freq="MS")
            test = df[tg].reindex(fm)
            for name, f in MODELS.items():
                p = f(train, fm, cal).clip(lower=0)
                rows.append({"target": tg, "fold": fold, "model": name, "kind": "baseline" if name in BASELINES else "model",
                             "n_train": len(train), **_metrics(test, p, train)})
                preds.append(pd.DataFrame({"Month": fm, "target": tg, "fold": fold, "model": name, "actual": test.values, "pred": p.values}))
    return pd.DataFrame(rows), pd.concat(preds, ignore_index=True)


def select_best(m: pd.DataFrame) -> dict:
    """Per target & fold: lowest MAPE among all candidates; records the best baseline and whether the best model beats it."""
    sel = {}
    for (tg, fold), g in m.groupby(["target", "fold"]):
        g = g.sort_values("MAPE_%")
        b, bb = g.iloc[0], g[g.kind == "baseline"].iloc[0]
        bm = g[g.kind == "model"].iloc[0]
        sel.setdefault(tg, {})[fold] = {
            "model": b.model, "mape": round(float(b["MAPE_%"]), 2), "best_baseline": bb.model,
            "baseline_mape": round(float(bb["MAPE_%"]), 2), "best_ml_model": bm.model, "ml_mape": round(float(bm["MAPE_%"]), 2),
            "ml_beats_baseline": bool(bm["MAPE_%"] < bb["MAPE_%"]),
            "usable": bool(b["MAPE_%"] <= 25.0)}
    return sel


# ----------------------------------------------------------------------------- public API
def forecast(df: pd.DataFrame, target: str, horizon_months: int, cal: pd.DataFrame, model: str = "auto",
             selection: dict | None = None, backtest_preds: pd.DataFrame | None = None) -> pd.DataFrame:
    """Forecast `target` for `horizon_months` (1..12) after the last month in `df`.

    model='auto' uses the back-test winner of the fold matching the horizon (<=3 -> 3m, <=6 -> 6m, else 12m).
    Returns DataFrame[Month, yhat, lo, hi, model, horizon_fold, mape_backtest, ml_beats_baseline, usable].
    lo/hi are an empirical envelope: yhat x (1 +/- max monthly APE seen in the matching back-test fold) - indicative only.
    """
    fold = "3m" if horizon_months <= 3 else ("6m" if horizon_months <= 6 else "12m")
    info = (selection or {}).get(target, {}).get(fold, {})
    name = info.get("model", "snaive12_growth") if model == "auto" else model
    y = df[target].dropna()
    fm = pd.date_range(y.index.max() + pd.offsets.MonthBegin(1), periods=horizon_months, freq="MS")
    yhat = MODELS[name](y, fm, cal).clip(lower=0)
    env = 0.15
    if backtest_preds is not None:
        b = backtest_preds[(backtest_preds.target == target) & (backtest_preds.fold == fold) & (backtest_preds.model == name)]
        if len(b):
            env = float(((b.actual - b.pred).abs() / b.actual.replace(0, np.nan)).max())
    out = pd.DataFrame({"Month": fm, "yhat": yhat.values, "lo": yhat.values * (1 - env), "hi": yhat.values * (1 + env)})
    out["model"], out["horizon_fold"] = name, fold
    out["mape_backtest"] = info.get("mape", np.nan)
    out["ml_beats_baseline"] = info.get("ml_beats_baseline", np.nan)
    out["usable"] = info.get("usable", np.nan)
    return out
