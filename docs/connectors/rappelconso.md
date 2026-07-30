# Spec: RappelConso (Francia)

| Campo | Valor |
|-------|-------|
| **source** | `rappelconso` |
| **Dominio PIT** | `regulatory` |
| **Tier** | 3 |
| **Prioridad** | Baja |
| **Auth** | Ninguna |

## Valor para CLI Market

Alertas de consumo francesas (alimentación, cosméticos) — útil cuando `target_market=FR` o como señal UE complementaria a RASFF.

## Enfoque técnico

API OpenData France:

Base: `https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/rappelconso-v2-gtin-trie/records`

| Parámetro | Uso |
|-----------|-----|
| `where` | `libelle like "{query}"` |
| `limit` | `limit` |
| `order_by` | `date_de_publication desc` |

Documentación: [data.economie.gouv.fr](https://data.economie.gouv.fr/explore/dataset/rappelconso-v2-gtin-trie/)

## Mapeo PIT → request

```python
if target_market not in ("FR", "EU"):
    return empty_response()  # o siempre ejecutar como señal EU

params = {
    "where": f"libelle LIKE '%{sanitize(query)}%'",
    "limit": limit,
    "order_by": "date_de_publication DESC",
}
```

Filtrar por `categorie_produit` = alimentación.

## Normalización (`works[]`)

```json
{
  "id": "rappelconso:{id_rappel}",
  "title": "Rappel — Chocolat noir — allergène non déclaré",
  "source": "rappelconso",
  "published_at": "2026-02-05",
  "url": "https://rappel.conso.gouv.fr/...",
  "metadata": {
    "id_rappel": "2026-02-001",
    "categorie": "alimentation",
    "risque": "Allergie",
    "marque": "Example",
    "gtin": "3760123456789",
    "pays_origine": "Pérou"
  }
}
```

## Agregación

```json
{
  "summary_type": "rappelconso_aggregation",
  "alerts_count": 3,
  "allergen_count": 2,
  "target_market": "FR"
}
```

Integrar en `regulatory_aggregation` junto RASFF/ePing.

## Scoring

- **Coverage:** `0.4` (nicho FR).
- Penalizar si `pays_origine` match origen exportador.

## Licence

Licence Ouverte / Open Licence (France).

## Rate limits

API publique — ~10 req/s razonable. Cache 24h.

## Archivos

- `src/pit/rappelconso.py`
- `tests/test_rappelconso.py`

## Tests

1. Mock OpenData response → parse alerts.
2. `target_market=PE` → skip o peso reducido.
3. Sanitize SQL-like injection en `where` clause.
