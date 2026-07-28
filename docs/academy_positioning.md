# PIT dentro de CLI Market Academy — pitch de posicionamiento

**Una línea:** Academy enseña a *leer el mercado* (SIRI) y a *comprar con datos* (DDM). Falta la pregunta anterior a ambas: *¿existe evidencia de que el producto merece estar en esa góndola?* Esa es PIT.

## El vacío concreto

El intake de Academy (`academy.cli-market.dev`) ya lista un rol sin track propio: *Research / Datos / Fintech*. Los otros cinco roles (Abastecimiento, Comercial, Pricing, Growth, Developer) caen naturalmente en Intelligence (SIRI: Sense → Interpret → Risk → Insight) o Procure (DDM: Detect → Compare → Decide → Execute → Improve). Research no tiene dónde aterrizar hoy — ese es el espacio.

## Qué resuelve PIT específicamente para ese rol

- Evidencia científica y de propiedad intelectual (OpenAlex, Crossref, PubMed, EPO OPS, CORDIS, NIH, NSF) — algo que ni SIRI (precio) ni DDM (compra) tocan.
- Datos regulatorios reales por SKU/categoría (OpenFDA, EFSA/EUR-Lex, FoodData Central), con trazabilidad SHA-256 por fuente — mismo estándar de rigor que Academy usa para su propio "moat" de precios.
- Claims exportables con atribución completa — exactamente lo que la propia Academy promete a su lente "Growth" ("extraigan claims citables con absoluta atribución") pero sin tener hoy una fuente que los genere.

## Sinergia técnica ya existente, no solo narrativa

El módulo 04 de *ambos* tracks de Academy (SIRI: "Search, compare, history" / DDM: "Comparación inteligente") resuelve normalización de unidades (kg/L/pack) para comparar precios de forma justa. PIT resuelve el mismo problema de normalización en su dominio `commerce`. Es un punto de integración concreto, no una analogía: o Academy expone su motor de normalización y PIT lo consume, o PIT aporta el suyo.

## Propuesta de entrada (bajo compromiso)

1. Posicionar PIT como *el módulo que sirve al rol Research/Datos/Fintech* dentro del intake actual — sin comprometerse todavía a un tercer track de 9 módulos.
2. Validar con el equipo de CLI Market si el flujo `commerce` de PIT (ya conectado a CLI Market) puede alimentarse de la señal SIRI real (freshness/confidence) en vez de re-derivarla.
3. Con tracción confirmada, evaluar un track completo con su propio acrónimo (siguiendo el patrón Sense-Interpret-Risk-Insight / Detect-Compare-Decide-Execute-Improve).

## El ask concreto para el equipo de Academy

¿El rol Research/Datos/Fintech tiene contenido asignado hoy, o está abierto? Si está abierto, PIT puede ser el primer track de ese rol sin pedirles que rediseñen nada de lo que ya construyeron.

## Estado de la validación técnica (paso 2)

Se probó el flujo real `enrich_with_commerce` → `CLIMarketConnector` (`src/pit/climarket.py`, `POST /products/compare` + `GET /v1/intel/brief` contra `https://cli-market-api.fly.dev`) con dos runs reales:

**Hallazgo 1 — el pipe funciona de punta a punta.** Autenticación con `CLIMARKET_API_KEY`, request completado, checksum SHA-256 almacenado, respuesta normalizada y agregada en `climarket_aggregation`. No es un problema de integración.

**Hallazgo 2 — la cobertura por país es muy desigual, y confirma que CLI Market es LATAM-first, no US-first:**

Cobertura real medida con la misma query ("arándano orgánico") contra los 7 mercados del formulario de `analyze.html`:

| Mercado | `shelf_products_count` | `stores_compared` | Precio min–max | Tiendas |
|---|---|---|---|---|
| `US` | 0 | 0 | — | ninguna (catálogo resuelve a DTC/wellness: allbirds, glossier, casper) |
| `PE` | 48 | 5 | S/3.90 – S/189.90 | organa_pe, nunaorganica_pe, solydarperu_pe, vega_pe, plazavea |
| `MX` | 52 | 2 | $21.50 – $303.00 | heb_mx, chedraui |
| `AR` | 32 | 2 | $1.68 – $24,800 | jumbo_ar, vea_ar |
| `CO` | 5 | 1 | $4,928 – $71,400 | carulla |
| `BR` | 5 | 1 | R$54.76 – R$1,237.90 | carrefour_br |
| `CL` | 0 | 0 | — | ninguna |

**Lectura del patrón:** cobertura fuerte en PE/MX/AR (multi-tienda, catálogo real de orgánicos/frescos), débil-pero-real en CO/BR (una sola tienda pero con datos de precio genuinos), y **cero en US y CL** — no por falla técnica, sino porque el catálogo indexado para esas dos combinaciones país/línea no incluye la categoría consultada.

**Hallazgo técnico adicional:** el campo `moat_freshness_pct` y `stores_active` del `intel_brief` (SIRI) solo aparecieron poblados en el run de PE — en el resto vinieron `None`. Revisando `CLIMarketConnector.search()` (`src/pit/climarket.py`), la llamada a `intel_brief()` está envuelta en un `try/except CLIMarketRequestError: pass` que traga el error silenciosamente y no lo registra como fuente fallida — a diferencia de `compare_products()`, cuyo fallo sí queda trazado. Vale la pena señalar esto en la conversación técnica con CLI Market: hoy PIT no puede distinguir "intel brief no disponible para este país" de "intel brief nunca se intentó".

**Implicancia directa para el positioning:** el módulo `commerce` de PIT ya sirve al rol Research/Datos/Fintech con datos reales en PE/MX/AR/CO/BR — 5 de 7 mercados soportados. El `<select>` de mercado en `analyze.html` no reflejaba ese espectro (solo tenía US/PE/MX/CL/CO/EU); se agregó AR y BR, alineando el formulario con los países que el propio Academy lista en su intake y con la huella real de retailers de CLI Market. El backend ya aceptaba cualquier código ISO-2 (`^[A-Z]{2}$`, sin enum) — el gap era solo de UI.

## Lectura de equipo — CITE Chavimochic sobre la narrativa de Academy

Análisis desde las tres perspectivas de servicio de un CITE (I+D+i+e, comercial y mercadotecnia) sobre la narrativa pública de `academy.cli-market.dev`, antes de recomendar su adopción para la red de productores/exportadores de Chavimochic.

### I+D+i+E — Investigación, Desarrollo, Innovación y Emprendimiento

Academy es metodológicamente sólida pero está calibrada un paso *después* de donde trabaja un CITE. SIRI (Sense→Interpret→Risk→Insight) es un framework legítimo para leer precio de góndola, pero no responde la pregunta que nosotros validamos primero: *¿este producto merece existir en esa góndola?* No hay una sola mención a I+D, patentes, evidencia científica ni transferencia tecnológica en toda la narrativa — es 100% señal de mercado, cero señal de producto.

Eso no es una crítica, es un diagnóstico de rol: Academy resuelve el "Pilar 2" (mercado) y "Pilar 3" (compra), pero el "Pilar 1" (¿existe respaldo científico/IP real?) — que es exactamente nuestro mandato como CITE — está ausente. Si llevamos productores de Chavimochic a Academy sin ese pilar previo, les enseñamos a *reaccionar* al precio existente, no a *construir* una oferta defendible. Eso refuerza comportamiento de price-taker, que es lo opuesto a lo que un CITE debe fomentar.

**Riesgo concreto:** adoptar Academy como si fuera formación completa, sin la capa de evidencia (PIT), gradúa productores que saben leer el mercado pero no saben si su producto tiene ángulo científico defendible frente a la competencia.

### Comercial

Academy está construida para el lado comprador, no el vendedor. Su track "Procure" (DDM: Detect→Compare→Decide→Execute→Improve) enseña a comprar institucionalmente con canastas multi-retailer — es la perspectiva de un corporativo que abastece, no de un exportador de Chavimochic que busca entrar a esa góndola. Dirección opuesta a la nuestra.

Dicho eso, hay valor comercial indirecto real: los datos de shelf price de SIRI (lo que de hecho ya validamos técnicamente — PE tiene cobertura fuerte, 48 productos, 5 tiendas comparadas) le dicen a un productor qué margen y qué poder de negociación existe río abajo en destino, algo que hoy negocian a ciegas con intermediarios.

**Oportunidad de timing:** el formulario de acceso dice "sin tarjeta, sin cargo automático" — es un funnel pre-lanzamiento. Es el momento de negociar un acuerdo institucional por cohorte (CITE patrocina un grupo de exportadores) en vez de que cada productor entre individualmente cuando el producto ya esté maduro y con pricing definido.

### Mercadotecnia

El tono de Academy — "moat", "shelf inflation", "affordability band", tipografía serif editorial, todo en modo desk-analyst — habla al perfil Pricing/Revenue de una corporación grande, no al productor o exportador regional de Chavimochic. Ese registro, tal cual, no conecta con nuestra base sin mediación — hay que traducirlo, no adoptarlo literal.

Lo que sí es aprovechable: su propio ejemplo de brief ("dónde está más barato hoy, mismo producto y tamaño") es genérico, sin storytelling de exportación real. Ahí es donde el caso del arándano (13 hallazgos científicos, 17 referencias comerciales, S/3.90 precio mínimo) es material de marketing más fuerte que cualquier cosa que Academy tiene hoy — un caso real, peruano, con nombre y apellido, contra un ejemplo abstracto de 5 tiendas.

La certificación "bajo rúbrica de rigor metodológico" que ofrecen solo tiene sentido de marca completa si va emparejada con una certificación de evidencia — un productor certificado en "leer el mercado" sin certificación en "validar el producto" es una credencial a medias.

### Convergencia de las tres lecturas

Academy no es territorio a evitar ni a copiar — es territorio complementario donde Chavimochic entra por el hueco que ya identificamos (rol Research/Datos/Fintech, sin track asignado), pero el equipo coincide en algo que la propuesta técnica todavía no decía explícito: **si vamos a llevar productores de Chavimochic a Academy, la secuencia correcta es Evidencia (PIT) → luego SIRI/DDM, nunca al revés** — porque enseñar a leer y comprar en un mercado antes de validar si el producto tiene ángulo competitivo es formación incompleta, casi contraproducente para nuestro mandato.
