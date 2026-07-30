# Spec: ClinicalTrials.gov

| Campo | Valor |
|-------|-------|
| **source** | `clinicaltrials` |
| **Dominio PIT** | `science` |
| **Tier** | 3 |
| **Prioridad** | Baja-media |
| **Auth** | Ninguna |

## Valor para CLI Market

Ensayos clínicos sobre ingredientes funcionales (probióticos, flavonoides, proteínas vegetales). Señal de innovación y claims de salud en mercados regulados.

## Endpoints

API v2: `https://clinicaltrials.gov/api/v2/studies`

| Parámetro | Uso |
|-----------|-----|
| `query.term` | `query_normalized` |
| `filter.overallStatus` | `RECRUITING,COMPLETED` |
| `filter.advanced` | `AREA[StartDate]RANGE[{from},MAX]` |
| `pageSize` | `limit` |
| `format` | `json` |

Ejemplo:

```
GET /api/v2/studies?query.term=high+flavanol+cocoa&pageSize=10&format=json
```

## Mapeo PIT → request

```python
params = {
    "query.term": query,
    "pageSize": min(limit, 50),
    "filter.advanced": f"AREA[StartDate]RANGE[{from_publication_date},MAX]",
}
```

## Normalización (`works[]`)

```json
{
  "id": "nct:{nctId}",
  "title": "Effects of cocoa flavanols on cardiovascular health",
  "source": "clinicaltrials",
  "published_at": "2023-05-01",
  "url": "https://clinicaltrials.gov/study/{nctId}",
  "metadata": {
    "nct_id": "NCT05123456",
    "status": "RECRUITING",
    "phase": "PHASE2",
    "conditions": ["Cardiovascular Diseases"],
    "interventions": ["Cocoa flavanol supplement"],
    "sponsor": "University X",
    "enrollment": 200
  }
}
```

## Agregación

```json
{
  "summary_type": "clinicaltrials_aggregation",
  "trials_count": 6,
  "recruiting_count": 2,
  "completed_count": 4,
  "phases": ["PHASE2", "PHASE3"]
}
```

Integrar en pipeline `science` (post-OpenAlex) o como sub-paso opcional.

## Scoring

- **Coverage:** `0.5` si ≥1 trial; bonus si `target_market` match en locations.
- **Score:** `min(100, trials_count * 15 + completed_count * 10)`.

## Rate limits

~50 req/min sin key (verificar docs actuales). User-Agent con contacto.

## Licencia

NIH public domain.

## Archivos

- `src/pit/clinicaltrials.py`
- `tests/test_clinicaltrials.py`

## Tests

1. Mock 2 studies → parse NCT IDs.
2. Query sin resultados → empty.
3. Filtro fecha respeta `from_publication_date`.
