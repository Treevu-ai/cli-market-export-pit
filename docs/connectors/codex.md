# Spec: Codex Alimentarius

| Campo | Valor |
|-------|-------|
| **source** | `codex` |
| **Dominio PIT** | `regulatory` |
| **Tier** | 3 |
| **Prioridad** | Media (alto valor, sin API oficial) |
| **Auth** | Ninguna |

## Valor para CLI Market

Estándares internacionales FAO/WHO de referencia: etiquetado, aditivos, cacao, frutas, contaminantes. Base para armonización regulatoria en exportación.

## Enfoque técnico

**No existe API REST oficial.** Estrategias:

### Estrategia A — Índice local (recomendada)

1. Script one-time `scripts/build_codex_index.py`:
   - Scrapear tabla en `https://www.fao.org/fao-who-codexalimentarius/codex-texts/list-standards/en/`
   - Extraer: `reference`, `title`, `committee`, `last_modified`, URLs PDF
2. Guardar en `data/codex_index.json` (versionado, ~500 KB)
3. Conector hace búsqueda local fuzzy por `query_normalized`

### Estrategia B — Búsqueda en vivo

- GET página de estándares con query param (si soportado)
- Fragilidad alta; no recomendado para producción

## Mapeo PIT → búsqueda local

```python
def search_codex(query: str, limit: int) -> list[dict]:
    tokens = query.lower().split()
    scores = []
    for std in load_index():
        title = std["title"].lower()
        score = sum(1 for t in tokens if t in title)
        if score > 0:
            scores.append((score, std))
    return [s for _, s in sorted(scores, reverse=True)[:limit]]
```

Mapeo taxonomía → estándares conocidos:

| Producto PIT | Estándares Codex |
|--------------|------------------|
| cacao | CXS 105-1981, CXS 141-1983, CXS 86-1981 |
| blueberry | (buscar por commodity) |
| quinoa | CXS 172-1989 |

## Normalización (`works[]`)

```json
{
  "id": "codex:CXS-105-1981",
  "title": "Standard for Cocoa Powders (Cocoas) and Dry Mixtures of Cocoa and Sugars",
  "source": "codex",
  "published_at": "2025-01-01",
  "url": "https://www.fao.org/fao-who-codexalimentarius/...",
  "metadata": {
    "reference": "CXS 105-1981",
    "committee": "CCS",
    "last_modified": 2025,
    "languages": ["EN", "ES", "FR"]
  }
}
```

## Agregación

```json
{
  "summary_type": "codex_aggregation",
  "standards_count": 4,
  "references": ["CXS 105-1981", "CXS 1-1985"],
  "latest_amendment_year": 2025
}
```

Integrar en `regulatory_aggregation`.

## Scoring

- **Coverage:** `0.5` si ≥1 estándar relevante.
- **Score:** informativo (no penalizar); usar en reporte como contexto, no driver GO/NO-GO.

## Licencia

Textos Codex libremente accesibles; atribución FAO/WHO Codex Alimentarius.

## Mantenimiento

Re-ejecutar `build_codex_index.py` trimestralmente (cron o manual). Comparar `last_modified` para detectar cambios.

## Archivos

- `src/pit/codex.py`
- `scripts/build_codex_index.py`
- `data/codex_index.json` (gitignore si >1MB; o versionar)
- `tests/test_codex.py`

## Tests

1. Index local → search "cocoa" returns CXS 105.
2. Empty query → no results.
3. Index file missing → `RuntimeError` claro.
