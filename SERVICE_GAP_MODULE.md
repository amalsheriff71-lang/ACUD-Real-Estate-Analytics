# Resident Service Gap module (Amal)

Files: `backend/app/analytics/service_gap.py` (all calculations), `backend/app/routers/survey_sales.py` (`GET /api/v1/survey-sales/service-gap[?district_id=]`, `/ask` now grounded in it), `survey-sales-dashboard.html` (new section), `backend/run_service_gap_analysis.py` (CSV run, writes `outputs/service_gap_analysis.json`), `backend/tests/test_service_gap.py`.

Run: `python backend/run_service_gap_analysis.py` · tests: `python -m pytest backend/tests -q` · API: seed DB as in `backend/README.md`, start uvicorn, open the dashboard.

Metric formulas, evidence-grade criteria, thresholds (`PARAMS`) and provenance are returned in every API response (`metric_definitions`, `grade_criteria`, `parameters`, `data_provenance`).

Contract keys: module, schema_version, area_id, analysis_status (`valid` | `demonstration_only` | `insufficient_data`), data_mode, service_findings, service_priority, commercial_context, alternative_explanations, recommended_actions (each with supports_finding_ids), missing_data, limitations, data_provenance, data_quality.

All repository data is synthetic; status is therefore always `demonstration_only`.
