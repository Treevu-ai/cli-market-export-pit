import { Stack, H1, Text, Table, Stat, Grid, Callout, BarChart } from "cursor/canvas";

export default function GoldenLucumaCrunchBom() {
  return (
    <Stack gap={16} style={{ padding: 16 }}>
      <H1>Golden Lucuma Crunch - Formulacion y BOM</H1>
      <Text tone="secondary">Concepto diferenciador v0.1 · barra 50g · vegan · clean-label</Text>

      <Callout tone="warning" title="Datos estimados">
        BOM hipotetico. Validar costos lucuma B2B y MO co-packer antes de gate go/no-go.
      </Callout>

      <Grid columns={2} gap={12}>
        <Stat value="50 g" label="Peso neto" />
        <Stat value="11%" label="Lucuma en masa" tone="info" />
        <Stat value="$0.32" label="COGS ingredientes" tone="warning" />
        <Stat value="$0.68" label="COGS total mid" tone="warning" />
      </Grid>

      <Text weight="semibold">Formulacion (% masa, 50g por barra)</Text>
      <Table
        headers={["Ingrediente", "%", "g", "Funcion"]}
        rows={[
          ["Avena GF", "36.0", "18.0", "Base"],
          ["Polvo lucuma organica", "11.0", "5.5", "Diferenciador"],
          ["Almendras", "13.0", "6.5", "Proteina"],
          ["Pasta datil", "11.0", "5.5", "Edulcorante"],
          ["Aceite coco", "5.0", "2.5", "Cohesion"],
          ["Semillas calabaza", "6.0", "3.0", "Crunch"],
          ["Semillas girasol", "5.0", "2.5", "Textura"],
          ["Quinoa inflada", "4.0", "2.0", "Ligereza"],
          ["Chia + linaza", "4.0", "2.0", "Fibra"],
          ["Vainilla + canela + sal", "1.0", "0.5", "Sabor"],
        ]}
        striped
      />

      <Text weight="semibold">Costo ingredientes por componente (USD/barra)</Text>
      <BarChart
        categories={["Avena", "Lucuma", "Almendras", "Datil", "Otros"]}
        series={[{ name: "USD", data: [0.04, 0.07, 0.07, 0.02, 0.12], tone: "info" }]}
        valuePrefix="$"
        height={160}
        showValues
      />

      <Text weight="semibold">Estructura COGS vs precio DTC $3.49</Text>
      <BarChart
        categories={["Ingredientes", "Empaque", "Co-pack", "Margen"]}
        series={[{ name: "USD", data: [0.32, 0.14, 0.22, 2.81], tone: "info" }]}
        valuePrefix="$"
        height={160}
        showValues
      />

      <Text weight="semibold">Objetivos nutricionales (50g)</Text>
      <Table
        headers={["Nutriente", "Objetivo"]}
        rows={[
          ["Calorias", "210-230 kcal"],
          ["Proteina", "6-8 g"],
          ["Fibra", "4-6 g"],
          ["Azucares", "8-11 g"],
          ["Sodio", "menos de 120 mg"],
        ]}
        striped
      />

      <Text weight="semibold">Alergenos</Text>
      <Table
        headers={["Alergeno", "Estado"]}
        rows={[
          ["Tree nuts (almonds)", "Contiene"],
          ["Gluten", "Sin gluten (cert. GF oats)"],
          ["Peanuts", "Puede contener"],
        ]}
        striped
      />

      <Text weight="semibold">BOM empaque</Text>
      <Table
        headers={["Componente", "Costo est."]}
        rows={[
          ["Flow-wrap PCR", "$0.06-0.09"],
          ["Carton 12-count", "$0.08-0.12"],
          ["Etiqueta FDA", "$0.04-0.07"],
        ]}
        striped
      />

      <Text weight="semibold">Checklist pre-prototipo</Text>
      <Table
        headers={["Item", "Estado"]}
        rows={[
          ["COA lucuma Peru", "Pendiente"],
          ["FSVP documentation", "Pendiente"],
          ["Sensory panel n=30", "Pendiente"],
          ["Pilot batch 50 uds", "Pendiente"],
          ["Nutrition Facts lab", "Pendiente"],
        ]}
        striped
      />
    </Stack>
  );
}
