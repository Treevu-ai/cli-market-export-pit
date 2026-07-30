# Spec: CFIA Recalls (Canadá)

| Campo | Valor |
|-------|-------|
| **source** | `cfia_canada` |
| **Dominio PIT** | `regulatory` |
| **Tier** | 3 |
| **Prioridad** | Baja-media |
| **Auth** | Ninguna |

## Valor para CLI Market

Alertas de recall del Canadian Food Inspection Agency — relevante cuando `target_market=CA`.

## Enfoque técnico

**Sin API REST documentada.** Opciones:

### Opción A — Open Government dataset

- Portal: [open.canada.ca](https://open.canada.ca/data/en/dataset)
- Buscar dataset "Recalls and Safety Alerts" — puede ofrecer CSV/JSON bulk
- Actualización periódica; descargar y indexar localmente

### Opción B — Scraping portal web

- URL: `https://recalls-rappels.canada.ca/en/search/site`
- Parsear resultados HTML o endpoint AJAX del portal
- User-Agent + rate limit 1 req/s

## Mapeo PIT → request

```python
if target_market != "CA":
    return empty_response()

params = {
    "keys": query,
    "f[0]": "category:food",  # verificar filtros del portal
    "page": 0,
}
```

## Normalización (`works[]`)

```json
{
  "id": "cfia:{recall_id}",
  "title": "Recall — Brand X frozen berries — Listeria",
  "source": "cfia_canada",
  "published_at": "2026-01-20",
  "url": "https://recalls-rappels.canada.ca/en/alert-recall/...",
  "metadata": {
    "recall_class": "Class 1",
    "hazard": "Listeria monocytogenes",
    "product": "Frozen mixed berries",
    "distribution": "National",
    "origin_country": "Peru"
  }
}
```

## Agregación

```json
{
  "summary_type": "cfia_canada_aggregation",
  "recalls_count": 2,
  "class1_count": 1,
  "hazards_top": ["Listeria"],
  "target_market": "CA"
}
```

## Scoring

Similar a RASFF: penalizar `class1_count`.

## Licencia

Open Government Licence – Canada.

## Archivos

- `src/pit/cfia_canada.py`
- `scripts/build_cfia_index.py` (si bulk CSV)
- `tests/test_cfia_canada.py`

## Tests

1. `target_market=US` → skip.
2. Mock HTML/JSON → 1 recall.
3. Origin country filter.

## Riesgo

Alta fragilidad sin API oficial; priorizar dataset bulk de open.canada.ca si disponible.
