# Spec: World Bank Indicators API

| Campo | Valor |
|-------|-------|
| **source** | `world_bank` |
| **Dominio PIT** | `macro` |
| **Tier** | 2 |
| **Prioridad** | Media |
| **Auth** | Ninguna |

## Valor para CLI Market

Contexto del mercado destino: PIB, población, costos logísticos (LPI 2.0), comercio como % PIB. Complementa BCRP (solo Perú) con datos del país importador.

## Endpoints

Base: `https://api.worldbank.org/v2`

| Endpoint | Uso |
|----------|-----|
| `GET /country/{iso3}/indicator/{code}` | Serie temporal |
| `GET /country/all/indicator/{code}` | Comparación global |

Indicadores prioritarios:

| Código | Descripción |
|--------|-------------|
| `NY.GDP.MKTP.CD` | PIB (USD corrientes) |
| `SP.POP.TOTL` | Población |
| `LP.LPI.OVRL.XQ` | LPI overall (verificar código LPI 2.0) |
| `NE.TRD.GNFS.ZS` | Comercio % PIB |
| `FP.CPI.TOTL.ZG` | Inflación |

Parámetros: `?format=json&per_page=50&date=2019:2024`

## Mapeo PIT → request

```python
country_iso3 = iso2_to_iso3(target_market)  # DE → DEU
indicators = ["NY.GDP.MKTP.CD", "SP.POP.TOTL", "LP.LPI.OVRL.XQ"]

for code in indicators:
    url = f"{base}/country/{country_iso3}/indicator/{code}?format=json&date={from_year}:{current_year}"
```

## Normalización (`works[]`)

```json
{
  "id": "world_bank:DEU:NY.GDP.MKTP.CD:2024",
  "title": "Germany GDP 2024: $4.5T",
  "source": "world_bank",
  "metadata": {
    "indicator": "NY.GDP.MKTP.CD",
    "country": "DEU",
    "value": 4500000000000,
    "year": 2024,
    "unit": "USD"
  }
}
```

## Agregación

```json
{
  "summary_type": "world_bank_aggregation",
  "gdp_usd_latest": 4500000000000,
  "population_latest": 84000000,
  "lpi_score_latest": 4.1,
  "trade_pct_gdp": 88.5,
  "inflation_pct": 2.3,
  "target_market": "DE"
}
```

## Scoring

- **Coverage:** `0.6` si ≥3 indicadores; `0.3` parcial.
- **Score:** LPI alto (>3.5) + PIB creciente → `macro` score 60–80.

## Rate limits

Sin auth; sin límite estricto documentado. Cache 30 días.

## Licencia

World Bank open data; atribución requerida.

## Archivos

- `src/pit/world_bank.py`
- `src/pit/research.py` — nuevo paso `enrich_with_macro` o extender BCRP
- `tests/test_world_bank.py`

## Tests

1. Mock GDP series → latest value.
2. País inválido → empty works.
3. Combinar con `bcrp_aggregation` en reporte macro.
