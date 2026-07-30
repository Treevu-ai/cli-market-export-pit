# Spec: FAOSTAT (FAO)

| Campo | Valor |
|-------|-------|
| **source** | `faostat` |
| **Dominio PIT** | `trade` (oferta global) |
| **Tier** | 1 |
| **Prioridad** | Alta |
| **Auth** | Ninguna |

## Valor para CLI Market

Producción, comercio agrícola, balances alimentarios y precios al consumidor en 180+ países (1961–presente). Contexto competitivo: *¿quién produce y cuánto exporta mi commodity?*

## Endpoints

Base: `https://fenixservices.fao.org/faostat/api/v1`

| Endpoint | Uso |
|----------|-----|
| `GET /en/groupsanddomains` | Catálogo de dominios |
| `GET /en/definitions/domain/{code}` | Metadatos y dimensiones |
| `GET /en/data/{domain}?area=...&item=...&element=...&year=...` | Datos |

Dominios prioritarios:

| Código | Descripción |
|--------|-------------|
| `QCL` | Producción cultivos y ganadería |
| `TCL` | Comercio cultivos/ganadería |
| `FBS` | Balances alimentarios |
| `CP` | Índices de precios al consumidor |
| `EI` | Emisiones agroambientales |

Bulk (opcional): `https://bulks-faostat.fao.org/production/datasets_E.json`

## Mapeo PIT → request

Mapear `query_normalized` → FAOSTAT `item` code vía tabla en `taxonomy.py`:

```python
FAOSTAT_ITEMS = {
    "cacao": "661",       # Cocoa beans
    "blueberry": "552",   # Blueberries (verificar código)
    "quinoa": "92",       # Quinoa
}
```

```python
params = {
    "area": faostat_area_codes(["PE", target_market, "5000"]),  # 5000 = World
    "item": faostat_item_code(query),
    "element": "2510",  # Production quantity (tonnes) — verificar por dominio
    "year": f"{from_year},{current_year}",
    "output_type": "objects",
}
```

## Normalización (`works[]`)

```json
{
  "id": "faostat:QCL:PER:661:2023",
  "title": "Peru cocoa production 2023: 145,000 tonnes",
  "source": "faostat",
  "published_at": "2023-01-01",
  "metadata": {
    "domain": "QCL",
    "area": "PER",
    "item": "661",
    "element": "2510",
    "value": 145000,
    "unit": "tonnes",
    "year": 2023
  }
}
```

## Agregación

```json
{
  "summary_type": "faostat_aggregation",
  "production_tonnes_origin": 145000,
  "production_tonnes_world": 5200000,
  "export_tonnes_origin": 120000,
  "import_tonnes_target": 85000,
  "price_index_target": 112.5,
  "origin_share_world_pct": 2.8
}
```

## Scoring

- **Coverage:** `0.7` si hay producción origen + import target; `0.4` solo producción.
- **Score:** basado en `origin_share_world_pct` (nicho = oportunidad diferenciada) y crecimiento YoY.

## Licencia

**CC BY-NC-SA 3.0 IGO** — revisar uso comercial del producto CLI Market. Atribución: "FAO FAOSTAT".

## Rate limits

Sin key; ser conservador (≤2 req/s). Cache 30 días.

## Archivos

- `src/pit/faostat.py`
- `src/pit/taxonomy.py` — mapeo producto → FAOSTAT item codes
- `tests/test_faostat.py`

## Tests

1. Mock QCL data → production tonnes parseado.
2. Producto sin mapeo FAOSTAT → skip graceful.
3. Live: `quinoa` + area `PER`.
