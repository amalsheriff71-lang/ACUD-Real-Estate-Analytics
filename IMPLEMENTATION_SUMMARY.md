# ACUD Prototype Upgrade Summary

## Implemented in this package

1. **PostgreSQL-backed data import**: `backend/seed_real_estate.py` imports the base CSVs and model outputs to `acud_*` tables.
2. **Live dashboard API**: `GET /api/v1/sales/dashboard` computes 24-month history and summary KPIs from the database and generates a simple seasonal-naive forecast each request.
3. **Dynamic Dashboard 2**: `public/dashboard2.html` fetches the API before rendering; the embedded dataset remains a fallback only. A status strip reports live versus fallback mode.
4. **Unsold inventory diagnostics**: `GET /api/v1/sales/diagnostics` joins inventory, district service/access indicators, and aggregate lead-funnel metrics.
5. **Cohere sales assistant**: `POST /api/v1/sales/ask` answers questions with database-derived evidence, optional district/project filters, and explicit synthetic-data caveats.
6. **Additional prototype features**: `data/extend_prototype_data.py` creates clearly labeled synthetic traffic/access/service and project-level funnel indicators. No individual-level customer data is generated.
7. **Secrets hygiene**: the uploaded `.env` file has been excluded from this deliverable; use `backend/.env.example` to configure local secrets.

## Validation performed

- Python syntax compilation passed for the new API router, app wiring, and import scripts.
- Imported all 30 CSVs into a temporary SQLite database to smoke-test the import pipeline.
- Called the dashboard, diagnostics, and project-performance functions against that temporary database. The dashboard returned 24 months and 126 forecast rows; diagnostics returned 10 district rows and 40 project rows.
- The Cohere call itself requires a valid `COHERE_API_KEY` and was not tested against the external service.

## Known prototype limitations

- All base and newly generated demo data is synthetic. Do not interpret it as actual ACUD market evidence.
- The new forecast is a simple seasonal-naive baseline with heuristic ranges. Use time-based backtesting and calibrated uncertainty before production.
- The older anomaly/risk/forecast evaluation tables in the existing dashboard remain supplied model outputs; they are not retrained automatically by this prototype API.
- For production, add authentication, role-based access, migrations, monitoring, and managed secrets before exposing endpoints.
