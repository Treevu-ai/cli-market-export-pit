# Spec: OECD SDMX API

| Campo | Valor |
|-------|-------|
| **source** | `oecd_sdmx` |
| **Dominio PIT** | `trade` |
| **Tier** | 3 |
| **Prioridad** | Baja |
| **Auth** | `OECD_API_KEY` (registro gratuito en [data.oecd.org](https://data.oecd.org/)) |

## Valor para CLI Market

Comercio en valor añadido (TiVA), estadísticas agrícolas OECD, indicadores avanzados de mercados desarrollados.

## Endpoints

Base: `https://sdmx.oecd.org/public/rest/data/`

| Dataset | Uso |
|---------|-----|
| `STAN08BIS` | Trade in value added |
| `AGR_OUTLOOK` | Agricultural outlook |
| `MEI` | Main Economic Indicators |

Ejemplo:

```
GET /data/OECD.STI.STAN08BIS,DSD_STAN08BIS@DF_STAN08BIS/.M.EXGRVA.../all?format=jsondata
```

Header (si requerido):

```
Authorization: Bearer {OECD_API_KEY}
```

*(Verificar esquema auth actual en portal OECD al implementar.)*

## Mapeo PIT → request

Complejidad alta — SDMX requiere conocer dimension keys. Estrategia MVP:

1. Predefinir 3–5 queries template por commodity HS mapeado
2. Solo activar para `target_market` ∈ OECD members

```python
if target_market not in OECD_ISO2:
    return empty_response()
```

## Normalización (`works[]`)

```json
{
  "id": "oecd:{dataset}:{key}",
  "title": "DE import content in cocoa products 2023",
  "source": "oecd_sdmx",
  "metadata": {
    "dataset": "STAN08BIS",
    "value": 1250000000,
    "unit": "USD",
    "year": 2023,
    "country": "DE"
  }
}
```

## Agregación

```json
{
  "summary_type": "oecd_sdmx_aggregation",
  "tiva_import_content_usd": 1250000000,
  "agr_outlook_growth_pct": 3.2,
  "datasets_queried": ["STAN08BIS"]
}
```

## Scoring

Terciario; coverage `0.4` máximo. Usar como señal de validación cruzada con Comtrade/Eurostat.

## Rate limits

Con key: ~20 req/min (verificar). Sin key: muy restrictivo.

## Licencia

OECD terms of use; atribución requerida. Uso comercial generalmente permitido con atribución.

## Archivos

- `src/pit/oecd_sdmx.py`
- `tests/test_oecd_sdmx.py`

## Tests

1. Mock JSON-stat response.
2. Non-OECD market → skip.
3. SDMX parse error → graceful degradation.

## Nota de implementación

Considerar postergar a Fase D por complejidad SDMX. Alternativa: descarga bulk CSV mensual si API es frágil.
