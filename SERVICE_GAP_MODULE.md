# Resident Service Intelligence module (Amal)

All data in this repository is synthetic. Every output is labelled `demonstration_only`; nothing here is evidence about real residents or real sales.

## Files
| File | Purpose |
|---|---|
| `backend/app/analytics/service_gap.py` | Validation, area x service metrics (Wilson CIs, area-vs-rest Fisher tests with Benjamini-Hochberg), evidence grades, district association test |
| `backend/app/analytics/executive.py` | Derived sales position, pain points, weaker-vs-stronger exact permutation test, hypothesis verdict, contradictory districts, priority classes + sensitivity, readiness, dynamic insights, metric contract |
| `backend/app/routers/survey_sales.py` | `GET /service-gap`, `GET /executive?district_id=&sales_position=`; `/ask` now receives the validated analysis; legacy tables show complaint share |
| `acud-executive-dashboard.html` | 6-view executive page (brief, landscape, pain points, hypothesis test, actions, methodology) |
| `survey-sales-dashboard.html` | Previous page: new service-gap section, complaint share column, KPI label fix |
| `backend/run_service_gap_analysis.py` | Writes `outputs/service_gap_analysis.json` and `outputs/executive_brief.json` from the CSVs |
| `backend/tests/` | 33 tests: calculations, hand-calculated cases, independent pandas recomputation, API vs recomputation on a temp SQLite DB, output staleness |

## Run
```
python backend/run_service_gap_analysis.py      # regenerate outputs
python -m pytest backend/tests -q               # tests
# API: seed (backend/README.md), then: cd backend && uvicorn app.main:app
# pages: python -m http.server 8080 (project root), open /acud-executive-dashboard.html
```
The API base can be overridden with `?api=<url>`.

## Key definitions
Full machine-readable contract (formula, numerator, denominator, filter behaviour, null handling) is returned as `metric_contract` and shown on the Methodology view.
* Dissatisfied = q9 rating 1-2; satisfied = 4-5; denominator = valid answers; nulls are never imputed or counted as dissatisfied. Not-applicable cannot be measured (no such option).
* **Sales position is derived**: no sales target or official weak/good classification exists in the repo. Districts below the median latest sell-through are "weaker". It is a relative split, not a target miss.
* Group tests use the district as the unit (respondents are nested). 10 districts (5 v 5) means the smallest possible exact p is 0.0079 and power is low. Groups also differ in development stage (confounder).
* Priority classes (rules, no weights): High / Further investigation / Medium / Monitor; sensitivity to thresholds is reported (classes are threshold dependent).

## Engineering acceptance report
| Bug | Severity | Root cause | Fix | Proof |
|---|---|---|---|---|
| Correlation with a constant variable returned `p = 0.0001` (false significance) | High | NaN correlation never matched the permutation comparison | Return undefined rho/p and a "not computable" label | `test_constant_variable_gives_undefined_correlation_not_false_significance` |
| Legacy tables compared raw top-complaint counts across areas of different sample size | Medium | Count shown without denominator | Same defect was fixed independently on `main` (`top_complaint_share_pct`); this branch adopts that field in the legacy table | `test_legacy_filters_and_complaint_share_regression` |
| KPI "Selected project units sold" was the latest-month portfolio total | Low | Misleading label | Relabelled "Units sold, latest month (selection)" | dashboard render check |
| Ties made the exact Mann-Whitney p unreliable | Medium | scipy exact method assumes no ties | Own exact label-permutation with average ranks | `test_exact_mwu_hand_calculated` |

## Not tested / blocked
* **Logo and brand colours**: official logo supplied by the owner and placed at `assets/acud-logo.png` (400x207, opaque white background, shown unmodified; a higher-resolution or transparent version would look sharper on the dark header). Brand red `#ED1C24`, black and white were supplied by the owner; chart colours are validated separately.
* Cohere `/ask` integration: no API key, not executed.
* PostgreSQL: API tested only on SQLite.
* Missing data: sales targets, availability data for 5 of 10 services, travel times/coordinates, prospective-buyer flag, "don't know" option, response rates. The existing questionnaire was left unchanged.
