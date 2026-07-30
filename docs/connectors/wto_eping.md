# Spec: WTO ePing (SPS/TBT)

| Campo | Valor |
|-------|-------|
| **source** | `wto_eping` |
| **Dominio PIT** | `regulatory` |
| **Tier** | 1 |
| **Prioridad** | Alta |
| **Auth** | API key gratuita (`WTO_API_KEY`) |

## Valor para CLI Market

Alertas de barreras sanitarias (SPS) y técnicas (TBT) notificadas por países importadores. Permite detectar cambios regulatorios *antes* de entrar en vigor: límites de residuos, etiquetado, certificaciones, embalaje.

## Endpoints

| Operación | URL base | Notas |
|-----------|----------|-------|
| Dataset metadata | `https://data.wto.org/en/dataset/ext_eping` | Documentación |
| API ePing | Portal WTO Data API | Ver OpenAPI en [apiportal.wto.org](https://apiportal.wto.org/) |

Header de autenticación (patrón WTO estándar):

```
Ocp-Apim-Subscription-Key: {WTO_API_KEY}
```

### Parámetros de búsqueda sugeridos

- `notifyingMember` — país que notifica (= mercado destino si exportamos hacia él)
- `productKeywords` — términos de `query_normalized`
- `hsCode` — desde `resolve_hs_code()`
- `icsCode` — opcional, mapeo desde taxonomía
- `notificationType` — `SPS` | `TBT` | `both`
- `dateFrom` — `from_publication_date`

## Mapeo PIT → request

```python
def build_eping_params(run: dict, hs_code: str | None) -> dict:
    return {
        "productKeywords": run["query_normalized"],
        "notifyingMember": iso_to_wto_member(run.get("target_market")),
        "hsCode": hs_code,
        "dateFrom": run.get("from_publication_date"),
        "limit": limit,
    }
```

Tabla ISO-2 → código WTO member: reutilizar/extender `ISO_TO_COMTRADE` o crear `ISO_TO_WTO` en `taxonomy.py`.

## Normalización (`works[]`)

```json
{
  "id": "eping:{notification_id}",
  "title": "EU — Draft regulation on pesticide MRL for berries",
  "source": "wto_eping",
  "published_at": "2026-01-15",
  "url": "https://eping.wto.org/en/Search/Index?notificationId=...",
  "snippet": "SPS notification covering HS 0810...",
  "metadata": {
    "notification_type": "SPS",
    "notifying_member": "EU",
    "affected_products": ["0810"],
    "measure_status": "draft",
    "comment_deadline": "2026-03-01"
  }
}
```

## Agregación

```json
{
  "summary_type": "wto_eping_aggregation",
  "notifications_count": 12,
  "sps_count": 8,
  "tbt_count": 4,
  "recent_count_12m": 3,
  "top_hazards": ["labelling", "MRL", "certification"],
  "target_market": "DE"
}
```

Integrar en `regulatory_aggregation` existente (sumar `total_records`).

## Scoring

- **Coverage:** `0.7` si ≥1 notificación relevante; `0.4` si solo históricas >2 años.
- **Score:** `min(100, notifications_count * 12 + recent_count_12m * 20)`.
- Penalizar si hay notificaciones `draft` con deadline próximo (alerta en reporte).

## Rate limits

- Tier gratuito WTO: ~60 req/min (verificar en portal al registrar key).
- Cachear respuestas por `(target_market, hs_code, query)` 24h.

## Licencia

WTO open data; atribución requerida. Uso comercial permitido con atribución.

## Archivos a crear/modificar

- `src/pit/wto_eping.py`
- `src/pit/research.py` — añadir a `enrich_with_regulatory`
- `tests/test_wto_eping.py`
- `.env.example` — `WTO_API_KEY=`

## Tests

1. Mock 200 con 3 notificaciones SPS → `works` length 3.
2. `target_market=US` filtra notificaciones US.
3. Sin API key → `RuntimeError` o skip graceful en pipeline.
4. Live (opcional): query `blueberry` + `target_market=EU`.
