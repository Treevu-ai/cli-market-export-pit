# Spec: arXiv

| Campo | Valor |
|-------|-------|
| **source** | `arxiv` |
| **Dominio PIT** | `science` |
| **Tier** | 3 |
| **Prioridad** | Baja |
| **Auth** | Ninguna |

## Valor para CLI Market

Preprints recientes antes de publicación formal — detectar tendencias científicas emergentes en ingredientes funcionales.

## Endpoints

API: `http://export.arxiv.org/api/query`

| Parámetro | Uso |
|-----------|-----|
| `search_query` | `all:{query}` o `ti:{query}` |
| `start` | 0 |
| `max_results` | `limit` |
| `sortBy` | `submittedDate` |
| `sortOrder` | `descending` |

Ejemplo:

```
GET /api/query?search_query=all:quinoa+protein&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending
```

Respuesta: Atom XML (parsear con `xml.etree` o `feedparser`).

## Mapeo PIT → request

```python
search_query = f"all:{quote_plus(query)}"
# Filtrar categorías relevantes post-parse: q-bio, physics.bio-ph, etc.
```

Opcional: filtrar `submittedDate >= from_publication_date` en cliente.

## Normalización (`works[]`)

```json
{
  "id": "arxiv:{arxiv_id}",
  "title": "Plant protein digestibility in quinoa-based formulations",
  "source": "arxiv",
  "published_at": "2025-11-20",
  "url": "https://arxiv.org/abs/2511.12345",
  "metadata": {
    "arxiv_id": "2511.12345",
    "authors": ["Garcia, M.", "Lee, S."],
    "categories": ["q-bio.QM"],
    "doi": null
  }
}
```

## Agregación

```json
{
  "summary_type": "arxiv_aggregation",
  "preprints_count": 8,
  "recent_12m_count": 5,
  "top_categories": ["q-bio.QM", "physics.bio-ph"]
}
```

Dedupe con OpenAlex/Crossref por DOI o título fuzzy.

## Scoring

- **Coverage:** `0.4` (secundario a journals indexados).
- **Score:** `min(100, recent_12m_count * 12)`.

## Rate limits

1 req cada 3 segundos (política arXiv). Cache 7 días.

## Licencia

arXiv license varies per paper; metadata CC0. No redistribuir PDFs completos.

## Archivos

- `src/pit/arxiv.py`
- `tests/test_arxiv.py`

## Tests

1. Mock Atom XML → 2 entries.
2. Rate limit: verificar sleep entre requests.
3. Dedupe key con OpenAlex DOI.
