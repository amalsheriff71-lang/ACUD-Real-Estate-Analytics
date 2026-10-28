# ACUD Prototype: Real-Estate Sales Analytics + Cohere Assistant

This prototype keeps the existing complaint API and adds a database-backed real-estate analytics API. It uses the supplied synthetic datasets and is intended for development and demonstration, not real-world investment or public-service decisions.

## Features added

- Imports real-estate source CSVs and model outputs into PostgreSQL tables prefixed with `acud_`.
- Adds live database-backed sales, collections, inventory, construction-cost, and utility aggregates.
- Recomputes a transparent seasonal-naive baseline forecast from the database monthly series when the dashboard loads. Forecast bands are heuristic, not probabilistic confidence intervals.
- Adds unsold-inventory diagnostics using price multiplier, inventory age, district transport/service indicators, and aggregate sales-funnel metrics.
- Adds a Cohere sales Q&A endpoint that receives database summaries and clearly identifies the data as synthetic.
- Updates `public/dashboard2.html` to fetch the live API before rendering and includes a Cohere question panel. The embedded snapshot is retained only as a fallback when the API is unavailable.
- Adds synthetic district traffic/access/service indicators and aggregated project lead-funnel data for prototyping. These fields must be replaced with measured data before production.

## Setup (Windows PowerShell)

1. Install Python 3.10+ and PostgreSQL 14+.
2. Create a development database and user, for example:

   ```sql
   CREATE USER acud_user WITH PASSWORD 'replace_with_a_strong_password';
   CREATE DATABASE acud_analytics OWNER acud_user;
   ```

3. In the `backend` directory, create and activate a virtual environment and install dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   Copy-Item .env.example .env
   ```

4. Edit `backend/.env` and set `DATABASE_URL`. Set `COHERE_API_KEY` to enable the assistant. Never commit `.env` or put the Cohere key in browser code.

5. From the `backend` directory, import the source CSVs and model outputs:

   ```powershell
   python seed_real_estate.py
   ```

   This replaces the prototype's `acud_*` tables on each import. Run it only against the development database. The CSVs under `data/` are synthetic. To regenerate the two supplementary demo datasets first, run `python ..\data\extend_prototype_data.py` from `backend/`.

6. Start the API from the `backend` directory:

   ```powershell
   uvicorn app.main:app --reload
   ```

   - API docs: `http://127.0.0.1:8000/docs`
   - Health: `http://127.0.0.1:8000/health`
   - Dashboard data: `http://127.0.0.1:8000/api/v1/sales/dashboard`
   - Unsold diagnostics: `http://127.0.0.1:8000/api/v1/sales/diagnostics`
   - Cohere Q&A: `POST http://127.0.0.1:8000/api/v1/sales/ask`

7. In a second terminal, serve the project root so the browser module and API requests work with CORS. From the project root:

   ```powershell
   python -m http.server 8080
   ```

   Open `http://127.0.0.1:8080/public/dashboard2.html`.

   To use another API host, set `window.ACUD_API_BASE` before the dashboard's module script in `public/dashboard2.html`.

## Main endpoints

- `GET /api/v1/sales/dashboard` — recent monthly aggregates and freshly computed seasonal-naive baseline forecasts.
- `GET /api/v1/sales/projects` — latest-month project performance.
- `GET /api/v1/sales/diagnostics` — latest district service/access signals, inventory, and aggregated sales-funnel indicators.
- `POST /api/v1/sales/ask` — evidence-grounded Cohere business Q&A; accepts `question`, optional `district_id` / `project_id`, and `language` (`en` or `ar`).

Example request body:

```json
{
  "question": "Which districts have high inventory and weak service indicators?",
  "language": "en",
  "district_id": "D09"
}
```

## Important data and modeling limits

- The supplied base data and added traffic/service/funnel fields are synthetic. Names such as “Synthetic District 01” are simulation labels, not actual ACUD district identities.
- Price premium, traffic, service availability, and conversion metrics can suggest what to investigate, but correlation does not prove that any factor caused a unit to remain unsold.
- The baseline forecast is deliberately simple. Its uncertainty bands are heuristic; replace them with time-based backtesting and calibrated prediction intervals before operational use.
- Production deployment should add authentication/authorization, rate limiting, audit logging, managed secrets, schema migrations, monitoring, and a reviewed data-retention/privacy policy. Do not expose the API publicly without these controls.
