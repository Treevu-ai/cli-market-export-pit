# Migración del frontend a Next.js

## Por qué

El frontend vanilla JS/HTML (`web/`, sin build step) llegó a un techo de diseño: sin imágenes de fondo, sin animaciones de scroll, sin ilustración — un diagnóstico de equipo (marketing + UX/UI) lo calificó de "aburrido" pese a tener contenido real. En paralelo, el usuario proveyó una plantilla completa de Next.js/React/Tailwind (v0.dev, "Compute — the platform to build and ship AI agents") y pidió migrar todo el contenido de PIT a ese stack, usando videos reales de puerto como fondo.

## Decisión de arquitectura

**Next.js con `output: "export"` (export estático), no un servidor Next en producción.** El export genera HTML/CSS/JS planos en `web-next/out/`, que el `Dockerfile` copia al mismo lugar donde antes vivía `web/` dentro de la imagen. El servidor FastAPI sigue sirviéndolo como estáticos, sin cambios en `src/pit/api.py`. Esto evita:

- Levantar un segundo servicio Node en producción.
- Configurar CORS (mismo origen sirve API y frontend, igual que antes).
- Perder el pipeline de deploy en Fly.io que ya funcionaba (`fly.toml`, volumen SQLite, health check).

La condición para que esto funcione: ninguna página necesita features de servidor de Next (API routes, server actions, ISR) — todo lo dinámico ya pasa por `fetch` a la API PIT existente, igual que hacía el vanilla JS.

## Qué se portó

| Página | Antes | Ahora |
|---|---|---|
| Landing | `web/index.html` | `web-next/app/page.tsx` — 9 secciones (hero con video, método, 3 pasos, fuentes, caso real, categorías, trazabilidad, API, footer) |
| Consola | `web/analyze.html` + `analyze.js` | `web-next/app/analyze/` — formulario, nota de cobertura por mercado, gauge SVG, grilla de dominios, ficha, historial local (`localStorage`) |
| Reporte | `web/report.html` + `report.js` | `web-next/app/report/` — misma vista de reporte (`components/console/report-view.tsx`), compartida con la consola, accesible por `?run_id=` |
| Cliente API | `web/js/pit-api.js` | `web-next/lib/pit-api.ts` — mismo contrato, tipado |

## Qué se dejó fuera deliberadamente

- **Testimonials y Pricing** (secciones del template original): sin contenido real para llenarlas — inventar testimonios o precios públicos rompe el mismo principio de honestidad aplicado en todo el resto del sitio.
- **Certificaciones falsas** (SOC 2, ISO 27001, HIPAA, GDPR) que traía el template: reemplazadas por licencias reales de las fuentes de datos (OpenAlex CC0, Crossref REST, CLI Market, SHA-256 por fuente).
- **Logos de integraciones falsas** (OpenAI, Slack, GitHub, Jira, etc., hardcodeados en SVG): reemplazados por las 6 categorías de producto reales (arándano, cacao, quinua, palta, mango, funcionales), cada una linkeando directo a `/analyze/?query=...&market=...`.
- **Imágenes hotlinkeadas** a storage de Vercel del propio template (`hebbkx1anhila5yf.public.blob.vercel-storage.com/...`): todas removidas o reemplazadas por assets propios (los 3 videos de puerto, comprimidos con ffmpeg a ~700KB-1.1MB c/u) o contenido generado (canvas de partículas, SVG propio).

## Bugs reales encontrados y corregidos en el camino

1. `useRef<HTMLSection>` en `developers-section.tsx` — tipo DOM inexistente, capturado recién al correr `tsc --noEmit` real (el template traía `typescript: { ignoreBuildErrors: true }` en `next.config.mjs`, que se sacó una vez el build quedó limpio).
2. Color "green" en el canvas de `metrics-section.tsx` resolvía a `rgba(236, 168, 214, …)` (rosado, residuo del acento original del template) en vez de teal — encontrado por inspección visual de la captura, no por el linter.
3. Tres bugs reales de `Dockerfile` (documentados en el commit `fix: Docker image was missing web/assets and couldn't import pit`) — no relacionados a esta migración, pero corregidos en el mismo ciclo de deploy.

## Cómo desarrollar y desplegar

Ver la sección "Frontend" de `README.md`. En resumen: `cd web-next && npm run dev` para desarrollo, `npm run build` genera el export estático, el `Dockerfile` lo compila automáticamente en el build de imagen — no hace falta correr `npm run build` a mano antes de `flyctl deploy` ni de `docker build`.
