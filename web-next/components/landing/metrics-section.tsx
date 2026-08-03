"use client";

import { useEffect, useState, useRef } from "react";
import {
  BookOpen, Link2, Stethoscope, GraduationCap, Shield, Newspaper, Ship,
  BarChart3, Wheat, ShoppingCart, ShieldCheck, Scale, Gavel, Apple, Leaf,
  FlaskConical, Microscope, Award, Landmark,
} from "lucide-react";
import { useLocale } from "@/lib/i18n/locale-context";

// Illustrative example figures for the "high-flavanol cacao → EU" case,
// confirmed live 2026-07-30 against the fixed pipeline: 38 real science
// evidence records (OpenAlex/Crossref/PubMed/SemanticScholar), 11 PE
// retail stores compared, 136 real shelf products found (CLIMarket, PE).
// Static, not fetched live -- update manually if the case changes again.
const METRIC_VALUES = [38, 11, 136];

// All 19 live connectors as of 2026-08-03 (18 + LexAPI, added that day for
// regulatory search). Keep in sync with pitchavi/src/pit/api.py's
// _default_services() wiring -- update this list, infrastructure-section's
// NODE_COUNTS/"18" copy, and the lead text together when a connector is
// added or removed. Proper nouns, not translated across locales.
// Generic per-source icons (lucide-react) rather than real brand logos --
// no bundled assets for 19 external services, and several (WITS, USDA FAS,
// BCRP...) don't have a clean square mark to begin with.
const DATA_SOURCES = [
  { name: "OpenAlex", Icon: BookOpen },
  { name: "Crossref", Icon: Link2 },
  { name: "PubMed", Icon: Stethoscope },
  { name: "Semantic Scholar", Icon: GraduationCap },
  { name: "EPO OPS", Icon: Shield },
  { name: "GDELT", Icon: Newspaper },
  { name: "UN Comtrade", Icon: Ship },
  { name: "WITS", Icon: BarChart3 },
  { name: "USDA FAS", Icon: Wheat },
  { name: "CLI Market", Icon: ShoppingCart },
  { name: "OpenFDA", Icon: ShieldCheck },
  { name: "EUR-Lex", Icon: Scale },
  { name: "LexAPI", Icon: Gavel },
  { name: "FoodData Central", Icon: Apple },
  { name: "Climatiq", Icon: Leaf },
  { name: "CORDIS", Icon: FlaskConical },
  { name: "NIH RePORTER", Icon: Microscope },
  { name: "NSF Awards", Icon: Award },
  { name: "BCRP", Icon: Landmark },
];

function AnimatedNumber({ end, suffix = "", prefix = "" }: { end: number; suffix?: string; prefix?: string }) {
  const [count, setCount] = useState(0);
  const [isScrambling, setIsScrambling] = useState(true);
  const ref = useRef<HTMLDivElement>(null);
  const [hasAnimated, setHasAnimated] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasAnimated) {
          setHasAnimated(true);
          const duration = 2500;
          const startTime = performance.now();
          const animate = (currentTime: number) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 4);
            setCount(Math.floor(eased * end));
            setIsScrambling(progress < 0.8);
            if (progress < 1) requestAnimationFrame(animate);
          };
          requestAnimationFrame(animate);
        }
      },
      { threshold: 0.5 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [end, hasAnimated]);

  const displayValue = count.toLocaleString();

  return (
    <div ref={ref} className="inline-flex items-baseline">
      <span className="text-muted-foreground mr-1">{prefix}</span>
      <span className="tabular-nums">
        {displayValue.split("").map((char, i) => (
          <span
            key={i}
            className={`inline-block transition-all duration-150 ${
              isScrambling && char !== "," ? "blur-[1px]" : ""
            }`}
          >
            {char}
          </span>
        ))}
      </span>
      <span className="text-muted-foreground">{suffix}</span>
    </div>
  );
}

function GridBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const timeRef = useRef(0);
  const frameRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
    };
    resize();
    window.addEventListener("resize", resize);

    const render = () => {
      const rect = canvas.getBoundingClientRect();
      const width = rect.width;
      const height = rect.height;
      ctx.clearRect(0, 0, width, height);
      const gridSize = 60;
      const time = timeRef.current;
      for (let x = 0; x < width; x += gridSize) {
        for (let y = 0; y < height; y += gridSize) {
          const wave = Math.sin(x * 0.01 + y * 0.01 + time) * 0.5 + 0.5;
          const size = 1 + wave * 2;
          ctx.beginPath();
          ctx.arc(x, y, size, 0, Math.PI * 2);
          ctx.fillStyle = "rgba(255, 255, 255, 0.04)";
          ctx.fill();
        }
      }
      const pulseY = (time * 30) % height;
      ctx.strokeStyle = "rgba(255, 255, 255, 0.03)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, pulseY);
      ctx.lineTo(width, pulseY);
      ctx.stroke();
      timeRef.current += 0.02;
      frameRef.current = requestAnimationFrame(render);
    };
    render();

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(frameRef.current);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-none"
      style={{ width: "100%", height: "100%" }}
    />
  );
}

function DotGraph({
  color = "white",
  height = 32,
  freq1 = 0.35,
  freq2 = 0.12,
  freqT = 0.7,
  speed = 0.025,
  baseline = 0.3,
  amplitude = 0.5,
}: {
  color?: string;
  height?: number;
  freq1?: number;
  freq2?: number;
  freqT?: number;
  speed?: number;
  baseline?: number;
  amplitude?: number;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frameRef = useRef(0);
  const timeRef = useRef(Math.random() * 100);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const W = canvas.offsetWidth || 300;
    const H = height;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    ctx.scale(dpr, dpr);

    const render = () => {
      ctx.clearRect(0, 0, W, H);
      const t = timeRef.current;
      const cols = Math.floor(W / 8);

      for (let i = 0; i < cols; i++) {
        const raw = baseline + amplitude * Math.sin(i * freq1 + t) * Math.cos(i * freq2 + t * freqT);
        const v = Math.max(0, Math.min(1, raw));
        const dotY = H - 4 - v * (H - 8);
        const x = i * 8 + 4;
        const alpha = 0.15 + v * 0.55;
        const r = 1.5 + v * 1.2;

        ctx.beginPath();
        ctx.arc(x, dotY, r, 0, Math.PI * 2);
        ctx.fillStyle = color === "green"
          ? `rgba(100, 255, 218, ${alpha})`
          : `rgba(255, 255, 255, ${alpha})`;
        ctx.fill();
      }

      timeRef.current += speed;
      frameRef.current = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(frameRef.current);
  }, [color, height, freq1, freq2, freqT, speed, baseline, amplitude]);

  return (
    <canvas
      ref={canvasRef}
      style={{ width: "100%", height: `${height}px`, display: "block" }}
    />
  );
}

export function MetricsSection() {
  const { t } = useLocale();
  const metrics = METRIC_VALUES.map((value, i) => ({
    value,
    suffix: "",
    prefix: "",
    label: t(`metrics.items.${i}.label`),
    sublabel: t(`metrics.items.${i}.sublabel`),
  }));
  const [isVisible, setIsVisible] = useState(false);
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

  return (
    <section id="metrics" ref={sectionRef} className="relative py-32 lg:py-40 overflow-hidden">
      <GridBackground />

      <div className="relative z-10 max-w-[1400px] mx-auto px-6 lg:px-12">
        {/* Header */}
        <div className="grid lg:grid-cols-12 gap-8 mb-20 lg:mb-32">
          <div className="lg:col-span-8 lg:col-start-1">
            <div className="flex items-center gap-4 mb-6">
              <span className="flex items-center gap-2 px-3 py-1 bg-[#64ffda]/10 text-[#64ffda] text-xs font-mono">
                <span className="w-2 h-2 rounded-full bg-[#64ffda] animate-pulse" />
                {t("metrics.tag")}
              </span>
              <span className="text-sm font-mono text-muted-foreground">
                {t("metrics.tagDetail")}
              </span>
            </div>

            <h2 className={`text-6xl md:text-7xl lg:text-[140px] font-display tracking-tight leading-[0.95] transition-all duration-1000 ${
              isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
            }`}>
              {t("metrics.headline")}
              <br />
              <span className="text-muted-foreground">{t("metrics.headlineAccent")}</span>
            </h2>
          </div>
        </div>

        {/* Metrics grid */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Large metric — same top-to-bottom structure as the other two
              cards (sublabel, label, graph, THEN the number) so all three
              read consistently; this one used to show the number first. */}
          <div className={`lg:col-span-1 bg-foreground/[0.02] border border-foreground/10 p-8 flex flex-col items-start justify-between gap-6 transition-all duration-700 ${
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"
          }`}>
            <div className="w-full">
              <div className="text-sm text-muted-foreground font-mono mb-2">{metrics[0].sublabel}</div>
              <div className="text-lg text-foreground mb-3">{metrics[0].label}</div>
              <DotGraph color="white" height={36} freq1={0.28} freq2={0.09} freqT={0.5} speed={0.018} baseline={0.35} amplitude={0.55} />
            </div>
            <div className="text-4xl md:text-5xl lg:text-6xl font-display tracking-tight w-full whitespace-nowrap overflow-hidden">
              <AnimatedNumber end={metrics[0].value} suffix={metrics[0].suffix} prefix={metrics[0].prefix} />
            </div>
          </div>

          {/* Metrics */}
          {metrics.slice(1).map((metric, index) => (
            <div
              key={metric.label}
              className={`bg-foreground/[0.02] border border-foreground/10 p-8 flex flex-col items-start justify-between gap-6 transition-all duration-700 ${
                isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"
              }`}
              style={{ transitionDelay: `${(index + 1) * 100}ms` }}
            >
              <div className="w-full">
                <div className="text-sm text-muted-foreground font-mono mb-2">{metric.sublabel}</div>
                <div className="text-base text-foreground mb-3">{metric.label}</div>
                <DotGraph
                  color={index === 0 ? "green" : "white"}
                  height={24}
                  freq1={index === 0 ? 0.45 : 0.22}
                  freq2={index === 0 ? 0.18 : 0.07}
                  freqT={index === 0 ? 1.1 : 0.4}
                  speed={index === 0 ? 0.032 : 0.015}
                  baseline={index === 0 ? 0.4 : 0.25}
                  amplitude={index === 0 ? 0.45 : 0.6}
                />
              </div>
              <div className="text-3xl md:text-4xl lg:text-5xl font-display tracking-tight w-full">
                <AnimatedNumber end={metric.value} suffix={metric.suffix} prefix={metric.prefix} />
              </div>
            </div>
          ))}
        </div>

        {/* Bottom ticker — live sources marquee */}
        <div className={`mt-16 pt-8 border-t border-foreground/10 transition-all duration-1000 delay-500 ${
          isVisible ? "opacity-100" : "opacity-0"
        }`}>
          <div className="flex items-center gap-2 mb-6 text-xs font-mono text-muted-foreground uppercase tracking-wider">
            <span className="w-2 h-2 rounded-full bg-[#64ffda] animate-pulse" />
            {t("metrics.sourcesLabel")}
          </div>

          <div className="sources-marquee-wrap relative overflow-hidden">
            {/* Edge fades so the loop seam isn't visible */}
            <div className="pointer-events-none absolute inset-y-0 left-0 w-16 lg:w-32 bg-gradient-to-r from-background to-transparent z-10" />
            <div className="pointer-events-none absolute inset-y-0 right-0 w-16 lg:w-32 bg-gradient-to-l from-background to-transparent z-10" />

            <div className="marquee flex w-max">
              {[...DATA_SOURCES, ...DATA_SOURCES].map((source, i) => (
                <span
                  key={`${source.name}-${i}`}
                  className="flex items-center gap-2 shrink-0 pr-8 text-sm font-mono text-muted-foreground"
                >
                  <source.Icon className="w-4 h-4 shrink-0" aria-hidden="true" />
                  {source.name}
                  <span className="w-1 h-1 rounded-full bg-foreground/20 ml-6" aria-hidden="true" />
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
