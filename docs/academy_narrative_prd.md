# PRD — Claridad de narrativa PIT × CLI Market Academy

> **Contexto:** deriva de `docs/academy_positioning.md` (pitch de posicionamiento, validación técnica del flujo `commerce`, y lectura de equipo CITE Chavimochic). Este PRD convierte esas recomendaciones en cambios implementables **dentro de este repo** — no propone editar `academy.cli-market.dev`, que no controlamos.

---

## Resumen ejecutivo

Las tres lecturas (I+D+i+e, comercial, mercadotecnia) coinciden en un punto que hoy PIT no comunica con claridad, ni interna ni externamente: **PIT es el paso de evidencia que precede a leer el mercado (SIRI) y comprar con datos (DDM), no un sustituto ni un competidor de ninguno de los dos.** Sin esa secuencia explícita, cualquier conversación con Academy o con productores de Chavimochic corre el riesgo de sonar como "otra herramienta más" en vez de la pieza que falta.

Este PRD ordena los cambios necesarios para que esa narrativa quede clara en tres superficies que sí controlamos: el código (`src/pit/climarket.py`), el producto (`web/`), y los materiales de conversación externa (assets de pitch).

---

## Problema

1. **El flujo `commerce` tiene un fallo de transparencia que contradice el principio de honestidad que admiramos en Academy** ("sin fingir ser el IPC"). `CLIMarketConnector.search()` traga en silencio los errores de `intel_brief()` (`except CLIMarketRequestError: pass`), así que PIT no puede distinguir "sin señal SIRI para este país" de "nunca se intentó la llamada". Eso es exactamente el tipo de opacidad que la propia metodología SIRI de Academy penaliza con su gate rojo/amarillo/verde.

2. **La consola no comunica honestamente la cobertura real por mercado.** Ya medimos que `US` y `CL` devuelven cero productos de CLI Market para categorías agro (no es un bug, es catálogo), pero el `<select>` de mercado no lo indica — un usuario puede elegir `US` esperando el mismo nivel de señal que en `PE` y llevarse una sorpresa silenciosa.

3. **No existe un asset externo que exprese la secuencia Evidencia → SIRI → DDM** de forma autocontenida y compartible — hoy esa narrativa vive dispersa en `docs/academy_positioning.md` (interno) y en un artifact de mockup (efímero). Si mañana hay que enviarle algo al equipo de Academy o a Chavimochic, no hay un documento único, versionado en el repo, que lo explique.

4. **La landing (`web/index.html`) no menciona en ningún lugar el rol de PIT relativo a un ecosistema de mercado/compra** — habla de "ciencia y mercado" en abstracto. Esto es intencional hasta no tener acuerdo con Academy (no vamos a usar "SIRI"/"DDM" en nuestra copy pública sin su visto bueno), pero sí podemos reforzar el framing de secuencia ("evidencia antes que todo") que ya es propio.

---

## Objetivos

- Que el flujo `commerce` sea trazable end-to-end, sin fallos silenciosos — condición para poder decirle a Academy "nuestros datos son tan auditables como los suyos".
- Que la consola comunique honestamente dónde hay señal real de CLI Market y dónde no, en vez de dejarlo implícito.
- Tener un documento único, versionado, listo para compartir, que explique la secuencia Evidencia → SIRI → DDM sin depender de un artifact efímero.
- Reforzar (sin sobre-prometer) el framing de "evidencia primero" en la landing pública, sin adoptar terminología de Academy que no nos pertenece todavía.

## No objetivos (fuera de alcance)

- No se edita ni se propone un PR contra `academy.cli-market.dev` — no tenemos acceso ni mandato.
- No se agrega branding "SIRI"/"DDM"/"Academy" a la landing pública de PIT sin acuerdo explícito con CLI Market — sería apropiarse de marca ajena antes de tiempo.
- No se construye el track completo de 9 módulos propuesto como opción 3 en el pitch — sigue condicionado a tracción confirmada.
- No se completa la cobertura de países más allá de los 7 ya medidos (US/PE/MX/CL/CO/AR/BR) en este ciclo.

---

## Cambios propuestos

### 1. Fix de trazabilidad — `src/pit/climarket.py` (código, TDD)

**Qué:** que un fallo de `intel_brief()` dentro de `CLIMarketConnector.search()` quede registrado como fuente fallida (igual que ya ocurre con `compare_products()`), en vez de tragarse en un `except: pass`.

**Por qué ahora:** es el hallazgo técnico #2 de `docs/academy_positioning.md`; corregirlo antes de la conversación con Academy evita que nos pregunten por qué nuestra propia trazabilidad tiene el mismo punto ciego que le criticamos implícitamente a "un número suelto en un slide" (una de las 5 brechas de señal que ellos mismos identifican).

**Cómo (alto nivel, sujeto a TDD):**
- `enrich_with_commerce` ya crea una `source_request` para `compare_products`. Envolver la llamada a `intel_brief()` en su propio `start_source_request`/`finish_source_request` (o registrar explícitamente el fallo con `status="failed"` y el motivo), en vez de `except CLIMarketRequestError: pass`.
- Test: mockear `intel_brief()` para que falle y verificar que el `run` resultante tiene una fuente `cli_market_intel` con `status == "failed"`, no que simplemente falte.

### 2. Honestidad de cobertura en la consola — `web/analyze.html` / `web/js/analyze.js`

**Qué:** anotar en el `<select>` de mercado (o como texto de ayuda debajo) qué mercados tienen cobertura de CLI Market confirmada y cuáles no, basado en la tabla ya medida:

| Cobertura | Mercados |
|---|---|
| Fuerte | PE, MX, AR |
| Parcial | CO, BR |
| Sin datos de góndola hoy | US, CL |

**Por qué:** es la aplicación directa del principio "sin fingir ser el IPC" a nuestro propio producto — si vamos a pedirle a Academy que nos tome en serio como par metodológico, nuestra propia UI no puede prometer implícitamente algo que el dato no sostiene.

**Cómo:** opción más simple — texto pequeño bajo el `<select>` (`"Cobertura de precio de góndola: fuerte en PE/MX/AR, limitada en CO/BR, sin datos aún en US/CL"`), sin bloquear la opción, solo informar antes de correr el pipeline.

### 3. One-pager versionado — `docs/academy_evidence_brief.md`

**Qué:** extraer de `academy_positioning.md` (que es un documento interno de trabajo, largo y en progreso) un documento corto, autocontenido y presentable, con la secuencia Evidencia → SIRI → DDM, el caso arándano, y la tabla de cobertura — pensado para copiar/pegar o exportar en una conversación real con Academy o Chavimochic.

**Por qué:** hoy esa narrativa solo existe completa en un artifact efímero (el mockup visual) y dispersa en un doc de trabajo largo. Un asset corto y versionado es lo que realmente se comparte en una reunión.

**Contenido:** 1 página, misma estructura que `PRD_CLI_Market_Export_Intelligence.md` ya usa para el caso arándano (números, no prosa larga).

### 4. Refuerzo de secuencia en la landing — `web/index.html`

**Qué:** un cambio de copy mínimo, no estructural. La landing ya dice "No desarrolles primero el producto. Desarrolla primero la evidencia." — se propone agregar una frase corta inmediatamente después que explicite la secuencia sin nombrar marcas ajenas: algo como *"La evidencia es el paso antes de leer el mercado o de comprar con datos."* (sin decir SIRI/DDM).

**Por qué así de acotado:** comunica la secuencia real sin apropiarse de terminología de Academy antes de tener acuerdo — si el acuerdo se concreta, ahí sí se evalúa nombrar SIRI/DDM explícitamente.

---

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Nombrar "SIRI"/"DDM" en copy pública antes de acuerdo formal | Cambio 4 evita nombrarlos; solo describe la secuencia |
| El fix de trazabilidad (cambio 1) cambia el conteo de `sources` que ya consumen `analyze.js`/`report.js` | Cubrir con test que valide forma del payload antes de tocar `research.py` |
| La nota de cobertura (cambio 2) puede leerse como "PIT no funciona en US/CL" | Redactar como información de cobertura de *CLI Market*, no de PIT — PIT sigue corriendo ciencia/patentes/regulatorio igual en cualquier mercado |

## Métricas de éxito

- 0 fuentes `cli_market_intel` con fallo silencioso (100% de los fallos quedan trazados).
- La consola muestra la nota de cobertura en el 100% de los mercados con dato medido.
- `docs/academy_evidence_brief.md` existe y es citable/copiable en una conversación real sin editar.

## Plan de fases

1. **Fase 1 (código, TDD):** fix de trazabilidad en `climarket.py` — cambio 1.
2. **Fase 2 (frontend):** nota de cobertura en `analyze.html`/`analyze.js` — cambio 2.
3. **Fase 3 (contenido):** `docs/academy_evidence_brief.md` — cambio 3.
4. **Fase 4 (frontend, copy mínimo):** refuerzo de secuencia en `index.html` — cambio 4.

Cada fase es independiente y puede aprobarse/ejecutarse por separado.
