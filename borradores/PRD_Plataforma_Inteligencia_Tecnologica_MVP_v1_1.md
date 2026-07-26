# PRD — Plataforma de Inteligencia Tecnológica

**Versión:** 1.1 (propuesta ejecutable)  
**Estado:** listo para diseño técnico y validación de fuentes  
**Fecha:** 2026-07-24  
**Documento base:** `PRD_Plataforma_Inteligencia_Tecnologica_Fases_1_2.md`

## 1. Decisión de producto

La plataforma responde consultas de innovación con evidencia trazable, no con una recomendación autónoma definitiva. El primer producto debe enfocarse en un caso vertical para demostrar valor y calidad antes de ampliar dominios.

**Caso MVP recomendado:** identificar oportunidades para un ingrediente o producto agroindustrial peruano destinado a exportación a Estados Unidos.

**Decisión que habilita:** priorizar una oportunidad para investigación, validación comercial o revisión regulatoria humana.

**No habilita:** aprobación regulatoria, libertad de operación, dictamen legal, ni cálculo de huella verificado.

## 2. Objetivo y métricas de éxito

Para una consulta formulada con producto, mercado destino y horizonte temporal, entregar una ficha ejecutiva reproducible que incluya evidencia, señales, limitaciones y una recomendación.

| Métrica | Criterio MVP |
|---|---|
| Trazabilidad | 100% de afirmaciones cuantitativas enlazadas a una fuente y fecha de extracción |
| Reproducibilidad | Misma consulta y versión de datos producen el mismo resultado o una diferencia explicada |
| Cobertura | Al menos 3 de los 4 dominios MVP con evidencia suficiente |
| Latencia | Resultado inicial en menos de 10 minutos; procesos pesados asíncronos |
| Utilidad | Un analista puede verificar, en menos de 15 minutos, por qué se recomendó o descartó una oportunidad |

## 3. Alcance

### Incluido en MVP

1. Evidencia científica: publicaciones, citas, tópicos, autores e instituciones.
2. Inteligencia de patentes: volumen, evolución temporal, titulares, IPC/CPC y estado cuando la fuente lo permita.
3. Señales de demanda: interés de búsqueda y cobertura noticiosa, distinguiendo señal de mercado de evidencia comercial.
4. Comercio exterior: flujos, países, códigos HS y evolución de importaciones/exportaciones.
5. Scoring explicable con cobertura, confianza, alertas y enlaces a la evidencia.
6. Exportación de reporte ejecutivo con anexos de fuentes.

### Excluido del MVP

- Resolución jurídica de claims, registro sanitario, libertad de operación o cumplimiento regulatorio.
- Sostenibilidad basada en LCA/PCF verificable.
- Inteligencia societaria integral.
- Procesamiento masivo, vigilancia continua y alertas en tiempo real.
- Recomendaciones automáticas de inversión o lanzamiento.

## 4. Fuentes y viabilidad

El criterio es **API-first con fuentes de bajo coste**, no “100% APIs públicas”. Cada conector debe pasar una prueba de viabilidad antes de entrar a producción: cobertura, licencia comercial, cuota, estabilidad, coste y datos obtenibles.

| Dominio | Fuente candidata | Estado MVP | Condición |
|---|---|---|---|
| Ciencia | OpenAlex, Crossref, PubMed, Semantic Scholar | Primaria / respaldo | Clave, cuota y atribución según fuente |
| Patentes | EPO OPS | Primaria | Registro, OAuth y control de volumen; tramo gratuito limitado |
| Patentes | Lens | Opcional | No asumir uso comercial gratuito; requiere acuerdo o suscripción |
| Tendencias | Google Trends | Experimental | API en alfa con acceso limitado; no es dependencia crítica |
| Tendencias | GDELT | Primaria | Normalizar ruido, idioma y duplicados |
| Noticias | NewsAPI | Opcional | El plan gratuito no sirve para producción |
| Comercio | UN Comtrade, FAOSTAT, World Bank | Primaria / complementaria | Requiere mapeo consistente de HS, país y periodo |
| Regulación | EUR-Lex, EFSA, OpenFDA | Descubrimiento | Solo para localizar evidencia; revisión humana obligatoria |
| Nutrición | FoodData Central | Complementaria | Datos nutricionales, no autorización de claims |
| Sostenibilidad | Climatiq, Agribalyse | Fase posterior | Validar licencia, metodología, unidad funcional y cobertura |

Referencias operativas: [EPO OPS](https://www.epo.org/en/searching-for-patents/data/web-services/ops), [Lens API terms](https://about.lens.org/lens-api-terms-of-use/), [Google Trends API](https://developers.google.com/search/apis/trends), [NewsAPI pricing](https://newsapi.org/pricing), [FoodData Central API](https://fdc.nal.usda.gov/api-guide/), [Climatiq pricing](https://www.climatiq.io/pricing).

## 5. Flujo de usuario

1. El usuario ingresa: producto/ingrediente, mercado destino, aplicación, periodo y, opcionalmente, códigos HS o términos sinónimos.
2. El sistema normaliza la consulta en un vocabulario versionado y crea un `research_run`.
3. Los conectores recuperan resultados, conservan respuesta cruda y generan registros normalizados.
4. El motor deduplica, vincula entidades y calcula indicadores por dominio.
5. El motor de decisión aplica reglas de cobertura, calcula score y confianza, y registra explicaciones.
6. El usuario recibe una ficha con recomendación, evidencia, vacíos, riesgos y acciones siguientes.

## 6. Arquitectura objetivo

```text
UI / API de consulta
        |
Servicio de investigación (research_run, parámetros, versión)
        |
Orquestador de tareas y límites por fuente
        |
Conectores --> almacenamiento crudo --> normalizador/deduplicador
                                      |
                              modelo de evidencia
                                      |
                       métricas por dominio + scoring
                                      |
                  reporte, auditoría, observabilidad y alertas
```

Componentes obligatorios:

- **Almacenamiento crudo inmutable:** respuesta, URL/identificador, fecha, licencia y checksum.
- **Modelo normalizado:** entidades de publicación, patente, señal, flujo comercial, fuente y afirmación.
- **Caché y cuotas:** evita reconsultas, protege límites y controla coste.
- **Orquestación asíncrona:** reintentos idempotentes, estados y timeouts por conector.
- **Observabilidad:** tasa de error, frescura, cuota consumida, cobertura y versiones de conectores/modelos.
- **Seguridad:** secretos fuera de código, control de acceso, retención limitada y auditoría de consultas.

## 7. Contrato de evidencia

Todo hallazgo visible debe incluir:

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

Los conectores nunca deben mezclar respuesta de fuente, inferencia del modelo y conclusión del sistema. Cada una debe conservarse como objeto distinto y versionado.

## 8. Scoring y reglas de decisión

Cada dimensión se normaliza a una escala 0–100 y se calcula con una versión explícita de metodología. Los pesos son una hipótesis inicial, no una verdad de producto:

```text
raw_score = 0.30 * science + 0.20 * patent + 0.20 * trend
          + 0.30 * trade

opportunity_score = raw_score * coverage_factor
```

`coverage_factor` es la proporción ponderada de dominios que alcanzan evidencia suficiente. Por lo tanto, una oportunidad incompleta no puede superar a una alternativa con igual score bruto y mayor cobertura.

| Regla | Resultado |
|---|---|
| Cobertura menor de 60% | No emitir recomendación; mostrar “evidencia insuficiente” |
| Confianza baja en un dominio crítico | Mantener score, añadir alerta y requerir revisión |
| Conflicto entre fuentes | Mostrar discrepancia; no promediar sin regla documentada |
| Score >= 70, cobertura >= 80% y sin alerta crítica | `Investigate` |
| Score 50–69 o cobertura 60–79% | `Validate` |
| Score < 50 | `Deprioritize` |

La salida debe incluir `score_version`, contribución de cada dimensión, cobertura, confianza, evidencia principal y razones de exclusión.

## 9. Evaluación regulatoria y sostenibilidad

El sistema solo genera una **pre-evaluación**:

- Identifica jurisdicción, categoría de alimento, ingrediente, claim y documentos relevantes.
- Distingue fuentes primarias, guías y señales no vinculantes.
- Produce estados `not_assessed`, `needs_review`, `potential_constraint` o `no_constraint_found`; nunca `approved` o `low risk` como conclusión legal.
- Exige revisor humano y fecha de corte para cualquier uso externo.

Para sostenibilidad, toda estimación requiere unidad funcional, frontera del sistema, región, año, factor usado y calidad de datos. Un rating como “B+” queda fuera hasta que exista una metodología publicada y validada.

## 10. Entregables del MVP

1. Formulario de consulta y API de ejecución.
2. Cuatro conectores productivos: ciencia, patentes, tendencias/noticias y comercio.
3. Repositorio de evidencia y trazabilidad por `research_run`.
4. Motor de scoring v1 con reglas de cobertura.
5. Reporte ejecutivo y anexo descargable de evidencia.
6. Panel operativo de cuotas, errores y frescura.
7. Matriz de viabilidad y licencia aprobada para cada fuente activa.

## 11. Plan de entrega sugerido

| Sprint | Resultado verificable |
|---|---|
| 0 | Caso de uso, taxonomía, mercados, definición de éxito y matriz de fuentes aprobada |
| 1 | Esquema de datos, `research_run`, conectores científicos y almacenamiento de evidencia |
| 2 | Conector de patentes, deduplicación y trazabilidad de entidades |
| 3 | Conectores de tendencias y comercio; indicadores normalizados |
| 4 | Scoring v1, cobertura, alertas y reporte ejecutivo |
| 5 | Validación con 10 consultas reales, calibración y endurecimiento operativo |

## 12. Criterios de aceptación

- Una consulta completa conserva parámetros, respuestas, versiones, fecha de corte y fuentes.
- Todo número del reporte puede rastrearse a una transformación y fuente.
- El sistema falla de forma visible cuando una fuente queda sin acceso, excede cuota o devuelve datos insuficientes.
- El reporte distingue hechos, inferencias y recomendaciones.
- La recomendación baja de categoría o se bloquea cuando falta cobertura crítica.
- Ningún texto afirma cumplimiento regulatorio, libertad de operación o sostenibilidad verificada sin revisión humana y metodología aplicable.

## 13. Decisiones pendientes

1. Producto/ingrediente inicial y mercado destino.
2. Definición oficial de taxonomía, sinónimos y códigos HS.
3. Presupuesto máximo mensual y política de fuentes con licencia.
4. Rol responsable de revisar regulación y validar resultados.
5. Periodicidad: consultas bajo demanda, monitoreo o ambos.
