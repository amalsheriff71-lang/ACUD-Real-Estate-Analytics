"""Create explicitly synthetic district-service and aggregate sales-funnel features for demos.

These are simulated demonstration features, not observations about actual ACUD districts,
customers, traffic, or developers. Run from the repository root with `python data/extend_prototype_data.py`.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
rng = np.random.default_rng(20261028)
districts = pd.read_csv(ROOT / "Dim_District.csv")
status = pd.read_csv(ROOT / "Fact_District_Monthly_Status.csv", parse_dates=["Month"])
projects = pd.read_csv(ROOT / "Dim_Project.csv")
months = sorted(pd.to_datetime(status["Month"]).dt.to_period("M").unique())

# District-month service/access feature table. Values are synthetic and should be replaced by measured data.
rows = []
for _, r in status.iterrows():
    d = str(r["District_ID"])
    congestion_base = 35 + (int(d[-2:]) * 3.2)
    rows.append({
        "District_ID": d, "Month": pd.Timestamp(r["Month"]).strftime("%Y-%m-%d"),
        "Traffic_Congestion_Index": round(float(np.clip(congestion_base + rng.normal(0, 7), 0, 100)), 2),
        "Average_Travel_Time_Min": round(float(np.clip(18 + congestion_base * 0.45 + rng.normal(0, 4), 8, 95)), 2),
        "Public_Transport_Coverage_Pct": round(float(np.clip(35 + r["Transport_Accessibility_Score"] * 5.5 + rng.normal(0, 4), 0, 100)), 2),
        "Healthcare_Access_Score": round(float(np.clip(4 + r["Essential_Service_Coverage_Pct"] / 18 + rng.normal(0, .35), 0, 10)), 2),
        "School_Access_Score": round(float(np.clip(4 + r["Essential_Service_Coverage_Pct"] / 17 + rng.normal(0, .4), 0, 10)), 2),
        "Retail_Access_Score": round(float(np.clip(3 + r["Essential_Service_Coverage_Pct"] / 15 + rng.normal(0, .4), 0, 10)), 2),
        "Utilities_Reliability_Pct": round(float(np.clip(60 + r["Infrastructure_Readiness_Pct"] * .35 + rng.normal(0, 5), 0, 100)), 2),
        "Source_Status": "Synthetic demonstration only",
    })
pd.DataFrame(rows).to_csv(ROOT / "Fact_District_Service_Indicators.csv", index=False)

# Aggregated project-month lead funnel. No person-level/customer-identifying information is generated.
funnel = []
for _, project in projects.iterrows():
    pid = str(project["Project_ID"])
    did = str(project["District_ID"])
    price_mult = float(project.get("Price_Multiplier", 1.0))
    for period in months:
        month = pd.Timestamp(str(period)).to_period("M").to_timestamp()
        leads = int(rng.integers(18, 150))
        viewing_rate = float(np.clip(.42 - max(0, price_mult - 1) * .25 + rng.normal(0, .04), .12, .55))
        viewings = min(leads, int(round(leads * viewing_rate)))
        booking_rate = float(np.clip(.22 - max(0, price_mult - 1) * .12 + rng.normal(0, .025), .04, .3))
        bookings = min(viewings, int(round(viewings * booking_rate)))
        cancellations = int(rng.binomial(bookings, .12))
        funnel.append({
            "Project_ID": pid, "District_ID": did, "Month": month.strftime("%Y-%m-%d"),
            "Leads": leads, "Viewings": viewings, "Bookings": bookings,
            "Booking_Cancellations": cancellations,
            "Average_Lead_Response_Hours": round(float(np.clip(rng.normal(9 + price_mult * 2, 4), .5, 48)), 2),
            "Marketing_Spend_EGP": round(float(leads * rng.uniform(700, 2200)), 2),
            "Budget_Segment_Leads_Under_5M": int(round(leads * rng.uniform(.1, .35))),
            "Budget_Segment_Leads_5M_to_10M": int(round(leads * rng.uniform(.25, .5))),
            "Budget_Segment_Leads_Over_10M": int(round(leads * rng.uniform(.1, .35))),
            "Source_Status": "Synthetic demonstration only",
        })
pd.DataFrame(funnel).to_csv(ROOT / "Fact_Project_Sales_Funnel.csv", index=False)
print(f"Created {len(rows)} synthetic district-service rows and {len(funnel)} synthetic project-funnel rows.")
print("Replace these demo indicators with measured service, traffic, and CRM data before production use.")
