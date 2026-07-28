const PLANS = [
  {
    name: "Free",
    price: "$0",
    period: "",
    limit: "5 análisis/mes",
    features: ["Todas las fuentes públicas (ciencia, comercio exterior, tendencias)", "Historial de runs"],
    cta: { label: "Crear cuenta gratis", href: "/signup" },
  },
  {
    name: "Pro",
    price: "$49",
    period: "/mes",
    limit: "50 análisis/mes",
    features: ["Todo lo de Free", "Dominio Commerce (CLI Market Pro)", "Soporte prioritario"],
    cta: { label: "Crear cuenta gratis", href: "/signup" },
    highlighted: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    limit: "Volumen a medida",
    features: ["Todo lo de Pro", "Integración con tu catálogo", "SLA y soporte dedicado"],
    cta: { label: "Contáctanos", href: "mailto:hola@treevu.ai?subject=CLI%20Market%20PIT%20Enterprise" },
  },
];

export default function PricingPage() {
  return (
    <main className="min-h-screen bg-background px-6 py-24 text-foreground">
      <div className="mx-auto max-w-5xl text-center">
        <h1 className="font-display text-4xl lg:text-5xl">Precios</h1>
        <p className="mt-4 text-muted-foreground">
          Valida oportunidades de exportación antes de invertir. Cancela cuando quieras.
        </p>
      </div>
      <div className="mx-auto mt-16 grid max-w-5xl gap-6 md:grid-cols-3">
        {PLANS.map((plan) => (
          <div
            key={plan.name}
            className={`flex flex-col border p-8 ${
              plan.highlighted ? "border-[#64ffda] bg-[#64ffda]/5" : "border-foreground/10 bg-foreground/[0.02]"
            }`}
          >
            <h2 className="font-display text-xl">{plan.name}</h2>
            <div className="mt-4 flex items-baseline gap-1">
              <span className="font-display text-4xl">{plan.price}</span>
              <span className="text-sm text-muted-foreground">{plan.period}</span>
            </div>
            <p className="mt-2 text-sm font-mono text-[#64ffda]">{plan.limit}</p>
            <ul className="mt-6 flex-1 space-y-3 text-sm text-muted-foreground">
              {plan.features.map((feature) => (
                <li key={feature} className="flex gap-2">
                  <span className="text-[#64ffda]">✓</span>
                  {feature}
                </li>
              ))}
            </ul>
            <a
              href={plan.cta.href}
              className={`mt-8 rounded-full px-5 py-3 text-center text-sm font-medium ${
                plan.highlighted
                  ? "bg-[#64ffda] text-[#0a192f]"
                  : "border border-foreground/20 text-foreground hover:border-[#64ffda]/60"
              }`}
            >
              {plan.cta.label}
            </a>
          </div>
        ))}
      </div>
    </main>
  );
}
