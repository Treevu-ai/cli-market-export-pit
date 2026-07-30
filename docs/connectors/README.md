# Especificaciones de conectores públicos — CLI Market PIT

Documentación técnica para integrar **17 fuentes públicas gratuitas** (o con tier gratuito) identificadas en la auditoría de conectores de julio 2026.

## Índice

| ID | Conector | Dominio PIT | Tier | Spec |
|----|----------|-------------|------|------|
| `wto_eping` | WTO ePing SPS/TBT | `regulatory` | 1 | [wto_eping.md](./wto_eping.md) |
| `wto_timeseries` | WTO Timeseries (aranceles) | `trade` | 1 | [wto_timeseries.md](./wto_timeseries.md) |
| `wits_trains` | WITS / UNCTAD TRAINS | `trade` | 1 | [wits_trains.md](./wits_trains.md) |
| `faostat` | FAOSTAT (FAO) | `trade` | 1 | [faostat.md](./faostat.md) |
| `usda_fas` | USDA FAS (PSD/GATS/ESR) | `trade` | 1 | [usda_fas.md](./usda_fas.md) |
| `rasff` | RASFF Window (UE) | `regulatory` | 1 | [rasff.md](./rasff.md) |
| `eurostat_comext` | Eurostat Comext | `trade` | 2 | [eurostat_comext.md](./eurostat_comext.md) |
| `uspto_odp` | USPTO Open Data Portal | `patent` | 2 | [uspto_odp.md](./uspto_odp.md) |
| `world_bank` | World Bank Indicators | `macro` | 2 | [world_bank.md](./world_bank.md) |
| `google_trends` | Google Trends | `trend` | 2 | [google_trends.md](./google_trends.md) |
| `clinicaltrials` | ClinicalTrials.gov | `science` | 3 | [clinicaltrials.md](./clinicaltrials.md) |
| `arxiv` | arXiv | `science` | 3 | [arxiv.md](./arxiv.md) |
| `imf_data` | IMF Data API | `macro` | 3 | [imf_data.md](./imf_data.md) |
| `oecd_sdmx` | OECD SDMX | `trade` | 3 | [oecd_sdmx.md](./oecd_sdmx.md) |
| `codex` | Codex Alimentarius | `regulatory` | 3 | [codex.md](./codex.md) |
| `cfia_canada` | CFIA Recalls (Canadá) | `regulatory` | 3 | [cfia_canada.md](./cfia_canada.md) |
| `rappelconso` | RappelConso (Francia) | `regulatory` | 3 | [rappelconso.md](./rappelconso.md) |

## Contrato común de implementación

Todos los conectores nuevos deben seguir el patrón existente en `src/pit/*.py`:

```python
class ExampleRequestError(RuntimeError):
    http_status: int | None
    raw_content: bytes | None
    request_url: str | None
    request_params: dict[str, Any] | None

@dataclass(frozen=True)
class ExampleResponse:
    request_url: str
    request_params: dict[str, Any]
    http_status: int
    raw_content: bytes
    works: list[dict[str, Any]]  # evidencia normalizada

class ExampleConnector:
    source = "example"           # clave en source_request
    license_name = "..."         # ver docs/license_matrix.md
    base_url = "https://..."

    def search(
        self,
        *,
        query: str,
        from_publication_date: str,
        limit: int,
        target_market: str | None = None,
        hs_code: str | None = None,
    ) -> ExampleResponse: ...
```

### Pipeline de integración

1. **Conector** (`src/pit/<source>.py`) — HTTP, parseo, normalización mínima.
2. **ResearchService** — método `enrich_with_<domain>()` o sub-paso dentro de un dominio compuesto.
3. **Almacenamiento** — `store.start_source_request` → raw SHA-256 → `finish_source_request`.
4. **Agregación** — `store.save_domain_summary(research_run_id, domain, summary_type="<source>_aggregation", payload=...)`.
5. **Scoring** — extender `estimate_coverage` / `estimate_score` en `scoring.py`.
6. **Tests** — `tests/test_<source>.py` con mocks HTTP; al menos un test live opcional con `@unittest.skipUnless(os.getenv("RUN_LIVE_CONNECTOR_TESTS"))`.
7. **API** — registrar en `ENRICHMENT_HANDLERS` si expone dominio propio; actualizar `/v1/connectors/status`.
8. **Env** — documentar en `.env.example` y `README.md`.

### Contexto de entrada (desde research run)

| Campo run | Uso en conectores |
|-----------|-------------------|
| `query_normalized` | Búsqueda por producto/ingrediente |
| `target_market` | ISO-2 (US, DE, PE…) → códigos reporter/partner |
| `from_publication_date` | Ventana temporal mínima |
| `taxonomy_version` + HS | `resolve_hs_code()` para trade/tariffs |
| `limit` | Tope de registros por fuente |

### Esquema de evidencia normalizada (`works[]`)

Cada item en `works` debe incluir como mínimo:

```json
{
  "id": "stable-dedup-key",
  "title": "human-readable label",
  "source": "wto_eping",
  "published_at": "2026-03-15",
  "url": "https://...",
  "snippet": "resumen <= 500 chars",
  "metadata": { }
}
```

### Roadmap de implementación sugerido

**Fase A — Acceso a mercado (semanas 1–2)**

- `wto_eping`, `wto_timeseries`, `wits_trains`

**Fase B — Oferta y demanda global (semanas 2–3)**

- `faostat`, `usda_fas`, `eurostat_comext`

**Fase C — Riesgo regulatorio (semana 3)**

- `rasff`, `codex`, `cfia_canada`, `rappelconso`

**Fase D — Señales complementarias (semana 4+)**

- `world_bank`, `uspto_odp`, `google_trends`, `clinicaltrials`, `arxiv`, `imf_data`, `oecd_sdmx`

### Variables de entorno nuevas (resumen)

| Variable | Conectores |
|----------|------------|
| `WTO_API_KEY` | wto_eping, wto_timeseries |
| `USDA_FAS_API_KEY` | usda_fas |
| `USPTO_ODP_API_KEY` | uspto_odp |
| `GOOGLE_TRENDS_API_KEY` | google_trends (alpha oficial) |
| `OECD_API_KEY` | oecd_sdmx (SDMX, registro gratuito) |
| *(ninguna)* | faostat, wits_trains, rasff, eurostat_comext, world_bank, clinicaltrials, arxiv, imf_data, codex, cfia_canada, rappelconso |

### Impacto en scoring (propuesta v1.1)

Los conectores nuevos enriquecen agregaciones existentes; no crean dominios nuevos salvo `market_access` (futuro, opcional).

| Dominio | Agregaciones actuales | Nuevas agregaciones |
|---------|----------------------|---------------------|
| `trade` | comtrade | wto_timeseries, wits_trains, faostat, usda_fas, eurostat_comext, oecd |
| `regulatory` | openfda, efsa, fooddata | wto_eping, rasff, codex, cfia, rappelconso |
| `patent` | epo_ops | uspto_odp |
| `macro` | bcrp | world_bank, imf_data |
| `trend` | gdelt | google_trends |
| `science` | openalex, crossref, pubmed, s2 | clinicaltrials, arxiv |

Pesos propuestos para v1.1: ver cada spec individual y `docs/scoring_calibration.md` (actualización pendiente tras implementación).
