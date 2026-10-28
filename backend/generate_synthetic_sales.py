"""Generate a denser synthetic sales snapshot for all known projects.

Run from backend/ after configuring .env and seeding the base real-estate dimensions:
    python generate_synthetic_sales.py

Adds/replaces only the generated snapshot month (2026-09-01) in
acud_fact_inventory_monthly. Earlier monthly records are preserved. All data is synthetic.
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from sqlalchemy import inspect, text

BACKEND = Path(__file__).resolve().parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
from app.database import engine  # noqa: E402

TABLE = "acud_fact_inventory_monthly"
PROJECT_TABLE = "acud_dim_project"
SNAPSHOT_MONTH = "2026-09-01"


def main():
    inspector = inspect(engine)
    for table in (TABLE, PROJECT_TABLE):
        if not inspector.has_table(table):
            raise SystemExit(f"Missing table {table}. Run `python seed_real_estate.py` first.")
    with engine.connect() as conn:
        projects = pd.read_sql(text(f'SELECT * FROM "{PROJECT_TABLE}" ORDER BY "Project_ID"'), conn)
        existing = pd.read_sql(text(f'SELECT * FROM "{TABLE}" WHERE "Month" = :month'), conn, params={"month": SNAPSHOT_MONTH})
    if not {"Project_ID", "District_ID"}.issubset(projects.columns):
        raise SystemExit("Project dimension must contain Project_ID and District_ID.")
    if projects.empty:
        raise SystemExit("No projects found in the project dimension.")

    # Spread projects across the requested sales performance tiers, reproducibly.
    rng = np.random.default_rng(20261028)
    ratios = []
    tier_specs = [(8, 0.06, 0.19), (12, 0.20, 0.49), (12, 0.50, 0.69), (8, 0.70, 0.92)]
    for count, low, high in tier_specs:
        ratios.extend(rng.uniform(low, high, count).tolist())
    # Support datasets with a different number of projects without dropping any.
    if len(ratios) < len(projects):
        ratios.extend(rng.uniform(0.20, 0.69, len(projects) - len(ratios)).tolist())
    ratios = ratios[:len(projects)]
    rng.shuffle(ratios)

    rows = []
    for (_, project), ratio in zip(projects.iterrows(), ratios):
        # 25–90 unit illustrative snapshot pool; the rate distribution is deliberate.
        pool = int(rng.integers(25, 91))
        sold = max(1, min(pool - 1, int(round(pool * float(ratio)))))
        available = pool - sold
        avg_ticket = float(rng.uniform(4_500_000, 18_000_000))
        rows.append({
            "Project_ID": str(project["Project_ID"]),
            "District_ID": str(project["District_ID"]),
            "Month": SNAPSHOT_MONTH,
            "Available_Start": pool,
            "Units_Released": 0,
            "Units_Sold": sold,
            "Units_Cancelled": 0,
            "Available_End": available,
            "Avg_Inventory_Age_Days": round(float(rng.uniform(30, 420)), 1),
            "Sales_Value_EGP": round(sold * avg_ticket, 2),
        })
    generated = pd.DataFrame(rows)
    with engine.begin() as conn:
        # Idempotent reruns: replace only this script's dedicated snapshot month.
        conn.execute(text(f'DELETE FROM "{TABLE}" WHERE "Month" = :month'), {"month": SNAPSHOT_MONTH})
        generated.to_sql(TABLE, conn, if_exists="append", index=False, chunksize=500, method="multi")

    pct = generated["Units_Sold"] / (generated["Units_Sold"] + generated["Available_End"]) * 100
    print(f"Generated {len(generated)} synthetic project sales snapshots for {SNAPSHOT_MONTH}.")
    print(f"Districts populated: {generated['District_ID'].nunique()} | Projects populated: {generated['Project_ID'].nunique()}")
    print(f"Critical <20%: {(pct < 20).sum()} | Low 20–<50%: {((pct >= 20) & (pct < 50)).sum()} | Medium 50–<70%: {((pct >= 50) & (pct < 70)).sum()} | High >=70%: {(pct >= 70).sum()}")
    print("Earlier monthly records were preserved. All generated figures are synthetic demonstration data.")

if __name__ == "__main__":
    main()
