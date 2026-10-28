"""Load the linked 1,000-row synthetic survey dataset into PostgreSQL.

Run from backend/ AFTER running seed_real_estate.py:
    python seed_survey_responses.py

This is a one-time database seeding step; the dashboard itself reads only from PostgreSQL.
The CSV is synthetic demonstration data and replaces the existing acud_survey_responses table.
"""
from pathlib import Path
import sys
import pandas as pd
from sqlalchemy import inspect, text

BACKEND = Path(__file__).resolve().parent
ROOT = BACKEND.parent
DATA_FILE = ROOT / "data" / "synthetic_survey_responses_ar.csv"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
from app.database import engine  # noqa: E402

TABLE = "acud_survey_responses"
REQUIRED = {"response_id", "is_eligible", "district_id", "district_name", "project_id", "project_name", "q5_most_impactful_problem", "q13_area_attractiveness_1_5"}


def main() -> None:
    if not DATA_FILE.exists():
        raise SystemExit(f"Survey data file not found: {DATA_FILE}")
    for dim_table in ("acud_dim_district", "acud_dim_project"):
        if not inspect(engine).has_table(dim_table):
            raise SystemExit(f"Missing {dim_table}. Run `python seed_real_estate.py` first.")
    df = pd.read_csv(DATA_FILE, encoding="utf-8-sig", low_memory=False)
    missing = sorted(REQUIRED - set(df.columns))
    if missing:
        raise SystemExit(f"Survey file is missing required columns: {missing}")
    with engine.connect() as conn:
        district_ids = set(pd.read_sql(text('SELECT "District_ID" FROM "acud_dim_district"'), conn)["District_ID"].astype(str))
        project_dims = pd.read_sql(text('SELECT "Project_ID", "District_ID" FROM "acud_dim_project"'), conn)
    project_ids = set(project_dims["Project_ID"].astype(str))
    bad_districts = sorted(set(df["district_id"].astype(str)) - district_ids)
    bad_projects = sorted(set(df["project_id"].astype(str)) - project_ids)
    if bad_districts or bad_projects:
        raise SystemExit(f"Survey has keys not found in the database. Districts={bad_districts}; projects={bad_projects}")
    project_to_district = project_dims.set_index("Project_ID")["District_ID"].astype(str).to_dict()
    mismatch = df[df.apply(lambda r: project_to_district.get(str(r["project_id"])) != str(r["district_id"]), axis=1)]
    if not mismatch.empty:
        raise SystemExit(f"{len(mismatch)} survey rows have a project/district mismatch. Import cancelled.")
    df.to_sql(TABLE, engine, if_exists="replace", index=False, chunksize=500, method="multi")
    eligible = df["is_eligible"].astype(str).str.lower().isin(["true", "1", "yes"])
    print(f"Loaded {len(df):,} survey rows into {TABLE}; eligible={int(eligible.sum()):,}; screened_out={int((~eligible).sum()):,}.")
    print("Source status: synthetic_linked_demo. These are not real customer responses.")


if __name__ == "__main__":
    main()
