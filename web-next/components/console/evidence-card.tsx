"use client";

import { useLocale } from "@/lib/i18n/locale-context";

export type Trend = "growing" | "declining" | "stable";

const TREND_CLASSES: Record<Trend, string> = {
  growing: "bg-[#64ffda]/15 text-[#64ffda]",
  declining: "bg-[#e11d48]/15 text-[#e11d48]",
  stable: "bg-foreground/10 text-muted-foreground",
};

type Props = {
  title: string;
  stat?: { value: string | number; label: string };
  trend?: Trend;
  chips?: string[];
  emptyLabel: string;
};

export function EvidenceCard({ title, stat, trend, chips, emptyLabel }: Props) {
  const { t } = useLocale();
  const hasContent = stat != null || (chips && chips.length > 0);

  return (
    <div className="border border-foreground/10 bg-foreground/[0.02] p-4">
      <div className="mb-2 flex items-center justify-between gap-2">
        <strong className="font-display text-sm">{title}</strong>
        {trend && (
          <span className={`rounded-full px-2 py-0.5 font-mono text-[10px] uppercase ${TREND_CLASSES[trend]}`}>
            {t(`report.trend.${trend}`)}
          </span>
        )}
      </div>
      {hasContent ? (
        <>
          {stat && (
            <p className="text-sm text-muted-foreground">
              <strong className="text-foreground">{stat.value}</strong> {stat.label}
            </p>
          )}
          {chips && chips.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {chips.slice(0, 5).map((chip) => (
                <span
                  key={chip}
                  className="rounded-full border border-foreground/10 px-2 py-0.5 text-[11px] text-muted-foreground"
                >
                  {chip}
                </span>
              ))}
            </div>
          )}
        </>
      ) : (
        <p className="text-sm text-muted-foreground">{emptyLabel}</p>
      )}
    </div>
  );
}
