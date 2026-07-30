# Spec: RASFF Window (UE)

| Campo | Valor |
|-------|-------|
| **source** | `rasff` |
| **Dominio PIT** | `regulatory` |
| **Tier** | 1 |
| **Prioridad** | Alta |
| **Auth** | Ninguna |

## Valor para CLI Market

~31.000 alertas públicas UE: recalls, rechazos en frontera, contaminantes (Salmonella, pesticidas, alérgenos). Señal de riesgo reputacional y barreras de entrada para exportadores hacia la UE.

## Endpoints

API pública no documentada oficialmente pero estable:

| Operación | URL |
|-----------|-----|
| Búsqueda (UI backend) | `https://webgate.ec.europa.eu/rasff-window/backend/public/notification/search` |
| Detalle notificación | `https://webgate.ec.europa.eu/rasff-window/backend/public/notification/view/id/{id}/` |

**Importante:** No hay endpoint de búsqueda full-text documentado; implementar:

1. POST/GET search con filtros de producto (ver network tab del UI)
2. O búsqueda por categoría + filtro local por keywords de `query_normalized`

User-Agent obligatorio; rate limit ≤1 req/s.

## Mapeo PIT → request

```python
search_body = {
    "productDescription": query,
    "productCategory": map_to_rasff_category(query),  # ej. "Fruits and vegetables"
    "notificationDateFrom": from_publication_date,
    "limit": limit,
}
```

Filtrar post-respuesta por:
- País origen = `origin_country` (default PE)
- Mercado destino relevante si `target_market` in EU

## Normalización (`works[]`)

```json
{
  "id": "rasff:{reference}",
  "title": "Salmonella in frozen blueberries — border rejection",
  "source": "rasff",
  "published_at": "2026-02-10",
  "url": "https://webgate.ec.europa.eu/rasff-window/screen/notification/{id}",
  "snippet": "Salmonella spp detected in frozen blueberries from Peru",
  "metadata": {
    "reference": "2026.0234",
    "risk_decision": "serious",
    "notification_type": "border rejection",
    "hazards": ["Salmonella spp."],
    "origin_country": "Peru",
    "product_category": "Fruits and vegetables"
  }
}
```

## Agregación

```json
{
  "summary_type": "rasff_aggregation",
  "alerts_count": 5,
  "serious_count": 2,
  "border_rejection_count": 3,
  "hazards_top": ["Salmonella", "pesticide residues"],
  "recent_12m_count": 1,
  "origin_country": "PE"
}
```

Integrar en `regulatory_aggregation`. Alerta en reporte si `serious_count > 0` para producto/categoría similar.

## Scoring

- **Coverage:** `0.6` si hay alertas; `0.8` si categoría exacta match.
- **Score:** `max(0, 100 - serious_count * 25 - border_rejection_count * 10)`.

## Licencia

**CC BY 4.0** — atribución: "European Commission – RASFF".

## Riesgos técnicos

- API no oficial; puede cambiar sin aviso.
- Implementar fallback graceful y monitor de health en `/v1/connectors/status`.
- Considerar cache local de búsquedas frecuentes.

## Archivos

- `src/pit/rasff.py`
- `tests/test_rasff.py`

## Tests

1. Mock detalle notificación → parse hazards.
2. Keyword filter post-search.
3. 0 resultados → coverage baja, no error.
