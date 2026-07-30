# Spec: Google Trends

| Campo | Valor |
|-------|-------|
| **source** | `google_trends` |
| **Dominio PIT** | `trend` |
| **Tier** | 2 |
| **Prioridad** | Media |
| **Auth** | `GOOGLE_TRENDS_API_KEY` (API alpha oficial) o sin key (trendspyg) |

## Valor para CLI Market

Interés de búsqueda del consumidor por keyword y país — señal de demanda real vs. volumen noticioso de GDELT.

## Opciones de implementación

### Opción A — API oficial (recomendada a medio plazo)

- Alpha: [developers.google.com/search/apis/trends](https://developers.google.com/search/apis/trends)
- Endpoint: `POST https://trends.googleapis.com/v1alpha/trends:query`
- Auth: OAuth2 / API key (según alpha terms)
- Ventajas: datos consistentemente escalados, 5 años, regiones

### Opción B — trendspyg (MVP)

- Librería: `trendspyg` (alternativa a pytrends archivado)
- Sin API key; scraping con Chrome headless
- Riesgo: inestabilidad, ToS de Google

**Recomendación PIT:** implementar interfaz `TrendConnector` con backend configurable (`official` | `trendspyg`).

## Mapeo PIT → request

```python
params = {
    "keywords": expand_query_with_synonyms(query, taxonomy),
    "geo": iso2_to_trends_geo(target_market),  # US, DE, PE
    "timeframe": f"{from_publication_date} today",
    "category": 71,  # Food & Drink (opcional)
}
```

## Normalización (`works[]`)

```json
{
  "id": "google_trends:{keyword}:{geo}:{date}",
  "title": "Search interest 'quinoa protein' in US — peak 78/100",
  "source": "google_trends",
  "published_at": "2026-01-01",
  "metadata": {
    "keyword": "quinoa protein",
    "geo": "US",
    "interest_score": 78,
    "interest_avg_12m": 45,
    "trend_direction": "rising",
    "related_queries": ["quinoa snack", "plant protein bar"]
  }
}
```

## Agregación

```json
{
  "summary_type": "google_trends_aggregation",
  "keywords_tracked": 3,
  "interest_avg": 52,
  "interest_peak": 78,
  "trend_direction": "rising",
  "related_queries_top": ["quinoa snack"],
  "geo": "US"
}
```

Combinar con `gdelt_aggregation` en dominio `trend` (peso 50/50 o preferir Trends para demanda).

## Scoring

- **Coverage:** `0.7` si interest data disponible.
- **Score:** `interest_avg` directo (ya 0–100) + bonus si `trend_direction=rising`.

## Licencia / riesgo

- API oficial: términos en evaluación (alpha).
- trendspyg: scraping — no para producción sin fallback.
- **GDELT** tiene restricción comercial pendiente; Trends puede reemplazar parcialmente.

## Archivos

- `src/pit/google_trends.py`
- `pyproject.toml` — optional dep `trendspyg` o `httpx` para API oficial
- `tests/test_google_trends.py`

## Tests

1. Mock interest over time → avg/peak.
2. Backend `official` sin key → skip.
3. Synonym expansion desde taxonomía.
