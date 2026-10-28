"""Loading helpers and monthly modelling dataset (P3-01)."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

FILES = ["Dim_Date", "Dim_Price_Index", "Dim_District", "Dim_Developer", "Dim_Project", "Dim_Unit", "Fact_Sales", "Fact_Inventory_Monthly",
         "Fact_Collections_Monthly", "Fact_Construction_Monthly", "Fact_District_Monthly_Status", "Fact_Utilities_Monthly",
         "Anomaly_Ground_Truth"]
TARGETS = {
    "units_sold": "Units sold (new sales)",
    "sales_value_egp": "Contract value sold (EGP)",
    "collections_egp": "Cash collected (EGP)",
    "available_inventory": "Available (unsold) units, end of month",
    "construction_cost_egp": "Construction cost incurred (EGP)",
    "electricity_kwh": "Electricity consumption (kWh)",
}
STOCK_TARGETS = {"available_inventory"}


def load_tables(data_dir) -> dict[str, pd.DataFrame]:
    """Load all CSVs. `Anomaly_Ground_Truth` is for offline evaluation only."""
    d = Path(data_dir)
    t = {n: pd.read_csv(d / f"{n}.csv") for n in FILES}
    for n in ("Fact_Inventory_Monthly", "Fact_Collections_Monthly", "Fact_Construction_Monthly",
              "Fact_District_Monthly_Status", "Fact_Utilities_Monthly"):
        t[n]["Month"] = pd.to_datetime(t[n]["Month"])
    t["Dim_Date"]["Date"] = pd.to_datetime(t["Dim_Date"]["Date"])
    for c in ("Sale_Date", "Cancel_Date"):
        t["Fact_Sales"][c] = pd.to_datetime(t["Fact_Sales"][c])
    t["Dim_Unit"]["Release_Date"] = pd.to_datetime(t["Dim_Unit"]["Release_Date"])
    for c in ("Start_Date", "End_Date"):
        t["Anomaly_Ground_Truth"][c] = pd.to_datetime(t["Anomaly_Ground_Truth"][c])
    return t


def monthly_calendar(dim_date: pd.DataFrame, start="2024-01-01", end="2026-12-01") -> pd.DataFrame:
    """Calendar covariates per month. All are KNOWN IN ADVANCE (lunar holidays included), so they are legitimate
    regressors for future months. Ramadan moves ~11 days earlier each year, which is why a plain 12-month
    seasonal-naive forecast mis-places the Ramadan dip."""
    d = dim_date.copy()
    d["M"] = d.Date.dt.to_period("M").dt.start_time
    g = d.groupby("M").agg(days=("Date", "size"), ramadan=("Ramadan_Flag", "sum"),
                           eid=("Eid_AlFitr_Flag", "sum"), eid_adha=("Eid_AlAdha_Flag", "sum"),
                           working_days=("Working_Day_Flag", "sum"), weekend=("Weekend_Flag", "sum"))
    g["eid_days"] = g.eid + g.eid_adha
    g["ramadan_share"] = g.ramadan / g.days
    g["working_share"] = g.working_days / g.days
    g["month"] = g.index.month
    g = g.loc[start:end]
    g["t"] = np.arange(len(g))
    return g[["days", "ramadan_share", "eid_days", "working_days", "working_share", "month", "t"]]


def monthly_series(t: dict, district: str | None = None, project: str | None = None) -> pd.DataFrame:
    """Monthly modelling dataset (city-level by default; optional district / project filter)."""
    inv, col, con, ut = (t["Fact_Inventory_Monthly"], t["Fact_Collections_Monthly"], t["Fact_Construction_Monthly"],
                         t["Fact_Utilities_Monthly"])
    def filt(df):
        if project:
            df = df[df.Project_ID == project] if "Project_ID" in df else df.iloc[0:0]
        if district:
            df = df[df.District_ID == district]
        return df
    out = pd.DataFrame({
        "units_sold": filt(inv).groupby("Month").Units_Sold.sum(),
        "sales_value_egp": filt(inv).groupby("Month").Sales_Value_EGP.sum(),
        "collections_egp": filt(col).groupby("Month").Amount_Collected_EGP.sum(),
        "available_inventory": filt(inv).groupby("Month").Available_End.sum(),
        "construction_cost_egp": filt(con).groupby("Month").Actual_Cost_EGP.sum(),
    })
    if not project:
        out["electricity_kwh"] = filt(ut).groupby("Month").Electricity_kWh.sum()
    out.index.name = "Month"
    return out
