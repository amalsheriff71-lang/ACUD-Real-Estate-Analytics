"""python run_all.py --data data --out outputs"""
import argparse, json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from nac_ml.data import load_tables, monthly_series, monthly_calendar, TARGETS
from nac_ml import forecasting as F, anomaly as A, risk as R

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
BLUE, ORANGE, RED, GREEN = "#2a78d6", "#eb6834", "#d03b3b", "#1baf7a"


def style(ax, title, ylabel=""):
    ax.set_title(title, loc="left", fontsize=12, color=INK, fontweight="bold")
    ax.set_ylabel(ylabel, color=MUTED); ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=MUTED, length=0)


def main(data, out):
    out = Path(out); (out / "charts").mkdir(parents=True, exist_ok=True); Path("models").mkdir(exist_ok=True)
    t = load_tables(data)
    df, cal = monthly_series(t), monthly_calendar(t["Dim_Date"])
    # ---------------- forecasting
    met, bp = F.backtest(df, cal)
    met.round(4).to_csv(out / "forecast_backtest_metrics.csv", index=False)
    bp.to_csv(out / "forecast_backtest_predictions.csv", index=False)
    sel = F.select_best(met)
    json.dump(sel, open(out / "model_selection.json", "w"), indent=2)
    fl = []
    for tg in df.columns:
        for h in (3, 6, 12):
            r = F.forecast(df, tg, h, cal, "auto", sel, bp)
            r.insert(0, "horizon_months", h); r.insert(0, "target", tg); fl.append(r)
    fc = pd.concat(fl)
    fc["Month"] = fc.Month.dt.strftime("%Y-%m")
    fc.round(2).to_csv(out / "forecast_2026.csv", index=False)

    # ---------------- anomalies
    det, ev = A.run_all(t)
    det.to_csv(out / "anomalies_all_scored.csv", index=False)
    det[det.flag == True].to_csv(out / "anomalies_flagged.csv", index=False)
    ev.to_csv(out / "anomaly_evaluation.csv", index=False)

    # ---------------- risk
    rm, rp, fitted, ctx = R.evaluate(t)
    rm.to_csv(out / "unsold_risk_metrics.csv", index=False)
    R.calibration(rp, "p_logistic").to_csv(out / "unsold_risk_calibration_logistic.csv", index=False)
    rp.to_csv(out / "unsold_risk_test_predictions.csv", index=False)
    final = R.fit_final(ctx, "logistic")
    joblib.dump({"model": final, "features": R.FEATURES, "horizon_days": R.H}, "models/unsold_risk_logistic.joblib")
    sc = R.score_units(ctx, final, "2025-12-31")
    sc.to_csv(out / "unsold_risk_scores_asof_2025-12-31.csv", index=False)
    agg = sc.groupby("Project_ID").agg(District_ID=("District_ID", "first"), units_on_market=("Unit_ID", "size"),
                                       expected_unsold_90d=("p_unsold_90d", "sum"), mean_p_unsold=("p_unsold_90d", "mean")).reset_index()
    agg["expected_sold_90d"] = agg.units_on_market - agg.expected_unsold_90d
    agg.round(3).sort_values("expected_unsold_90d", ascending=False).to_csv(out / "unsold_risk_by_project_asof_2025-12-31.csv", index=False)

    # ---------------- charts
    def line_fc(ax, tg, label):
        ax.plot(df.index, df[tg] / 1e0, color=INK, lw=2, label="Actual")
    # 1: 12m fold, units sold - Ramadan effect
    fig, ax = plt.subplots(figsize=(9, 4.2))
    g = bp[(bp.target == "units_sold") & (bp.fold == "12m")]
    ax.plot(df.index, df.units_sold, color=INK, lw=2, label="Actual")
    for mdl, col, lab in (("snaive12", ORANGE, "Same month last year (baseline)"), ("ridge_egypt", BLUE, "Ridge + Egyptian calendar")):
        s = g[g.model == mdl].set_index("Month").pred
        ax.plot(s.index, s.values, color=col, lw=2, label=lab)
    for a, b in (("2024-03-11", "2024-04-09"), ("2025-03-01", "2025-03-29")):
        ax.axvspan(pd.Timestamp(a), pd.Timestamp(b), color="#c9c8c2", alpha=0.5, lw=0)
    ax.text(pd.Timestamp("2024-03-12"), ax.get_ylim()[1] * 0.97, "Ramadan", color=MUTED, fontsize=9, va="top")
    ax.legend(frameon=False, loc="lower left"); style(ax, "Units sold per month: 12-month back-test (train 2024, test 2025)", "units")
    fig.tight_layout(); fig.savefig(out / "charts/01_units_sold_backtest_12m.png", dpi=150); plt.close(fig)
    # 2: forecast units sold + collections
    for tg, fn, ttl, sc_ in (("units_sold", "02_forecast_units_sold_2026.png", "Units sold: forecast 2026", 1), ("collections_egp", "03_forecast_collections_2026.png", "Cash collected (EGP m): forecast 2026", 1e6)):
        fig, ax = plt.subplots(figsize=(9, 4.2))
        ax.plot(df.index, df[tg] / sc_, color=INK, lw=2, label="Actual 2024-25")
        r = fc[(fc.target == tg) & (fc.horizon_months == 12)].copy(); r["Month"] = pd.to_datetime(r.Month)
        ax.plot(r.Month, r.yhat / sc_, color=BLUE, lw=2, label=f"Forecast ({r.model.iloc[0]})")
        ax.fill_between(r.Month, r.lo / sc_, r.hi / sc_, color=BLUE, alpha=0.15, lw=0)
        ax.legend(frameon=False, loc="upper left"); style(ax, ttl, ""); fig.tight_layout(); fig.savefig(out / f"charts/{fn}", dpi=150); plt.close(fig)
    # 4: sales-drop evidence for P022
    fig, ax = plt.subplots(figsize=(9, 4.2))
    d_ = det[det.detector_type == "sales_drop"]
    for pid, g in d_.groupby("Entity_ID"):
        if pid != "P022":
            ax.plot(g.Period_Start, g.score, color="#c9c8c2", lw=0.6)
    g = d_[d_.Entity_ID == "P022"]; ax.plot(g.Period_Start, g.score, color=RED, lw=2, label="P022 (injected sales drop Apr-Jun 2025)")
    ax.axhline(2, color=MUTED, ls="--", lw=1); ax.text(d_.Period_Start.min(), 2.1, "p = 0.01", color=MUTED, fontsize=9)
    ax.plot([], [], color="#c9c8c2", label="Other projects"); ax.legend(frameon=False, loc="upper left")
    style(ax, "Sales-drop score: -log10 p (Poisson, seasonality-adjusted)", ""); fig.tight_layout(); fig.savefig(out / "charts/04_sales_drop_score.png", dpi=150); plt.close(fig)
    # 5: calibration
    cal_ = R.calibration(rp, "p_logistic")
    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    ax.plot([0.5, 1], [0.5, 1], color="#c9c8c2", lw=1); ax.plot(cal_.mean_pred, cal_.observed, color=BLUE, lw=2, marker="o")
    style(ax, "Unsold-90d risk: calibration (test)", "observed unsold rate"); ax.set_xlabel("predicted probability", color=MUTED)
    fig.tight_layout(); fig.savefig(out / "charts/05_unsold_risk_calibration.png", dpi=150); plt.close(fig)
    print("done")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--data", default="data"); ap.add_argument("--out", default="outputs")
    a = ap.parse_args(); main(a.data, a.out)
