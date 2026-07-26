# PRD — Pitchavi
## Plataforma de Inteligencia Tecnológica con Evidencia Trazable

**Versión:** 2.0  
**Estado:** documento maestro — listo para diseño técnico y ejecución por fases  
**Fecha:** 2026-07-24  
**Producto:** Pitchavi  
**Documentos base:** `PRD_Plataforma_Inteligencia_Tecnologica_MVP_v1_1.md`, `PRD_Plataforma_Inteligencia_Tecnologica_Fases_1_2.md`

---

## Tabla de contenidos

1. [Resumen ejecutivo](#1-resumen-ejecutivo)
2. [Problema y oportunidad](#2-problema-y-oportunidad)
3. [Visión y propuesta de valor](#3-visión-y-propuesta-de-valor)
4. [Usuarios y casos de uso](#4-usuarios-y-casos-de-uso)
5. [Alcance del producto](#5-alcance-del-producto)
6. [Requisitos funcionales](#6-requisitos-funcionales)
7. [Requisitos no funcionales](#7-requisitos-no-funcionales)
8. [Fuentes de datos y viabilidad](#8-fuentes-de-datos-y-viabilidad)
9. [Arquitectura técnica](#9-arquitectura-técnica)
10. [Modelo de datos](#10-modelo-de-datos)
11. [Contrato de evidencia](#11-contrato-de-evidencia)
12. [Scoring y reglas de decisión](#12-scoring-y-reglas-de-decisión)
13. [API y contratos](#13-api-y-contratos)
14. [Flujos de usuario](#14-flujos-de-usuario)
15. [Evaluación regulatoria y sostenibilidad](#15-evaluación-regulatoria-y-sostenibilidad)
16. [Seguridad, privacidad y cumplimiento](#16-seguridad-privacidad-y-cumplimiento)
17. [Métricas y KPIs](#17-métricas-y-kpis)
18. [Plan de entrega](#18-plan-de-entrega)
19. [Riesgos y mitigaciones](#19-riesgos-y-mitigaciones)
20. [Estado de implementación actual](#20-estado-de-implementación-actual)
21. [Criterios de aceptación](#21-criterios-de-aceptación)
22. [Decisiones pendientes](#22-decisiones-pendientes)
23. [Anexos](#23-anexos)

---

## 1. Resumen ejecutivo

**Pitchavi** es una plataforma de inteligencia tecnológica que responde consultas de innovación con **evidencia trazable y reproducible**, no con recomendaciones autónomas definitivas.

La pregunta de negocio que resuelve es:

> ¿Qué oportunidades existen para desarrollar o exportar un producto o ingrediente agroindustrial, y con qué evidencia se puede respaldar esa decisión?

El primer caso vertical recomendado es **identificar oportunidades para un ingrediente o producto agroindustrial peruano destinado a exportación a Estados Unidos** (por ejemplo, cacao de alto flavanol, proteína vegetal, superalimentos funcionales).

**Decisión que habilita:** priorizar una oportunidad para investigación adicional, validación comercial o revisión regulatoria humana.

**No habilita:** aprobación regulatoria, libertad de operación, dictamen legal, ni cálculo de huella verificada.

### Principios de producto

| Principio | Descripción |
|---|---|
| Evidencia primero | Toda afirmación cuantitativa enlaza a fuente, fecha de extracción y transformación |
| Reproducibilidad | Misma consulta + misma versión de datos = mismo resultado o diferencia explicada |
| API-first | Integración con fuentes externas vía conectores; no scraping frágil como base |
| Coste controlado | Priorizar fuentes de bajo coste; licencias comerciales solo con aprobación explícita |
| Humano en el loop | Regulación, claims y sostenibilidad requieren revisión humana antes de uso externo |
| Falla visible | Sin acceso, cuota agotada o datos insuficientes se reportan; no se inventan conclusiones |

---

## 2. Problema y oportunidad

### Problema

Equipos de innovación, I+D y comercio exterior en agroindustria enfrentan:

- **Fragmentación:** la evidencia científica, patentes, tendencias y comercio viven en silos distintos.
- **Opacidad:** reportes de consultoría difíciles de auditar; no se sabe de dónde salió cada número.
- **Lentitud:** armar un panorama completo manualmente toma semanas.
- **Riesgo de sobreconfianza:** herramientas con IA generan recomendaciones sin trazabilidad ni límites claros.
- **Coste de licencias:** bases comerciales (patentes, noticias, societaria) encarecen el MVP.

### Oportunidad

Una plataforma que:

1. Consolide señales de múltiples dominios en una sola **ficha ejecutiva reproducible**.
2. Conserve respuestas crudas de fuentes de forma **inmutable** para auditoría.
3. Calcule un **Opportunity Score explicable** con cobertura y confianza por dominio.
4. Escale desde un MVP acotado (ciencia + comercio) hacia inteligencia avanzada (technology scout, sostenibilidad, societaria).

### Contexto peruano

Perú exporta productos agroindustriales con potencial de valor agregado (cacao, café, quinua, aguaymanto, maca, aceites vegetales, proteínas vegetales). La decisión de innovar o posicionar un ingrediente en mercados como EE.UU. requiere cruzar evidencia científica, panorama de patentes, señales de demanda y flujos comerciales — hoy sin una herramienta unificada y trazable.

---

## 3. Visión y propuesta de valor

### Visión (3 años)

Ser la plataforma de referencia para equipos de innovación en LATAM que necesitan **inteligencia tecnológica verificable** para decisiones de producto, exportación e I+D, con foco inicial en agroindustria.

### Propuesta de valor

| Para quién | Valor |
|---|---|
| Analista de innovación | Ficha ejecutiva en minutos, no semanas; cada número es auditable |
| Gerente de I+D | Panorama de estado del arte, patentes y tendencias con gaps explícitos |
| Equipo comercial / exportación | Señales de demanda y comercio exterior alineadas al producto consultado |
| Compliance / regulación | Pre-evaluación con estados conservadores; nunca dictamen legal automático |
| Dirección | Opportunity Score con explicación, no caja negra |

### Diferenciadores

- **Trazabilidad end-to-end:** `research_run` → petición a fuente → respuesta cruda (SHA-256) → evidencia normalizada → claim → score.
- **Separación estricta:** hecho de fuente ≠ inferencia del sistema ≠ recomendación de negocio.
- **Modularidad:** cada dominio es un conector independiente con cuotas, reintentos y versionado.
- **Honestidad operativa:** cobertura insuficiente bloquea o baja la recomendación.

---

## 4. Usuarios y casos de uso

### Personas

| Persona | Rol | Necesidad principal |
|---|---|---|
| **Ana — Analista de innovación** | Usuario principal | Ejecutar consultas, revisar evidencia, exportar reporte |
| **Carlos — Líder de I+D** | Consumidor de insights | Validar si un ingrediente tiene respaldo científico y espacio tecnológico |
| **María — Export manager** | Usuario secundario | Entender demanda importadora y competidores por país/código HS |
| **Luis — Asesor regulatorio** | Revisor humano | Revisar pre-evaluación regulatoria antes de uso externo |
| **Ops — Operaciones** | Administrador | Monitorear cuotas, errores, frescura de fuentes |

### Casos de uso principales

#### UC-01 — Consulta de oportunidad integral
**Actor:** Ana  
**Flujo:** Ingresa producto, mercado destino (US), aplicación y periodo → sistema ejecuta `research_run` → recibe ficha con score, evidencia y vacíos.  
**Resultado:** Decisión `Investigate`, `Validate` o `Deprioritize` con justificación.

#### UC-02 — Investigación científica puntual
**Actor:** Carlos  
**Flujo:** Consulta solo dominio ciencia (publicaciones, citas, tópicos) para un ingrediente.  
**Resultado:** Lista de papers trazables con DOI, fecha, citas y enlace a respuesta cruda.

#### UC-03 — Enriquecimiento bibliográfico
**Actor:** Ana  
**Flujo:** Tras un run científico, solicita enriquecimiento Crossref por DOI sin duplicar evidencia.  
**Resultado:** Mismo registro de evidencia con `source_links` adicionales (OpenAlex + Crossref).

#### UC-04 — Auditoría de un hallazgo
**Actor:** Ana / Compliance  
**Flujo:** Desde un número en el reporte, navega al `claim` → `source_refs` → respuesta cruda almacenada.  
**Resultado:** Verificación en menos de 15 minutos.

#### UC-05 — Pre-evaluación regulatoria (fase posterior)
**Actor:** Luis  
**Flujo:** Sistema identifica documentos y categorías relevantes; Luis marca revisión y fecha de corte.  
**Resultado:** Estado `needs_review` o `potential_constraint`; nunca `approved`.

#### UC-06 — Monitoreo operativo
**Actor:** Ops  
**Flujo:** Revisa panel de cuotas consumidas, tasa de error por conector y frescura de datos.  
**Resultado:** Acción correctiva antes de degradación silenciosa.

---

## 5. Alcance del producto

### 5.1 Fase 0 — Fundación (implementado parcialmente)

**Objetivo:** Infraestructura de `research_run`, almacenamiento inmutable y primer conector científico.

| Capacidad | Estado |
|---|---|
| `research_run` con parámetros versionados | ✅ Implementado |
| Almacenamiento crudo SHA-256 | ✅ Implementado |
| Evidencia normalizada (dominio ciencia) | ✅ Implementado |
| Conector OpenAlex | ✅ Implementado |
| Enriquecimiento Crossref sin duplicar DOI | ✅ Implementado |
| API REST FastAPI | ✅ Implementado |
| Tests unitarios y de API | ✅ Implementado |

### 5.2 MVP — Fase 1 (objetivo inmediato)

**Objetivo:** Ficha ejecutiva con al menos 3 de 4 dominios críticos y scoring v1.

| Dominio | Incluido | Descripción |
|---|---|---|
| Evidencia científica | ✅ Parcial | Publicaciones, citas, tópicos, autores, instituciones |
| Inteligencia de patentes | 🔲 Pendiente | Volumen, evolución, titulares, IPC/CPC, estado |
| Señales de demanda | 🔲 Pendiente | Interés de búsqueda, cobertura noticiosa (GDELT) |
| Comercio exterior | 🔲 Pendiente | Flujos, países, códigos HS, evolución import/export |
| Scoring explicable | 🔲 Pendiente | Cobertura, confianza, alertas, enlaces a evidencia |
| Reporte ejecutivo | 🔲 Pendiente | Exportación PDF/JSON con anexo de fuentes |
| Panel operativo | 🔲 Pendiente | Cuotas, errores, frescura |

**Caso vertical MVP:** ingrediente agroindustrial peruano → mercado US.

### 5.3 Fase 2 — Inteligencia avanzada

| Capacidad | Descripción |
|---|---|
| Technology Scout | Proyectos financiados, TRL estimado, tecnologías emergentes (CORDIS, NIH RePORTER, NSF) |
| Sostenibilidad | Huella estimada con unidad funcional y metodología explícita (Climatiq, Agribalyse) |
| Inteligencia societaria | Titulares, subsidiarias (OpenCorporates, GS1) |
| Pre-evaluación regulatoria ampliada | OpenFDA, EFSA, EUR-Lex, FoodData Central |
| Vigilancia continua | Alertas programadas sobre consultas guardadas (fuera de MVP) |

### 5.4 Fuera de alcance (todas las fases iniciales)

- Resolución jurídica de claims, registro sanitario o libertad de operación.
- LCA/PCF verificable con rating tipo "B+".
- Inteligencia societaria integral en MVP.
- Procesamiento masivo y alertas en tiempo real.
- Recomendaciones automáticas de inversión o lanzamiento.
- Dictamen legal o afirmación de "bajo riesgo regulatorio".

---

## 6. Requisitos funcionales

### 6.1 Gestión de consultas y runs

| ID | Requisito | Prioridad | Fase |
|---|---|---|---|
| RF-001 | El sistema debe crear un `research_run` único (`rr_<hex32>`) por consulta | Must | 0 |
| RF-002 | Debe conservar consulta original, normalizada, mercado destino, aplicación y fecha de corte | Must | 0 |
| RF-003 | Debe versionar taxonomía usada (`taxonomy_version`) | Must | 0 |
| RF-004 | Debe exponer estados: `running`, `completed`, `failed` | Must | 0 |
| RF-005 | Debe permitir re-ejecutar enriquecimientos sobre un run existente | Must | 0 |
| RF-006 | Debe soportar consultas asíncronas para dominios pesados | Should | 1 |
| RF-007 | Debe permitir guardar y re-ejecutar consultas (plantillas) | Could | 2 |

### 6.2 Conectores y almacenamiento

| ID | Requisito | Prioridad | Fase |
|---|---|---|---|
| RF-010 | Cada petición a fuente debe registrarse como `source_request` con URL, parámetros y licencia | Must | 0 |
| RF-011 | La respuesta cruda debe almacenarse de forma inmutable con checksum SHA-256 | Must | 0 |
| RF-012 | Los conectores deben ser independientes, intercambiables y con manejo de errores explícito | Must | 0 |
| RF-013 | Debe existir caché por checksum para evitar re-descargas idénticas | Should | 1 |
| RF-014 | Debe respetar cuotas y rate limits por fuente con backoff exponencial | Must | 1 |
| RF-015 | Cada conector debe pasar prueba de viabilidad antes de producción | Must | 1 |

### 6.3 Dominio — Evidencia científica

| ID | Requisito | Prioridad | Fase |
|---|---|---|---|
| RF-020 | Buscar publicaciones por término, fecha mínima y límite | Must | 0 |
| RF-021 | Normalizar: OpenAlex ID, DOI, título, fecha, citas, tipo, ubicación primaria | Must | 0 |
| RF-022 | Enriquecer por DOI vía Crossref sin duplicar evidencia | Must | 0 |
| RF-023 | Vincular múltiples fuentes al mismo registro (`evidence_source_links`) | Must | 0 |
| RF-024 | Extraer tópicos, autores e instituciones principales | Should | 1 |
| RF-025 | Integrar PubMed y Semantic Scholar como respaldo | Could | 1 |
| RF-026 | Estimar TRL a partir de señales bibliométricas (con disclaimer) | Could | 2 |

**Salida esperada (dominio ciencia):**

```json
{
  "domain": "science",
  "papers_count": 142,
  "top_topics": ["Plant Protein", "Bioactive Peptides", "Functional Foods"],
  "top_authors": [],
  "citation_trend": "growing",
  "trl_estimate": 4,
  "evidence_refs": ["ev_abc123"]
}
```

### 6.4 Dominio — Inteligencia de patentes

| ID | Requisito | Prioridad | Fase |
|---|---|---|---|
| RF-030 | Buscar patentes por término, IPC/CPC y rango de fechas | Must | 1 |
| RF-031 | Normalizar: número, titular, fecha, IPC/CPC, estado, resumen | Must | 1 |
| RF-032 | Calcular volumen y evolución temporal | Must | 1 |
| RF-033 | Identificar top assignees y familias relevantes | Should | 1 |
| RF-034 | Deduplicar entre EPO OPS y fuentes opcionales (Lens) | Should | 1 |

**Salida esperada:**

```json
{
  "domain": "patent",
  "patents_count": 81,
  "top_assignees": ["Nestlé", "DSM", "PepsiCo"],
  "top_ipc": ["A23L", "C12N"],
  "filing_trend": "stable",
  "evidence_refs": ["ev_def456"]
}
```

### 6.5 Dominio — Señales de demanda

| ID | Requisito | Prioridad | Fase |
|---|---|---|---|
| RF-040 | Obtener interés de búsqueda por mercado destino (Google Trends — experimental) | Could | 1 |
| RF-041 | Obtener cobertura noticiosa vía GDELT con normalización de idioma y duplicados | Must | 1 |
| RF-042 | Distinguir señal de mercado de evidencia comercial verificada | Must | 1 |
| RF-043 | Calcular tendencia y crecimiento relativo en periodo | Must | 1 |

**Salida esperada:**

```json
{
  "domain": "trend",
  "trend": "growing",
  "growth_percent": 48,
  "top_countries": ["USA", "Japan", "Germany"],
  "news_volume": 234,
  "signal_quality": "medium",
  "evidence_refs": ["ev_ghi789"]
}
```

### 6.6 Dominio — Comercio exterior

| ID | Requisito | Prioridad | Fase |
|---|---|---|---|
| RF-050 | Consultar flujos por código HS, país origen/destino y periodo | Must | 1 |
| RF-051 | Calcular CAGR y ranking de exportadores/importadores | Must | 1 |
| RF-052 | Mapear producto consultado a códigos HS con taxonomía versionada | Must | 1 |
| RF-053 | Complementar con FAOSTAT y World Bank cuando aplique | Should | 1 |

**Salida esperada:**

```json
{
  "domain": "trade",
  "major_exporters": ["Peru", "Chile", "Ecuador"],
  "imports_growth_percent": 22.4,
  "hs_codes": ["1806.10", "1806.32"],
  "period": {"from": "2022", "to": "2025"},
  "evidence_refs": ["ev_jkl012"]
}
```

### 6.7 Scoring y recomendación

| ID | Requisito | Prioridad | Fase |
|---|---|---|---|
| RF-060 | Calcular score por dimensión normalizado 0–100 | Must | 1 |
| RF-061 | Aplicar `coverage_factor` al score bruto | Must | 1 |
| RF-062 | Emitir recomendación: `Investigate`, `Validate`, `Deprioritize` o `Insufficient evidence` | Must | 1 |
| RF-063 | Incluir `score_version`, contribución por dimensión y razones de exclusión | Must | 1 |
| RF-064 | Bloquear recomendación si cobertura < 60% | Must | 1 |
| RF-065 | Mostrar alertas cuando confianza es baja en dominio crítico | Must | 1 |

### 6.8 Reportes y exportación

| ID | Requisito | Prioridad | Fase |
|---|---|---|---|
| RF-070 | Generar ficha ejecutiva con resumen, score, evidencia y vacíos | Must | 1 |
| RF-071 | Exportar anexo de fuentes con checksums y fechas de extracción | Must | 1 |
| RF-072 | Distinguir visualmente hechos, inferencias y recomendaciones | Must | 1 |
| RF-073 | Exportar en JSON y PDF | Should | 1 |

### 6.9 Pre-evaluación regulatoria (Fase 2)

| ID | Requisito | Prioridad | Fase |
|---|---|---|---|
| RF-080 | Identificar jurisdicción, categoría de alimento, ingrediente y claims relevantes | Should | 2 |
| RF-081 | Buscar documentos en OpenFDA, EFSA, EUR-Lex | Should | 2 |
| RF-082 | Emitir solo estados: `not_assessed`, `needs_review`, `potential_constraint`, `no_constraint_found` | Must | 2 |
| RF-083 | Registrar revisor humano y fecha de corte para uso externo | Must | 2 |

### 6.10 Technology Scout (Fase 2)

| ID | Requisito | Prioridad | Fase |
|---|---|---|---|
| RF-090 | Buscar proyectos financiados y publicaciones en CORDIS, Europe PMC, OpenAIRE | Could | 2 |
| RF-091 | Estimar TRL y monto de financiamiento cuando la fuente lo permita | Could | 2 |

### 6.11 Sostenibilidad (Fase 2)

| ID | Requisito | Prioridad | Fase |
|---|---|---|---|
| RF-100 | Estimar huella con unidad funcional, frontera, región, año y factor usado | Could | 2 |
| RF-101 | Nunca emitir rating agregado (ej. "B+") sin metodología publicada y validada | Must | 2 |

---

## 7. Requisitos no funcionales

| ID | Categoría | Requisito | Objetivo |
|---|---|---|---|
| RNF-001 | Trazabilidad | 100% de afirmaciones cuantitativas enlazadas a fuente y fecha | Auditoría completa |
| RNF-002 | Reproducibilidad | Misma consulta + versión = mismo resultado o diff explicado | Confianza |
| RNF-003 | Latencia | Resultado inicial < 10 min; procesos pesados asíncronos | UX |
| RNF-004 | Disponibilidad | 99% en horario laboral (MVP) | Operación |
| RNF-005 | Escalabilidad | Arquitectura modular; conectores independientes | Evolución |
| RNF-006 | Coste | Presupuesto mensual de APIs definido y monitoreado | Sostenibilidad |
| RNF-007 | Seguridad | Secretos fuera de código; control de acceso; auditoría de consultas | Compliance |
| RNF-008 | Retención | Política de retención de datos crudos y metadatos documentada | Privacidad |
| RNF-009 | Observabilidad | Métricas de error, cuota, frescura y cobertura por conector | Ops |
| RNF-010 | Idempotencia | Reintentos de conectores no duplican evidencia ni peticiones | Robustez |
| RNF-011 | Licencias | Cumplir atribución y términos de cada fuente activa | Legal |
| RNF-012 | Accesibilidad | API documentada (OpenAPI); respuestas con envelope consistente | Integración |

---

## 8. Fuentes de datos y viabilidad

### Criterio de selección

**API-first con fuentes de bajo coste**, no "100% APIs públicas gratuitas". Cada conector debe pasar prueba de viabilidad: cobertura, licencia comercial, cuota, estabilidad, coste y datos obtenibles.

### Matriz de fuentes

| Dominio | Fuente | Rol | Estado | Condición |
|---|---|---|---|---|
| Ciencia | OpenAlex | Primaria | ✅ Activa | Atribución requerida |
| Ciencia | Crossref | Enriquecimiento | ✅ Activa | `PITCHAVI_CONTACT_EMAIL` para pool cortés |
| Ciencia | PubMed | Respaldo | 🔲 Pendiente | Clave NCBI recomendada |
| Ciencia | Semantic Scholar | Respaldo | 🔲 Pendiente | Cuota y clave según plan |
| Patentes | EPO OPS | Primaria | 🔲 Pendiente | OAuth; tramo gratuito limitado |
| Patentes | Lens | Opcional | 🔲 Evaluar | Requiere acuerdo o suscripción |
| Patentes | WIPO Patentscope | Respaldo | 🔲 Pendiente | Validar términos |
| Tendencias | GDELT | Primaria | 🔲 Pendiente | Normalizar ruido e idioma |
| Tendencias | Google Trends | Experimental | 🔲 Evaluar | API en alfa; no dependencia crítica |
| Noticias | NewsAPI | Opcional | 🔲 Evaluar | Plan gratuito no sirve para producción |
| Comercio | UN Comtrade | Primaria | 🔲 Pendiente | Mapeo HS consistente |
| Comercio | FAOSTAT | Complementaria | 🔲 Pendiente | Validar granularidad |
| Comercio | World Bank | Complementaria | 🔲 Pendiente | Indicadores macro |
| Regulación | OpenFDA | Descubrimiento | Fase 2 | Solo localizar evidencia |
| Regulación | EFSA / EUR-Lex | Descubrimiento | Fase 2 | Revisión humana obligatoria |
| Nutrición | FoodData Central | Complementaria | Fase 2 | No autoriza claims |
| Sostenibilidad | Climatiq / Agribalyse | Fase 2 | Evaluar | Licencia y metodología |
| Societaria | OpenCorporates | Fase 2 | Evaluar | Plan y cobertura LATAM |
| Financiamiento | CORDIS, NIH, NSF | Fase 2 | Evaluar | Technology scout |

### Referencias operativas

- [EPO OPS](https://www.epo.org/en/searching-for-patents/data/web-services/ops)
- [Lens API terms](https://about.lens.org/lens-api-terms-of-use/)
- [Google Trends API](https://developers.google.com/search/apis/trends)
- [NewsAPI pricing](https://newsapi.org/pricing)
- [FoodData Central API](https://fdc.nal.usda.gov/api-guide/)
- [Climatiq pricing](https://www.climatiq.io/pricing)
- [OpenAlex documentation](https://docs.openalex.org/)
- [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)

### Proceso de aprobación de fuente

1. Spike técnico (1–2 días): cobertura, campos, cuota, errores típicos.
2. Revisión legal: licencia comercial, atribución, restricciones de redistribución.
3. Aprobación en matriz con owner, fecha y versión de conector.
4. Solo entonces el conector entra a producción.

---

## 9. Arquitectura técnica

### 9.1 Diagrama de alto nivel

```text
                    UI / Cliente API
                           |
                    FastAPI (Pitchavi)
                           |
              Servicio de investigación
              (ResearchService / research_run)
                           |
              Orquestador de tareas
              (sync MVP → async Fase 1+)
                           |
        ┌──────────────────┼──────────────────┐
        |                  |                  |
   Conectores          ResearchStore      Motor de scoring
   (OpenAlex,          (SQLite + raw       (Fase 1)
    Crossref,           SHA-256)
    EPO, GDELT,
    Comtrade...)
        |                  |
        └────────► normalizador / deduplicador
                           |
                    modelo de evidencia
                           |
              claims + métricas por dominio
                           |
              reporte + observabilidad + auditoría
```

### 9.2 Componentes

| Componente | Responsabilidad | Estado |
|---|---|---|
| `pitchavi.api` | Endpoints REST, validación, envelope de respuesta | ✅ |
| `pitchavi.research` | Orquestación de runs y enriquecimientos | ✅ |
| `pitchavi.storage` | SQLite, raw inmutable, evidencia | ✅ |
| `pitchavi.openalex` | Conector OpenAlex | ✅ |
| `pitchavi.crossref` | Conector Crossref | ✅ |
| Conector patentes | EPO OPS | 🔲 |
| Conector tendencias | GDELT | 🔲 |
| Conector comercio | UN Comtrade | 🔲 |
| Motor de scoring | Cálculo y reglas de cobertura | 🔲 |
| Generador de reportes | PDF/JSON ejecutivo | 🔲 |
| Panel operativo | Métricas y alertas | 🔲 |
| Orquestador async | Cola de tareas (Celery/RQ/ARQ) | 🔲 |

### 9.3 Stack tecnológico

| Capa | Tecnología | Notas |
|---|---|---|
| Lenguaje | Python ≥ 3.11 | Actual |
| API | FastAPI + Uvicorn | Actual |
| Persistencia | SQLite (MVP) → PostgreSQL (prod) | Migración planificada |
| Raw storage | Filesystem local (MVP) → S3-compatible | Content-addressed |
| Tests | unittest + TestClient | Actual |
| Observabilidad | Logging estructurado → Prometheus/Grafana | Fase 1 |
| Despliegue | Contenedor Docker | Fase 1 |

### 9.4 Variables de entorno

| Variable | Descripción | Default |
|---|---|---|
| `PITCHAVI_DB_PATH` | Ruta a base SQLite | `data/pitchavi.db` |
| `PITCHAVI_RAW_DIR` | Directorio de respuestas crudas | `data/raw/` |
| `PITCHAVI_CONTACT_EMAIL` | Email para pool cortés Crossref | — |

---

## 10. Modelo de datos

### 10.1 Entidades principales (implementadas)

#### `research_runs`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | TEXT PK | `rr_<hex32>` |
| `query_original` | TEXT | Consulta ingresada por el usuario |
| `query_normalized` | TEXT | Consulta normalizada (casefold, espacios) |
| `taxonomy_version` | TEXT | Versión del vocabulario (ej. `cacao-functional-v1`) |
| `target_market` | TEXT | Código ISO 3166-1 alpha-2 (ej. `US`) |
| `application` | TEXT | Aplicación objetivo |
| `cutoff_at` | TEXT ISO8601 | Fecha de corte de la investigación |
| `status` | TEXT | `running`, `completed`, `failed` |
| `created_at` | TEXT ISO8601 | — |
| `completed_at` | TEXT ISO8601 | Nullable |
| `error` | TEXT | Mensaje si `failed` |

#### `source_requests`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | TEXT PK | Identificador único |
| `research_run_id` | TEXT FK | Run padre |
| `source` | TEXT | `openalex`, `crossref`, etc. |
| `request_url` | TEXT | URL completa de la petición |
| `request_params` | TEXT JSON | Parámetros serializados |
| `fetched_at` | TEXT ISO8601 | Fecha de obtención |
| `http_status` | INTEGER | Código HTTP |
| `checksum` | TEXT | SHA-256 del contenido crudo |
| `raw_object_key` | TEXT | Clave en almacenamiento crudo |
| `license` | TEXT | Licencia de la fuente |
| `status` | TEXT | `running`, `completed`, `failed` |
| `error` | TEXT | Mensaje si `failed` |

#### `evidence_records`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | TEXT PK | Identificador único |
| `research_run_id` | TEXT FK | Run padre |
| `source_request_id` | TEXT FK | Petición que originó el registro |
| `source` | TEXT | Fuente primaria del registro |
| `domain` | TEXT | `science`, `patent`, `trend`, `trade` |
| `external_id` | TEXT | ID en la fuente (OpenAlex ID, DOI, etc.) |
| `title` | TEXT | Título normalizado |
| `published_at` | TEXT | Fecha de publicación |
| `geography` | TEXT | País/región si aplica |
| `normalized_payload` | TEXT JSON | Payload normalizado completo |
| `dedupe_key` | TEXT | Clave de deduplicación (DOI normalizado) |
| `created_at` | TEXT ISO8601 | — |

**Constraint:** `UNIQUE(research_run_id, source, dedupe_key)`

#### `evidence_source_links`
Vincula múltiples fuentes al mismo registro de evidencia (ej. OpenAlex + Crossref por DOI).

### 10.2 Entidades planificadas (Fase 1+)

| Entidad | Propósito |
|---|---|
| `claims` | Afirmaciones derivadas con método, periodo, confianza |
| `domain_scores` | Score por dimensión con versión de metodología |
| `opportunity_scores` | Score agregado con recomendación |
| `hs_mappings` | Mapeo producto → códigos HS versionado |
| `reports` | Reportes generados con versión y formato |

### 10.3 Ejemplo de registro unificado (objetivo)

```json
{
  "source": "openalex",
  "entity": "paper",
  "domain": "science",
  "title": "Protein Extraction from Quinoa",
  "date": "2025-05-01",
  "country": "Peru",
  "score": 0.91,
  "metadata": {
    "doi": "10.1000/example",
    "authors": [],
    "topics": [],
    "cited_by_count": 12
  },
  "trace": {
    "research_run_id": "rr_abc...",
    "source_request_id": "sr_def...",
    "checksum": "a1b2c3..."
  }
}
```

---

## 11. Contrato de evidencia

Todo hallazgo visible en reportes o API debe cumplir este contrato.

### 11.1 Estructura de un claim

```json
{
  "claim_id": "clm_01",
  "statement": "La demanda importadora del código HS seleccionado creció en el periodo analizado.",
  "domain": "trade",
  "value": 22.4,
  "unit": "percent",
  "method": "CAGR",
  "period": {"from": "2022", "to": "2025"},
  "geography": "US",
  "source_refs": ["src_123", "src_456"],
  "confidence": "medium",
  "limitations": ["Cobertura pendiente de revisión para subpartidas HS."]
}
```

### 11.2 Reglas de separación

| Tipo | Descripción | Ejemplo |
|---|---|---|
| **Hecho de fuente** | Dato tal como lo devuelve la API, sin interpretación | "OpenAlex reporta 142 works para la consulta" |
| **Inferencia del sistema** | Transformación documentada sobre hechos | "CAGR 22.4% calculado con método X sobre series Y" |
| **Recomendación** | Conclusión de negocio con reglas explícitas | "`Investigate` porque score ≥ 70 y cobertura ≥ 80%" |

Los conectores **nunca** deben mezclar estos tres tipos en un solo objeto. Cada uno se conserva versionado y por separado.

### 11.3 Niveles de confianza

| Nivel | Criterio |
|---|---|
| `high` | ≥ 2 fuentes concordantes o fuente primaria con cobertura completa |
| `medium` | 1 fuente primaria con cobertura parcial o 2 fuentes con discrepancia menor |
| `low` | 1 fuente, cobertura incompleta, o señal experimental (Trends) |

---

## 12. Scoring y reglas de decisión

### 12.1 Fórmula MVP

```text
raw_score = 0.30 × science
          + 0.20 × patent
          + 0.20 × trend
          + 0.30 × trade

opportunity_score = raw_score × coverage_factor
```

`coverage_factor` = proporción ponderada de dominios con evidencia suficiente.

**Versión inicial:** `score_version: "v1.0-mvp"`

### 12.2 Normalización por dimensión (0–100)

Cada dimensión usa indicadores específicos documentados en su `score_version`. Ejemplos orientativos:

| Dimensio | Indicadores |
|---|---|
| Science | Volumen de publicaciones, tendencia de citas, recencia, diversidad de tópicos |
| Patent | Volumen de filings, crecimiento, concentración de titulares, white space IPC |
| Trend | Crecimiento de búsqueda/noticias, geografía de señal |
| Trade | CAGR de importaciones, posición de Perú, concentración de mercado |

### 12.3 Reglas de decisión

| Regla | Resultado |
|---|---|
| Cobertura < 60% | No emitir recomendación → `Insufficient evidence` |
| Confianza baja en dominio crítico | Mantener score, añadir alerta, requerir revisión |
| Conflicto entre fuentes | Mostrar discrepancia; no promediar sin regla documentada |
| Score ≥ 70, cobertura ≥ 80%, sin alerta crítica | `Investigate` |
| Score 50–69 o cobertura 60–79% | `Validate` |
| Score < 50 | `Deprioritize` |

### 12.4 Salida de scoring

```json
{
  "score_version": "v1.0-mvp",
  "opportunity_score": 72.4,
  "coverage_factor": 0.85,
  "recommendation": "Investigate",
  "dimensions": {
    "science": {"score": 78, "confidence": "high", "weight": 0.30},
    "patent": {"score": 65, "confidence": "medium", "weight": 0.20},
    "trend": {"score": 70, "confidence": "medium", "weight": 0.20},
    "trade": {"score": 80, "confidence": "high", "weight": 0.30}
  },
  "alerts": [],
  "exclusions": []
}
```

### 12.5 Fórmula Fase 2 (referencia)

```text
Opportunity = 0.30 × Science
            + 0.20 × Patent
            + 0.20 × Trends
            + 0.15 × Supply
            + 0.15 × Regulation
```

Solo aplica cuando dominios de Supply y Regulation tengan conectores aprobados y cobertura suficiente.

---

## 13. API y contratos

### 13.1 Endpoints implementados

| Método | Ruta | Descripción | Estado |
|---|---|---|---|
| `POST` | `/v1/research-runs` | Crear y ejecutar investigación científica | ✅ |
| `GET` | `/v1/research-runs/{run_id}` | Obtener detalle de un run | ✅ |
| `POST` | `/v1/research-runs/{run_id}/enrichments/crossref` | Enriquecer con Crossref | ✅ |

### 13.2 Request — Crear research run

```json
{
  "query": "high-flavanol cocoa powder",
  "target_market": "US",
  "application": "functional foods and beverages",
  "from_publication_date": "2021-01-01",
  "limit": 25
}
```

| Campo | Tipo | Validación | Default |
|---|---|---|---|
| `query` | string | 3–300 caracteres | — (requerido) |
| `target_market` | string | `^[A-Z]{2}$` | `US` |
| `application` | string | 3–200 caracteres | `functional foods and beverages` |
| `from_publication_date` | string | `YYYY-MM-DD` | `2021-01-01` |
| `limit` | integer | 1–100 | `25` |

### 13.3 Response envelope

Todas las respuestas usan envelope consistente:

```json
{
  "data": { },
  "meta": {
    "confidence": "ok",
    "evidence_count": 25
  },
  "trace": {
    "version": "0.1.0",
    "timestamp": "2026-07-24T18:00:00+00:00"
  }
}
```

### 13.4 Endpoints planificados (Fase 1)

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/v1/research-runs/{run_id}/domains/patent` | Ejecutar dominio patentes |
| `POST` | `/v1/research-runs/{run_id}/domains/trend` | Ejecutar dominio tendencias |
| `POST` | `/v1/research-runs/{run_id}/domains/trade` | Ejecutar dominio comercio |
| `POST` | `/v1/research-runs/{run_id}/score` | Calcular Opportunity Score |
| `GET` | `/v1/research-runs/{run_id}/report` | Obtener ficha ejecutiva |
| `GET` | `/v1/research-runs/{run_id}/report/export` | Exportar PDF/JSON |
| `GET` | `/v1/health` | Health check |
| `GET` | `/v1/connectors/status` | Estado de conectores y cuotas |

### 13.5 Códigos de error

| HTTP | Situación |
|---|---|
| `201` | Run creado y completado |
| `404` | Run no encontrado |
| `422` | Validación de payload |
| `502` | Error de conector externo (con `research_run_id` y mensaje) |

---

## 14. Flujos de usuario

### 14.1 Flujo principal — Consulta integral (objetivo MVP)

```text
1. Usuario ingresa: producto, mercado destino, aplicación, periodo, HS opcional
2. Sistema normaliza consulta → crea research_run
3. Orquestador ejecuta conectores (ciencia → patentes → tendencias → comercio)
4. Cada conector: petición → raw inmutable → evidencia normalizada
5. Motor deduplica, vincula entidades, calcula indicadores por dominio
6. Motor de scoring aplica reglas de cobertura → score + recomendación
7. Usuario recibe ficha: recomendación, evidencia, vacíos, riesgos, acciones
```

### 14.2 Flujo actual — Solo ciencia (implementado)

```text
1. POST /v1/research-runs con query
2. OpenAlex → source_request + raw SHA-256 → evidence_records
3. (Opcional) POST enrichments/crossref → source_links por DOI
4. GET /v1/research-runs/{id} → detalle con evidencia y fuentes
```

### 14.3 Flujo de auditoría

```text
1. Usuario ve número en reporte (ej. "CAGR 22.4%")
2. Navega a claim_id → source_refs
3. Abre source_request → checksum → archivo raw
4. Verifica que el cálculo coincide con la transformación documentada
```

### 14.4 Flujo de falla de conector

```text
1. Conector falla (HTTP 429, timeout, etc.)
2. source_request marcado como failed con error y raw parcial si existe
3. research_run marcado como failed (dominio único) o parcial (multi-dominio)
4. API retorna 502 con research_run_id para inspección
5. Usuario puede reintentar enriquecimiento o re-ejecutar dominio
```

---

## 15. Evaluación regulatoria y sostenibilidad

### 15.1 Pre-evaluación regulatoria

El sistema **solo** genera pre-evaluación, nunca dictamen.

**Entrada:** ingrediente, mercado destino, claim propuesto (opcional).

**Proceso:**
1. Identificar jurisdicción, categoría de alimento, ingrediente y documentos relevantes.
2. Buscar en fuentes de descubrimiento (OpenFDA, EFSA, EUR-Lex).
3. Clasificar fuentes: primaria, guía, señal no vinculante.

**Estados permitidos:**

| Estado | Significado |
|---|---|
| `not_assessed` | No se evaluó este aspecto |
| `needs_review` | Evidencia encontrada; requiere revisor humano |
| `potential_constraint` | Señal de posible restricción; no es conclusión |
| `no_constraint_found` | No se encontró restricción en fuentes consultadas (no es aprobación) |

**Estados prohibidos como salida automática:** `approved`, `low risk`, `compliant`.

**Requisito:** revisor humano + fecha de corte para cualquier uso externo.

### 15.2 Sostenibilidad

Toda estimación debe incluir:

| Campo | Descripción |
|---|---|
| `functional_unit` | Unidad funcional (ej. kg producto) |
| `system_boundary` | Frontera del análisis |
| `region` | Región geográfica del factor |
| `year` | Año del factor de emisión |
| `factor_source` | Fuente del factor usado |
| `data_quality` | Calidad de los datos de entrada |

Un rating agregado (ej. "B+") queda **fuera de alcance** hasta existir metodología publicada, validada y aprobada por el equipo de producto.

---

## 16. Seguridad, privacidad y cumplimiento

| Área | Requisito |
|---|---|
| Secretos | API keys y tokens fuera de código; variables de entorno o vault |
| Acceso | Autenticación en API para entornos no locales (Fase 1) |
| Auditoría | Log de quién ejecutó cada `research_run` y cuándo |
| Retención | Política documentada para raw y metadatos (sugerido: 12 meses MVP) |
| PII | No almacenar datos personales de usuarios finales en evidencia |
| Licencias | Matriz de licencia aprobada por fuente activa; atribución en reportes |
| Redistribución | No republicar datos crudos de fuentes con restricción |
| Rate limiting | Protección de API propia contra abuso |

---

## 17. Métricas y KPIs

### 17.1 Métricas de producto

| Métrica | Criterio MVP | Medición |
|---|---|---|
| Trazabilidad | 100% de claims cuantitativos con fuente | Auditoría automática |
| Reproducibilidad | Misma consulta = mismo resultado o diff explicado | Test de regresión |
| Cobertura | ≥ 3 de 4 dominios con evidencia suficiente | Por run |
| Latencia | Resultado inicial < 10 min | p95 de `research_run` |
| Utilidad | Analista verifica en < 15 min | Test con usuarios |
| Tasa de falla de conectores | < 5% en horario laboral | Por fuente |

### 17.2 Métricas operativas

| Métrica | Descripción |
|---|---|
| Cuota consumida | Por fuente y periodo |
| Frescura | Tiempo desde última extracción exitosa |
| Cobertura de conectores | Dominios con evidencia vs. solicitados |
| Error rate | Por conector y código HTTP |
| Coste mensual | Suma de APIs de pago |

### 17.3 Métricas de adopción (post-MVP)

| Métrica | Descripción |
|---|---|
| Runs por semana | Volumen de uso |
| Reportes exportados | Adopción de salida ejecutiva |
| Tiempo ahorrado | vs. proceso manual (encuesta) |
| NPS / satisfacción | Por persona analista |

---

## 18. Plan de entrega

### 18.1 Roadmap por sprint

| Sprint | Entregable | APIs / componentes | Criterio de done |
|---|---|---|---|
| **0** ✅ | Fundación científica | OpenAlex, Crossref, SQLite, FastAPI | Tests pasan; raw inmutable; dedup DOI |
| **1** | Taxonomía + ampliación ciencia | PubMed, Semantic Scholar | Tópicos, autores; taxonomía versionada |
| **2** | Patentes | EPO OPS | Volumen, titulares, IPC; dedup |
| **3** | Tendencias + comercio | GDELT, UN Comtrade | Indicadores normalizados por dominio |
| **4** | Scoring + reporte | Motor v1, generador PDF/JSON | Score explicable; exportación |
| **5** | Validación + hardening | Panel ops, auth, Docker | 10 consultas reales; calibración |
| **6** | Technology scout | CORDIS, NIH, NSF | TRL estimado; financiamiento |
| **7** | Regulación + sostenibilidad | OpenFDA, EFSA, Climatiq | Pre-evaluación; huella con metodología |

### 18.2 Hitos

| Hito | Fecha objetivo | Descripción |
|---|---|---|
| M0 — Alpha ciencia | ✅ 2026-07 | API científica trazable funcional |
| M1 — MVP funcional | TBD | 4 dominios + scoring + reporte |
| M2 — Validación usuarios | TBD | 10 consultas reales con analistas |
| M3 — Beta cerrada | TBD | Auth, Docker, panel ops |
| M4 — Fase 2 | TBD | Scout, regulación, sostenibilidad |

### 18.3 Dependencias entre sprints

```text
Sprint 0 (ciencia) ──► Sprint 1 (taxonomía)
        │
        ├──► Sprint 2 (patentes)
        ├──► Sprint 3 (tendencias + comercio)
        │           │
        │           ▼
        └──► Sprint 4 (scoring + reporte)
                    │
                    ▼
              Sprint 5 (validación)
                    │
                    ▼
              Sprint 6–7 (Fase 2)
```

---

## 19. Riesgos y mitigaciones

| Riesgo | Impacto | Probabilidad | Mitigación |
|---|---|---|---|
| Cuota agotada en EPO OPS o Comtrade | Alto | Media | Caché, backoff, límites por run, alertas |
| Google Trends API inestable | Medio | Alta | Marcar como experimental; GDELT como primaria |
| Lens requiere licencia comercial | Medio | Alta | EPO OPS como primaria; Lens solo con presupuesto |
| Datos HS mal mapeados | Alto | Media | Taxonomía versionada; revisión humana de mapeo |
| Score mal calibrado genera falsa confianza | Alto | Media | Cobertura mínima; alertas; validación con 10 casos reales |
| Usuario interpreta pre-evaluación como aprobación | Crítico | Media | Estados conservadores; disclaimers; revisor obligatorio |
| SQLite no escala en producción | Medio | Alta | Migración a PostgreSQL planificada en Sprint 5 |
| Dependencia de una sola fuente por dominio | Medio | Media | Fuentes de respaldo documentadas en matriz |
| Coste de APIs excede presupuesto | Alto | Media | Panel de coste; aprobación previa de fuentes de pago |

---

## 20. Estado de implementación actual

### 20.1 Resumen

**Pitchavi v0.1.0** implementa la Fase 0 (fundación científica). El código vive en `src/pitchavi/`.

### 20.2 Lo que funciona hoy

| Capacidad | Archivo | Verificado |
|---|---|---|
| Crear `research_run` | `storage.py`, `research.py` | ✅ Tests |
| Buscar en OpenAlex | `openalex.py` | ✅ Tests |
| Almacenar raw SHA-256 | `storage.py` | ✅ Tests |
| Normalizar evidencia científica | `research.py` | ✅ Tests |
| Enriquecer con Crossref (sin dup DOI) | `crossref.py`, `research.py` | ✅ Tests |
| API REST con envelope | `api.py` | ✅ Tests |
| Manejo de fallas de conector | `research.py`, `api.py` | ✅ Tests |
| `evidence_source_links` multi-fuente | `storage.py` | ✅ Tests |

### 20.3 Lo que falta para MVP

- Conectores: patentes, tendencias, comercio
- Motor de scoring y claims
- Generador de reportes
- Panel operativo
- Autenticación y despliegue productivo
- Taxonomía HS formal
- Orquestación asíncrona

### 20.4 Cómo ejecutar

```powershell
$env:PYTHONPATH = "src"
python -m uvicorn pitchavi.api:app --reload
```

Documentación interactiva: `http://127.0.0.1:8000/docs`

---

## 21. Criterios de aceptación

### 21.1 Generales (todas las fases)

- [ ] Una consulta completa conserva parámetros, respuestas, versiones, fecha de corte y fuentes.
- [ ] Todo número del reporte puede rastrearse a una transformación y fuente.
- [ ] El sistema falla de forma visible cuando una fuente queda sin acceso, excede cuota o devuelve datos insuficientes.
- [ ] El reporte distingue hechos, inferencias y recomendaciones.
- [ ] La recomendación baja de categoría o se bloquea cuando falta cobertura crítica.
- [ ] Ningún texto afirma cumplimiento regulatorio, libertad de operación o sostenibilidad verificada sin revisión humana.

### 21.2 Fase 0 (ciencia) — aceptación

- [x] `POST /v1/research-runs` crea run y devuelve evidencia normalizada.
- [x] Respuesta cruda almacenada con checksum SHA-256 verificable.
- [x] DOI duplicado no genera segundo registro de evidencia.
- [x] Crossref enriquece registro existente vía `source_links`.
- [x] Falla de OpenAlex marca run como `failed` con detalle de error.
- [x] Tests unitarios y de API pasan.

### 21.3 MVP — aceptación

- [ ] Consulta integral ejecuta ≥ 3 dominios y produce score.
- [ ] Cobertura < 60% bloquea recomendación.
- [ ] Reporte exportable en JSON con anexo de fuentes.
- [ ] 10 consultas reales validadas por analista en < 15 min de verificación c/u.
- [ ] Panel muestra cuota y error rate por conector.
- [ ] Matriz de licencias aprobada para cada fuente activa.

---

## 22. Decisiones pendientes

| # | Decisión | Opciones | Impacto | Owner sugerido |
|---|---|---|---|---|
| 1 | Producto/ingrediente inicial del caso vertical | Cacao flavanol, quinua proteína, aguaymanto, otro | Define taxonomía y pruebas | Producto |
| 2 | Mercado destino inicial | US (recomendado), EU, ambos | Fuentes regulatorias y comercio | Producto |
| 3 | Taxonomía y mapeo HS oficial | Versión `cacao-functional-v1` vs. nueva | Calidad de dominio trade | I+D + Comercio |
| 4 | Presupuesto mensual máximo de APIs | $0, $50, $200, otro | Fuentes de pago (Lens, NewsAPI) | Finanzas |
| 5 | Rol de revisor regulatorio | Interno, externo, ambos | Flujo de pre-evaluación | Compliance |
| 6 | Periodicidad de uso | Bajo demanda, monitoreo programado, ambos | Arquitectura async y alertas | Producto |
| 7 | Base de datos producción | PostgreSQL managed vs. self-hosted | Sprint 5 | Ingeniería |
| 8 | Autenticación | API key, OAuth2, SSO | Seguridad MVP | Ingeniería |

---

## 23. Anexos

### 23.1 Glosario

| Término | Definición |
|---|---|
| `research_run` | Unidad de trabajo que agrupa una consulta, sus parámetros, fuentes y evidencia |
| `source_request` | Petición individual a una fuente externa con trazabilidad completa |
| `evidence_record` | Registro normalizado de un hallazgo (paper, patente, señal, flujo) |
| `claim` | Afirmación derivada con método, valor, confianza y referencias |
| `coverage_factor` | Proporción de dominios con evidencia suficiente; modula el score |
| `dedupe_key` | Clave para evitar duplicados (típicamente DOI normalizado) |
| `taxonomy_version` | Versión del vocabulario de sinónimos y mapeos HS |
| TRL | Technology Readiness Level; estimación orientativa, no certificación |
| HS | Harmonized System; clasificación arancelaria de comercio exterior |
| CAGR | Compound Annual Growth Rate |

### 23.2 Agentes del sistema (visión Fases 1–2)

| Agente | Dominio | APIs principales |
|---|---|---|
| Scientific Evidence | Ciencia | OpenAlex, Crossref, PubMed, Semantic Scholar |
| Patent Intelligence | Patentes | EPO OPS, WIPO, Lens |
| Consumer Trends | Demanda | Google Trends, GDELT, NewsAPI |
| Supply Chain | Comercio | UN Comtrade, FAOSTAT, World Bank |
| Regulatory | Regulación | OpenFDA, EFSA, EUR-Lex, FoodData Central |
| Technology Scout | I+D emergente | CORDIS, Europe PMC, NIH, NSF |
| Sustainability | Huella | Climatiq, Agribalyse, EPA |
| Company Intelligence | Societaria | OpenCorporates, GS1 |
| Opportunity Scoring | Decisión | Motor interno (sin API externa) |

### 23.3 Flujo de agentes (visión completa)

```text
Consulta del usuario
        │
        ▼
Scientific Evidence ──► Patent Intelligence
        │                       │
        ▼                       ▼
Consumer Trends ◄──► Supply Chain
        │                       │
        └───────────┬───────────┘
                    ▼
              Regulatory (Fase 2)
                    │
                    ▼
           Technology Scout (Fase 2)
                    │
                    ▼
           Sustainability (Fase 2)
                    │
                    ▼
           Opportunity Scoring
                    │
                    ▼
            Reporte Ejecutivo
```

### 23.4 Referencias de documentación

| Documento | Descripción |
|---|---|
| `README.md` | Guía de ejecución y ejemplo de API |
| `PRD_Plataforma_Inteligencia_Tecnologica_MVP_v1_1.md` | PRD MVP ejecutable v1.1 |
| `PRD_Plataforma_Inteligencia_Tecnologica_Fases_1_2.md` | Visión de fases y agentes |
| Este documento | PRD maestro unificado v2.0 |

---

*Fin del documento — Pitchavi PRD v2.0*
