import {
  BarChart,
  Callout,
  Card,
  CardBody,
  CardHeader,
  CollapsibleSection,
  computeDAGLayout,
  Grid,
  H1,
  H2,
  H3,
  Pill,
  Row,
  Stack,
  Stat,
  Swatch,
  Table,
  Text,
  TodoListCard,
  useHostTheme,
} from "cursor/canvas";

const VERSION = "1.0";
const DOC_DATE = "2026-07-30";

const SCORING_WEIGHTS = [
  { domain: "Science", weight: 20 },
  { domain: "Trade", weight: 20 },
  { domain: "Commerce", weight: 15 },
  { domain: "Regulatory", weight: 10 },
  { domain: "Patent", weight: 10 },
  { domain: "Trend", weight: 10 },
  { domain: "Macro", weight: 5 },
  { domain: "Sustainability", weight: 5 },
  { domain: "Tech scout", weight: 5 },
];

const AGENTS_BY_LAYER: Array<{
  layer: string;
  color: "purple" | "blue" | "green" | "orange" | "red" | "yellow" | "cyan";
  agents: Array<{ name: string; role: string; output: string; llm: string }>;
}> = [
  {
    layer: "Orquestación",
    color: "purple",
    agents: [
      {
        name: "Run Director",
        role: "Dueño del ciclo de vida del run",
        output: "Paquete final de ejecución",
        llm: "Coordinación",
      },
    ],
  },
  {
    layer: "Planificación",
    color: "blue",
    agents: [
      {
        name: "Intent & Scope Analyzer",
        role: "Clasifica producto, HS, mercado, marco regulatorio",
        output: "run_brief.json",
        llm: "1 llamada",
      },
      {
        name: "Evidence Gap Planner",
        role: "Prioriza dominios y conectores por mercado destino",
        output: "Plan de evidencia",
        llm: "1 llamada + reglas",
      },
      {
        name: "Execution Planner",
        role: "DAG de tareas, paralelismo, fallbacks",
        output: "execution_plan.json",
        llm: "Reglas",
      },
    ],
  },
  {
    layer: "Ejecución",
    color: "green",
    agents: [
      {
        name: "Connector Runner",
        role: "Pipeline PIT: /v1/research-runs/full",
        output: "source_request + raw SHA-256",
        llm: "Sin LLM",
      },
      {
        name: "Domain Synthesizers ×9",
        role: "Síntesis por dominio de evidencia",
        output: "domain_syntheses/*.yaml",
        llm: "9 en paralelo",
      },
      {
        name: "Quality & Coverage Guard",
        role: "Cobertura, contradicciones, re-enrichment",
        output: "Gate de calidad",
        llm: "Reglas + 1 si conflicto",
      },
    ],
  },
  {
    layer: "Sistematización",
    color: "orange",
    agents: [
      {
        name: "Evidence Graph Builder",
        role: "Entidades, relaciones, claims trazables",
        output: "evidence_graph.json",
        llm: "Reglas",
      },
      {
        name: "Score Interpreter",
        role: "Traduce scores a significado de negocio",
        output: "Narrativa de recomendación",
        llm: "1 corta",
      },
      {
        name: "Claim Classifier",
        role: "Hecho vs inferencia; compliance",
        output: "Filtro de lenguaje",
        llm: "Reglas",
      },
    ],
  },
  {
    layer: "Salida",
    color: "cyan",
    agents: [
      {
        name: "Executive Writer",
        role: "Informe ejecutivo en 9 secciones",
        output: "executive_report.md",
        llm: "1 larga",
      },
      {
        name: "Presentation Composer",
        role: "UI / PDF / API / Slack",
        output: "presentation/",
        llm: "Plantillas",
      },
      {
        name: "Action Pack Generator",
        role: "Checklist operativa y próximo run",
        output: "action_pack.json",
        llm: "Reglas",
      },
    ],
  },
];

const SYNTHESIZERS = [
  ["Science Analyst", "OpenAlex, PubMed, Crossref, S2", "Claims defendibles"],
  ["Patent Scout", "EPO OPS, USPTO", "Saturación IP"],
  ["Market Access", "Comtrade, WTO, WITS, Eurostat", "Aranceles y barreras"],
  ["Shelf Intelligence", "CLI Market", "Precios en góndola"],
  ["Regulatory Officer", "OpenFDA, EFSA, ePing, RASFF", "Riesgo regulatorio"],
  ["Trend Analyst", "GDELT, Google Trends", "Demanda del consumidor"],
  ["Sustainability", "Climatiq", "Huella ESG"],
  ["Macro Context", "BCRP, World Bank, IMF", "Contexto destino"],
  ["Tech Scout", "CORDIS, NIH, NSF", "I+D relevante"],
];

const ARTIFACTS = [
  ["run_brief.json", "Intención, scope, HS, mercados"],
  ["execution_plan.json", "DAG ejecutado y status de conectores"],
  ["domain_syntheses/", "Un YAML por dominio (contrato pit_agents)"],
  ["evidence_graph.json", "Entidades y relaciones entre claims"],
  ["executive_report.md", "Narrativa principal del run"],
  ["presentation/", "Variantes UI, PDF y API"],
  ["action_pack.json", "Checklist y próximos pasos"],
  ["agent_trace.json", "Log de delegación para auditoría"],
];

const ROADMAP = [
  {
    id: "phase-1",
    content: "Fase 1 — Informe inteligente: Director, 4 synthesizers, Writer, Action Pack",
    status: "in_progress" as const,
  },
  {
    id: "phase-2",
    content: "Fase 2 — Planificación adaptativa: Gap Planner, Quality Guard, Evidence Graph",
    status: "pending" as const,
  },
  {
    id: "phase-3",
    content: "Fase 3 — Producto completo: Product Intelligence, memoria entre runs, alertas",
    status: "pending" as const,
  },
];

const DAG_NODES = [
  { id: "input", label: "Entrada PIT", layer: "input" },
  { id: "director", label: "Run Director", layer: "orch" },
  { id: "intent", label: "Intent Analyzer", layer: "plan" },
  { id: "gap", label: "Gap Planner", layer: "plan" },
  { id: "execplan", label: "Execution Planner", layer: "plan" },
  { id: "runner", label: "Connector Runner", layer: "exec" },
  { id: "synth", label: "Synthesizers ×9", layer: "exec" },
  { id: "guard", label: "Quality Guard", layer: "exec" },
  { id: "graph", label: "Evidence Graph", layer: "sys" },
  { id: "score", label: "Score Interpreter", layer: "sys" },
  { id: "claims", label: "Claim Classifier", layer: "sys" },
  { id: "writer", label: "Executive Writer", layer: "out" },
  { id: "present", label: "Presentation", layer: "out" },
  { id: "actions", label: "Action Pack", layer: "out" },
];

const DAG_EDGES = [
  { from: "input", to: "director" },
  { from: "director", to: "intent" },
  { from: "intent", to: "gap" },
  { from: "gap", to: "execplan" },
  { from: "execplan", to: "runner" },
  { from: "runner", to: "synth" },
  { from: "synth", to: "guard" },
  { from: "guard", to: "graph" },
  { from: "graph", to: "score" },
  { from: "score", to: "claims" },
  { from: "claims", to: "writer" },
  { from: "claims", to: "present" },
  { from: "claims", to: "actions" },
];

const LAYER_FILL: Record<string, "purple" | "blue" | "green" | "orange" | "cyan" | "gray"> = {
  input: "gray",
  orch: "purple",
  plan: "blue",
  exec: "green",
  sys: "orange",
  out: "cyan",
};

function FlowDiagram() {
  const theme = useHostTheme();
  const layout = computeDAGLayout({
    nodes: DAG_NODES.map((n) => ({ id: n.id })),
    edges: DAG_EDGES,
    direction: "vertical",
    nodeWidth: 168,
    nodeHeight: 36,
    rankGap: 40,
    nodeGap: 20,
    padding: 20,
  });

  const labelById = Object.fromEntries(DAG_NODES.map((n) => [n.id, n.label]));
  const layerById = Object.fromEntries(DAG_NODES.map((n) => [n.id, n.layer]));
  const category = theme.category;

  return (
    <Stack gap={8}>
      <H3>Flujo de ejecución por run</H3>
      <Text size="small" tone="tertiary">
        Source: agentic_execution_system.md v{VERSION} · {DOC_DATE} · 14 nodos, 13 aristas
      </Text>
      <div style={{ overflowX: "auto", width: "100%" }}>
        <svg
          width={layout.width}
          height={layout.height}
          viewBox={`0 0 ${layout.width} ${layout.height}`}
          role="img"
          aria-label="Diagrama de flujo del sistema agéntico CLI Market PIT"
        >
          {layout.edges.map((edge) => (
            <line
              key={`${edge.from}-${edge.to}`}
              x1={edge.sourceX}
              y1={edge.sourceY}
              x2={edge.targetX}
              y2={edge.targetY}
              stroke={theme.stroke.secondary}
              strokeWidth={1.5}
              strokeDasharray={edge.isBackEdge ? "4 3" : undefined}
            />
          ))}
          {layout.nodes.map((node) => {
            const colorKey = LAYER_FILL[layerById[node.id] ?? "gray"];
            const fill = category[colorKey] ?? theme.fill.secondary;
            return (
              <g key={node.id}>
                <rect
                  x={node.x}
                  y={node.y}
                  width={168}
                  height={36}
                  rx={6}
                  fill={fill}
                  stroke={theme.stroke.primary}
                />
                <text
                  x={node.x + 84}
                  y={node.y + 22}
                  textAnchor="middle"
                  fill={theme.text.primary}
                  fontSize={11}
                  fontFamily="system-ui, sans-serif"
                >
                  {labelById[node.id]}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
      <Row gap={12} wrap>
        {(
          [
            ["Entrada", "gray"],
            ["Orquestación", "purple"],
            ["Planificación", "blue"],
            ["Ejecución", "green"],
            ["Sistematización", "orange"],
            ["Salida", "cyan"],
          ] as const
        ).map(([label, color]) => (
          <Row key={label} gap={6} align="center">
            <Swatch color={color} />
            <Text size="small" tone="secondary">
              {label}
            </Text>
          </Row>
        ))}
      </Row>
    </Stack>
  );
}

export default function PitAgenticSystemCanvas() {
  return (
    <Stack gap={24} style={{ padding: 4, maxWidth: 960 }}>
      <Stack gap={8}>
        <Row gap={8} align="center" wrap>
          <H1 style={{ margin: 0 }}>Sistema agéntico — CLI Market PIT</H1>
          <Pill size="sm">v{VERSION}</Pill>
        </Row>
        <Text tone="secondary">
          Orquestador por ejecución que analiza, delega, ejecuta el pipeline de evidencia,
          sistematiza hallazgos y presenta un informe ejecutivo trazable en cada research run.
        </Text>
      </Stack>

      <Callout tone="info" title="Principio rector">
        Los agentes no inventan datos. Interpretan, sintetizan y recomiendan sobre evidencia
        trazable: cada claim enlaza a un source_request (raw SHA-256), un dominio, o una
        inferencia explícita.
      </Callout>

      <Grid columns={4} gap={16}>
        <Stat value="13" label="Agentes especializados" />
        <Stat value="9" label="Domain synthesizers" tone="info" />
        <Stat value="7" label="Capas arquitectónicas" />
        <Stat value="<30s" label="Latencia agéntica objetivo" tone="success" />
      </Grid>

      <Card>
        <CardBody>
          <FlowDiagram />
        </CardBody>
      </Card>

      <Stack gap={12}>
        <H2>Agentes por capa</H2>
        {AGENTS_BY_LAYER.map((group) => (
          <CollapsibleSection
            key={group.layer}
            title={group.layer}
            count={group.agents.length}
            leading={<Swatch color={group.color} />}
            defaultOpen={group.layer === "Orquestación" || group.layer === "Ejecución"}
          >
            <Table
              framed={false}
              headers={["Agente", "Rol", "Artefacto", "LLM"]}
              rows={group.agents.map((a) => [a.name, a.role, a.output, a.llm])}
              columnAlign={["left", "left", "left", "right"]}
            />
          </CollapsibleSection>
        ))}
      </Stack>

      <Stack gap={8}>
        <H2>Pesos de scoring v1.0-mvp</H2>
        <Text size="small" tone="tertiary">
          Source: src/pit/scoring.py · pesos por dominio (%) usados por Score Interpreter
        </Text>
        <BarChart
          categories={SCORING_WEIGHTS.map((d) => d.domain)}
          series={[{ name: "Peso de dominio (%)", data: SCORING_WEIGHTS.map((d) => d.weight) }]}
          horizontal
          height={280}
          valueSuffix="%"
          showValues
        />
      </Stack>

      <Stack gap={8}>
        <H2>Domain Synthesizers</H2>
        <Table
          headers={["Agente", "Fuentes PIT", "Produce"]}
          rows={SYNTHESIZERS}
          striped
        />
      </Stack>

      <Stack gap={8}>
        <H2>Artefactos por ejecución</H2>
        <Text size="small" tone="tertiary">
          Paquete persistente ligado al run_id · Source: agentic_execution_system.md §7
        </Text>
        <Table
          headers={["Archivo", "Contenido"]}
          rows={ARTIFACTS}
          columnAlign={["left", "left"]}
        />
      </Stack>

      <Stack gap={8}>
        <H2>Roadmap de implementación</H2>
        <TodoListCard todos={ROADMAP} defaultExpanded />
      </Stack>

      <Card variant="borderless">
        <CardHeader>Relación con PIT existente</CardHeader>
        <CardBody>
          <Grid columns={2} gap={12}>
            <Stack gap={4}>
              <Text weight="semibold">Motor (sin LLM)</Text>
              <Text size="small" tone="secondary">
                ResearchService, conectores, ScoringEngine, reports.py — capa de evidencia y
                scoring determinista.
              </Text>
            </Stack>
            <Stack gap={4}>
              <Text weight="semibold">Capa agéntica (con LLM)</Text>
              <Text size="small" tone="secondary">
                Interpretación, narrativa, compliance y Action Pack — encima del motor, no lo
                reemplaza.
              </Text>
            </Stack>
          </Grid>
        </CardBody>
      </Card>

      <Grid columns={4} gap={16}>
        <Stat value="100%" label="Claims trazables" tone="success" />
        <Stat value="≥60%" label="Coverage mínimo" tone="warning" />
        <Stat value="4" label="Recomendaciones posibles" />
        <Stat value="8" label="Artefactos por run" tone="info" />
      </Grid>

      <Text size="small" tone="quaternary">
        Documentación completa: acuba/downloads/agentic_execution_system.md · CLI Market Export
        Intelligence · {DOC_DATE}
      </Text>
    </Stack>
  );
}
