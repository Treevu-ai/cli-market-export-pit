import type { DomainScore } from "@/lib/pit-api";

const DOMAIN_LABELS: Record<string, string> = {
  science: "Ciencia",
  patent: "Patentes",
  trend: "Tendencias",
  trade: "Comercio exterior",
  commerce: "Retail / góndola",
  regulatory: "Regulatorio",
  sustainability: "Sostenibilidad",
  technology_scout: "I+D y proyectos",
};

type Props = {
  dimensions: Record<string, DomainScore>;
};

export function DomainGrid({ dimensions }: Props) {
  const entries = Object.entries(dimensions || {});
  if (!entries.length) {
    return <p className="text-sm text-muted-foreground">Sin dominios puntuados en este run.</p>;
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
      {entries.map(([domain, data]) => {
        const pct = Math.max(0, Math.min(100, Number(data.score) || 0));
        return (
          <div
            key={domain}
            className="border border-foreground/10 bg-foreground/[0.02] p-4 transition-colors hover:border-[#64ffda]/60"
          >
            <div className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
              {DOMAIN_LABELS[domain] || domain}
            </div>
            <div className="mt-1 font-display text-2xl">{data.score ?? "—"}</div>
            <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-foreground/10">
              <div className="h-full rounded-full bg-[#64ffda]" style={{ width: `${pct}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
