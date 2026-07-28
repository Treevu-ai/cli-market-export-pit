"use client";

import { useState, useEffect, useRef } from "react";

const features = [
  {
    title: "Endpoints documentados",
    description: "OpenAPI en /docs, listo para probar sin configuración previa.",
  },
  {
    title: "JSON o PDF",
    description: "Mismo research run, exportable como reporte ejecutivo o datos crudos.",
  },
  {
    title: "Trazabilidad por diseño",
    description: "Cada fuente con checksum SHA-256, cada score con versión.",
  },
  {
    title: "Sin vendor lock-in",
    description: "Conectores abiertos, sin depender de un solo proveedor de datos.",
  },
];

export function DevelopersSection() {
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
    <section id="developers" ref={sectionRef} className="relative py-24 lg:py-32 overflow-hidden">

      {/* Code preview — absolute, bottom-right, behind text content */}
      <div
        className={`absolute bottom-12 right-6 lg:right-12 hidden lg:block w-[42%] max-w-lg transition-all duration-1000 delay-300 ${
          isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
        }`}
      >
        <div className="border border-foreground/10 bg-foreground/[0.02] p-6 font-mono text-xs leading-relaxed text-muted-foreground overflow-hidden">
          <div className="flex gap-1.5 mb-4">
            <span className="w-2.5 h-2.5 rounded-full bg-foreground/20" />
            <span className="w-2.5 h-2.5 rounded-full bg-foreground/20" />
            <span className="w-2.5 h-2.5 rounded-full bg-foreground/20" />
          </div>
          <pre className="whitespace-pre-wrap">{`curl -X POST /v1/research-runs/full \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "arándano orgánico",
    "target_market": "PE",
    "limit": 10
  }'`}</pre>
        </div>
      </div>

      {/* All text content sits on top */}
      <div className="relative z-10 max-w-[1400px] mx-auto px-6 lg:px-12">
        {/* Header — Full width */}
        <div
          className={`mb-16 transition-all duration-700 ${
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}
        >
          <span className="inline-flex items-center gap-3 text-sm font-mono text-muted-foreground mb-6">
            <span className="w-8 h-px bg-foreground/30" />
            API abierta
          </span>
          <h2 className="text-6xl md:text-7xl lg:text-[128px] font-display tracking-tight leading-[0.9]">
            Automatiza
            <br />
            <span className="text-muted-foreground">el research.</span>
          </h2>
        </div>

        {/* Description + Features — left half only */}
        <div
          className={`max-w-[50%] transition-all duration-700 delay-100 ${
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}
        >
          <p className="text-xl text-muted-foreground mb-12 leading-relaxed max-w-md">
            Una API REST documentada para correr research runs, generar reportes y fichas
            ejecutivas — sin depender de la consola web.
          </p>
          <div className="grid grid-cols-2 gap-6 mb-10">
            {features.map((feature, index) => (
              <div
                key={feature.title}
                className={`transition-all duration-500 ${
                  isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
                }`}
                style={{ transitionDelay: `${index * 50 + 200}ms` }}
              >
                <h3 className="font-medium mb-1">{feature.title}</h3>
                <p className="text-sm text-muted-foreground">{feature.description}</p>
              </div>
            ))}
          </div>
          <a
            href="https://cli-market-pit-backend.fly.dev/docs" target="_blank" rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-sm font-mono text-foreground border-b border-foreground/30 pb-1 hover:border-foreground transition-colors"
          >
            Ver documentación OpenAPI →
          </a>
        </div>
      </div>
    </section>
  );
}
