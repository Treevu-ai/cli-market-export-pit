# PRD -- Plataforma de Inteligencia Tecnológica (Fases 1 y 2)

**Versión:** 1.0\
**Objetivo:** Construir una plataforma de inteligencia tecnológica y de
innovación basada prioritariamente en **APIs públicas y abiertas**,
minimizando costos de licenciamiento y permitiendo la evolución hacia
una solución empresarial.

------------------------------------------------------------------------

# 1. Visión

La plataforma integrará múltiples fuentes abiertas para responder una
pregunta de negocio como:

> **¿Qué oportunidades existen para desarrollar un nuevo producto
> agroindustrial para exportación?**

En lugar de consultar bases aisladas, un conjunto de agentes
especializados recopilará, normalizará y correlacionará información
científica, tecnológica y comercial.

------------------------------------------------------------------------

# 2. Objetivos

## Funcionales

-   Buscar evidencia científica.
-   Buscar patentes relacionadas.
-   Identificar tecnologías emergentes.
-   Detectar tendencias de consumo.
-   Analizar cadenas de suministro.
-   Evaluar sostenibilidad.
-   Generar un Opportunity Score.

## No funcionales

-   100% API-first.
-   Arquitectura modular.
-   Escalable.
-   Coste operativo bajo.
-   Sin dependencia de licencias comerciales.

------------------------------------------------------------------------

# 3. Arquitectura

``` text
                  Usuario
                     │
                     ▼
          Orquestador (LLM Agent)
                     │
────────────────────────────────────────────
│          │          │         │
Papers   Patentes  Tendencias Regulación
│          │          │         │
└──────────┴──────────┴─────────┘
           │
           ▼
Technology Scout
           │
           ▼
Supply Chain
           │
           ▼
Sustainability
           │
           ▼
Opportunity Scoring
```

------------------------------------------------------------------------

# 4. FASE 1 -- MVP (100% APIs públicas)

## Agente 1 -- Scientific Evidence

### Objetivo

Encontrar el estado del arte científico.

### APIs

-   **OpenAlex**: autores, instituciones, citas, topics, DOI.
-   **Crossref**: DOI, metadata, publisher, referencias.
-   **Semantic Scholar**: citation count, influential citations,
    embeddings.
-   **PubMed**: abstracts, MeSH, ensayos clínicos.

### Salida

``` json
{
  "papers": 142,
  "top_topics": ["Plant Protein","Bioactive Peptides","Functional Foods"],
  "top_authors": [],
  "TRL_estimate": 4
}
```

------------------------------------------------------------------------

## Agente 2 -- Patent Intelligence

### Objetivo

Buscar innovación protegida.

### APIs

-   Espacenet OPS
-   WIPO Patentscope
-   Google Patents Dataset
-   Lens API

### Salida

``` json
{
  "patents":81,
  "top_assignees":["Nestlé","DSM","PepsiCo"],
  "top_IPC":["A23L","C12N"]
}
```

------------------------------------------------------------------------

## Agente 3 -- Consumer Trends

### APIs

-   Google Trends
-   GDELT
-   NewsAPI
-   YouTube Data API

### Salida

``` json
{
 "trend":"Growing",
 "growth":48,
 "countries":["USA","Japan","Germany"]
}
```

------------------------------------------------------------------------

## Agente 4 -- Supply Chain

### APIs

-   UN Comtrade
-   FAOSTAT
-   World Bank API

### Salida

``` json
{
 "major_exporters":["Peru","Chile"],
 "imports_growth":22
}
```

------------------------------------------------------------------------

## Agente 5 -- Regulatory

### APIs

-   OpenFDA
-   FoodData Central
-   EFSA Open Data
-   EUR-Lex

### Salida

``` json
{
 "claims_allowed":["High Protein"],
 "risk_level":"Low"
}
```

------------------------------------------------------------------------

## Agente 6 -- Opportunity Scoring

No consume APIs directamente.

### Variables

-   Science Score
-   Patent Score
-   Trend Score
-   Supply Score
-   Regulatory Score

### Fórmula

``` text
Opportunity =
0.30 Science +
0.20 Patent +
0.20 Trends +
0.15 Supply +
0.15 Regulation
```

### Salida

``` json
{
 "opportunity_score":81,
 "recommendation":"Proceed"
}
```

------------------------------------------------------------------------

# 5. FASE 2 -- Inteligencia avanzada (sin licencias obligatorias)

## Technology Scout

### APIs

-   CORDIS
-   Europe PMC
-   OpenAIRE
-   NIH RePORTER
-   NSF Awards

### Salida

``` json
{
 "technology":"Precision Fermentation",
 "TRL":6,
 "funding":24000000
}
```

------------------------------------------------------------------------

## Sustainability

### APIs

-   Climatiq
-   Agribalyse
-   EPA APIs
-   Carbon Interface

### Salida

``` json
{
 "carbon":2.4,
 "water":134,
 "rating":"B+"
}
```

------------------------------------------------------------------------

## Company Intelligence

### APIs

-   OpenCorporates
-   GS1 GEPIR

### Salida

``` json
{
 "company":"Nestlé",
 "subsidiaries":48
}
```

------------------------------------------------------------------------

# 6. Flujo

``` text
Consulta
   ↓
Scientific Evidence
   ↓
Patent Intelligence
   ↓
Technology Scout
   ↓
Consumer Trends
   ↓
Supply Chain
   ↓
Regulatory
   ↓
Sustainability
   ↓
Opportunity Score
   ↓
Reporte Ejecutivo
```

------------------------------------------------------------------------

# 7. Modelo de datos unificado

``` json
{
  "source":"OpenAlex",
  "entity":"paper",
  "title":"Protein Extraction from Quinoa",
  "date":"2025-05-01",
  "country":"Peru",
  "score":0.91,
  "metadata":{
    "doi":"...",
    "authors":[],
    "topics":[]
  }
}
```

------------------------------------------------------------------------

# 8. Roadmap

  ------------------------------------------------------------------------
  Sprint                Entregable                       APIs
  --------------------- -------------------------------- -----------------
  1                     Scientific Evidence              OpenAlex,
                                                         Crossref,
                                                         Semantic Scholar,
                                                         PubMed

  2                     Patent Intelligence              Espacenet OPS,
                                                         WIPO, Lens

  3                     Consumer Trends                  Google Trends,
                                                         GDELT, NewsAPI

  4                     Supply Chain + Regulatory        UN Comtrade,
                                                         FAOSTAT, World
                                                         Bank, OpenFDA,
                                                         EFSA

  5                     Opportunity Scoring              Motor de scoring

  6                     Technology Scout                 CORDIS, Europe
                                                         PMC, OpenAIRE,
                                                         NIH RePORTER, NSF
                                                         Awards

  7                     Sustainability + Company         Climatiq,
                        Intelligence                     Agribalyse, EPA,
                                                         OpenCorporates,
                                                         GS1
  ------------------------------------------------------------------------

------------------------------------------------------------------------

# Resultado esperado

La plataforma responderá preguntas estratégicas sobre oportunidades de
innovación, estado del arte científico, patentamiento, tendencias de
mercado, regulación, sostenibilidad y viabilidad comercial utilizando
principalmente APIs públicas.
