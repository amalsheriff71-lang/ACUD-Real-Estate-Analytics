"""Unit-level 90-day unsold-risk model (P3-05).

Question answered at an as-of date a for every unit that is on the market (released, not actively sold):
    "Will this unit still be unsold 90 days later?"   y = 1 if no sale occurs in (a, a + 90 days].
Only information available at a is used. Calendar features describing the NEXT 90 days (Ramadan/Eid/working days) are
legitimate because those dates are known in advance. Evaluation uses a purged temporal split.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

H = 90
NUM = ["area_m2", "price_premium", "plan_years", "down_pct", "listing_age", "completion", "schedule_lag", "handover",
       "svc_coverage", "svc_gaps", "occupancy", "proj_sold_90d", "proj_avail", "proj_rate_90d", "dist_avail_log",
       "dev_quality", "fut_ramadan_days", "fut_eid_days", "fut_working_days", "fut_launch_days", "fut_summer_days",
       "sin_m", "cos_m", "price_index"]
TYPES = ["Apartment", "Townhouse", "Villa", "Commercial", "Office"]
FEATURES = NUM + [f"type_{x}" for x in TYPES]
SPLIT = {"train": ("2024-03-01", "2025-01-01"), "test": ("2025-04-02", "2025-10-01")}  # as-of ranges, label windows purged


class Context:
    """Pre-computed lookups so that scoring many as-of dates is fast."""
    def __init__(self, t):
        self.u = t["Dim_Unit"].merge(t["Dim_Project"][["Project_ID", "Developer_ID"]], on="Project_ID") \
            .merge(t["Dim_Developer"][["Developer_ID", "Quality_Index"]], on="Developer_ID")
        bench = self.u.groupby("Unit_Type").Price_per_m2_Jan2024.median()
        self.u["price_premium"] = self.u.Price_per_m2_Jan2024 / self.u.Unit_Type.map(bench) - 1
        self.sales = t["Fact_Sales"].sort_values("Sale_Date")
        self.cons = t["Fact_Construction_Monthly"].copy()
        self.cons["lag"] = self.cons.Planned_Pct - self.cons.Actual_Pct
        self.st = t["Fact_District_Monthly_Status"]
        self.cal = t["Dim_Date"].set_index("Date")
        self.pidx = {pd.Timestamp(m): v for m, v in zip(t["Dim_Price_Index"].Month, t["Dim_Price_Index"].Price_Index)}
        self.dist_of = self.u.drop_duplicates("Project_ID").set_index("Project_ID").District_ID

    def state(self, a: pd.Timestamp):
        """Units on the market at `a` and their listing start (release, or last cancellation before a)."""
        u, s = self.u, self.sales
        done = s[s.Sale_Date <= a]
        active = done[done.Cancel_Date.isna() | (done.Cancel_Date > a)].Unit_ID
        canc = done[done.Cancel_Date.notna() & (done.Cancel_Date <= a)].groupby("Unit_ID").Cancel_Date.max()
        on = u[(u.Release_Date <= a) & ~u.Unit_ID.isin(set(active))].copy()
        on["listing_start"] = np.maximum(on.Release_Date.values, on.Unit_ID.map(canc).fillna(pd.Timestamp("1900-01-01")).values)
        return on


def features(ctx: Context, a: pd.Timestamp, with_label=True) -> pd.DataFrame:
    on = ctx.state(a)
    f = pd.DataFrame({"Unit_ID": on.Unit_ID.values, "Project_ID": on.Project_ID.values, "District_ID": on.District_ID.values,
                      "Unit_Type": on.Unit_Type.values, "as_of": a})
    f["area_m2"], f["price_premium"] = on.Area_m2.values, on.price_premium.values
    f["plan_years"], f["down_pct"] = on.Plan_Years.values, on.Down_Payment_Pct.values
    f["listing_age"] = (a - on.listing_start).dt.days.values
    f["dev_quality"] = on.Quality_Index.values
    km = (a.to_period("M") - 1).start_time                     # last fully reported month
    c = ctx.cons[ctx.cons.Month == km].set_index("Project_ID")
    f["completion"] = f.Project_ID.map(c.Actual_Pct)
    f["schedule_lag"] = f.Project_ID.map(c.lag)
    f["handover"] = f.Project_ID.map(c.Handover_Pct)
    s = ctx.st[ctx.st.Month == km].set_index("District_ID")
    f["svc_coverage"] = f.District_ID.map(s.Essential_Service_Coverage_Pct)
    f["svc_gaps"] = f.District_ID.map(s.Service_Gap_Count)
    f["occupancy"] = f.District_ID.map(s.Occupancy_Pct)
    f["price_index"] = ctx.pidx.get(km, np.nan)
    recent = ctx.sales[(ctx.sales.Sale_Date > a - pd.Timedelta(days=90)) & (ctx.sales.Sale_Date <= a)]
    ps = recent.groupby("Project_ID").size()
    pav = f.groupby("Project_ID").size()
    f["proj_sold_90d"] = f.Project_ID.map(ps).fillna(0)
    f["proj_avail"] = f.Project_ID.map(pav)
    f["proj_rate_90d"] = f.proj_sold_90d / (f.proj_avail + f.proj_sold_90d)
    dav = f.groupby("District_ID").size()
    f["dist_avail_log"] = np.log1p(f.District_ID.map(dav))
    w = ctx.cal.loc[a + pd.Timedelta(days=1): a + pd.Timedelta(days=H)]
    f["fut_ramadan_days"] = w.Ramadan_Flag.sum()
    f["fut_eid_days"] = (w.Eid_AlFitr_Flag + w.Eid_AlAdha_Flag).sum()
    f["fut_working_days"] = w.Working_Day_Flag.sum()
    f["fut_launch_days"] = w.Launch_Season_Flag.sum()
    f["fut_summer_days"] = w.Summer_Expat_Flag.sum()
    f["sin_m"], f["cos_m"] = np.sin(2 * np.pi * a.month / 12), np.cos(2 * np.pi * a.month / 12)
    for x in TYPES:
        f[f"type_{x}"] = (f.Unit_Type == x).astype(int)
    if with_label:
        fut = ctx.sales[(ctx.sales.Sale_Date > a) & (ctx.sales.Sale_Date <= a + pd.Timedelta(days=H))]
        f["y_unsold"] = (~f.Unit_ID.isin(set(fut.Unit_ID))).astype(int)
    return f


def build(ctx: Context, dates) -> pd.DataFrame:
    return pd.concat([features(ctx, pd.Timestamp(d)) for d in dates], ignore_index=True)


def _models():
    return {"prior_rate": None,
            "project_rate_rule": None,
            "logistic": make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=3000)),
            "gbm": HistGradientBoostingClassifier(max_depth=4, learning_rate=0.05, max_iter=250, l2_regularization=1.0, random_state=0)}


def _rule(df: pd.DataFrame) -> np.ndarray:
    """Baseline: constant-hazard assumption from the project's trailing 90-day sales per unit on the market."""
    return np.exp(-np.clip(df.proj_rate_90d.fillna(0).values, 0, 1) * 1.0) ** 1.0


def evaluate(t):
    ctx = Context(t)
    tr_d = pd.date_range(*SPLIT["train"], freq="14D")
    te_d = pd.date_range(*SPLIT["test"], freq="14D")
    assert tr_d.max() + pd.Timedelta(days=H) < te_d.min(), "label leakage between train and test windows"
    tr, te = build(ctx, tr_d), build(ctx, te_d)
    tr[FEATURES] = tr[FEATURES].fillna(0)
    te[FEATURES] = te[FEATURES].fillna(0)
    rows, preds, fitted = [], te[["Unit_ID", "Project_ID", "District_ID", "as_of", "y_unsold"]].copy(), {}
    for name, mdl in _models().items():
        if name == "prior_rate":
            p = np.full(len(te), tr.y_unsold.mean())
        elif name == "project_rate_rule":
            p = np.clip(_rule(te), 0.01, 0.99)
        else:
            mdl.fit(tr[FEATURES], tr.y_unsold)
            p = mdl.predict_proba(te[FEATURES])[:, 1]
            fitted[name] = mdl
        preds[f"p_{name}"] = p
        top = te.assign(p=p).groupby("as_of").apply(lambda g: g.nlargest(max(int(len(g) * 0.2), 1), "p").y_unsold.mean()).mean()
        rows.append({"model": name, "n_train": len(tr), "n_test": len(te), "unsold_rate_train": round(tr.y_unsold.mean(), 3),
                     "unsold_rate_test": round(te.y_unsold.mean(), 3),
                     "ROC_AUC": roc_auc_score(te.y_unsold, p) if name != "prior_rate" else 0.5,
                     "PR_AUC": average_precision_score(te.y_unsold, p), "Brier": brier_score_loss(te.y_unsold, p),
                     "LogLoss": log_loss(te.y_unsold, np.clip(p, 1e-4, 1 - 1e-4)), "Precision@top20%": top})
    return pd.DataFrame(rows).round(4), preds, fitted, ctx


def calibration(preds: pd.DataFrame, col: str, bins=10) -> pd.DataFrame:
    q = pd.qcut(preds[col], bins, duplicates="drop")
    return preds.groupby(q, observed=True).agg(n=("y_unsold", "size"), mean_pred=(col, "mean"), observed=("y_unsold", "mean")).reset_index(drop=True).round(4)


def fit_final(ctx: Context, model_name="logistic", last_asof="2025-10-02"):
    d = build(ctx, pd.date_range("2024-03-01", last_asof, freq="14D"))
    d[FEATURES] = d[FEATURES].fillna(0)
    mdl = _models()[model_name]
    mdl.fit(d[FEATURES], d.y_unsold)
    return mdl


def score_units(ctx: Context, model, as_of: str) -> pd.DataFrame:
    """Probability that each currently available unit is still unsold 90 days after `as_of`."""
    f = features(ctx, pd.Timestamp(as_of), with_label=False)
    f[FEATURES] = f[FEATURES].fillna(0)
    f["p_unsold_90d"] = model.predict_proba(f[FEATURES])[:, 1]
    f["risk_band"] = pd.cut(f.p_unsold_90d, [0, 0.8, 0.92, 1.0], labels=["Lower", "Elevated", "High"], include_lowest=True)
    return f[["Unit_ID", "Project_ID", "District_ID", "Unit_Type", "as_of", "listing_age", "price_premium", "p_unsold_90d", "risk_band"]]
