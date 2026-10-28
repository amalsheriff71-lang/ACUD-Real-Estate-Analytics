"""Import the prototype's supplied CSV datasets into PostgreSQL tables prefixed with acud_.

Run from backend/ after configuring DATABASE_URL in .env:
    python seed_real_estate.py
Use only synthetic/test data in development. Existing acud_* tables are replaced.
"""
from pathlib import Path
import re
import sys

import pandas as pd
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from app.database import engine  # noqa: E402

DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"


def safe_table(name: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name).lower()
    return f"acud_{name}"


def import_csv(path: Path) -> None:
    df = pd.read_csv(path, low_memory=False)
    table = safe_table(path.stem)
    # Explicitly quote table names and replace only the prototype table of this dataset.
    df.to_sql(table, engine, if_exists="replace", index=False, chunksize=500, method="multi")
    print(f"Imported {path.relative_to(ROOT)} -> {table}: {len(df):,} rows, {len(df.columns)} columns")


def main() -> None:
    files = sorted(DATA_DIR.glob("*.csv")) + sorted(OUTPUT_DIR.glob("*.csv"))
    if not files:
        raise SystemExit("No CSV datasets found under data/ or outputs/.")
    for path in files:
        import_csv(path)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print(f"\nDone. Imported {len(files)} CSV files into the configured database.")
    print("The data is synthetic; do not use it to make real-world ACUD investment or service decisions.")


if __name__ == "__main__":
    main()
