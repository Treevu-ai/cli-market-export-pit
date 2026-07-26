# PIT CLI Market Export Intelligence

Motor de **inteligencia exportadora con evidencia trazable** para CLI Market. Dado un producto y mercado objetivo, consulta fuentes públicas, guarda respuestas crudas inmutables (SHA-256), normaliza evidencia y produce scores + reporte para decidir si vale la pena exportar.

**PIT** es el motor interno; **CLI Market Export Intelligence** es el producto comercial (landing + ficha de oportunidad).

## Arquitectura

```
Consulta + mercado → Research Run → Conectores (14 fuentes)
    → Raw inmutable + Evidencia normalizada → Resúmenes por dominio
    → Scoring (ScoringEngine v1.0-mvp) → Claims → Reporte JSON/PDF
```

**Dominios:** `science`, `patent`, `trend`, `trade`, `regulatory`, `sustainability`, `technology_scout`

## Ejecutar

```powershell
$env:PYTHONPATH = "src"
python -m uvicorn pitchavi.api:app --reload
```

API: http://127.0.0.1:8000/docs

Docker:

```powershell
docker compose up --build
```

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/v1/research-runs` | Run científico (OpenAlex) |
| POST | `/v1/research-runs/full` | Pipeline completo multi-dominio |
| POST | `/v1/research-runs/{id}/enrich/{domain}` | Enrichment por dominio |
| GET | `/v1/research-runs/{id}` | Detalle con evidencia |
| GET | `/v1/research-runs/{id}/report` | Reporte JSON |
| GET | `/v1/research-runs/{id}/report.pdf` | Reporte PDF |
| GET | `/v1/connectors/status` | Salud de conectores |

Dominios de enrichment: `crossref`, `pubmed`, `semanticscholar`, `patent`, `trend`, `trade`, `regulatory`, `sustainability`, `techscout`.

## Ejemplo — pipeline completo

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/v1/research-runs/full" `
  -ContentType "application/json" `
  -Body '{"query":"high-flavanol cocoa powder","target_market":"US","limit":10}'
```

## Variables de entorno

| Variable | Descripción |
|----------|-------------|
| `PITCHAVI_DB_PATH` | SQLite DB (default: `data/pitchavi.db`) |
| `PITCHAVI_RAW_DIR` | Raw responses (default: `data/raw`) |
| `DATABASE_URL` | PostgreSQL (`postgresql://...`) |
| `PITCHAVI_CONTACT_EMAIL` | Email para pool cortés Crossref |
| `PITCHAVI_API_KEY` | API key (header `X-API-Key`) |
| `PITCHAVI_CORS_ORIGINS` | Orígenes CORS separados por coma |
| `EPO_OPS_CONSUMER_KEY` / `SECRET` | Patentes EPO OPS |
| `FOODDATA_CENTRAL_API_KEY` | USDA FoodData Central |
| `CLIMATIQ_API_KEY` | Huella de carbono Climatiq |

## Taxonomía y HS codes

Al crear un run se carga la taxonomía `cacao-functional-v1` con sinónimos (cacao/cocoa, arándano/blueberry, quinoa) y mapeos HS para Comtrade. El enrichment de `trade` resuelve el código HS automáticamente si no se pasa `hs_code`.

## Scoring

Pesos v1.0-mvp: Science 30%, Patent 20%, Trend 20%, Trade 30%. Recomendaciones: `Investigate`, `Validate`, `Deprioritize`, `Insufficient evidence`. Ver `docs/scoring_calibration.md`.

## Tests

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

## Demo arándano

```powershell
$env:PYTHONPATH = "src"
python scripts/demo_arandano.py
```

## Landing comercial

Borrador estático en `landing/index.html` (hero + CTA según PRD).

## Repo

https://github.com/Treevu-ai/cli-market-export-pit
