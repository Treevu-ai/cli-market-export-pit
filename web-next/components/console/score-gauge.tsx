"use client";

import { useEffect, useState } from "react";

const CIRCUMFERENCE = 263.9;

type Props = {
  score: number | null;
};

export function ScoreGauge({ score }: Props) {
  const [offset, setOffset] = useState(CIRCUMFERENCE);

  useEffect(() => {
    const pct = Math.max(0, Math.min(100, Number(score) || 0));
    const target = CIRCUMFERENCE - (pct / 100) * CIRCUMFERENCE;
    const id = requestAnimationFrame(() => setOffset(target));
    return () => cancelAnimationFrame(id);
  }, [score]);

  return (
    <div className="relative h-28 w-28 shrink-0">
      <svg viewBox="0 0 100 100" width="112" height="112" className="-rotate-90">
        <circle cx="50" cy="50" r="42" fill="none" stroke="currentColor" strokeWidth="8" className="text-foreground/10" />
        <circle
          cx="50"
          cy="50"
          r="42"
          fill="none"
          stroke="#64ffda"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 1.1s cubic-bezier(0.16, 1, 0.3, 1)" }}
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center font-display text-3xl tracking-tight">
        {score ?? "—"}
      </span>
    </div>
  );
}
