import {
  BarChart,
  Callout,
  Card,
  CardBody,
  CardHeader,
  Divider,
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
  useHostTheme,
} from "cursor/canvas";

const WORKSHOP = {
  title: "De la evidencia a la decisión de exportación",
  subtitle: "Taller intensivo CLI Market Export Intelligence",
  duration: "2 horas",
  format: "En vivo · 70% práctica",
  tier: "Suscripción PRO",
  audience: "Ciencia, mercado, regulatorio y exportación",
  cohort: "12–20 profesionales",
};

const AGENDA = [
  ["0:00", "10 min", "Apertura y contrato del taller"],
  ["0:10", "15 min", "Marco PIT: evidencia trazable por dominio"],
  ["0:25", "15 min", "Ejercicio 1 — Brief de intención"],
  ["0:40", "25 min", "Ejercicio 2 — Pipeline completo en vivo"],
  ["1:05", "5 min", "Pausa"],
  ["1:10", "20 min", "Ejercicio 3 — Lectura crítica del reporte"],
  ["1:30", "15 min", "Ejercicio 4 — Matriz GO condicionado"],
  ["1:45", "10 min", "Ejercicio 5 — Pitch de 90 segundos"],
  ["1:55", "5 min", "Cierre y checklist PRO"],
];

const OUTCOMES = [
  ["Ejecutar", "Research run con evidencia trazable"],
  ["Interpretar", "Score, cobertura y recomendación"],
  ["Diagnosticar", "Vacíos críticos por dominio"],
  ["Decidir", "GO / GO condicionado / PIVOT / NO-GO"],
  ["Presentar", "Brief ejecutivo en 90 segundos"],
];

const PRO_INCLUDES = [
  ["Pipeline multi-dominio", "Science, trade, commerce, regulatory y más"],
  ["Enrichment por dominio", "Re-ejecución dirigida en vivo"],
  ["Reporte PDF", "Checklist de mejora integrado"],
  ["Plantillas de decisión", "Run brief + matriz 30/60/90"],
  ["Product Intelligence", "Ficha de oportunidad post-taller"],
];

const DOMAINS = [
  { name: "Science", pct: 20 },
  { name: "Trade", pct: 20 },
  { name: "Commerce", pct: 15 },
  { name: "Regulatory", pct: 10 },
  { name: "Patent", pct: 10 },
  { name: "Trend", pct: 10 },
  { name: "Macro", pct: 5 },
  { name: "Sustainability", pct: 5 },
  { name: "Tech scout", pct: 5 },
];

function HeroBand() {
  const theme = useHostTheme();
  return (
    <div
      style={{
        background: theme.fill.secondary,
        border: `1px solid ${theme.stroke.primary}`,
        borderRadius: 12,
        padding: "28px 24px",
      }}
    >
      <Stack gap={12}>
        <Row gap={8} wrap align="center">
          <Pill active>CLI Market PIT</Pill>
          <Pill size="sm">{WORKSHOP.tier}</Pill>
        </Row>
        <H1 style={{ margin: 0, lineHeight: 1.1 }}>{WORKSHOP.title}</H1>
        <Text tone="secondary" weight="medium">
          {WORKSHOP.subtitle}
        </Text>
        <Row gap={16} wrap>
          <Stat value={WORKSHOP.duration} label="Duración" />
          <Stat value="5" label="Ejercicios prácticos" tone="info" />
          <Stat value="8" label="Dominios de evidencia" />
          <Stat value="70%" label="Tiempo en práctica" tone="success" />
        </Row>
      </Stack>
    </div>
  );
}

export default function ProWorkshopFlyerCanvas() {
  return (
    <Stack gap={20} style={{ padding: 4, maxWidth: 720 }}>
      <HeroBand />

      <Callout tone="info" title="Para quién es">
        Profesionales de ciencia e I+D, inteligencia de mercado, exportación y
        regulatorio que necesitan decidir con datos — no con intuición — si un
        producto tiene oportunidad real en un mercado destino.
      </Callout>

      <Grid columns={2} gap={16}>
        <Stack gap={8}>
          <H2>Qué aprenderás</H2>
          <Table framed={false} headers={["Habilidad", "Resultado"]} rows={OUTCOMES} />
        </Stack>
        <Stack gap={8}>
          <H2>Incluido con PRO</H2>
          <Table framed={false} headers={["Beneficio", "En el taller"]} rows={PRO_INCLUDES} />
        </Stack>
      </Grid>

      <Divider />

      <Stack gap={8}>
        <H2>Agenda · 120 minutos</H2>
        <Text size="small" tone="tertiary">
          Formato: {WORKSHOP.format} · Cohorte: {WORKSHOP.cohort}
        </Text>
        <Table
          headers={["Hora", "Duración", "Bloque"]}
          rows={AGENDA}
          columnAlign={["left", "right", "left"]}
          striped
        />
      </Stack>

      <Card variant="borderless">
        <CardHeader trailing={<Pill size="sm">Motor PIT</Pill>}>Dominios que analizarás</CardHeader>
        <CardBody>
          <Stack gap={8}>
            <Text size="small" tone="tertiary">
              Pesos de scoring v1.0-mvp · cada dominio aporta evidencia independiente al
              informe final
            </Text>
            <BarChart
              categories={DOMAINS.map((d) => d.name)}
              series={[{ name: "Peso en score global (%)", data: DOMAINS.map((d) => d.pct) }]}
              horizontal
              height={260}
              valueSuffix="%"
              showValues
            />
          </Stack>
        </CardBody>
      </Card>

      <Grid columns={3} gap={12}>
        <Stack gap={6}>
          <Row gap={6} align="center">
            <Swatch color="purple" />
            <H3 style={{ margin: 0 }}>Trae tu producto</H3>
          </Row>
          <Text size="small" tone="secondary">
            Nombre comercial, mercado destino tentativo y una restricción conocida
            (regulatoria, logística o de claim).
          </Text>
        </Stack>
        <Stack gap={6}>
          <Row gap={6} align="center">
            <Swatch color="green" />
            <H3 style={{ margin: 0 }}>Sal con un plan</H3>
          </Row>
          <Text size="small" tone="secondary">
            Matriz GO condicionado, 3 acciones a 30/60/90 días y un pitch de 90
            segundos listo para comité.
          </Text>
        </Stack>
        <Stack gap={6}>
          <Row gap={6} align="center">
            <Swatch color="blue" />
            <H3 style={{ margin: 0 }}>Evidencia trazable</H3>
          </Row>
          <Text size="small" tone="secondary">
            Cada afirmación del informe enlaza a fuente, dominio o inferencia
            explícita. Sin datos inventados.
          </Text>
        </Stack>
      </Grid>

      <div
        style={{
          borderTop: "2px solid",
          borderColor: "currentColor",
          paddingTop: 16,
        }}
      >
        <Stack gap={8}>
          <H2>Reserva tu lugar</H2>
          <Row gap={8} wrap align="center">
            <Text weight="semibold">cli-market.dev/workshops</Text>
            <Pill active>Requiere PRO activo</Pill>
          </Row>
          <Text size="small" tone="tertiary">
            CLI Market Export Intelligence · Taller en vivo · Material y plantillas
            incluidas · Cupos limitados
          </Text>
        </Stack>
      </div>
    </Stack>
  );
}
