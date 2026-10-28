"""Database-backed ACUD real-estate analytics endpoints.

The prototype imports the supplied synthetic CSVs into tables prefixed with ``acud_``.
The dashboard reads current aggregates from those tables rather than trusting embedded HTML data.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

import cohere
import pandas as pd
import numpy as np
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import inspect, text

from app.config import get_settings
from app.database import engine

router = APIRouter(prefix="/api/v1/sales", tags=["ACUD real-estate analytics"])

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
OUTPUT_DIR = Path(__file__).resolve().parents[3] / "outputs"
TARGETS = {
    "units_sold": "Units sold (new sales)",
    "sales_value_egp": "Contract value sold (EGP)",
    "collections_egp": "Cash collected (EGP)",
    "available_inventory": "Available (unsold) units, end of month",
    "construction_cost_egp": "Construction cost incurred (EGP)",
    "electricity_kwh": "Electricity consumption (kWh)",
}


def _table_exists(name: str) -> bool:
    return inspect(engine).has_table(name)


def _read(name: str) -> pd.DataFrame:
    table = f"acud_{re.sub(r'[^a-zA-Z0-9_]', '_', name).lower()}"
    if not _table_exists(table):
        raise HTTPException(status_code=503, detail=f"Dataset table '{table}' is missing. Run backend/seed_real_estate.py first.")
    with engine.connect() as conn:
        return pd.read_sql(text(f'SELECT * FROM "{table}"'), conn)


def _monthly_dashboard() -> dict:
    inv = _read("Fact_Inventory_Monthly")
    col = _read("Fact_Collections_Monthly")
    con = _read("Fact_Construction_Monthly")
    util = _read("Fact_Utilities_Monthly")
    projects = _read("Dim_Project")
    districts = _read("Dim_District")
    units = _read("Dim_Unit")

    for frame in (inv, col, con, util):
        frame["Month"] = pd.to_datetime(frame["Month"]).dt.to_period("M").dt.to_timestamp()
    inv_month = inv.groupby("Month").agg(units_sold=("Units_Sold", "sum"), sales_value_egp=("Sales_Value_EGP", "sum"), available_inventory=("Available_End", "sum"))
    col_month = col.groupby("Month")["Amount_Collected_EGP"].sum().rename("collections_egp")
    con_month = con.groupby("Month")["Actual_Cost_EGP"].sum().rename("construction_cost_egp")
    util_month = util.groupby("Month")["Electricity_kWh"].sum().rename("electricity_kwh")
    monthly = inv_month.join(col_month, how="outer").join(con_month, how="outer").join(util_month, how="outer").sort_index().fillna(0)
    # Keep the same recent 24-month window used by the supplied dashboard when available.
    monthly = monthly.tail(24)
    months = monthly.index.strftime("%Y-%m").tolist()
    hist = {key: [float(v) for v in monthly[key].tolist()] for key in TARGETS}

    sales_window = int(monthly["units_sold"].sum())
    value_window = float(monthly["sales_value_egp"].sum())
    available_end = int(monthly["available_inventory"].iloc[-1]) if len(monthly) else 0
    summary = {
        "districts": int(districts["District_ID"].nunique()),
        "projects": int(projects["Project_ID"].nunique()),
        "units": int(units["Unit_ID"].nunique()),
        "sales_window": sales_window,
        "value_window": value_window,
        "collected": float(monthly["collections_egp"].sum()),
        "available_end": available_end,
        "unit_scored": available_end,
    }

    # Recompute a transparent seasonal-naive forecast from the database series on each request.
    # This is a baseline, not a causal model; intervals are heuristic and must be back-tested on real data.
    forecast = []
    if len(monthly) >= 12:
        last_month = monthly.index.max()
        for target in TARGETS:
            series = monthly[target].astype(float)
            scale = max(float(series.tail(12).mean()), 1.0)
            for horizon in (3, 6, 12):
                for step in range(1, horizon + 1):
                    future_month = last_month + pd.offsets.MonthBegin(step)
                    prior_month = future_month - pd.DateOffset(years=1)
                    base = float(series.loc[prior_month]) if prior_month in series.index else float(series.iloc[-1])
                    # A wider heuristic band is used for longer horizons.
                    margin = scale * ({3: 0.15, 6: 0.22, 12: 0.30}[horizon])
                    forecast.append({"target": target, "horizon_months": horizon, "Month": future_month.strftime("%Y-%m"),
                                    "yhat": max(0.0, base), "lo": max(0.0, base - margin), "hi": max(0.0, base + margin),
                                    "model": "database_seasonal_naive", "horizon_fold": f"{horizon}m", "mape_backtest": None,
                                    "ml_beats_baseline": False, "usable": True})

    result = {"source": "postgresql", "generated_at": pd.Timestamp.now(tz="UTC").isoformat(), "targets": TARGETS,
              "months": months, "hist": hist, "summary": summary, "forecast": forecast,
              "data_status": "synthetic_prototype_data",
              "notes": ["Prototype data is synthetic; results are not evidence about actual ACUD market conditions.",
                        "Monthly values and baseline forecasts are computed from database tables populated by the supplied CSV files.",
                        "Forecast bands are heuristic and are not probabilistic confidence intervals."]}

    # Risk output was generated by the supplied model and is imported as a table too.
    try:
        risk = _read("unsold_risk_scores_asof_2025-12-31")
        if "Project_ID" in risk and "District_ID" in risk:
            pcol = next((c for c in risk.columns if c.lower() in {"p_unsold_90d", "prob_unsold_90d", "p_unsold", "predicted_probability"}), None)
            if pcol:
                risk[pcol] = pd.to_numeric(risk[pcol], errors="coerce").fillna(0).clip(0, 1)
                grp = risk.groupby(["Project_ID", "District_ID"]).agg(units_on_market=("Unit_ID", "count"), mean_p_unsold=(pcol, "mean")).reset_index()
                grp["expected_unsold_90d"] = grp.units_on_market * grp.mean_p_unsold
                grp["expected_sold_90d"] = grp.units_on_market - grp.expected_unsold_90d
                result["risk_proj"] = grp.sort_values("expected_unsold_90d", ascending=False).head(40).to_dict("records")
                dg = risk.groupby("District_ID").agg(units=("Unit_ID", "count"), mean_p=(pcol, "mean")).reset_index()
                dg["expected_unsold"] = dg.units * dg.mean_p
                dg["high"] = risk.assign(_high=risk[pcol] >= .8).groupby("District_ID")["_high"].sum().reindex(dg.District_ID).to_numpy()
                result["risk_dist"] = dg.to_dict("records")
    except HTTPException:
        pass
    return result


@router.get("/dashboard")
def sales_dashboard():
    """Live sales, collections, inventory, cost and utility aggregates from the database."""
    return _monthly_dashboard()


@router.get("/projects")
def project_performance():
    inv = _read("Fact_Inventory_Monthly")
    projects = _read("Dim_Project")
    developers = _read("Dim_Developer")
    latest = pd.to_datetime(inv["Month"]).max()
    recent = inv[pd.to_datetime(inv["Month"]) == latest]
    agg = recent.groupby("Project_ID", as_index=False).agg(units_sold=("Units_Sold", "sum"), available_end=("Available_End", "sum"), sales_value_egp=("Sales_Value_EGP", "sum"))
    out = agg.merge(projects, on="Project_ID", how="left")
    if "Developer_ID" in out and "Developer_ID" in developers:
        out = out.merge(developers, on="Developer_ID", how="left", suffixes=("", "_developer"))
    return {"source": "postgresql", "as_of": str(pd.Timestamp(latest).date()), "projects": out.replace({float("nan"): None}).to_dict("records")}


@router.get("/diagnostics")
def unsold_diagnostics():
    """Return project/district indicators to investigate unsold inventory; associations are not causal proof."""
    district_status = _read("Fact_District_Monthly_Status")
    services = _read("Fact_District_Service_Indicators")
    inventory = _read("Fact_Inventory_Monthly")
    projects = _read("Dim_Project")
    funnel = _read("Fact_Project_Sales_Funnel")
    for frame in (district_status, services, inventory, funnel):
        frame["Month"] = pd.to_datetime(frame["Month"])
    latest_status_month = district_status["Month"].max()
    latest_service_month = services["Month"].max()
    latest_inventory_month = inventory["Month"].max()
    latest_funnel_month = funnel["Month"].max()
    ds = district_status[district_status.Month == latest_status_month]
    sv = services[services.Month == latest_service_month]
    inv = inventory[inventory.Month == latest_inventory_month].groupby(["Project_ID", "District_ID"], as_index=False).agg(
        available_units=("Available_End", "sum"), units_sold=("Units_Sold", "sum"), sales_value_egp=("Sales_Value_EGP", "sum"))
    project_district = projects[[c for c in ["Project_ID", "Project_Name", "District_ID", "Developer_ID", "Price_Multiplier"] if c in projects]]
    district_view = ds.merge(sv, on="District_ID", how="left", suffixes=("_status", "_service"))
    district_inventory = inv.groupby("District_ID", as_index=False).agg(available_units=("available_units", "sum"), units_sold=("units_sold", "sum"))
    district_view = district_view.merge(district_inventory, on="District_ID", how="left")
    funnel_latest = funnel[funnel.Month == latest_funnel_month].copy()
    funnel_latest["viewing_rate"] = funnel_latest["Viewings"] / funnel_latest["Leads"].replace(0, pd.NA)
    funnel_latest["booking_rate"] = funnel_latest["Bookings"] / funnel_latest["Viewings"].replace(0, pd.NA)
    funnel_latest["cancellation_rate"] = funnel_latest["Booking_Cancellations"] / funnel_latest["Bookings"].replace(0, pd.NA)
    funnel_project = funnel_latest.groupby(["Project_ID", "District_ID"], as_index=False).agg(
        leads=("Leads", "sum"), viewings=("Viewings", "sum"), bookings=("Bookings", "sum"),
        cancellations=("Booking_Cancellations", "sum"), avg_lead_response_hours=("Average_Lead_Response_Hours", "mean"),
        marketing_spend_egp=("Marketing_Spend_EGP", "sum"))
    funnel_project["viewing_rate"] = funnel_project["viewings"] / funnel_project["leads"].replace(0, pd.NA)
    funnel_project["booking_rate"] = funnel_project["bookings"] / funnel_project["viewings"].replace(0, pd.NA)
    funnel_project["cancellation_rate"] = funnel_project["cancellations"] / funnel_project["bookings"].replace(0, pd.NA)
    project_view = inv.merge(project_district, on=["Project_ID", "District_ID"], how="left").merge(funnel_project, on=["Project_ID", "District_ID"], how="left")
    clean_districts = district_view.sort_values("available_units", ascending=False).astype(object).where(pd.notna(district_view.sort_values("available_units", ascending=False)), None)
    clean_projects = project_view.sort_values("available_units", ascending=False).head(50)
    clean_projects = clean_projects.astype(object).where(pd.notna(clean_projects), None)
    return {
        "source": "postgresql", "data_status": "synthetic_prototype_data",
        "latest_district_month": str(pd.Timestamp(latest_status_month).date()),
        "latest_funnel_month": str(pd.Timestamp(latest_funnel_month).date()),
        "district_indicators": clean_districts.to_dict("records"),
        "project_funnel_and_inventory": clean_projects.to_dict("records"),
        "interpretation_note": "Traffic, access, service, price multiplier, and funnel features are synthetic demonstrations. Associations are investigative signals, not proven causes."
    }


class SalesQuestion(BaseModel):
    question: str = Field(min_length=2, max_length=4000)
    language: Literal["en", "ar"] = "en"
    district_id: str | None = None
    project_id: str | None = None


@router.post("/ask")
def ask_sales(payload: SalesQuestion):
    """Answer sales questions from focused, time-relevant database evidence."""
    settings = get_settings()
    if not settings.cohere_api_key:
        raise HTTPException(status_code=503, detail="Cohere is not configured. Add COHERE_API_KEY to backend/.env.")

    # IDs are accepted from the optional filters, but also extracted from the question
    # so asking "what happened to P022?" works without filling in the filter controls.
    project_match = re.search(r"\bP\d{3}\b", payload.question.upper())
    district_match = re.search(r"\bD\d{2}\b", payload.question.upper())
    project_id = payload.project_id or (project_match.group(0) if project_match else None)
    district_id = payload.district_id or (district_match.group(0) if district_match else None)

    evidence = {
        "data_status": "synthetic_prototype_data",
        "question": payload.question,
        "selected_project_id": project_id,
        "selected_district_id": district_id,
        "data_granularity_warning": "Sales and operational indicators are monthly; they cannot establish an event on a specific day in mid-May.",
    }

    inventory = _read("Fact_Inventory_Monthly").copy()
    inventory["Month"] = pd.to_datetime(inventory["Month"], errors="coerce")
    projects_dim = _read("Dim_Project")
    district_id_for_project = None
    project_meta = pd.DataFrame()
    if project_id:
        inventory = inventory[inventory["Project_ID"].astype(str).str.upper() == project_id]
        project_meta = projects_dim[projects_dim["Project_ID"].astype(str).str.upper() == project_id]
        if not project_meta.empty:
            district_id_for_project = str(project_meta.iloc[0].get("District_ID", "")) or None
    if district_id:
        inventory = inventory[inventory["District_ID"].astype(str).str.upper() == district_id]
    if not district_id:
        district_id = district_id_for_project
    if district_id:
        evidence["selected_district_id"] = district_id

    # Preserve the monthly timeline instead of sending only a lifetime aggregate.
    evidence["project_monthly_sales_and_inventory"] = inventory.sort_values("Month").tail(36).assign(
        Month=lambda df: df["Month"].dt.strftime("%Y-%m-%d")
    ).where(pd.notna(inventory.sort_values("Month").tail(36)), None).to_dict("records")
    if not project_meta.empty:
        evidence["project_details"] = project_meta.replace({np.nan: None}).to_dict("records")

    # Attach flagged anomaly records, which contain observed-vs-expected metrics and dates.
    try:
        anomalies = _read("anomalies_flagged").copy()
        if project_id and "Entity_ID" in anomalies:
            anomalies = anomalies[anomalies["Entity_ID"].astype(str).str.upper() == project_id]
        if district_id and "Entity_ID" in anomalies and not project_id:
            anomalies = anomalies[anomalies["Entity_ID"].astype(str).str.upper() == district_id]
        evidence["flagged_sales_anomalies"] = anomalies.tail(30).replace({np.nan: None}).to_dict("records")
    except Exception as exc:
        evidence["flagged_sales_anomalies_note"] = f"Anomaly table unavailable: {type(exc).__name__}"

    # Add funnel metrics, including customer-budget segments and conversion indicators.
    try:
        funnel = _read("Fact_Project_Sales_Funnel").copy()
        funnel["Month"] = pd.to_datetime(funnel["Month"], errors="coerce")
        if project_id:
            funnel = funnel[funnel["Project_ID"].astype(str).str.upper() == project_id]
        if district_id:
            funnel = funnel[funnel["District_ID"].astype(str).str.upper() == district_id]
        funnel = funnel.sort_values("Month").tail(36).copy()
        if not funnel.empty:
            funnel["viewing_rate"] = (funnel["Viewings"] / funnel["Leads"].replace(0, np.nan)).round(4)
            funnel["booking_rate"] = (funnel["Bookings"] / funnel["Viewings"].replace(0, np.nan)).round(4)
            funnel["cancellation_rate"] = (funnel["Booking_Cancellations"] / funnel["Bookings"].replace(0, np.nan)).round(4)
            funnel["Month"] = funnel["Month"].dt.strftime("%Y-%m-%d")
        evidence["project_monthly_sales_funnel"] = funnel.replace({np.nan: None}).to_dict("records")
    except Exception as exc:
        evidence["project_monthly_sales_funnel_note"] = f"Sales funnel data unavailable: {type(exc).__name__}"

    # District service/access indicators and status history around the anomaly month.
    for dataset, key in [
        ("Fact_District_Service_Indicators", "district_service_history"),
        ("Fact_District_Monthly_Status", "district_status_history"),
    ]:
        try:
            frame = _read(dataset).copy()
            frame["Month"] = pd.to_datetime(frame["Month"], errors="coerce")
            if district_id and "District_ID" in frame:
                frame = frame[frame["District_ID"].astype(str).str.upper() == district_id]
            frame = frame.sort_values("Month").tail(36).copy()
            frame["Month"] = frame["Month"].dt.strftime("%Y-%m-%d")
            evidence[key] = frame.replace({np.nan: None}).to_dict("records")
        except Exception as exc:
            evidence[key + "_note"] = f"Dataset unavailable: {type(exc).__name__}"

    # Historical transaction dates allow a direct monthly count from sales records.
    try:
        sales = _read("Fact_Sales").copy()
        sales["Sale_Date"] = pd.to_datetime(sales["Sale_Date"], errors="coerce")
        if project_id:
            sales = sales[sales["Project_ID"].astype(str).str.upper() == project_id]
        if district_id:
            sales = sales[sales["District_ID"].astype(str).str.upper() == district_id]
        if not sales.empty:
            sales["Month"] = sales["Sale_Date"].dt.to_period("M").astype(str)
            monthly_sales = sales.groupby("Month", as_index=False).agg(
                transactions=("Sale_ID", "count"), contract_value_egp=("Contract_Value_EGP", "sum"))
            evidence["transaction_sales_by_month"] = monthly_sales.tail(36).replace({np.nan: None}).to_dict("records")
    except Exception as exc:
        evidence["transaction_sales_by_month_note"] = f"Transaction-level sales unavailable: {type(exc).__name__}"

    system_prompt = (
        "You are ACUD's evidence-grounded real-estate sales analyst. Answer in the requested language. "
        "You MUST analyze the supplied evidence rather than give generic advice. Start by identifying the relevant project and period. "
        "For a sales-drop question, compare the month(s) before, during, and after the flagged period; cite exact observed and expected values, "
        "and calculate percentage changes when possible. Use the anomaly table's Period_Start, observed_3m, expected_3m, score, and p_value when present. "
        "Then check whether funnel conversion, lead volume, price multiplier, district service/access indicators, or status indicators changed around that period. "
        "Only claim a factor changed if the provided records show it; distinguish correlation from causation. If data is monthly, explicitly say it cannot identify an event on a specific day. "
        "If evidence is missing, name the missing table/field instead of stopping at a generic disclaimer. "
        "This prototype data is synthetic; state that findings demonstrate the analysis method and are not actual ACUD market findings. "
        "Do not invent facts or metrics."
    )
    try:
        client = cohere.ClientV2(api_key=settings.cohere_api_key)
        response = client.chat(model=settings.cohere_model, messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Database evidence (JSON):\n" + json.dumps(evidence, ensure_ascii=False, default=str) +
             "\n\nQuestion: " + payload.question + "\nLanguage: " + payload.language},
        ], temperature=0.1, max_tokens=1200)
        content = getattr(response.message, "content", None) or []
        answer = "\n".join(part.text for part in content if getattr(part, "text", None)).strip()
        if not answer:
            raise RuntimeError("Cohere returned an empty response")
    except Exception as exc:
        print(f"Cohere sales analytics error: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=502, detail="The sales assistant is temporarily unavailable.") from exc
    return {"reply": answer, "provider": "cohere", "model": settings.cohere_model,
            "evidence_source": "postgresql", "data_status": evidence["data_status"]}
