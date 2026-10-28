"""Anomaly detection (P3-04): sales drops, cost overruns, construction delays, inventory spikes, collection drops.

Principles
  * Label-free detectors with thresholds fixed BEFORE looking at ground truth (p<0.01 / robust z >= 3.5 / ratio<0.3).
  * `Anomaly_Ground_Truth` is used only inside `evaluate()`.
  * Seasonality (Ramadan, Eid, summer, weekends) is removed by comparing each entity with the CITY index of the same
    month, so a Ramadan dip is not reported as an anomaly.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.stats import poisson

Z_THR = 3.5


def robust_z(s: pd.Series) -> pd.Series:
    med = s.median()
    mad = (s - med).abs().median()
    scale = 1.4826 * mad if mad > 0 else (s.std(ddof=0) or 1.0)
    return (s - med) / scale


def _persist(flag: pd.Series, run: int = 2) -> pd.Series:
    ok = flag.astype(int).rolling(run, min_periods=run).sum() == run
    out = ok.copy()
    for k in range(1, run):
        out |= ok.shift(-k, fill_value=False)
    return out


# ----------------------------------------------------------------------------- 1. sales drop
def detect_sales_drop(t) -> pd.DataFrame:
    """Poisson lower-tail test: sales in the last 3 months vs. what the project's own previous 6 months imply, after
    adjusting for the city seasonal index. Exposure = units on the market."""
    inv = t["Fact_Inventory_Monthly"].sort_values(["Project_ID", "Month"]).copy()
    inv["exposure"] = inv.Available_Start + 0.5 * inv.Units_Released
    city = inv.groupby("Month").agg(s=("Units_Sold", "sum"), e=("exposure", "sum"))
    city["rate"] = city.s / city.e
    city["season"] = city.rate / city.rate.mean()          # city seasonal index (includes Ramadan / summer / launch effects)
    inv = inv.merge(city[["season"]], left_on="Month", right_index=True)
    rows = []
    months = sorted(inv.Month.unique())
    for pid, g in inv.groupby("Project_ID"):
        g = g.set_index("Month")
        for i, m in enumerate(months):
            if i < 8:
                continue
            win, base = months[i - 2:i + 1], months[i - 8:i - 2]
            e_w = (g.loc[win, "exposure"] * g.loc[win, "season"]).sum()
            e_b = (g.loc[base, "exposure"] * g.loc[base, "season"]).sum()
            if e_b < 50 or e_w < 20:                       # not enough units on the market to test
                rows.append((pid, m, np.nan, np.nan, np.nan, False)); continue
            lam = g.loc[base, "Units_Sold"].sum() / e_b
            exp = lam * e_w
            obs = g.loc[win, "Units_Sold"].sum()
            p = float(poisson.cdf(obs, exp))
            rows.append((pid, m, obs, exp, p, bool(exp >= 5 and p < 0.01)))
    d = pd.DataFrame(rows, columns=["Entity_ID", "Period_Start", "observed_3m", "expected_3m", "p_value", "flag"])
    d["score"] = -np.log10(d.p_value.clip(lower=1e-12))
    d["detector_type"] = "sales_drop"
    return d


# ----------------------------------------------------------------------------- 2. cost overrun
def detect_cost_overrun(t) -> pd.DataFrame:
    """Unit-cost index = (actual cost / actual progress) / (planned cost / planned progress), compared across projects in the
    same month (robust z). Stalled months (progress < 50% of plan) are excluded - they belong to the delay detector."""
    c = t["Fact_Construction_Monthly"].sort_values(["Project_ID", "Month"]).copy()
    c["d_plan"] = c.groupby("Project_ID").Planned_Pct.diff()
    c["d_act"] = c.groupby("Project_ID").Actual_Pct.diff()
    c = c[(c.d_plan > 0.3) & (c.Planned_Cost_EGP > 0) & (c.d_act >= 0.5 * c.d_plan)].copy()
    c["cost_index"] = (c.Actual_Cost_EGP / c.d_act) / (c.Planned_Cost_EGP / c.d_plan)
    c["score"] = c.groupby("Month").cost_index.transform(lambda s: robust_z(np.log(s)) if len(s) >= 5 else np.nan)
    c = c.sort_values(["Project_ID", "Month"])
    c["flag"] = c.groupby("Project_ID").score.transform(lambda s: s >= Z_THR)
    c["detector_type"] = "cost_overrun"
    return c.rename(columns={"Project_ID": "Entity_ID", "Month": "Period_Start"})[
        ["Entity_ID", "Period_Start", "cost_index", "score", "flag", "detector_type"]]


# ----------------------------------------------------------------------------- 3. construction delay
def detect_construction_delay(t) -> pd.DataFrame:
    """Business rule: progress speed (actual / planned monthly increment) below 0.30 for 2 consecutive months."""
    c = t["Fact_Construction_Monthly"].sort_values(["Project_ID", "Month"]).copy()
    c["d_plan"] = c.groupby("Project_ID").Planned_Pct.diff()
    c["d_act"] = c.groupby("Project_ID").Actual_Pct.diff()
    c = c[c.d_plan > 0.3].copy()
    c["speed"] = c.d_act / c.d_plan
    c["score"] = 1 - c.speed
    c["flag"] = c.groupby("Project_ID").speed.transform(lambda s: _persist(s < 0.30))
    c["detector_type"] = "construction_delay"
    return c.rename(columns={"Project_ID": "Entity_ID", "Month": "Period_Start"})[
        ["Entity_ID", "Period_Start", "speed", "score", "flag", "detector_type"]]


# ----------------------------------------------------------------------------- 4. inventory spike
def detect_inventory_spike(t) -> pd.DataFrame:
    """Net inventory increase of a project in a month (End - Start), robust z against all project-months."""
    inv = t["Fact_Inventory_Monthly"].copy()
    inv["delta"] = inv.Available_End - inv.Available_Start
    inv["rel_delta"] = inv.delta / inv.Available_Start.clip(lower=20)
    z = robust_z(inv.rel_delta)
    inv["score"] = z
    inv["flag"] = (z >= 6.0) & (inv.delta >= 25)
    inv["detector_type"] = "inventory_spike"
    return inv.rename(columns={"Project_ID": "Entity_ID", "Month": "Period_Start"})[
        ["Entity_ID", "Period_Start", "delta", "score", "flag", "detector_type"]]


# ----------------------------------------------------------------------------- 5. collections drop
def detect_collections_drop(t) -> pd.DataFrame:
    """District collection rate (collected / due) relative to the city rate of the same month (removes Ramadan/Eid
    effects), compared with the district's own previous 6 months; robust z pooled over districts; 2 consecutive months."""
    c = t["Fact_Collections_Monthly"].copy()
    d = c.groupby(["District_ID", "Month"]).agg(due=("Amount_Due_EGP", "sum"), col=("Amount_Collected_EGP", "sum")).reset_index()
    city = c.groupby("Month").agg(due=("Amount_Due_EGP", "sum"), col=("Amount_Collected_EGP", "sum"))
    city["crate"] = city.col / city.due
    d = d.merge(city[["crate"]], left_on="Month", right_index=True).sort_values(["District_ID", "Month"])
    d["rel"] = np.log((d.col / d.due.clip(lower=1)).clip(lower=1e-3) / d.crate)
    d["base"] = d.groupby("District_ID").rel.transform(lambda s: s.shift(1).rolling(6, min_periods=4).median())
    d["resid"] = d.rel - d.base
    ok = d.resid.notna()
    d["score"] = np.nan
    d.loc[ok, "score"] = robust_z(d.loc[ok, "resid"])
    d["flag"] = d.groupby("District_ID").score.transform(lambda s: _persist(s <= -Z_THR))
    d["detector_type"] = "collections_drop"
    return d.rename(columns={"District_ID": "Entity_ID", "Month": "Period_Start"})[
        ["Entity_ID", "Period_Start", "rel", "score", "flag", "detector_type"]]


# ----------------------------------------------------------------------------- evaluation
LABEL_TO_DET = {"sales_drop": "sales_drop", "cost_overrun": "cost_overrun", "construction_delay": "construction_delay",
                "inventory_spike": "inventory_spike", "collections_drop": "collections_drop"}


def evaluate(det: pd.DataFrame, truth: pd.DataFrame, label: str) -> dict:
    """Entity-level and entity-month-level precision / recall / F1 + detection delay (months after event start)."""
    d = det[det.detector_type == LABEL_TO_DET[label]].copy()
    tr = truth[truth.Ground_Truth_Label == label]
    d["end"] = d.Period_Start + pd.offsets.MonthEnd(0)
    d["y"] = False
    for _, ev in tr.iterrows():
        d.loc[(d.Entity_ID == ev.Entity_ID) & (d.end >= ev.Start_Date) & (d.Period_Start <= ev.End_Date), "y"] = True
    d["pred"] = d.flag.fillna(False).astype(bool)
    def prf(y, p):
        tp, fp, fn = int((y & p).sum()), int((~y & p).sum()), int((y & ~p).sum())
        pr, rc = tp / (tp + fp) if tp + fp else 0.0, tp / (tp + fn) if tp + fn else 0.0
        return tp, fp, fn, pr, rc, 2 * pr * rc / (pr + rc) if pr + rc else 0.0
    ent = d.groupby("Entity_ID").agg(y=("y", "any"), pred=("pred", "any"))
    e = prf(ent.y, ent.pred)
    p = prf(d.y, d.pred)
    delays = []
    for _, ev in tr.iterrows():
        f = d[(d.Entity_ID == ev.Entity_ID) & d.pred & (d.end >= ev.Start_Date)]
        if len(f):
            delays.append((f.Period_Start.min().to_period("M") - ev.Start_Date.to_period("M")).n)
    return {"event_label": label, "n_true_entities": int(ent.y.sum()), "n_entities_tested": len(ent),
            "entity_TP": e[0], "entity_FP": e[1], "entity_FN": e[2], "entity_precision": round(e[3], 3),
            "entity_recall": round(e[4], 3), "entity_F1": round(e[5], 3), "month_TP": p[0], "month_FP": p[1], "month_FN": p[2],
            "month_precision": round(p[3], 3), "month_recall": round(p[4], 3), "month_F1": round(p[5], 3),
            "mean_detection_delay_months": float(np.mean(delays)) if delays else np.nan}


def run_all(t):
    det = pd.concat([detect_sales_drop(t), detect_cost_overrun(t), detect_construction_delay(t),
                     detect_inventory_spike(t), detect_collections_drop(t)], ignore_index=True)
    ev = pd.DataFrame([evaluate(det, t["Anomaly_Ground_Truth"], l) for l in LABEL_TO_DET])
    return det, ev
