"use client";

import { useEffect, useState, useRef } from "react";
import { Grape, FlaskConical, Wheat, Leaf, Citrus, Sprout, Coffee, Wine, Pill, Cherry, Nut, Flower2, Flame, CircleDot, Sparkles, TreeDeciduous } from "lucide-react";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion";
import { useLocale } from "@/lib/i18n/locale-context";

type Family =
  | "frutasFrescas"
  | "especiasAromaticas"
  | "granosSemillas"
  | "vegetalesRaices"
  | "bebidasEstimulantes"
  | "derivadosFuncionales";

type Integration = {
  name: string;
  category: string;
  query: string;
  market: string;
  Icon: typeof Grape;
  family: Family;
  hsCode: string | null;
  exclusive: boolean | null;
};

const integrations: Integration[] = [
  { name: "Arándano", category: "PE→US", query: "arándano orgánico", market: "US", Icon: Grape, family: "frutasFrescas", hsCode: "081040", exclusive: true },
  { name: "Cacao", category: "PE→US", query: "cacao alto flavanol", market: "US", Icon: FlaskConical, family: "derivadosFuncionales", hsCode: "180610", exclusive: true },
  { name: "Quinua", category: "PE→EU", query: "quinua orgánica", market: "EU", Icon: Wheat, family: "granosSemillas", hsCode: "100850", exclusive: true },
  { name: "Palta", category: "PE→US", query: "palta hass", market: "US", Icon: Leaf, family: "frutasFrescas", hsCode: "080440", exclusive: true },
  { name: "Mango", category: "PE→US", query: "mango kent", market: "US", Icon: Citrus, family: "frutasFrescas", hsCode: "080450", exclusive: true },
  { name: "Funcionales", category: "Claims", query: "bebida funcional antioxidante", market: "US", Icon: Sprout, family: "derivadosFuncionales", hsCode: null, exclusive: null },
  { name: "Café", category: "PE→US", query: "café tostado especial", market: "US", Icon: Coffee, family: "bebidasEstimulantes", hsCode: "090121", exclusive: true },
  { name: "Uva", category: "PE→US", query: "uva red globe", market: "US", Icon: Grape, family: "frutasFrescas", hsCode: "080610", exclusive: true },
  { name: "Mandarina", category: "PE→US", query: "mandarina w murcott", market: "US", Icon: Citrus, family: "frutasFrescas", hsCode: "080520", exclusive: true },
  { name: "Pisco", category: "PE→US", query: "pisco puro quebranta", market: "US", Icon: Wine, family: "bebidasEstimulantes", hsCode: "220820", exclusive: true },
  { name: "Maca", category: "PE→US", query: "maca negra gelatinizada", market: "US", Icon: Pill, family: "vegetalesRaices", hsCode: "121190", exclusive: true },
  { name: "Kiwicha", category: "PE→US", query: "kiwicha organica", market: "US", Icon: Wheat, family: "granosSemillas", hsCode: "100890", exclusive: true },
  { name: "Camu camu", category: "PE→US", query: "camu camu pulpa congelada", market: "US", Icon: Cherry, family: "derivadosFuncionales", hsCode: "081190", exclusive: true },
  { name: "Chía", category: "PE→US", query: "semillas de chia organica", market: "US", Icon: Nut, family: "granosSemillas", hsCode: "120799", exclusive: true },
  { name: "Alcachofa", category: "PE→US", query: "alcachofa en conserva", market: "US", Icon: Flower2, family: "vegetalesRaices", hsCode: "070991", exclusive: true },
  { name: "Ají panca", category: "PE→US", query: "ají panca deshidratado", market: "US", Icon: Flame, family: "especiasAromaticas", hsCode: "090421", exclusive: true },
  { name: "Espárrago", category: "PE→US", query: "espárrago fresco", market: "US", Icon: Sprout, family: "vegetalesRaices", hsCode: "070920", exclusive: true },
  { name: "Banano", category: "PE→EU", query: "banano orgánico", market: "EU", Icon: Leaf, family: "frutasFrescas", hsCode: "080390", exclusive: true },
  { name: "Limón", category: "PE→US", query: "limón sutil", market: "US", Icon: Citrus, family: "frutasFrescas", hsCode: "080550", exclusive: true },
  { name: "Páprika", category: "PE→US", query: "paprika molida", market: "US", Icon: Flame, family: "especiasAromaticas", hsCode: "090422", exclusive: true },
  { name: "Aguaymanto", category: "PE→US", query: "aguaymanto deshidratado", market: "US", Icon: CircleDot, family: "frutasFrescas", hsCode: "081090", exclusive: false },
  { name: "Cúrcuma", category: "PE→US", query: "curcuma en polvo organico", market: "US", Icon: Sparkles, family: "especiasAromaticas", hsCode: "091030", exclusive: true },
  { name: "Higo", category: "PE→US", query: "higos frescos", market: "US", Icon: TreeDeciduous, family: "frutasFrescas", hsCode: "080420", exclusive: true },
  { name: "Maracuyá", category: "PE→EU", query: "pulpa de maracuya", market: "EU", Icon: Citrus, family: "derivadosFuncionales", hsCode: "200899", exclusive: false },
];

const FAMILY_ORDER: Family[] = [
  "frutasFrescas",
  "derivadosFuncionales",
  "especiasAromaticas",
  "granosSemillas",
  "vegetalesRaices",
  "bebidasEstimulantes",
];

function HsQualityBadge({ exclusive, t }: { exclusive: boolean; t: (key: string) => string }) {
  return (
    <span
      className={`absolute top-3 left-3 text-[9px] font-mono px-2 py-0.5 rounded-sm ${
        exclusive ? "bg-[#64ffda]/15 text-[#64ffda]" : "bg-foreground/10 text-muted-foreground"
      }`}
    >
      {t(exclusive ? "integrations.hsQuality.exclusive" : "integrations.hsQuality.basket")}
    </span>
  );
}

export function IntegrationsSection() {
  const { t } = useLocale();
  const [isVisible, setIsVisible] = useState(false);
  const [hoveredName, setHoveredName] = useState<string | null>(null);
  const [mousePos, setMousePos] = useState<{ x: number; y: number } | null>(null);
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setIsVisible(true);
      },
      { threshold: 0.1 }
    );

    if (sectionRef.current) observer.observe(sectionRef.current);
    return () => observer.disconnect();
  }, []);

  const familyGroups = FAMILY_ORDER.map((family) => ({
    family,
    items: integrations.filter((integration) => integration.family === family),
  }));

  return (
    <section id="integrations" ref={sectionRef} className="relative overflow-hidden">

      {/* Header — centré verticalement sur l'image */}
      <div className="relative z-10 pt-32 lg:pt-40 text-center">
        <span className={`inline-flex items-center gap-4 text-sm font-mono text-muted-foreground mb-8 transition-all duration-700 justify-center ${
          isVisible ? "opacity-100" : "opacity-0"
        }`}>
          <span className="w-12 h-px bg-foreground/20" />
          {t("integrations.eyebrow")}
          <span className="w-12 h-px bg-foreground/20" />
        </span>

        <h2 className={`text-6xl md:text-7xl lg:text-[128px] font-display tracking-tight leading-[0.9] transition-all duration-1000 ${
          isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
        }`}>
          {t("integrations.headline")}
          <br />
          <span className="text-muted-foreground">{t("integrations.headlineAccent")}</span>
        </h2>

        <p className={`mt-8 text-xl text-muted-foreground leading-relaxed max-w-lg mx-auto transition-all duration-1000 delay-100 ${
          isVisible ? "opacity-100" : "opacity-0"
        }`}>
          {t("integrations.lead")}
        </p>
      </div>

      {/* Integration families */}
      <div className="relative z-10 mt-16 lg:mt-24 max-w-[1400px] mx-auto px-6 lg:px-12">
        <Accordion
          type="multiple"
          defaultValue={["frutasFrescas"]}
          className={`mb-16 transition-all duration-1000 ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
        >
          {familyGroups.map(({ family, items }) => (
            <AccordionItem key={family} value={family} className="border-foreground/10">
              <AccordionTrigger className="py-6 hover:no-underline">
                <span className="flex flex-1 flex-wrap items-baseline gap-x-4 gap-y-1 text-left">
                  <span className="font-display text-2xl lg:text-3xl tracking-tight">
                    {t(`integrations.families.${family}.name`)}
                  </span>
                  <span className="text-xs font-mono px-2 py-0.5 bg-foreground/10 text-muted-foreground rounded-sm">
                    {items.length}
                  </span>
                  <span className="text-sm text-muted-foreground font-normal">
                    {t(`integrations.families.${family}.description`)}
                  </span>
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 pt-2">
                  {items.map((integration) => (
                    <a
                      key={integration.name}
                      href={`/analyze/?query=${encodeURIComponent(integration.query)}&market=${integration.market}`}
                      className={`group relative overflow-hidden p-6 lg:p-7 border transition-all duration-500 block ${
                        hoveredName === integration.name
                          ? "border-foreground bg-foreground/[0.04] scale-[1.02]"
                          : "border-foreground/10 hover:border-foreground/30"
                      }`}
                      onMouseEnter={(e) => {
                        setHoveredName(integration.name);
                        const rect = e.currentTarget.getBoundingClientRect();
                        setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
                      }}
                      onMouseMove={(e) => {
                        const rect = e.currentTarget.getBoundingClientRect();
                        setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
                      }}
                      onMouseLeave={() => {
                        setHoveredName(null);
                        setMousePos(null);
                      }}
                    >
                      {/* Cursor-following halo */}
                      {hoveredName === integration.name && mousePos && (
                        <span
                          aria-hidden="true"
                          className="pointer-events-none absolute inset-0 z-0"
                          style={{
                            background: `radial-gradient(200px circle at ${mousePos.x}px ${mousePos.y}px, rgba(255,255,255,0.1) 0%, transparent 70%)`,
                          }}
                        />
                      )}

                      {/* HS evidence-quality badge */}
                      {integration.exclusive !== null && (
                        <HsQualityBadge exclusive={integration.exclusive} t={t} />
                      )}

                      {/* Category tag */}
                      <span className={`absolute top-3 right-3 text-[10px] font-mono px-2 py-0.5 transition-colors ${
                        hoveredName === integration.name
                          ? "bg-foreground text-background"
                          : "bg-foreground/10 text-muted-foreground"
                      }`}>
                        {integration.category}
                      </span>

                      {/* Icon */}
                      <div className={`w-10 h-10 mb-6 mt-4 flex items-center justify-center transition-colors ${
                        hoveredName === integration.name ? "text-white" : "text-foreground/60"
                      }`}>
                        <integration.Icon className="w-6 h-6" />
                      </div>

                      <span className="font-medium block">{t(`integrations.names.${integration.name}`)}</span>

                      {/* Animated underline */}
                      <div className="absolute bottom-0 left-0 right-0 h-px bg-foreground/20 overflow-hidden">
                        <div className={`h-full bg-foreground transition-all duration-500 ${
                          hoveredName === integration.name ? "w-full" : "w-0"
                        }`} />
                      </div>
                    </a>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>

        {/* Bottom row */}
        <div className={`flex flex-wrap items-center justify-between gap-8 pt-12 border-t border-foreground/10 transition-all duration-1000 delay-500 pb-32 lg:pb-40 ${
          isVisible ? "opacity-100" : "opacity-0"
        }`}>
          <div className="flex flex-wrap gap-12">
            {[
              { value: String(integrations.length), label: t("integrations.statCategoriesLabel") },
              { value: "ISO-2", label: t("integrations.statMarketLabel") },
              { value: t("integrations.statQueryValue"), label: t("integrations.statQueryLabel") },
            ].map((stat) => (
              <div key={stat.label} className="flex items-baseline gap-3">
                <span className="text-3xl font-display">{stat.value}</span>
                <span className="text-sm text-muted-foreground">{stat.label}</span>
              </div>
            ))}
          </div>

          <a href="/analyze/" className="group inline-flex items-center gap-2 text-sm font-mono text-muted-foreground hover:text-foreground transition-colors">
            {t("integrations.otherProduct")}
            <span className="group-hover:translate-x-1 transition-transform">&rarr;</span>
          </a>
        </div>
      </div>
    </section>
  );
}
