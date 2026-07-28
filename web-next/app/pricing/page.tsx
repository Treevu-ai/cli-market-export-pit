"use client";

import { AppHeader } from "@/components/app-header";
import { useLocale } from "@/lib/i18n/locale-context";
import { es } from "@/lib/i18n/dictionaries/es";
import { en } from "@/lib/i18n/dictionaries/en";

const PLANS_BY_LOCALE = { es: es.pricing.plans, en: en.pricing.plans };

const PLAN_HREFS = [
  { href: "/signup" },
  { href: "mailto:hello@cli-market.dev?subject=CLI%20Market%20PIT%20Pro", highlighted: true },
  { href: "mailto:hello@cli-market.dev?subject=CLI%20Market%20PIT%20Enterprise" },
];

export default function PricingPage() {
  const { t, locale } = useLocale();
  const plans = PLANS_BY_LOCALE[locale];
  const PLANS = plans.map((plan, i) => ({
    ...plan,
    cta: { label: plan.cta, href: PLAN_HREFS[i].href },
    highlighted: PLAN_HREFS[i].highlighted,
  }));
  return (
    <>
      <AppHeader />
      <main className="min-h-screen bg-background px-6 py-24 text-foreground">
      <div className="mx-auto max-w-5xl text-center">
        <h1 className="font-display text-4xl lg:text-5xl">{t("pricing.title")}</h1>
        <p className="mt-4 text-muted-foreground">
          {t("pricing.subtitle")}
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
    </>
  );
}
