"use client";

import { useState } from "react";
import { login } from "@/lib/pit-api";

export function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email, password);
      window.location.href = "/analyze/";
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <h1 className="font-display text-3xl">Inicia sesión</h1>
      <form onSubmit={handleSubmit} className="mt-8 space-y-4">
        <div>
          <label className="mb-1 block font-mono text-xs uppercase tracking-wide text-muted-foreground">
            Email
          </label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full border border-foreground/20 bg-transparent px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="mb-1 block font-mono text-xs uppercase tracking-wide text-muted-foreground">
            Contraseña
          </label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full border border-foreground/20 bg-transparent px-3 py-2 text-sm"
          />
        </div>
        {error && <p className="text-sm text-[#e11d48]">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-full bg-[#64ffda] px-5 py-3 text-sm font-medium text-[#0a192f] transition-opacity disabled:opacity-40"
        >
          {submitting ? "Ingresando…" : "Iniciar sesión"}
        </button>
      </form>
      <p className="mt-6 text-sm text-muted-foreground">
        ¿No tienes cuenta?{" "}
        <a href="/signup" className="text-[#64ffda] hover:underline">
          Crea una gratis
        </a>
      </p>
    </div>
  );
}
