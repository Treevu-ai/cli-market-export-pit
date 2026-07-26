# Sprint Plan — Pitchavi Fase 1 MVP

**Proyecto:** Pitchavi — Plataforma de Inteligencia Tecnológica con Evidencia Trazable  
**Versión del plan:** 2026-07-25  
**Hito objetivo:** MVP funcional (M1) — 4 dominios + scoring + reporte exportable  
**Base:** `PRD_Pitchavi_Completo.md` v2.0, `PRD_Plataforma_Inteligencia_Tecnologica_MVP_v1_1.md`

---

## Estado actual (Sprint 0 completado)

| Capacidad | Estado |
|---|---|
| `research_run` con parámetros versionados | ✅ |
| Almacenamiento crudo SHA-256 inmutable | ✅ |
| Evidencia normalizada (dominio ciencia) | ✅ |
| Conector OpenAlex | ✅ |
| Enriquecimiento Crossref sin duplicar DOI | ✅ |
| API REST FastAPI con envelope | ✅ |
| Tests unitarios y de API | ✅ |
| Health check | ❌ |
| Autenticación | ❌ |
| Conectores: patentes, tendencias, comercio | ❌ |
| Motor de scoring y claims | ❌ |
| Generador de reportes | ❌ |
| Panel operativo | ❌ |
| Taxonomía HS formal | ❌ |
| Orquestación asíncrona | ❌ |

---

## Sprint 1 — Taxonomía y ampliación del dominio científico

**Duración estimada:** 2 semanas  
**Objetivo:** Convertir el dominio científico en producción listo para MVP con taxonomía versionada, respaldo de fuentes y hooks para scoring.

### Deliverables

- [ ] Taxonomía versionada para vocabulario científico y sinónimos de productos
- [ ] Conector PubMed (NCBI E-utilities)
- [ ] Conector Semantic Scholar
- [ ] Extracción de tópicos, autores e instituciones principales desde OpenAlex
- [ ] Cacheo por checksum de respuesta (content-addressable)
- [ ] Endpoint `GET /v1/health`
- [ ] Tests de viabilidad para cada conector nuevo

### Tareas desglosadas

| ID | Tarea | Tipo | Prioridad |
|---|---|---|---|
| S1-01 | Diseñar taxonomía `cacao-functional-v2` con sinónimos, HS preliminar y variantes | Diseño | Alta |
| S1-02 | Implementar almacén de taxonomía en SQLite (`taxonomies`, `synonyms`, `hs_mappings`) | Backend | Alta |
| S1-03 | Implementar `PubMedConnector` con E-utilities (search, esummary) | Backend | Alta |
| S1-04 | Implementar `SemanticScholarConnector` con /paper/search | Backend | Media |
| S1-05 | Extraer `top_topics`, `top_authors`, `top_institutions` desde works de OpenAlex | Backend | Media |
| S1-06 | Implementar cacheo por checksum en `ResearchStore` (skip re-descarga) | Backend | Alta |
| S1-07 | Agregar `GET /v1/health` | API | Alta |
| S1-08 | Tests unitarios PubMed/Semantic Scholar y cacheo | Tests | Alta |
| S1-09 | Documentar licencias y atribución por fuente | Docs | Media |

### Criterios de aceptación

- [ ] 2 fuentes de respaldo (PubMed, Semantic Scholar) producen `source_request` + `evidence_records` correctos
- [ ] Cacheo evita re-descarga cuando checksum coincide
- [ ] Taxonomía versionada persiste y se consulta en tiempo de ejecución
- [ ] `GET /v1/health` retorna `{"status": "ok"}` con versión
- [ ] Tests nuevos pasan (`python -m unittest tests/`)

### Dependencias

- Sprint 0 completado
- Cuentas API NCBI (PubMed) y Semantic Scholar

---

## Sprint 2 — Inteligencia de patentes (EPO OPS)

**Duración estimada:** 2 semanas  
**Objetivo:** Conectar dominio de patentes con normalización, deduplicación y trazabilidad completa.

### Deliverables

- [ ] Conector EPO OPS (OAuth 2.0 client credentials)
- [ ] Normalización de patentes (número, titular, IPC/CPC, estado, resumen)
- [ ] Cálculo de volumen y evolución temporal
- [ ] Identificación de top assignees y familias
- [ ] Deduplicación entre fuentes de patentes
- [ ] Endpoint `POST /v1/research-runs/{run_id}/domains/patent`

### Tareas desglosadas

| ID | Tarea | Tipo | Prioridad |
|---|---|---|---|
| S2-01 | Registrar aplicación en EPO OPS y obtener credenciales OAuth | Infra | Alta |
| S2-02 | Implementar `EPOOPSConnector` con auth y búsqueda por término/IPC | Backend | Alta |
| S2-03 | Implementar normalizador de patentes (`PatentNormalizer`) | Backend | Alta |
| S2-04 | Implementar deduplicador de familias de patentes | Backend | Alta |
| S2-05 | Calcular indicadores: volumen, evolución, top assignees, top IPC | Backend | Media |
| S2-06 | Agregar endpoint de dominio patente en API | API | Alta |
| S2-07 | Manejo de errores EPO (429, 503, auth) con backoff exponencial | Backend | Alta |
| S2-08 | Tests unitarios y de integración EPO OPS | Tests | Alta |
| S2-09 | Documentar términos de uso EPO OPS | Docs | Media |

### Criterios de aceptación

- [ ] `POST /domains/patent` ejecuta búsqueda y retorna evidencia normalizada
- [ ] Mismo número de patente no se duplica dentro del mismo run
- [ ] Errores EPO se propagan como `502` con `research_run_id` y detalle
- [ ] Indicadores de patente están presentes en detalle de run
- [ ] Tests pasan con cuenta de prueba EPO OPS

### Dependencias

- Sprint 0 completado
- Cuenta EPO OPS activa
- Sprint 1 (taxonomía) para mapeo inicial

---

## Sprint 3 — Tendencias (GDELT) y comercio exterior (UN Comtrade)

**Duración estimada:** 3 semanas  
**Objetivo:** Agregar señales de demanda y comercio exterior con normalización, mapeo HS y cálculo de CAGR.

### Deliverables

- [ ] Conector GDELT (Document Search o Events según disponibilidad)
- [ ] Normalización de noticias/señales con deduplicación
- [ ] Conector UN Comtrade
- [ ] Mapeo producto → códigos HS versionado
- [ ] Cálculo de CAGR, ranking exportadores/importadores
- [ ] Complemento FAOSTAT para productos agroindustriales
- [ ] Endpoints de dominios trend y trade
- [ ] Distinción explícita entre señal de mercado y evidencia comercial

### Tareas desglosadas

| ID | Tarea | Tipo | Prioridad |
|---|---|---|---|
| S3-01 | Diseñar taxonomía HS provisional para productos objetivo (cacao, quinua, etc.) | Diseño | Alta |
| S3-02 | Implementar `GDELTConnector` con normalización de idioma y deduplicación | Backend | Alta |
| S3-03 | Implementar `ComtradeConnector` con parámetros HS, reporter, partner, periodo | Backend | Alta |
| S3-04 | Implementar `FAOSTATConnector` (opcional) para productos agro | Backend | Media |
| S3-05 | Calcular CAGR y ranking de exportadores/importadores | Backend | Media |
| S3-06 | Implementar mapeo producto→HS con versión (`hs_mappings` en SQLite) | Backend | Alta |
| S3-07 | Agregar endpoints de dominios trend y trade en API | API | Alta |
| S3-08 | Implementar clasificador señal de mercado vs evidencia comercial | Backend | Media |
| S3-09 | Tests unitarios GDELT, Comtrade, CAGR, mapeo HS | Tests | Alta |
| S3-10 | Documentar términos de uso GDELT y UN Comtrade | Docs | Media |

### Criterios de aceptación

- [ ] `POST /domains/trend` y `POST /domains/trade` funcionan contra fuentes reales
- [ ] Mapeo HS devuelve códigos válidos para productos objetivo
- [ ] CAGR coincide con cálculo manual sobre datos de prueba
- [ ] GDELT deduplica noticias por URL/título normalizado
- [ ] Faena visible cuando fuente retorna datos insuficientes
- [ ] Tests pasan

### Dependencias

- Sprint 0 completado
- Sprint 1 (taxonomía) para mapeo HS
- Cuentas API si aplica (GDELT es público; Comtrade tiene API pública)

---

## Sprint 4 — Scoring v1 y generador de reportes

**Duración estimada:** 3 semanas  
**Objetivo:** Implementar motor de scoring, reglas de decisión y generación de ficha ejecutiva exportable.

### Deliverables

- [ ] Motor de scoring por dimensión (0–100)
- [ ] Cálculo de `coverage_factor`
- [ ] Reglas de decisión (Investigate/Validate/Deprioritize/Insufficient evidence)
- [ ] Sistema de claims con `source_refs` y niveles de confianza
- [ ] Generador de reporte JSON ejecutivo
- [ ] Generador de reporte PDF (Jinja2 + WeasyPrint o similar)
- [ ] Anexo de fuentes con checksums y fechas
- [ ] Distinción visual hechos/inferencias/recomendaciones
- [ ] Endpoints `POST /v1/research-runs/{run_id}/score` y `GET /v1/research-runs/{run_id}/report`

### Tareas desglosadas

| ID | Tarea | Tipo | Prioridad |
|---|---|---|---|
| S4-01 | Diseñar esquema de `claims` y `domain_scores` en SQLite | Backend | Alta |
| S4-02 | Implementar `ScoringEngine` con pesos y normalización por dimensión | Backend | Alta |
| S4-03 | Implementar cálculo de `coverage_factor` y aplicación de reglas | Backend | Alta |
| S4-04 | Implementar `ClaimBuilder` con `source_refs`, confianza y limitaciones | Backend | Alta |
| S4-05 | Implementar `ReportGenerator` JSON ejecutivo | Backend | Alta |
| S4-06 | Implementar `PDFReportGenerator` con anexo de fuentes | Backend | Media |
| S4-07 | Implementar endpoint `POST /v1/research-runs/{run_id}/score` | API | Alta |
| S4-08 | Implementar endpoint `GET /v1/research-runs/{run_id}/report` | API | Alta |
| S4-09 | Implementar endpoint `GET /v1/research-runs/{run_id}/report/export` | API | Media |
| S4-10 | Tests unitarios scoring engine, claim builder, generadores | Tests | Alta |
| S4-11 | Calibración con 3–5 casos de prueba manuales | Calidad | Alta |

### Criterios de aceptación

- [ ] Score v1 devuelve oportunidad, cobertura, recomendación y dimensiones
- [ ] Cobertura < 60% bloquea recomendación con `Insufficient evidence`
- [ ] Claims incluyen `source_refs` trazables a `source_request` y checksum
- [ ] JSON reporte contiene resumen, score, evidencia, vacíos y anexo
- [ ] PDF reporte distingue hechos, inferencias y recomendaciones visualmente
- [ ] Tests pasan

### Dependencias

- Sprint 0 completado
- Sprint 2 (patentes) completado
- Sprint 3 (tendencias + comercio) completado

---

## Sprint 5 — Validación, hardening y despliegue productivo

**Duración estimada:** 3 semanas  
**Objetivo:** Validar el MVP con consultas reales, endurecer operaciones y preparar despliegue.

### Deliverables

- [ ] 10 consultas reales validadas con analista
- [ ] Panel operativo (cuotas, errores, frescura por conector)
- [ ] Autenticación API key para entornos no locales
- [ ] Dockerfile y docker-compose para despliegue
- [ ] Logging estructurado y métricas básicas
- [ ] Migración documentada a PostgreSQL (preparación)
- [ ] Matriz de licencias aprobada por fuente

### Tareas desglosadas

| ID | Tarea | Tipo | Prioridad |
|---|---|---|---|
| S5-01 | Definir 10 casos de consulta real (productos, mercados, aplicaciones) | Producto | Alta |
| S5-02 | Ejecutar 10 consultas y documentar resultados, vacíos y calibración | Calidad | Alta |
| S5-03 | Implementar panel operativo `/v1/connectors/status` | Backend | Alta |
| S5-04 | Implementar autenticación API key (middleware FastAPI) | Backend | Alta |
| S5-05 | Implementar logging estructurado (JSON) | Backend | Media |
| S5-06 | Implementar métricas Prometheus básicas | Backend | Media |
| S5-07 | Crear Dockerfile y docker-compose para producción | DevOps | Alta |
| S5-08 | Documentar migración SQLite → PostgreSQL | Docs | Media |
| S5-09 | Completar matriz de licencias por fuente | Docs | Alta |
| S5-10 | Ajustar pesos de scoring según validación | Calidad | Alta |

### Criterios de aceptación

- [ ] 10 consultas reales completadas y documentadas
- [ ] Analista puede verificar cualquier número en < 15 minutos
- [ ] Panel operativo muestra cuota consumida, error rate y frescura por conector
- [ ] API sin autenticación rechaza requests fuera de `127.0.0.1`
- [ ] Docker Compose levanta API + DB en un comando
- [ ] Matriz de licencias aprobada completa
- [ ] Tests pasan

### Dependencias

- Sprint 1, 2, 3, 4 completados

---

## Sprint 6 — Technology Scout (Fase 2)

**Duración estimada:** 2 semanas  
**Objetivo:** Implementar agentes de scouting tecnológico con proyectos financiados y estimación TRL.

### Deliverables

- [ ] Conector CORDIS (proyectos financiados UE)
- [ ] Conector NIH RePORTER
- [ ] Conector NSF Awards
- [ ] Extracción de TRL estimado y montos de financiamiento
- [ ] Endpoint de dominio technology scout

### Criterios de aceptación

- [ ] Proyectos CORDIS se normalizan y vinculan a `research_run`
- [ ] TRL estimado se calcula con señales bibliométricas (con disclaimer)
- [ ] Montos de financiamiento se extraen cuando la fuente lo permita
- [ ] Tests pasan

### Dependencias

- Sprint 4 completado
- Cuentas API si aplica (CORDIS/NIH/NSF públicas en general)

---

## Sprint 7 — Regulación y sostenibilidad (Fase 2)

**Duración estimada:** 3 semanas  
**Objetivo:** Implementar pre-evaluación regulatoria y estimación de sostenibilidad con metodología explícita.

### Deliverables

- [ ] Conector OpenFDA (descubrimiento)
- [ ] Conector EFSA / EUR-Lex (descubrimiento)
- [ ] Conector FoodData Central (complementario)
- [ ] Conector Climatiq / Agribalyse (huella)
- [ ] Motor de pre-evaluación regulatoria con estados conservadores
- [ ] Motor de sostenibilidad con unidad funcional, frontera y metodología
- [ ] Registro de revisor humano y fecha de corte
- [ ] Endpoints de dominios regulatory y sustainability

### Criterios de aceptación

- [ ] Pre-evaluación emite solo estados: `not_assessed`, `needs_review`, `potential_constraint`, `no_constraint_found`
- [ ] Nunca emite `approved`, `low risk` o `compliant`
- [ ] Huella incluye unidad funcional, frontera, región, año, factor y calidad
- [ ] Sin rating agregado sin metodología validada
- [ ] Tests pasan

### Dependencias

- Sprint 4 completado
- Sprint 6 completado (opcional, para TRL)
- Validación legal de términos de uso de fuentes regulatorias

---

## Resumen de sprint

| Sprint | Tema | Duración | Depende de | Hito |
|---|---|---|---|---|
| 0 | Fundación científica | ✅ | — | M0 Alpha |
| 1 | Taxonomía + ciencia ampliada | 2 sem | 0 | — |
| 2 | Patentes (EPO OPS) | 2 sem | 0, 1 | — |
| 3 | Tendencias + comercio | 3 sem | 0, 1 | — |
| 4 | Scoring + reporte | 3 sem | 0, 2, 3 | — |
| 5 | Validación + hardening | 3 sem | 1–4 | M1 MVP |
| 6 | Technology Scout | 2 sem | 4 | M2 |
| 7 | Regulación + sostenibilidad | 3 sem | 4, 6 | M3 Beta |

---

## Métricas y Definition of Done

### Definition of Done por sprint

1. Código mergeado a `main`
2. Tests unitarios y de API pasan
3. Endpoint documentado en `/docs`
4. Tipo de evidencia normalizada y almacenada
5. Manejo de fallas del conector verificado
6. Licencia y atribución documentadas

### Definition of Done MVP (Sprint 5)

- [ ] ≥ 3 de 4 dominios con evidencia suficiente por consulta
- [ ] Score v1 funcional con reglas de cobertura
- [ ] Reporte JSON ejecutivo con anexo de fuentes
- [ ] 10 consultas reales validadas por analista
- [ ] Panel operativo funcional
- [ ] Autenticación API key activa
- [ ] Docker Compose funcional

---

## Decisiones pendientes a resolver antes de Sprint 1

| # | Decisión | Opciones | Impacto | Owner |
|---|---|---|---|---|
| 1 | Producto/ingrediente inicial del caso vertical | Cacao flavanol, quinua proteína, aguaymanto | Define taxonomía y pruebas | Producto |
| 2 | Mercado destino inicial | US (recomendado), EU, ambos | Fuentes regulatorias y comercio | Producto |
| 3 | Taxonomía y mapeo HS oficial | Versión `cacao-functional-v2` vs. nueva | Calidad de dominio trade | I+D + Comercio |
| 4 | Presupuesto mensual máximo de APIs | $0, $50, $200 | Fuentes de pago (Lens, NewsAPI) | Finanzas |
| 5 | Base de datos producción | PostgreSQL managed vs. self-hosted | Sprint 5 | Ingeniería |
| 6 | Autenticación | API key, OAuth2, SSO | Seguridad MVP | Ingeniería |

---

*Fin del documento — Sprint Plan Pitchavi v2026-07-25*
