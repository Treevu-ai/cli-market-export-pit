export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-background px-6 py-24 text-foreground">
      <div className="mx-auto max-w-2xl">
        <h1 className="font-display text-4xl">Política de privacidad</h1>
        <p className="mt-2 text-sm text-muted-foreground">Última actualización: julio 2026</p>

        <div className="mt-10 space-y-8 text-sm leading-relaxed text-muted-foreground">
          <section>
            <h2 className="mb-2 font-display text-lg text-foreground">Qué datos recolectamos</h2>
            <p>
              Al crear una cuenta guardamos tu email y una versión con hash (bcrypt) de tu contraseña —
              nunca la contraseña en texto plano. Guardamos también tu plan de suscripción y un contador
              de uso mensual (cuántos análisis has corrido este mes) para aplicar los límites de tu plan.
            </p>
          </section>

          <section>
            <h2 className="mb-2 font-display text-lg text-foreground">Qué guardamos de cada análisis</h2>
            <p>
              Cada consulta que ejecutas (producto, mercado objetivo, aplicación) y la evidencia recolectada
              de fuentes públicas (científicas, comercio exterior, góndola de retail) se guarda de forma
              trazable para que puedas volver a ver el reporte. No compartimos tus consultas con terceros.
            </p>
          </section>

          <section>
            <h2 className="mb-2 font-display text-lg text-foreground">Cookies de sesión</h2>
            <p>
              Usamos una única cookie httpOnly (<code>pit_session</code>) para mantener tu sesión iniciada.
              No usamos cookies de tracking ni de publicidad de terceros.
            </p>
          </section>

          <section>
            <h2 className="mb-2 font-display text-lg text-foreground">Terceros que consultamos</h2>
            <p>
              El motor PIT enriquece cada análisis con datos públicos de fuentes como OpenAlex, Crossref,
              PubMed, GDELT, UN Comtrade, CLI Market y BCRP, entre otras. Estas consultas no incluyen tus
              datos personales — solo el producto/mercado que estás analizando.
            </p>
          </section>

          <section>
            <h2 className="mb-2 font-display text-lg text-foreground">Tus derechos</h2>
            <p>
              Puedes pedir la eliminación de tu cuenta y tus datos en cualquier momento escribiendo a{" "}
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
