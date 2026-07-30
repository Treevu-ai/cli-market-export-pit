import {
  BarChart,
  Callout,
  Card,
  CardBody,
  CardHeader,
  CollapsibleSection,
  Divider,
  Grid,
  H1,
  H2,
  Stack,
  Stat,
  Swatch,
  Table,
  Text,
} from "cursor/canvas";

const DECISION = "CONDITIONAL GO";
const PRODUCT = "Golden Lucuma Crunch — barra 50 g";

const COMPETITORS = [
  ["Amaru Lucuma Granola", "Granola 200 g", "$8+", "Import specialty", "Peru — no barra"],
  ["Elemental Lucuma Seedbar", "Barra 51 g", "$3.31", "DTC", "Seed bar, no granola"],
  ["Foundation Lucuma Cacao", "Barra 56 g", "$9.25", "Specialty", "Cacao ultra-premium"],
  ["KIND / Nature Valley", "Barra 40-50 g", "$1.69-2.29", "Mass retail", "Indirecto"],
];

const RISKS = [
  ["Categoria saturada", "Alta", "Mainstream domina 50-55% ventas"],
  ["Baja awareness lucuma", "Alta", "Polvo vende; barras son excepcion"],
  ["Economia unitaria sin cerrar", "Media", "COGS + co-pack pendiente"],
  ["Claims no sustentados", "Media", "GI bajo no confirmado"],
  ["FSVP importacion Peru", "Media", "21 CFR 1.502"],
];

const CLAIMS = [
  ["Made with lucuma, Peruvian superfruit", "Defendible", "Descriptivo"],
  ["Source of fiber", "Condicional", "Si cumple 10% DV"],
  ["Low glycemic", "No recomendado", "Sin evidencia clinica"],
  ["Sustained energy", "No recomendado", "Requiere substantiation FDA"],
];

const AGENT_TRACE = [
  ["Brief Architect", "Problema estructurado para validar nicho premium", "Alta"],
  ["Scientific Evidence", "Evidencia composicional; vacio GI humano", "Media"],
  ["Market Intelligence", "Nicho observable; pocos directos", "Media-baja"],
  ["Regulatory Readiness", "Lucuma no en SAFFA; FSVP requerido", "Media"],
  ["Product Designer", "Concepto 50 g, 10-12% lucuma, vegan", "Media"],
  ["Commercial Feasibility", "DTC first; margen objetivo 45%+", "Baja-media"],
  ["Red Team", "CONDITIONAL GO — validar con <=$15K", "Media"],
];

const PLAN_30 = [
  ["Semana 1", "Sourcing lucuma organica Peru (3 proveedores, COA, FOB)"],
  ["Semana 2", "Cotizacion co-packer US + formulacion"],
  ["Semana 3", "Revision etiqueta FDA + borrador FSVP"],
  ["Semana 4", "Prototipo 50 barras + taste test + gate go/no-go"],
];

const EXPERIMENTS = [
  ["E1", "Landing page + ads ($2K) — CTR e intencion de compra"],
  ["E2", "Prototipo 100 uds + taste test n=30 ($5K)"],
  ["E3", "Amazon listing test 500 uds ($8K)"],
  ["E4", "Entrevistas n=20 compradores Sprouts/Whole Foods"],
];

export default function LucumaGranolaUsOpportunity() {
  return (
    <Stack gap={20} style={{ padding: 20 }}>
      <H1>Barras de granola con lucuma — EE.UU.</H1>
      <Text tone="secondary">
        Ficha de Oportunidad · agentic-execution-system · 30 jul 2026
      </Text>

      <Callout tone="warning" title={"Decision ejecutiva: " + DECISION}>
        Oportunidad plausible en segmento premium/superfood, no en volumen masivo. Avanzar solo con
        experimentos reversibles de hasta $15K antes de produccion comercial.
      </Callout>

      <Grid columns={2} gap={12}>
        <Stat value="$3.49" label="Precio objetivo DTC" tone="info" />
        <Stat value="$2.99-3.29" label="Corredor specialty" />
        <Stat value="45%+" label="Margen bruto objetivo" tone="success" />
        <Stat value="$15K max" label="Presupuesto validacion" tone="warning" />
      </Grid>

      <H2>Corredor de precio por segmento (USD/barra)</H2>
      <BarChart
        categories={["Value", "Mainstream", "Natural", "Super-premium"]}
        series={[{ name: "Precio medio", data: [1.19, 1.99, 2.99, 3.74] }]}
        valuePrefix="$"
        height={200}
        referenceLines={[{ value: 3.14, label: "Target", tone: "warning" }]}
      />
      <Text size="small" tone="tertiary">
        Fuente: IndexBox 2025-2026, elementalsuperfood.com · corte jul 2026.
      </Text>

      <H2>Posicionamiento competitivo</H2>
      <BarChart
        categories={["Directos lucuma", "Indirectos mainstream", "Polvo lucuma"]}
        series={[{ name: "Referencias observadas", data: [3, 12, 44], tone: "info" }]}
        horizontal
        height={140}
        showValues
      />

      <H2>Producto recomendado</H2>
      <Card>
        <CardHeader>{PRODUCT}</CardHeader>
        <CardBody>
          <Text>
            Avena + 10-12% polvo de lucuma organica peruana + almendras + datiles. Vegan, sin azucar
            refinado. Sabor caramelo-andino como diferenciador sensorial.
          </Text>
        </CardBody>
      </Card>

      <H2>Competidores observados</H2>
      <Table
        headers={["Producto", "Formato", "Precio", "Canal", "Notas"]}
        rows={COMPETITORS}
        columnAlign={["left", "left", "right", "left", "left"]}
        striped
      />

      <Grid columns={2} gap={16}>
        <Stack gap={8}>
          <H2>Riesgos criticos</H2>
          <Table headers={["Riesgo", "Severidad", "Evidencia"]} rows={RISKS} striped />
        </Stack>
        <Stack gap={8}>
          <H2>Claims regulatorios</H2>
          <Table headers={["Claim", "Estado", "Notas"]} rows={CLAIMS} striped />
        </Stack>
      </Grid>

      <H2>Trazabilidad por agente</H2>
      {AGENT_TRACE.map((row) => (
        <CollapsibleSection
          key={row[0]}
          title={row[0]}
          leading={<Swatch color="blue" />}
          trailing={row[2]}
        >
          <Text tone="secondary">{row[1]}</Text>
        </CollapsibleSection>
      ))}

      <Grid columns={2} gap={16}>
        <Stack gap={8}>
          <H2>Plan de 30 dias</H2>
          <Table headers={["Semana", "Accion"]} rows={PLAN_30} striped />
        </Stack>
        <Stack gap={8}>
          <H2>Experimentos requeridos</H2>
          <Table headers={["ID", "Descripcion"]} rows={EXPERIMENTS} striped />
        </Stack>
      </Grid>

      <Callout tone="danger" title="Hecho invalidante">
        Si co-packing + lucuma B2B eleva COGS por encima de $1.80/barra, el corredor premium no
        sostiene margen bruto de 45%+ en DTC.
      </Callout>

      <Divider />
      <Text size="small" tone="quaternary">
        Analisis CLI Product Intelligence Orchestrator · jul 2026
      </Text>
    </Stack>
  );
}
