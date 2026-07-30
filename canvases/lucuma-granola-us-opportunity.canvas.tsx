import { Stack, H1, Text, Table, Stat, Grid, Callout, BarChart } from "cursor/canvas";

export default function LucumaGranolaUsOpportunity() {
  return (
    <Stack gap={16} style={{ padding: 16 }}>
      <H1>Barras de granola con lucuma - EE.UU.</H1>
      <Text tone="secondary">Ficha de Oportunidad · CONDITIONAL GO · 30 jul 2026</Text>

      <Callout tone="warning" title="Decision ejecutiva: CONDITIONAL GO">
        Oportunidad plausible en segmento premium/superfood. Avanzar solo con experimentos
        reversibles de hasta $15K antes de produccion comercial.
      </Callout>

      <Grid columns={2} gap={12}>
        <Stat value="$3.49" label="Precio DTC" tone="info" />
        <Stat value="$2.99-3.29" label="Corredor specialty" />
        <Stat value="45%+" label="Margen objetivo" tone="success" />
        <Stat value="$15K" label="Presupuesto validacion" tone="warning" />
      </Grid>

      <Text weight="semibold">Corredor de precio (USD/barra)</Text>
      <BarChart
        categories={["Value", "Mainstream", "Natural", "Super-premium"]}
        series={[{ name: "Precio", data: [1.19, 1.99, 2.99, 3.74] }]}
        valuePrefix="$"
        height={180}
      />

      <Text weight="semibold">Producto recomendado</Text>
      <Text>
        Golden Lucuma Crunch 50g: avena + 10-12% lucuma organica peruana + almendras + datiles.
        Vegan, sin azucar refinado, sabor caramelo-andino.
      </Text>

      <Text weight="semibold">Competidores observados</Text>
      <Table
        headers={["Producto", "Precio", "Canal"]}
        rows={[
          ["Elemental Lucuma Seedbar", "$3.31", "DTC"],
          ["Foundation Lucuma Cacao", "$9.25", "Specialty"],
          ["Amaru Lucuma Granola", "$8+", "Import"],
          ["KIND / Nature Valley", "$1.69-2.29", "Mass retail"],
        ]}
        striped
      />

      <Text weight="semibold">Riesgos criticos</Text>
      <Table
        headers={["Riesgo", "Severidad"]}
        rows={[
          ["Categoria saturada", "Alta"],
          ["Baja awareness lucuma", "Alta"],
          ["Economia unitaria sin cerrar", "Media"],
          ["Claims no sustentados", "Media"],
          ["FSVP importacion Peru", "Media"],
        ]}
        striped
      />

      <Text weight="semibold">Plan 30 dias</Text>
      <Table
        headers={["Semana", "Accion"]}
        rows={[
          ["1", "Sourcing lucuma organica Peru"],
          ["2", "Cotizacion co-packer US"],
          ["3", "Revision etiqueta FDA + FSVP"],
          ["4", "Prototipo 50 barras + taste test"],
        ]}
        striped
      />

      <Callout tone="danger" title="Hecho invalidante">
        Si COGS supera $1.80/barra, el corredor premium no sostiene margen 45%+ en DTC.
      </Callout>
    </Stack>
  );
}
