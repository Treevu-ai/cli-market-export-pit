# Spec: USDA FAS Open Data (PSD / GATS / ESR)

| Campo | Valor |
|-------|-------|
| **source** | `usda_fas` |
| **Dominio PIT** | `trade` |
| **Tier** | 1 |
| **Prioridad** | Alta |
| **Auth** | `USDA_FAS_API_KEY` (registro gratuito) |

## Valor para CLI Market

Tres datasets críticos para mercado destino **US**:

1. **PSD** — oferta, demanda, stocks por commodity/país
2. **GATS** — comercio agro bilateral (complementa Comtrade)
3. **ESR** — ventas de exportación semanales hacia EE.UU.

## Endpoints

Portal: [apps.fas.usda.gov/opendataweb](https://apps.fas.usda.gov/opendataweb/home)

| API | Base path (aprox.) | Uso |
|-----|-------------------|-----|
| PSD commodities | `/api/psd/commodities` | Catálogo |
| PSD data | `/api/psd/commodity/{code}/country/{country}/year/{year}` | Oferta/demanda |
| GATS | `/api/gats/...` | Flujos comercio agro |
| ESR | `/api/esr/...` | Export sales semanales |

Header:

```
X-Api-Key: {USDA_FAS_API_KEY}
```

*(Confirmar nombre exacto del header en OpenAPI del portal al implementar.)*

## Mapeo PIT → request

Solo activo si `target_market == "US"` (o incluir datos globales PSD para contexto).

```python
commodity_code = usda_commodity_map(query)  # ej. "cocoa" → "2231000"
country_code = "PE"  # origen
years = range(from_year, current_year)
```

Mapeo commodity en `taxonomy.py` junto a HS codes.

## Normalización (`works[]`)

```json
{
  "id": "usda_psd:2231000:PE:2025",
  "title": "Peru cocoa exports 2025: 95,000 MT",
  "source": "usda_fas",
  "metadata": {
    "dataset": "PSD",
    "commodity": "Cocoa Beans",
    "attribute": "Exports",
    "value_mt": 95000,
    "country": "PE",
    "market_year": "2024/25"
  }
}
```

## Agregación

```json
{
  "summary_type": "usda_fas_aggregation",
  "psd_export_mt": 95000,
  "psd_import_us_mt": 420000,
  "gats_trade_value_usd": 125000000,
  "esr_weekly_net_sales_mt": 1200,
  "commodity_code": "2231000",
  "target_market": "US"
}
```

## Scoring

- **Coverage:** `0.85` si target US y datos PSD+GATS; `0.5` solo PSD global.
- **Score:** `esr_weekly_net_sales_mt` trend positivo + import US alto → mayor score.

## Rate limits

Verificar en portal FAS; típicamente generoso con key.

## Licencia

USDA public domain / open government data.

## Archivos

- `src/pit/usda_fas.py`
- `tests/test_usda_fas.py`

## Tests

1. `target_market=DE` → skip ESR, opcional PSD global.
2. Mock PSD → export tonnes.
3. Sin API key → connector no configurado.
