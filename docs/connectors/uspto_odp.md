# Spec: USPTO Open Data Portal

| Campo | Valor |
|-------|-------|
| **source** | `uspto_odp` |
| **Dominio PIT** | `patent` |
| **Tier** | 2 |
| **Prioridad** | Media |
| **Auth** | `USPTO_ODP_API_KEY` (gratuita, cuenta USPTO.gov) |

## Valor para CLI Market

Patentes y solicitudes US — complementa EPO OPS cuando `target_market=US`. Relevante para ingredientes funcionales, formulaciones, packaging.

## Endpoints

Base: `https://api.uspto.gov`

| Método | Path | Uso |
|--------|------|-----|
| GET | `/api/v1/patent/applications/search` | Búsqueda por query |
| POST | `/api/v1/patent/applications/search` | Búsqueda JSON payload |
| GET | `/api/v1/patent/applications/{appNumber}` | Detalle |

Header:

```
X-API-Key: {USPTO_ODP_API_KEY}
```

Ejemplo GET:

```
GET /api/v1/patent/applications/search?q=high+flavanol+cocoa&limit=25&sort=applicationMetaData.filingDate desc
```

## Mapeo PIT → request

```python
params = {
    "q": query,
    "limit": limit,
    "sort": "applicationMetaData.filingDate desc",
    "rangeFilters": f"applicationMetaData.filingDate {from_publication_date}:{today}",
}
```

Solo activar si `target_market` es `US` o `None` (global); para otros mercados, ejecutar como señal secundaria con peso reducido.

## Normalización (`works[]`)

```json
{
  "id": "uspto:{applicationNumber}",
  "title": "High-flavanol cocoa extract composition",
  "source": "uspto_odp",
  "published_at": "2024-06-15",
  "url": "https://data.uspto.gov/...",
  "metadata": {
    "application_number": "17/123456",
    "patent_number": "US11234567",
    "filing_date": "2024-06-15",
    "assignee": "Example Corp",
    "inventors": ["Smith, J."],
    "cpc_codes": ["A23G1/00"]
  }
}
```

## Agregación

```json
{
  "summary_type": "uspto_odp_aggregation",
  "patents_count": 8,
  "applications_count": 15,
  "top_assignees": ["Mars Inc", "Nestlé"],
  "recent_24m_count": 5
}
```

Fusionar con `epo_ops_aggregation` en dominio `patent` (sumar counts, dedupe por familia si posible).

## Scoring

Extender `estimate_score` patent: `min(100, (epo_count + uspto_count) * 4)`.

## Rate limits

Verificar en portal USPTO; típicamente 60 req/min con key.

## Licencia

USPTO public domain.

## Archivos

- `src/pit/uspto_odp.py`
- `src/pit/research.py` — `enrich_with_patent` (ejecutar EPO + USPTO)
- `tests/test_uspto_odp.py`

## Tests

1. Sin API key → skip.
2. Mock search → 3 applications.
3. Dedupe con EPO por título similar (fase 2).
