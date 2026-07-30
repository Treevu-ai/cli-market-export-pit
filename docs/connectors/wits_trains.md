# Spec: WITS / UNCTAD TRAINS

| Campo | Valor |
|-------|-------|
| **source** | `wits_trains` |
| **Dominio PIT** | `trade` |
| **Tier** | 1 |
| **Prioridad** | Alta |
| **Auth** | Ninguna |

## Valor para CLI Market

Aranceles MFN/preferenciales y medidas no arancelarias (NTM) por HS6. Complementa WTO Timeseries con datos UNCTAD TRAINS vía World Bank WITS.

## Endpoints

Base: `https://wits.worldbank.org/API/V1/SDMX/V21/`

| API | URL patrón |
|-----|------------|
| Data availability | `/datasource/TRN/reporter/{code}/year/{year}/partner/{partner}/product/{hs6}/datatype/reported?format=JSON` |
| Tariff schedule | `/datasource/TRN/reporter/{code}/partner/{partner}/product/{hs6}/year/{year}/datatype/reported?format=JSON` |
| Reporter list | `/datasource/TRN/reporter/all/all/all?format=JSON` |

Documentación: [WITS API User Guide](https://wits.worldbank.org/data/public/WITSAPI_UserGuide.pdf)

## Mapeo PIT → request

```python
reporter = wits_country_code(target_market)   # ISO3 o numérico WITS
partner = wits_country_code(origin_country)    # default PE
product = hs_code[:6].ljust(6, "0")
year = date.today().year - 1

url = (
    f"{base}/datasource/TRN/reporter/{reporter}/partner/{partner}"
    f"/product/{product}/year/{year}/datatype/reported?format=JSON"
)
```

Códigos país: usar ISO3 (`PER`, `USA`, `DEU`) — mapear desde ISO-2 en `taxonomy.py`.

## Normalización (`works[]`)

```json
{
  "id": "wits:{reporter}:{partner}:{hs6}:{year}",
  "title": "Applied tariff 6.0% — US imports from Peru HS 0810",
  "source": "wits_trains",
  "published_at": "2024-01-01",
  "metadata": {
    "duty_rate": 6.0,
    "duty_type": "ad_valorem",
    "ntm_count": 2,
    "hs_code": "081040",
    "reporter": "USA",
    "partner": "PER"
  }
}
```

## Agregación

```json
{
  "summary_type": "wits_trains_aggregation",
  "duty_rate_avg": 6.0,
  "ntm_count": 2,
  "hs_code": "081040",
  "years_queried": [2020, 2021, 2022, 2023, 2024]
}
```

## Scoring

Similar a `wto_timeseries`: menor arancel = mayor score. Sumar penalización por NTM count (`ntm_count * 5` restado del score).

## Rate limits

Sin auth documentada; usar backoff exponencial (429/503). Máx 1 req/s.

## Licencia

World Bank / UNCTAD open data; atribución requerida.

## Archivos

- `src/pit/wits_trains.py`
- `tests/test_wits_trains.py`

## Tests

1. Mock JSON SDMX → parse duty rate.
2. Producto sin datos → `works: []`, no error.
3. HS inválido → `WITSRequestError` con http_status.
