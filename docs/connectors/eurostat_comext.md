# Spec: Eurostat Comext

| Campo | Valor |
|-------|-------|
| **source** | `eurostat_comext` |
| **Dominio PIT** | `trade` |
| **Tier** | 2 |
| **Prioridad** | Media-alta |
| **Auth** | Ninguna |

## Valor para CLI Market

Comercio detallado de bienes UE (hasta HS8) — importaciones por país de origen. Esencial cuando `target_market` ∈ {DE, FR, ES, IT, EU, ...}.

## Endpoints

Base Comext: `https://ec.europa.eu/eurostat/api/comext/dissemination/1.0/data/{datasetCode}`

Datasets prioritarios (verificar códigos actuales en catálogo):

| Dataset | Descripción |
|---------|-------------|
| `DS-016893` | EU trade since 1988 by HS2-HS8 (ejemplo) |
| `DS-045064` | Extra-EU trade by HS6 |

Catálogo: `GET .../comext/dissemination/1.0/dataflow`

Parámetros típicos:

```
?format=JSON&lang=EN
&reporter=DE
&partner=PE
&product=081040
&time=2020,2021,2022,2023,2024
&flow=1
```

`flow=1` = importaciones del reporter.

## Mapeo PIT → request

```python
if target_market not in EU_MEMBER_ISO2:
    return empty_response()  # skip

reporter = target_market  # o EU27_2020 para agregado UE
partner = origin_country   # PE
product = hs_code[:6]      # HS6 mínimo
```

**Restricción:** Datasets Comext no permiten descarga completa sin filtros; siempre incluir `reporter`, `partner`, `product`, `time`.

## Normalización (`works[]`)

```json
{
  "id": "eurostat:{reporter}:{partner}:{hs6}:{year}",
  "title": "DE imports from PE HS 081040 2024: €12.3M",
  "source": "eurostat_comext",
  "metadata": {
    "trade_value_eur": 12300000,
    "trade_quantity_kg": 4500000,
    "reporter": "DE",
    "partner": "PE",
    "hs_code": "081040",
    "year": 2024,
    "flow": "import"
  }
}
```

## Agregación

```json
{
  "summary_type": "eurostat_comext_aggregation",
  "import_value_eur_latest": 12300000,
  "import_growth_yoy_pct": 8.5,
  "years_available": 5,
  "reporter": "DE",
  "partner": "PE"
}
```

## Scoring

- **Coverage:** `0.85` si target EU y datos recientes.
- **Score:** `min(100, import_growth_yoy_pct * 5 + 50)` si crecimiento positivo.

## Rate limits

Sin auth; respuestas grandes. Timeout 60s; cache 14 días.

## Licencia

Eurostat open data; atribución: "Eurostat".

## Archivos

- `src/pit/eurostat_comext.py`
- `tests/test_eurostat_comext.py`

## Tests

1. `target_market=US` → skip.
2. Mock JSON-stat → parse value.
3. Sin filtros → error 400 manejado.
