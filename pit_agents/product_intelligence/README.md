# CLI Market Product Intelligence

Capa multiagente que produce una **Ficha de Oportunidad de Producto** (GO / CONDITIONAL GO / PIVOT / NO-GO) usando evidencia trazable de **PIT** cuando está disponible.

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `SPEC.md` | Especificación operativa v2.0 (9 actores, flujo, criterios) |
| `instructions.py` | Prompts estructurados importables |
| `runner.py` | Orquestador OpenAI Agents SDK |
| `adapters/pit_context.py` | Cliente HTTP PIT → snapshots para agentes |

## Instalación

Desde la raíz del repo:

```powershell
pip install -e ".[agents]"
```

Dependencias opcionales: `anthropic`, `pydantic`, `python-dotenv`.

## Modo 1 — Con PIT (recomendado)

1. Levanta la API PIT:

```powershell
$env:PYTHONPATH = "src"
python -m uvicorn pit.api:app --reload
```

2. Ejecuta el análisis con pipeline completo PIT + agentes:

```powershell
$env:PYTHONPATH = "src;."
$env:ANTHROPIC_API_KEY = "..."
python -m pit_agents.product_intelligence `
  --product "Snack proteico de quinua" `
  --market "Perú" `
  --segment "jóvenes profesionales" `
  --stage "concepto" `
  --use-pit `
  --target-market PE `
  --save-context data/pit_context.json `
  --output dossier.md
```

Flujo:

1. `POST /v1/research-runs/full` en PIT
2. `GET /v1/research-runs/{id}/report`
3. Mapeo a contextos científico / mercado / regulatorio
4. Orquestación multiagente → Ficha ejecutiva

## Modo 2 — Reutilizar un run PIT existente

```powershell
python -m pit_agents.product_intelligence `
  --product "Arándano orgánico" `
  --market "US" `
  --segment "retail premium" `
  --pit-run-id "<uuid>" `
  --output dossier.md
```

## Modo 3 — Snapshots JSON (legacy v1)

Sin PIT en vivo, usando archivos estáticos:

```powershell
$env:CLI_MARKET_CONTEXT_FILE = "./data/cli_market_snapshot.json"
$env:SCIENTIFIC_CONTEXT_FILE = "./data/scientific_snapshot.json"
$env:REGULATORY_CONTEXT_FILE = "./data/regulatory_snapshot.json"
python -m pit_agents.product_intelligence --skip-pit --product "..." --market "..." --segment "..."
```

## Relación PIT ↔ Agentes

| Capa | Salida | Rol |
|------|--------|-----|
| **PIT** | `Investigate` / `Validate` / `Deprioritize` + score numérico | Evidencia trazable por dominio |
| **Agentes** | `GO` / `CONDITIONAL GO` / `PIVOT` / `NO-GO` | Decisión ejecutiva y ficha comercial |

El adaptador `pit_context.py` incluye `pit_recommendation` y `pit_opportunity_score` en cada snapshot para que los agentes alineen su decisión con la evidencia base.

## Variables de entorno

| Variable | Uso |
|----------|-----|
| `ANTHROPIC_API_KEY` | Requerida para el runner |
| `PIT_API_URL` | Base URL PIT (default `http://127.0.0.1:8000`) |
| `PIT_API_KEY` | Header `X-API-Key` si la API está protegida |
| `CLI_MARKET_CONTEXT_FILE` | Snapshot mercado (modo legacy) |
| `SCIENTIFIC_CONTEXT_FILE` | Snapshot ciencia (modo legacy) |
| `REGULATORY_CONTEXT_FILE` | Snapshot regulación (modo legacy) |

## Archivos históricos

Los zips originales v1/v2 están en `assets/archives/` como referencia. El código vivo está en este directorio.
