# Spec: IMF Data API

| Campo | Valor |
|-------|-------|
| **source** | `imf_data` |
| **Dominio PIT** | `macro` |
| **Tier** | 3 |
| **Prioridad** | Baja |
| **Auth** | Ninguna (SDMX JSON REST) |

## Valor para CLI Market

Tipo de cambio, balanza comercial, reservas, inflación — contexto macro del mercado destino. Complemento a World Bank y BCRP.

## Endpoints

Base: `http://dataservices.imf.org/REST/SDMX_JSON.svc/`

| Operación | URL patrón |
|-----------|------------|
| Dataflows | `/Dataflow` |
| Compact data | `/CompactData/{database}/{key}` |

Databases útiles:

| DB | Uso |
|----|-----|
| `IFS` | International Financial Statistics (FX, inflación) |
| `DOT` | Direction of Trade (comercio bilateral) |
| `BOP` | Balance of Payments |

Ejemplo tipo de cambio:

```
GET /CompactData/IFS/M.PER.PX_END.XDC_USD_RATE?startPeriod=2020&endPeriod=2024
```

## Mapeo PIT → request

```python
# Para mercado destino
country_code = imf_country_code(target_market)  # PE, US, DE...

series = [
    f"M.{country_code}.PX_END.XDC_USD_RATE",      # FX
    f"M.{country_code}.PCPI_PC_CP_A_PT",           # Inflación YoY
]
```

## Normalización (`works[]`)

```json
{
  "id": "imf:IFS:PE:PX_END:2024-12",
  "title": "Peru PEN/USD exchange rate Dec 2024: 3.72",
  "source": "imf_data",
  "metadata": {
    "database": "IFS",
    "indicator": "PX_END.XDC_USD_RATE",
    "country": "PE",
    "value": 3.72,
    "period": "2024-12"
  }
}
```

## Agregación

```json
{
  "summary_type": "imf_data_aggregation",
  "fx_rate_latest": 3.72,
  "inflation_yoy_pct": 2.8,
  "trade_balance_usd": -1200000000,
  "target_market": "PE"
}
```

Fusionar con `world_bank_aggregation` y `bcrp_aggregation` en dominio `macro`.

## Scoring

Secundario; usar para alertas (FX volátil, inflación >10%).

## Rate limits

Sin auth; ser conservador. Cache 7 días.

## Licencia

IMF open data; atribución requerida.

## Archivos

- `src/pit/imf_data.py`
- `tests/test_imf_data.py`

## Tests

1. Mock CompactData JSON → parse series.
2. País sin datos → skip.
