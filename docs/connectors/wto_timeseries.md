# Spec: WTO Timeseries (aranceles y comercio)

| Campo | Valor |
|-------|-------|
| **source** | `wto_timeseries` |
| **Dominio PIT** | `trade` |
| **Tier** | 1 |
| **Prioridad** | Alta |
| **Auth** | `WTO_API_KEY` (misma key que ePing) |

## Valor para CLI Market

Aranceles MFN, preferenciales y consolidados por producto y mercado destino. Responde: *¿qué arancel paga mi producto al entrar?* y *¿hay ventaja preferencial vs competidores?*

## Endpoints

Base: `https://api.wto.org/timeseries/v1`

| Endpoint | Uso |
|----------|-----|
| `GET /data` | Series temporales con filtros |
| Query Builder | [apiportal.wto.org](https://apiportal.wto.org/) — generar URLs de prueba |

Indicadores clave (códigos a confirmar en catálogo WTO):

- Arancel MFN aplicado (HS6)
- Arancel preferencial (por acuerdo comercial)
- Arancel consolidado (bound)
- Volumen importaciones (complemento Comtrade)

Header:

```
Ocp-Apim-Subscription-Key: {WTO_API_KEY}
```

## Mapeo PIT → request

```python
params = {
    "reporter": iso_to_wto_member(target_market),      # país importador
    "partner": iso_to_wto_member("PE"),                  # país exportador (origen; configurable)
    "product": hs_code[:6],                              # HS6
    "startYear": from_year,
    "endYear": current_year - 1,
    "indicator": "TP_A_0010",  # placeholder — verificar código real
}
```

**Nota:** El país exportador debería ser configurable (`origin_country` en research run; default `PE` para CLI Market Perú).

## Normalización (`works[]`)

```json
{
  "id": "wto_tariff:{reporter}:{hs6}:{year}",
  "title": "MFN applied tariff 8.5% — DE imports HS 1806",
  "source": "wto_timeseries",
  "published_at": "2025-01-01",
  "url": "https://timeseries.wto.org/",
  "snippet": "Applied MFN ad valorem 8.5% for cocoa preparations",
  "metadata": {
    "tariff_type": "MFN_applied",
    "rate_percent": 8.5,
    "hs_code": "180610",
    "reporter": "DE",
    "partner": "PE",
    "year": 2024,
    "preferential_rate": 0.0,
    "trade_agreement": "EU-Peru FTA"
  }
}
```

## Agregación

```json
{
  "summary_type": "wto_timeseries_aggregation",
  "mfn_rate_latest": 8.5,
  "preferential_rate_latest": 0.0,
  "tariff_advantage": true,
  "years_available": 5,
  "hs_code": "180610",
  "reporter": "DE"
}
```

## Scoring

- **Coverage:** `0.8` si hay tarifa para HS6 + año reciente; `0.0` sin HS.
- **Score:** inverso del arancel — `max(0, 100 - mfn_rate_latest * 5)`; bonus +15 si tarifa preferencial < MFN.

## Rate limits

Misma key WTO; compartir rate limit con ePing. Cache 7 días (aranceles cambian poco).

## Licencia

WTO open data; atribución requerida.

## Archivos

- `src/pit/wto_timeseries.py`
- `src/pit/research.py` — `enrich_with_trade` o paso post-Comtrade
- `tests/test_wto_timeseries.py`

## Tests

1. HS code ausente → skip con coverage 0.
2. Mock tarifa MFN 12% → score penalizado.
3. Mock tarifa preferencial 0% → `tariff_advantage: true`.
