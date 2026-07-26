# Sprint 7 + Sprint 5 — Session Summary

**Date:** 2026-07-25
**Tests:** 20/20 OK
**Python:** 3.11–3.14

---

## Sprint 7 — Regulation & Sustainability Domain Connectors

### Connectors Created
| File | Source | Domain |
|------|--------|--------|
| `src/pitchavi/openfda.py` | FDA Food Enforcement | regulatory |
| `src/pitchavi/efsa_eurlex.py` | EUR-Lex | regulatory |
| `src/pitchavi/fooddata_central.py` | USDA FoodData Central | regulatory |
| `src/pitchavi/climatiq.py` | Climatiq/Agribalyse | sustainability |

### ResearchService Methods Added
- `enrich_with_regulatory()` — iterates OpenFDA, EFSA, FoodData Central
- `_store_regulatory_work()` — normalizes evidence with dedupe keys
- `_save_regulatory_summary()` — saves `regulatory_aggregation`
- `enrich_with_sustainability()` — uses Climatiq connector
- `_store_sustainability_work()` — normalizes sustainability evidence
- `_save_sustainability_summary()` — saves `climatiq_aggregation`

### API Endpoints Added
- `POST /v1/research-runs/{run_id}/domains/regulatory`
- `POST /v1/research-runs/{run_id}/domains/sustainability`

### Tests Added
- `test_regulatory_enrichment_stores_evidence`
- `test_sustainability_enrichment_stores_evidence`

---

## Sprint 5 — Validation, Hardening & Deployment

### Docker / Deployment
- **`Dockerfile`** — multi-stage, non-root user `pitchavi`, `HEALTHCHECK`
- **`.dockerignore`** — excludes tests, docs, venv, .env
- **`docker-compose.yml`** — `api` + `db` (PostgreSQL 16-alpine) with healthchecks
- **`ResearchStore`** — dual-backend SQLite/PostgreSQL via `DATABASE_URL`

### Observability
- **`GET /metrics`** — Prometheus metrics endpoint
- **`GET /v1/connectors/status`** — real stats from `source_requests` table

### CI/CD
- **`.github/workflows/ci.yml`** — test matrix (3.11–3.14), ruff, mypy, docker build

### Dependencies (`pyproject.toml`)
- Added: `psycopg2-binary`, `pytest`, `pytest-cov`, `httpx`, `ruff`, `mypy`

---

## Files Modified (Complete List)

### Source
- `src/pitchavi/research.py` — regulatory/sustainability/techscout methods, ScoringService fixes
- `src/pitchavi/api.py` — new endpoints, _envelope helper, metrics endpoint
- `src/pitchavi/storage.py` — PostgreSQL dual-backend support
- `src/pitchavi/openfda.py` — new connector
- `src/pitchavi/efsa_eurlex.py` — new connector
- `src/pitchavi/fooddata_central.py` — new connector
- `src/pitchavi/climatiq.py` — new connector
- `src/pitchavi/cordis.py` — techscout connector (Sprint 6)
- `src/pitchavi/nih_reporter.py` — techscout connector (Sprint 6)
- `src/pitchavi/nsf_awards.py` — techscout connector (Sprint 6)
- `src/pitchavi/scoring.py` — ScoringEngine (Sprint 4)
- `src/pitchavi/reports.py` — ReportGenerator (Sprint 4)
- `src/pitchavi/__init__.py` — version bump to 0.2.0

### Tests
- `tests/test_research.py` — added regulatory, sustainability, techscout tests; updated _service helper

### Config / Deployment
- `pyproject.toml` — dev dependencies, psycopg2
- `Dockerfile` — hardened multi-stage
- `docker-compose.yml` — added PostgreSQL service
- `.dockerignore` — new file
- `.github/workflows/ci.yml` — new CI workflow

---

## Known Issues / Next Steps

1. **Scoring unification** — `ScoringEngine` and `ScoringService` have different algorithms
2. **PDF report styling** — `generate_pdf` is minimal, needs visual enhancement
3. **`/report/export` endpoint** — not yet implemented
4. **Calibration tests** — `docs/scoring_calibration.md` cases not automated
5. **Sprint 8** — not yet defined in project docs
