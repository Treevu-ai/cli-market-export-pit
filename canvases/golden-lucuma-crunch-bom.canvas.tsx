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
  H3,
  Stack,
  Stat,
  Swatch,
  Table,
  Text,
} from "cursor/canvas";

const NET_WEIGHT_G = 50;

const FORMULATION = [
  ["Avena enrollada cert. GF", "36.0", "18.0", "Base / crunch", "US supplier"],
  ["Polvo de lucuma organica", "11.0", "5.5", "Diferenciador / dulzor", "Peru — FSVP"],
  ["Almendras laminadas", "13.0", "6.5", "Proteina / textura", "US / CA"],
  ["Pasta de datil Medjool", "11.0", "5.5", "Edulcorante / aglutinante", "US"],
  ["Aceite de coco virgen", "5.0", "2.5", "Cohesion", "US"],
  ["Semillas de calabaza", "6.0", "3.0", "Crunch", "US"],
  ["Semillas de girasol", "5.0", "2.5", "Textura", "US"],
  ["Quinoa inflada", "4.0", "2.0", "Ligereza", "US / BO"],
  ["Chia", "2.0", "1.0", "Fibra", "US"],
  ["Linaza molida", "2.0", "1.0", "Fibra", "US / CA"],
  ["Extracto de vainilla", "0.2", "0.1", "Aroma", "US"],
  ["Canela molida", "0.3", "0.15", "Aroma", "US"],
  ["Sal marina", "0.5", "0.25", "Balance", "US"],
];

const INGREDIENT_COST_USD = [
  ["Avena GF", "0.04"],
  ["Lucuma org.", "0.07"],
  ["Almendras", "0.07"],
  ["Datil", "0.02"],
  ["Coco + semillas + otros", "0.12"],
];

const PACKAGING_BOM = [
  ["Flow-wrap film PCR", "1/barra", "$0.06-0.09"],
  ["Carton 12-count FSC", "1/12 barras", "$0.08-0.12"],
  ["Etiqueta FDA", "1 unidad", "$0.04-0.07"],
  ["Master case 48 uds", "1/48 barras", "$0.03-0.05"],
];

const NUTRITION_TARGETS = [
  ["Calorias", "210-230 kcal"],
  ["Proteina", "6-8 g"],
  ["Grasa total", "10-12 g"],
  ["Fibra dietetica", "4-6 g"],
  ["Azucares totales", "8-11 g"],
  ["Sodio", "menos de 120 mg"],
];

const ALLERGENS = [
  ["Tree nuts (almonds)", "Contiene"],
  ["Gluten", "Sin gluten (cert. GF oats)"],
  ["Peanuts", "Puede contener (shared facility)"],
  ["Soy / milk / egg", "No intencional"],
];

const PROCESS_STEPS = [
  ["1. Pre-mezcla seca", "Tamizar avena, lucuma, canela, sal. Mezclar semillas y almendras."],
  ["2. Fase humeda", "Calentar aceite coco + pasta de datil a 45-55 C. Incorporar vainilla."],
  ["3. Aglomerado", "Mezcladora planetaria 3-5 min hasta masa homogenea."],
  ["4. Formado", "Prensa barra 50 g. Densidad objetivo 0.75-0.85 g/cm3."],
  ["5. Enfriamiento", "Banda enfriadora 8-12 min antes de envolver."],
  ["6. Envasado", "Flow-wrap + detector metales + etiquetado."],
];

const VARIANT_COMPARE = [
  ["Conservador", "8% lucuma", "45 g", "$2.79-2.99"],
  ["Golden Lucuma Crunch", "11% lucuma", "50 g", "$3.29-3.49"],
  ["Disruptivo", "18% lucuma + maca", "40 g", "$3.79-4.29"],
];

const CHECKLIST = [
  ["COA lucuma (micro, heavy metals)", "Supplier Peru", "Pendiente"],
  ["FSVP documentation", "Regulatory / QA", "Pendiente"],
  ["Sensory panel n=30", "R&D", "Pendiente"],
  ["Pilot batch 50 uds", "Co-packer", "Pendiente"],
  ["Nutrition Facts lab analysis", "Third-party lab", "Pendiente"],
  ["Label review FDA", "Consultor legal", "Pendiente"],
];

export default function GoldenLucumaCrunchBom() {
  const ingredientCogs = 0.32;
  const packagingMid = 0.14;
  const copackMid = 0.22;
  const totalCogs = ingredientCogs + packagingMid + copackMid;
  const dtcPrice = 3.49;
  const marginPct = Math.round(((dtcPrice - totalCogs) / dtcPrice) * 100);

  return (
    <Stack gap={20} style={{ padding: 20 }}>
      <H1>Golden Lucuma Crunch — Formulacion y BOM</H1>
      <Text tone="secondary">
        Concepto diferenciador v0.1 · barra {NET_WEIGHT_G} g · vegan · clean-label
      </Text>

      <Callout tone="warning" title="Datos estimados">
        BOM hipotetico para prototipo. Costos de lucuma B2B y MO co-packer requieren cotizacion real
        antes de gate go/no-go.
      </Callout>

      <Grid columns={2} gap={12}>
        <Stat value={NET_WEIGHT_G + " g"} label="Peso neto objetivo" />
        <Stat value="11%" label="Lucuma en masa" tone="info" />
        <Stat value={"~$" + ingredientCogs.toFixed(2)} label="COGS ingredientes (est.)" tone="warning" />
        <Stat value={"~$" + totalCogs.toFixed(2)} label="COGS total mid (est.)" tone="warning" />
      </Grid>

      <H2>Formulacion (% masa terminada)</H2>
      <Table
        headers={["Ingrediente", "%", "g/barra", "Funcion", "Origen"]}
        rows={FORMULATION}
        columnAlign={["left", "right", "right", "left", "left"]}
        striped
      />
      <Text size="small" tone="tertiary">
        Total 100% = {NET_WEIGHT_G} g. Lucuma en posicion 2-3 en etiqueta FDA (despues de avena).
      </Text>

      <H3>Costo estimado de ingredientes por barra (USD)</H3>
      <BarChart
        categories={INGREDIENT_COST_USD.map((r) => r[0])}
        series={[
          {
            name: "USD por barra",
            data: INGREDIENT_COST_USD.map((r) => parseFloat(r[1])),
            tone: "info",
          },
        ]}
        valuePrefix="$"
        height={180}
        showValues
      />
      <Text size="small" tone="tertiary">
        Rangos B2B hipoteticos small-batch US. Lucuma org. ~$12/kg FOB+freight.
      </Text>

      <H3>Estructura de COGS vs precio DTC ($3.49)</H3>
      <BarChart
        categories={["Ingredientes", "Empaque", "Co-pack MO", "Margen bruto"]}
        series={[
          {
            name: "USD por barra",
            data: [ingredientCogs, packagingMid, copackMid, dtcPrice - totalCogs],
            tone: "info",
          },
        ]}
        valuePrefix="$"
        height={180}
        showValues
      />
      <Text size="small" tone="tertiary">
        Margen bruto estimado: {marginPct}% antes de fulfillment y marketing. Umbral: COGS total
        mayor a $1.80 invalida tesis premium.
      </Text>

      <Grid columns={2} gap={16}>
        <Stack gap={8}>
          <H2>Objetivos nutricionales</H2>
          <Table headers={["Nutriente", "Objetivo (50 g)"]} rows={NUTRITION_TARGETS} striped />
        </Stack>
        <Stack gap={8}>
          <H2>Matriz de alergenos</H2>
          <Table headers={["Alergeno", "Estado"]} rows={ALLERGENS} striped />
        </Stack>
      </Grid>

      <H2>BOM de empaque</H2>
      <Table
        headers={["Componente", "Cantidad", "Costo est."]}
        rows={PACKAGING_BOM}
        columnAlign={["left", "left", "right"]}
        striped
      />

      <H2>Proceso de manufactura</H2>
      {PROCESS_STEPS.map((row) => (
        <CollapsibleSection key={row[0]} title={row[0]} leading={<Swatch color="blue" />}>
          <Text tone="secondary">{row[1]}</Text>
        </CollapsibleSection>
      ))}

      <H2>Comparativa de variantes</H2>
      <Table
        headers={["Variante", "Lucuma", "Formato", "Precio target"]}
        rows={VARIANT_COMPARE}
        striped
      />

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>Polvo lucuma organica</CardHeader>
          <CardBody>
            <Text tone="secondary">
              5.5 g/barra a ~$12/kg = ~$0.07 solo lucuma (~35% COGS ingredientes). Negociar FOB Peru
              + consolidacion maritima.
            </Text>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>MO minima co-packer</CardHeader>
          <CardBody>
            <Text tone="secondary">
              MO tipica US specialty bar: 2,000-5,000 uds/lote. A 3,000 uds y COGS $1.35 = capital
              ~$4,050 + setup $1,500-3,000.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <H2>Checklist pre-prototipo</H2>
      <Table headers={["Item", "Responsable", "Estado"]} rows={CHECKLIST} striped />

      <Divider />
      <Text size="small" tone="quaternary">
        BOM Golden Lucuma Crunch · jul 2026 · complementa ficha CONDITIONAL GO
      </Text>
    </Stack>
  );
}
