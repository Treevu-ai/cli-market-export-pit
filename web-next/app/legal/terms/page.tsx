export default function TermsPage() {
  return (
    <main className="min-h-screen bg-background px-6 py-24 text-foreground">
      <div className="mx-auto max-w-2xl">
        <h1 className="font-display text-4xl">Términos de servicio</h1>
        <p className="mt-2 text-sm text-muted-foreground">Última actualización: julio 2026</p>

        <div className="mt-10 space-y-8 text-sm leading-relaxed text-muted-foreground">
          <section>
            <h2 className="mb-2 font-display text-lg text-foreground">El servicio</h2>
            <p>
              CLI Market PIT es una herramienta de research que combina evidencia científica, de comercio
              exterior y de retail para ayudarte a evaluar oportunidades de exportación. Los resultados son
              apoyo a tu decisión, no asesoría de inversión ni garantía de éxito comercial.
            </p>
          </section>

          <section>
            <h2 className="mb-2 font-display text-lg text-foreground">Planes y límites de uso</h2>
            <p>
              El plan Free incluye 5 análisis por mes. Los planes de pago (Pro, Enterprise) amplían ese
              límite según lo publicado en{" "}
              <a href="/pricing" className="text-[#64ffda] hover:underline">
                /pricing
              </a>
              . Nos reservamos el derecho de ajustar límites y precios con aviso previo a los usuarios activos.
            </p>
          </section>

          <section>
            <h2 className="mb-2 font-display text-lg text-foreground">Uso aceptable</h2>
            <p>
              No debes usar la cuenta de otra persona, intentar evadir los límites de uso, ni usar el
              servicio para actividades ilegales.
            </p>
          </section>

          <section>
            <h2 className="mb-2 font-display text-lg text-foreground">Sin garantía</h2>
            <p>
              El servicio se ofrece "tal cual". La evidencia mostrada proviene de fuentes públicas de
              terceros — hacemos lo posible por que sea trazable y verificable, pero no garantizamos su
              exactitud o vigencia absoluta.
            </p>
          </section>

          <section>
            <h2 className="mb-2 font-display text-lg text-foreground">Contacto</h2>
            <p>
              Preguntas sobre estos términos:{" "}
              <a href="mailto:hello@cli-market.dev" className="text-[#64ffda] hover:underline">
                hello@cli-market.dev
              </a>
              .
            </p>
          </section>
        </div>
      </div>
    </main>
  );
}
