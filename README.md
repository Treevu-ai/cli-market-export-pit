# PIT — CLI Market Export Intelligence

Motor de **inteligencia exportadora con evidencia trazable** para CLI Market. Dado un producto y mercado objetivo, consulta fuentes públicas, guarda respuestas crudas inmutables (SHA-256), normaliza evidencia y produce scores + reporte para decidir si vale la pena exportar.

**PIT** es el motor interno; **CLI Market Export Intelligence** es el producto comercial (landing + ficha de oportunidad).

## Arquitectura

```
Consulta + mercado → Research Run → Conectores (14 fuentes)
    → Raw inmutable + Evidencia normalizada → Resúmenes por dominio
    → Scoring (ScoringEngine v1.0-mvp) → Claims → Reporte JSON/PDF
```

**Dominios:** `science`, `patent`, `trend`, `trade`, `commerce`, `regulatory`, `sustainability`, `technology_scout`

## Ejecutar

```powershell
$env:PYTHONPATH = "src"
python -m uvicorn pit.api:app --reload
```

- **Landing:** http://127.0.0.1:8000/
- **Consola PIT:** http://127.0.0.1:8000/analyze.html
- **API:** http://127.0.0.1:8000/docs

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

Dominios de enrichment: `crossref`, `pubmed`, `semanticscholar`, `patent`, `trend`, `trade`, `commerce`, `regulatory`, `sustainability`, `techscout`.

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
| `PIT_DB_PATH` | SQLite DB (default: `data/pit.db`) |
| `PIT_RAW_DIR` | Raw responses (default: `data/raw`) |
| `DATABASE_URL` | PostgreSQL (`postgresql://...`) |
| `PIT_CONTACT_EMAIL` | Email para pool cortés Crossref |
| `PIT_API_KEY` | API key (header `X-API-Key`) |
| `PIT_CORS_ORIGINS` | Orígenes CORS separados por coma |
| `EPO_OPS_CONSUMER_KEY` / `SECRET` | Patentes EPO OPS |
| `FOODDATA_CENTRAL_API_KEY` | USDA FoodData Central |
| `CLIMATIQ_API_KEY` | Huella de carbono Climatiq |
| `CLIMARKET_API_KEY` / `MARKET_API_KEY` | CLI Market shelf prices e intel |
| `CLIMARKET_API_URL` / `MARKET_API_URL` | API CLI Market (default: `https://cli-market-api.fly.dev`) |
| `SEMANTICSCHOLAR_API_KEY` | Semantic Scholar (menos 429, más cuota) |

PIT carga automáticamente `.env` al iniciar (archivo en gitignore).

## Taxonomía y HS codes

Al crear un run se carga la taxonomía `cacao-functional-v1` con sinónimos (cacao/cocoa, arándano/blueberry, quinoa) y mapeos HS para Comtrade. El enrichment de `trade` resuelve el código HS automáticamente si no se pasa `hs_code`.

## CLI Market (góndola)

El dominio `commerce` consulta la API de [CLI Market](https://cli-market-api.fly.dev): comparación de precios en góndola (`/products/compare`) e inteligencia de mercado (`/v1/intel/brief`) filtrada por `target_market` y línea `supermercados`.

## Scoring

Pesos v1.0-mvp: Science 25%, Patent 15%, Trend 15%, Trade 25%, Commerce 20%. Recomendaciones: `Investigate`, `Validate`, `Deprioritize`, `Insufficient evidence`. Ver `docs/scoring_calibration.md`.

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

## Frontend

Frontend en `web-next/` — Next.js 15 (App Router) con export estático, Tailwind v4 y componentes shadcn/Radix, tema Deep Tech Blue/Teal. Tres páginas: landing (`/`), consola de análisis (`/analyze/`) y visor de reporte (`/report/?run_id=...`), todas consumiendo la API PIT vía `lib/pit-api.ts`.

**Desarrollo local:**

```powershell
cd web-next
npm install
npm run dev        # http://localhost:3000, apunta a la API con window.PIT_API_BASE si corre en otro puerto
```

**Build de producción** (`npm run build`) genera export estático en `web-next/out/` — sin servidor Node en producción. El `Dockerfile` compila este export en un stage Node y copia el resultado a `web/` dentro de la imagen final; el servidor FastAPI lo sirve como estáticos en `/`, igual que antes. Por eso mismo origin sirve API y frontend en producción, sin configuración de CORS.

Reemplaza el frontend vanilla JS/HTML anterior (ver `docs/academy_narrative_prd.md` y el historial de commits para el contexto de la migración). Borrador original en `landing/index.html`.

## Product Intelligence (agentes)

Capa multiagente opcional que genera una **Ficha de Oportunidad** (`GO` / `CONDITIONAL GO` / `PIVOT` / `NO-GO`) sobre evidencia PIT.

```powershell
pip install -e ".[agents]"
$env:PYTHONPATH = "src;."
$env:ANTHROPIC_API_KEY = "..."
python -m pit_agents.product_intelligence `
  --product "Snack proteico de quinua" `
  --market "Perú" `
  --segment "jóvenes profesionales" `
  --use-pit `
  --target-market PE `
  --output dossier.md
```

Documentación completa: `pit_agents/product_intelligence/README.md` · Spec: `pit_agents/product_intelligence/SPEC.md`

Los zips históricos v1/v2 están en `assets/archives/`.

## Repo

https://github.com/Treevu-ai/cli-market-export-pit
