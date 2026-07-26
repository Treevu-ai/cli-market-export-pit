# Wireframe de Alta Fidelidad — CLI Market Export Intelligence

**Versión:** 1.0  
**Estado:** Especificación lista para diseño UI y desarrollo frontend  
**Producto:** CLI Market Export Intelligence  
**URL objetivo:** `https://cli-market.dev/intel-latam`  
**Base:** PRD Maestro, punto 52  
**Fecha:** 25 de julio de 2026  

---

# 1. Objetivo del entregable

Este documento traduce el PRD de CLI Market Export Intelligence a una especificación visual y funcional de alta fidelidad.

Define:

- layout desktop;
- layout móvil;
- jerarquía visual;
- copy final;
- componentes;
- estados;
- comportamiento;
- responsive design;
- especificación de implementación en Next.js;
- eventos de analítica;
- criterios de aceptación por bloque.

El objetivo es que un diseñador o desarrollador pueda construir la landing sin reinterpretar la estrategia del producto.

---

# 2. Principios de diseño

## 2.1 Claridad antes que densidad

Cada sección debe responder una sola pregunta.

- Hero: ¿qué resuelve?
- Problema: ¿por qué importa?
- Método: ¿cómo funciona?
- Caso: ¿puede demostrarlo?
- Entregable: ¿qué recibe el cliente?
- Formulario: ¿cómo empieza?

## 2.2 Evidencia visible

La landing debe parecer una herramienta de inteligencia, no una web institucional.

Elementos visuales prioritarios:

- cifras;
- referencias;
- etiquetas de fuente;
- tarjetas de productos;
- chips de estado;
- módulos de evidencia;
- fragmentos de formulación.

## 2.3 Menos ornamento, más señal

Evitar:

- ilustraciones genéricas;
- iconografía excesiva;
- fotografías sin función;
- bloques largos de prosa;
- gradientes decorativos sin utilidad.

## 2.4 Jerarquía ejecutiva

El usuario debe poder escanear la página en menos de tres minutos y comprender:

1. qué ofrece;
2. qué evidencia utiliza;
3. qué caso demuestra;
4. qué entregable recibe;
5. cómo solicitarlo.

---

# 3. Sistema visual

## 3.1 Paleta

| Token | Uso | Valor sugerido |
|---|---|---|
| `bg-page` | Fondo general | `#F7F8F6` |
| `bg-card` | Tarjetas | `#FFFFFF` |
| `bg-dark` | Secciones de cierre | `#0B0D0C` |
| `text-primary` | Texto principal | `#111311` |
| `text-secondary` | Texto secundario | `#5C645E` |
| `border-default` | Bordes | `#DDE3DE` |
| `green-primary` | CTA y énfasis | `#41F56C` |
| `green-dark` | Texto/íconos verdes | `#0A6B2F` |
| `green-soft` | Fondos de apoyo | `#E9FDED` |
| `yellow-signal` | Alertas secundarias | `#E9FF55` |
| `error` | Validaciones | `#C83232` |

## 3.2 Tipografía

### Principal

**Inter**

Usos:

- cuerpo;
- botones;
- navegación;
- formularios.

### Display

**Space Grotesk**

Usos:

- H1;
- H2;
- cifras principales;
- titulares de alto impacto.

### Datos

**IBM Plex Mono**

Usos:

- precios;
- métricas;
- etiquetas;
- fuente;
- indicadores;
- códigos.

## 3.3 Escala tipográfica

| Estilo | Desktop | Móvil |
|---|---:|---:|
| Display | 72/76 | 46/50 |
| H1 | 64/68 | 42/46 |
| H2 | 44/50 | 34/40 |
| H3 | 28/34 | 24/30 |
| Lead | 21/32 | 18/28 |
| Body | 17/28 | 16/26 |
| Small | 14/22 | 14/21 |
| Label | 12/18 | 12/18 |

## 3.4 Grid

### Desktop

- ancho máximo: `1280px`;
- columnas: `12`;
- gutter: `24px`;
- margen lateral mínimo: `32px`;
- secciones: `96px–128px` vertical.

### Tablet

- columnas: `8`;
- gutter: `20px`;
- margen lateral: `24px`.

### Móvil

- columnas: `4`;
- gutter: `16px`;
- margen lateral: `20px`;
- secciones: `64px–80px` vertical.

## 3.5 Radios y sombras

- radio pequeño: `10px`;
- radio mediano: `18px`;
- radio grande: `28px`;
- sombra estándar: `0 16px 40px rgba(0,0,0,.07)`;
- sombra flotante: `0 20px 60px rgba(0,0,0,.12)`.

---

# 4. Mapa general de la landing

```text
01. Navbar
02. Hero
03. Proof Strip
04. Problema
05. Método de 3 capas
06. Caso Arándano
07. Ficha de Oportunidad
08. Casos de uso
09. Categorías
10. Comparativa
11. Formulario
12. FAQ
13. CTA final
14. Footer
15. WhatsApp flotante
```

---

# 5. Navbar

## 5.1 Objetivo

Permitir navegación rápida y mantener visible el CTA principal.

## 5.2 Desktop

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ CLI MARKET   Método   Caso real   Qué recibe   Categorías   [Solicitar] │
└──────────────────────────────────────────────────────────────────────────┘
```

## 5.3 Móvil

```text
┌────────────────────────────┐
│ CLI MARKET          [☰]    │
└────────────────────────────┘
```

Menú abierto:

```text
┌────────────────────────────┐
│ Cómo funciona              │
│ Caso real                  │
│ Qué recibe                 │
│ Categorías                 │
│ [Solicitar análisis]       │
└────────────────────────────┘
```

## 5.4 Comportamiento

- navbar sticky;
- transparente al inicio;
- fondo blanco con blur después de 40 px;
- borde inferior al hacer scroll;
- CTA verde;
- sección activa marcada con subrayado o cambio de peso.

## 5.5 Estados

- default;
- hover;
- active;
- focus-visible;
- mobile-open;
- scrolled.

## 5.6 Componente

```tsx
<Navbar
  items={navItems}
  primaryCta={{
    label: "Solicitar análisis",
    href: "#solicitar"
  }}
/>
```

---

# 6. Hero

## 6.1 Objetivo

Comunicar propuesta, credibilidad y acción inmediata.

## 6.2 Desktop

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ [CLI MARKET EXPORT INTELLIGENCE]                                             │
│                                                                              │
│ Antes de exportar,                     ┌───────────────────────────────────┐  │
│ valida la ciencia                      │ PAPER / MARKET / FORMULATION     │  │
│ y el mercado.                          │                                   │  │
│                                        │ 13 findings     17 products       │  │
│ Descubre si tu producto tiene          │                                   │  │
│ respaldo científico, espacio           │ Product card                      │  │
│ competitivo y una oportunidad real.    │ Ingredient card                   │  │
│                                        │ Market map                        │  │
│ [Analizar una oportunidad]             └───────────────────────────────────┘  │
│ [Ver caso: arándano]                                                        │
│                                                                              │
│ ✓ Ciencia trazable  ✓ Mercado verificable  ✓ Decisiones defendibles         │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 6.3 Móvil

```text
[CLI MARKET EXPORT INTELLIGENCE]

Antes de exportar,
valida la ciencia
y el mercado.

Descubre si tu producto tiene
respaldo científico, espacio
competitivo y una oportunidad real.

[Analizar una oportunidad]
[Ver caso: arándano]

[VISUAL COMPUESTO]

✓ Ciencia trazable
✓ Mercado verificable
✓ Decisiones defendibles
```

## 6.4 Copy final

### Eyebrow

`CLI MARKET EXPORT INTELLIGENCE`

### H1

**Antes de exportar, valida la ciencia y el mercado.**

### Lead

Descubre si tu producto tiene respaldo científico, espacio competitivo y una oportunidad real en el mercado objetivo.

### Microcopy

**No desarrolles primero el producto. Desarrolla primero la evidencia.**

### CTA

- Primario: `Analizar una oportunidad`
- Secundario: `Ver caso real: arándano`

## 6.5 Visual hero

Composición recomendada:

- tarjeta de evidencia científica;
- tarjeta de producto retail;
- tarjeta de formulación;
- mini mapa de mercado destino;
- indicadores `13 hallazgos`, `17 referencias`, `S/ 3.90+`.

No usar fotografía como único visual. Debe parecer una interfaz de inteligencia.

## 6.6 Animación

- entrada suave de tarjetas;
- desplazamiento vertical de 8–12 px;
- duración de 400–600 ms;
- respetar `prefers-reduced-motion`.

## 6.7 Eventos

- `hero_primary_cta_click`
- `hero_case_click`

---

# 7. Proof Strip

## 7.1 Objetivo

Reforzar credibilidad inmediatamente después del hero.

## 7.2 Layout

```text
[OpenAlex] [Crossref] [Retailers] [Product data] [Public sources]
```

## 7.3 Copy

**Fuentes científicas, datos de góndola y fichas públicas de producto integradas en una misma lectura.**

## 7.4 Móvil

Scroll horizontal de chips, sin autoplay.

---

# 8. Sección problema

## 8.1 Título

**Exportar no debería comenzar con una suposición.**

## 8.2 Desktop

```text
[Título + texto introductorio]

┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ RIESGO         │ │ RIESGO         │ │ RIESGO         │ │ RIESGO         │
│ CIENTÍFICO     │ │ COMERCIAL      │ │ COMPETITIVO    │ │ REGULATORIO    │
│ Copy breve     │ │ Copy breve     │ │ Copy breve     │ │ Copy breve     │
└────────────────┘ └────────────────┘ └────────────────┘ └────────────────┘
```

## 8.3 Móvil

Tarjetas apiladas o carrusel horizontal manual.

## 8.4 Copy de tarjetas

### Riesgo científico

El beneficio puede no contar con evidencia suficiente o trazable.

### Riesgo comercial

La categoría puede estar saturada o dominarse por formatos diferentes.

### Riesgo competitivo

La propuesta puede no diferenciarse frente a marcas existentes.

### Riesgo regulatorio

El ingrediente, claim o presentación puede requerir validación adicional.

## 8.5 Estado hover

- borde verde;
- icono se desplaza 2 px;
- fondo `green-soft`.

---

# 9. Método de tres capas

## 9.1 Título

**Una oportunidad exportadora debe sostenerse en tres capas de evidencia.**

## 9.2 Desktop

```text
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│ 01 CIENCIA          │ --> │ 02 MERCADO          │ --> │ 03 FORMULACIÓN      │
│ Preguntas           │     │ Preguntas           │     │ Preguntas           │
│ Fuentes             │     │ Variables           │     │ Ingredientes        │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
```

## 9.3 Móvil

```text
01 Ciencia
   ↓
02 Mercado
   ↓
03 Formulación
```

## 9.4 Componente

```tsx
<ProcessStep
  number="01"
  title="Ciencia"
  description="Identificamos respaldo, tendencias y vacíos."
  bullets={[
    "Publicaciones",
    "Autores",
    "Citas",
    "Patentes"
  ]}
/>
```

## 9.5 Interacción

En desktop:

- hover revela preguntas clave;
- clic fija la capa activa.

En móvil:

- acordeón;
- primera capa abierta por defecto.

## 9.6 Estado activo

- borde verde;
- número en fondo verde;
- flecha de conexión resaltada.

---

# 10. Caso real: Arándano

## 10.1 Objetivo

Transformar la promesa en evidencia concreta.

## 10.2 Fondo

Sección oscura para crear quiebre visual.

## 10.3 Desktop

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ CASO REAL                                                                  │
│ Arándano: de la hipótesis a la evidencia.                                  │
│                                                                             │
│ [13]              [17]              [S/ 3.90+]          [FORMULACIONES]     │
│ hallazgos         referencias       entrada             visibles           │
│                                                                             │
│ [CIENCIA] [MERCADO] [FORMULACIÓN]                                          │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ Contenido activo                                                        │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ [Solicitar un análisis similar]                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 10.4 Móvil

Métricas 2 × 2:

```text
[13] [17]
[S/3.90+] [FORM.]
```

Tabs con scroll horizontal.

## 10.5 Tab Ciencia

Contenido:

- 13 hallazgos;
- arándano;
- antocianinas;
- publicaciones;
- fuentes;
- líneas de investigación.

Visual:

- lista de papers simulada;
- gráfico simple de temas;
- badges de fuente.

## 10.6 Tab Mercado

Tarjetas:

| Producto | Marca | Precio |
|---|---|---:|
| Yogurt Pro+ Arándano 160 g | Vakimu | S/ 3.90 |
| Barra Chocolate 72% 50 g | Calypso | S/ 12.90 |
| Arándanos con Chocolate 40 g | Mazomayo | S/ 9.50 |
| Mermelada con Yacón 280 g | Mahuis | S/ 19.90 |
| Vegan Protein 500 g | Biocenter | S/ 89.90 |

## 10.7 Tab Formulación

Producto destacado:

**Barra Chocolate 72% Arándano 50 g — Calypso**

Ingredientes:

- pasta de cacao;
- manteca de cacao;
- panela;
- arándanos deshidratados.

## 10.8 Estado de fuente

Cada dato debe mostrar:

- fuente;
- fecha;
- mercado;
- disponibilidad.

Ejemplo:

```text
FUENTE PÚBLICA · CONSULTADO JUL 2026
```

## 10.9 Criterios de aceptación

- tabs operativas;
- métricas visibles;
- datos legibles;
- CTA presente;
- limitaciones explícitas;
- no presentar inferencias como hechos.

---

# 11. Ficha de Oportunidad Exportadora

## 11.1 Objetivo

Explicar el entregable final.

## 11.2 Layout desktop

```text
[Mockup de ficha]          [Contenido]
                           Resumen ejecutivo
                           Evidencia científica
                           Radar de góndola
                           Formulación
                           Diferenciación
                           Próximas validaciones
```

## 11.3 Copy

### Título

**De la información a una ficha de oportunidad exportadora.**

### Texto

No recibe únicamente datos. Recibe una estructura de decisión que muestra qué se sabe, qué falta y qué debe validarse después.

## 11.4 Mockup

Visual tipo documento ejecutivo con:

- portada;
- score de evidencia;
- tabla de productos;
- gráfico de precios;
- resumen de formulación;
- recomendaciones.

## 11.5 CTA

**Solicitar una ficha de oportunidad**

---

# 12. Casos de uso

## 12.1 Layout

Grid de seis tarjetas en desktop, dos columnas en tablet, una en móvil.

## 12.2 Tarjetas

- Exportadores
- Agroindustrias
- Equipos de innovación
- Consultores
- Organizaciones empresariales
- Compradores e importadores

## 12.3 Estructura

```text
[ICONO]
TÍTULO
Descripción de dos líneas
Resultado esperado
```

## 12.4 Estado hover

- elevar 4 px;
- borde verde;
- mostrar enlace `Ver aplicación →`.

---

# 13. Categorías analizables

## 13.1 Título

**Empieza con una materia prima, un ingrediente o una categoría.**

## 13.2 Estados

### Disponible

Chip verde:

`CASO DISPONIBLE`

### Próximamente

Chip gris:

`PRÓXIMAMENTE`

### Bajo solicitud

Chip amarillo:

`BAJO SOLICITUD`

## 13.3 Tarjetas

- Arándano
- Cacao
- Uva
- Quinua
- Café
- Palta
- Frutas deshidratadas
- Ingredientes funcionales
- Snacks saludables

## 13.4 Interacción

Al hacer clic:

- categoría disponible → caso;
- próximamente → formulario con categoría precargada;
- bajo solicitud → formulario con categoría precargada.

## 13.5 Evento

`category_click`

Propiedades:

- `category_name`;
- `category_status`.

---

# 14. Comparativa

## 14.1 Desktop

Tabla de dos columnas.

## 14.2 Móvil

Tarjetas comparativas apiladas:

```text
INFORME TRADICIONAL
- estático
- datos aislados
- tendencias

CLI MARKET
- actualizable
- ciencia + mercado
- productos reales
```

## 14.3 Frase final

**No te decimos solamente que existe una tendencia. Te mostramos cómo se materializa en productos reales.**

---

# 15. Formulario

## 15.1 Objetivo

Captar información suficiente sin crear fricción excesiva.

## 15.2 Diseño recomendado

Formulario de dos pasos.

### Paso 1

- Nombre
- Empresa
- Correo
- WhatsApp

### Paso 2

- País de origen
- Producto
- Mercado destino
- Etapa
- Necesidad
- Comentario

## 15.3 Desktop

Formulario a la izquierda; panel de confianza a la derecha.

```text
┌─────────────────────────────┐  ┌─────────────────────────────┐
│ FORMULARIO                  │  │ QUÉ OCURRE DESPUÉS          │
│ Paso 1 de 2                 │  │ 1. Revisamos                │
│ Campos                      │  │ 2. Calificamos              │
│ [Continuar]                 │  │ 3. Contactamos              │
└─────────────────────────────┘  └─────────────────────────────┘
```

## 15.4 Móvil

Formulario ancho completo.

Barra de progreso:

```text
●────○
1    2
```

## 15.5 Estados de campo

- default;
- hover;
- focus;
- filled;
- error;
- disabled;
- success.

## 15.6 Mensajes de error

- `Ingresa tu nombre.`
- `Usa un correo válido.`
- `Selecciona un mercado destino.`
- `Acepta la política de privacidad.`

## 15.7 Estado de envío

Botón:

`Enviando solicitud…`

Spinner discreto.

## 15.8 Estado de éxito

```text
Solicitud registrada

Revisaremos tu producto y mercado para determinar el siguiente paso.

[Contactar por WhatsApp]
```

## 15.9 Estado de error del servidor

```text
No pudimos registrar la solicitud.

Tus datos se mantienen. Intenta nuevamente o continúa por WhatsApp.
```

## 15.10 CTA

**Solicitar análisis inicial**

---

# 16. FAQ

## 16.1 Layout

Acordeón en columna.

## 16.2 Preguntas

- ¿CLI Market realiza estudios de mercado?
- ¿Pueden analizar cualquier producto?
- ¿Los ingredientes siempre están disponibles?
- ¿Pueden analizar mercados internacionales?
- ¿Qué recibe la empresa?
- ¿Garantizan éxito comercial?

## 16.3 Estados

- collapsed;
- expanded;
- focus;
- hover.

## 16.4 Evento

`faq_open`

---

# 17. CTA final

## 17.1 Fondo

Negro.

## 17.2 Copy

### H2

**La exportación no comienza en el puerto.**

### Texto

Comienza cuando puedes demostrar por qué tu producto merece entrar al mercado.

### CTA

**Analizar una oportunidad**

## 17.3 Visual

Línea de proceso:

```text
Materia prima → Evidencia → Producto → Mercado
```

---

# 18. Footer

Contenido:

- logo;
- descriptor;
- contacto;
- privacidad;
- términos;
- LinkedIn;
- URL principal;
- copyright.

Estructura móvil apilada.

---

# 19. WhatsApp flotante

## 19.1 Aparición

- después de 20% de scroll;
- no visible sobre el hero;
- oculto mientras el menú móvil está abierto;
- oculto si el formulario está activo en móvil.

## 19.2 Tooltip desktop

`Consultar por WhatsApp`

## 19.3 Mensaje

```text
Hola, quiero evaluar una oportunidad de exportación con CLI Market.

Producto:
Mercado destino:
Etapa:
```

---

# 20. Responsive behavior

## Breakpoints

```ts
sm: 640
md: 768
lg: 1024
xl: 1280
2xl: 1536
```

## Reglas

### Hero

- desktop: 6/6 columnas;
- tablet: 5/3;
- móvil: apilado.

### Método

- desktop: horizontal;
- móvil: vertical.

### Caso

- desktop: tabs y contenido amplio;
- móvil: métricas 2 × 2 y tabs scrollables.

### Formulario

- desktop: dos columnas;
- móvil: una columna.

### Tabla comparativa

- desktop: tabla;
- móvil: tarjetas.

---

# 21. Microinteracciones

Permitidas:

- hover de tarjetas;
- transición de tabs;
- entrada de métricas;
- barra de progreso;
- acordeón;
- estados de formulario.

No permitidas:

- parallax intenso;
- animaciones continuas;
- contadores artificiales;
- carruseles automáticos;
- movimiento que afecte lectura.

---

# 22. Accesibilidad

- contraste AA;
- foco visible;
- navegación por teclado;
- `aria-expanded` en FAQ;
- tabs con roles correctos;
- labels persistentes;
- errores asociados por `aria-describedby`;
- botones con nombres claros;
- alt text descriptivo;
- reduced motion.

---

# 23. Arquitectura de componentes Next.js

```text
app/
└── intel-latam/
    ├── page.tsx
    ├── layout.tsx
    ├── loading.tsx
    ├── error.tsx
    └── metadata.ts

components/
└── export-intelligence/
    ├── Navbar.tsx
    ├── Hero.tsx
    ├── ProofStrip.tsx
    ├── ProblemSection.tsx
    ├── MethodSection.tsx
    ├── CaseStudySection.tsx
    ├── EvidenceTabs.tsx
    ├── DeliverableSection.tsx
    ├── UseCasesSection.tsx
    ├── CategoriesSection.tsx
    ├── ComparisonSection.tsx
    ├── LeadForm.tsx
    ├── FAQSection.tsx
    ├── FinalCTA.tsx
    ├── Footer.tsx
    └── WhatsAppButton.tsx

lib/
├── analytics.ts
├── lead-validation.ts
├── crm.ts
└── whatsapp.ts

content/
├── case-study-blueberry.ts
├── categories.ts
├── faq.ts
└── use-cases.ts
```

---

# 24. Server y client components

## Server Components

- página;
- secciones estáticas;
- contenido;
- SEO;
- tarjetas no interactivas.

## Client Components

- navbar móvil;
- tabs;
- formulario;
- FAQ;
- WhatsApp;
- tracking de scroll;
- animaciones.

Regla: minimizar `use client`.

---

# 25. Props principales

```ts
type HeroProps = {
  eyebrow: string;
  title: string;
  description: string;
  primaryCta: CTA;
  secondaryCta: CTA;
  metrics: Metric[];
};
```

```ts
type EvidenceTab = {
  id: "science" | "market" | "formulation";
  label: string;
  content: React.ReactNode;
};
```

```ts
type CategoryCardProps = {
  name: string;
  status: "available" | "soon" | "request";
  image?: string;
  href?: string;
};
```

```ts
type LeadFormValues = {
  name: string;
  company: string;
  email: string;
  whatsapp: string;
  originCountry: string;
  product: string;
  destinationMarket: string;
  projectStage: string;
  analysisNeeds: string[];
  notes?: string;
  consent: boolean;
};
```

---

# 26. Validación con Zod

```ts
import { z } from "zod";

export const leadSchema = z.object({
  name: z.string().min(2, "Ingresa tu nombre."),
  company: z.string().min(2, "Ingresa la empresa."),
  email: z.string().email("Usa un correo válido."),
  whatsapp: z.string().min(8, "Ingresa un WhatsApp válido."),
  originCountry: z.string().min(2),
  product: z.string().min(2, "Indica el producto."),
  destinationMarket: z.string().min(2, "Selecciona un mercado."),
  projectStage: z.string().min(1),
  analysisNeeds: z.array(z.string()).min(1),
  notes: z.string().optional(),
  consent: z.literal(true, {
    errorMap: () => ({
      message: "Acepta la política de privacidad."
    })
  })
});
```

---

# 27. Metadata

```ts
export const metadata = {
  title: "Inteligencia científica y de mercado para exportadores | CLI Market",
  description:
    "Evalúa oportunidades de exportación con evidencia científica, precios reales, productos competidores y formulaciones disponibles.",
  alternates: {
    canonical: "https://cli-market.dev/intel-latam"
  },
  openGraph: {
    title: "Antes de exportar, valida la ciencia y el mercado",
    description:
      "Evidencia científica, inteligencia de góndola y formulación competitiva.",
    url: "https://cli-market.dev/intel-latam",
    type: "website",
    images: ["/og/export-intelligence.png"]
  }
};
```

---

# 28. Eventos de analítica

```ts
track("hero_primary_cta_click");
track("hero_case_click");
track("case_study_view");
track("case_tab_click", { tab: "market" });
track("category_click", {
  category: "cacao",
  status: "soon"
});
track("form_start");
track("form_step_complete", { step: 1 });
track("form_submit");
track("form_error", { field: "email" });
track("whatsapp_click", { section: "floating" });
track("faq_open", { question: "ingredients" });
track("scroll_50");
track("scroll_90");
```

---

# 29. Estados globales

## Loading

Usar skeletons únicamente en componentes que dependan de datos.

## Error

Mostrar mensaje contextual, no página genérica, cuando falle:

- formulario;
- CRM;
- carga de caso.

## Empty

Si una formulación no está disponible:

```text
Ingredientes no disponibles en la fuente pública consultada.
```

No ocultar el vacío.

## Offline

Formulario:

```text
Parece que no tienes conexión. Conservaremos tus datos hasta que vuelvas a intentarlo.
```

---

# 30. Criterios de aceptación por sección

## Hero

- propuesta comprensible;
- CTA visible;
- carga sin salto de layout.

## Método

- tres capas diferenciadas;
- responsive;
- contenido accesible.

## Caso

- métricas correctas;
- tabs funcionales;
- fuentes visibles;
- CTA operativo.

## Formulario

- validación;
- UTMs;
- éxito;
- error;
- privacidad;
- integración CRM.

## FAQ

- teclado;
- `aria-expanded`;
- evento de apertura.

---

# 31. Checklist de diseño

- [ ] H1 de máximo dos líneas en desktop
- [ ] CTA primario visible sin scroll
- [ ] Contraste AA
- [ ] Métricas visibles
- [ ] Tabs comprensibles
- [ ] Fuentes identificadas
- [ ] Formularios con labels
- [ ] Estados de error
- [ ] Layout móvil
- [ ] Open Graph 1200 × 630
- [ ] Favicon y marca
- [ ] Sin carruseles automáticos

---

# 32. Checklist de desarrollo

- [ ] Next.js App Router
- [ ] TypeScript estricto
- [ ] Componentes reutilizables
- [ ] Server Components por defecto
- [ ] Zod
- [ ] React Hook Form
- [ ] Captura UTMs
- [ ] Integración CRM
- [ ] GA4/GTM
- [ ] Schema.org
- [ ] Sitemap
- [ ] Robots
- [ ] Lighthouse móvil > 85
- [ ] Accesibilidad AA
- [ ] Rate limit
- [ ] Anti-spam
- [ ] Logs de error

---

# 33. Orden de implementación

## Sprint 1 — Estructura

- layout;
- navbar;
- hero;
- problema;
- método;
- estilos base.

## Sprint 2 — Evidencia

- caso;
- tabs;
- productos;
- formulación;
- entregable.

## Sprint 3 — Conversión

- categorías;
- comparativa;
- formulario;
- WhatsApp;
- FAQ.

## Sprint 4 — Lanzamiento

- analítica;
- SEO;
- accesibilidad;
- performance;
- QA;
- publicación.

---

# 34. Resultado esperado

La página debe sentirse como una combinación de:

- una landing de Stripe;
- una interfaz de Bloomberg;
- un documento ejecutivo;
- un radar de innovación;
- una herramienta de decisión.

No debe parecer:

- una página institucional;
- un informe académico;
- una web genérica de consultoría;
- un ecommerce;
- un catálogo de productos.

---

# 35. Copy consolidado

## Hero

**Antes de exportar, valida la ciencia y el mercado.**

Descubre si tu producto tiene respaldo científico, espacio competitivo y una oportunidad real en el mercado objetivo.

**No desarrolles primero el producto. Desarrolla primero la evidencia.**

## Problema

**Exportar no debería comenzar con una suposición.**

## Método

**Una oportunidad exportadora debe sostenerse en tres capas de evidencia.**

## Caso

**Arándano: de la hipótesis a la evidencia.**

## Entregable

**De la información a una ficha de oportunidad exportadora.**

## Categorías

**Empieza con una materia prima, un ingrediente o una categoría.**

## Formulario

**¿Tienes un producto que quieres exportar?**

## Cierre

**La exportación no comienza en el puerto.**

Comienza cuando puedes demostrar por qué tu producto merece entrar al mercado.

---

# 36. Definition of Done

El wireframe se considera implementado cuando:

1. todos los bloques definidos están construidos;
2. la jerarquía coincide con este documento;
3. funciona en desktop, tablet y móvil;
4. el caso real es interactivo;
5. el formulario registra y valida leads;
6. WhatsApp funciona;
7. los eventos analíticos se registran;
8. las fuentes y limitaciones son visibles;
9. el rendimiento móvil supera el objetivo;
10. la landing está lista para campaña y validación comercial.
