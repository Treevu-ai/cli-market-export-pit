/** PIT API client — TypeScript port of web/js/pit-api.js */

declare global {
  interface Window {
    PIT_API_BASE?: string;
    PIT_API_KEY?: string;
  }
}

export function getApiBase(): string {
  if (typeof window === "undefined") return "";
  if (window.PIT_API_BASE) return window.PIT_API_BASE.replace(/\/$/, "");
  if (process.env.NEXT_PUBLIC_PIT_API_URL) {
    return process.env.NEXT_PUBLIC_PIT_API_URL.replace(/\/$/, "");
  }
  if (window.location.protocol === "file:") return "http://127.0.0.1:8000";
  return window.location.origin.replace(/\/$/, "");
}

// Sessions live in the httpOnly `pit_session` cookie the backend sets on
// signup/login (credentials: "include" below) — never in localStorage, which
// any XSS could read. The backend also returns the raw token in the response
// body for non-browser API clients; the browser client intentionally never
// persists it.

export class QuotaExceededError extends Error {
  tier: string;
  limit: number | null;
  upgradeUrl: string;

  constructor(detail: { message?: string; tier: string; limit: number | null; upgrade_url: string }) {
    super(detail.message || "Monthly limit reached");
    this.tier = detail.tier;
    this.limit = detail.limit;
    this.upgradeUrl = detail.upgrade_url;
  }
}

export class EmailNotVerifiedError extends Error {
  constructor(message?: string) {
    super(message || "Verify your email before running analyses");
  }
}

// CSRF token, held in memory only (never localStorage/cookie). The backend
// delivers it in the JSON body of signup/login/me responses rather than a
// cookie: frontend and backend live on different subdomains in production,
// and a cookie set by the backend's origin is invisible to frontend JS via
// document.cookie regardless of httpOnly — a real double-submit cookie
// can't work across that boundary. Being in-memory means a page reload
// loses it, but every page that cares about auth state already calls
// getMe() on mount, which re-populates it.
let cachedCsrfToken: string | null = null;

function rememberCsrfToken(token: unknown): void {
  if (typeof token === "string" && token) {
    cachedCsrfToken = token;
  }
}

export async function pitRequest<T = unknown>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...((options.headers as Record<string, string>) || {}),
  };
  if (typeof window !== "undefined" && window.PIT_API_KEY) {
    headers["X-API-Key"] = window.PIT_API_KEY;
  }
  if (cachedCsrfToken) {
    headers["X-CSRF-Token"] = cachedCsrfToken;
  }
  const response = await fetch(`${getApiBase()}${path}`, { ...options, headers, credentials: "include" });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 402 && payload.detail && typeof payload.detail === "object") {
      throw new QuotaExceededError(payload.detail);
    }
    if (response.status === 403 && payload.detail?.code === "email_not_verified") {
      throw new EmailNotVerifiedError(payload.detail.message);
    }
    const detail = payload.detail || payload.message || response.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return payload as T;
}

export interface RunFullPipelineBody {
  query: string;
  target_market: string;
  application: string;
  limit: number;
  hs_code?: string;
}

export interface DomainScore {
  score: number;
  confidence?: string;
  weight?: number;
  coverage?: number;
}

export interface ScoreBlock {
  score_version: string;
  opportunity_score: number;
  coverage_factor: number;
  recommendation: string;
  dimensions: Record<string, DomainScore>;
  alerts: string[];
  exclusions?: string[];
}

export interface ChecklistItem {
  priority: "high" | "medium" | "low";
  title: string;
  action: string;
}

export interface SourceEntry {
  source: string;
  request_url: string;
  checksum: string | null;
  status: string;
  http_status?: number | null;
}

export interface ReportData {
  run_id: string;
  query: string;
  target_market: string;
  application: string;
  cutoff_at: string;
  score: ScoreBlock;
  improvement_checklist: ChecklistItem[];
  evidence_summary: Record<string, any>;
  claims: unknown[];
  sources: SourceEntry[];
}

export interface RunSummary {
  id: string;
  status: string;
}

export async function runFullPipeline(body: RunFullPipelineBody): Promise<RunSummary> {
  const envelope = await pitRequest<{ data: RunSummary }>("/v1/research-runs/full", {
    method: "POST",
    body: JSON.stringify(body),
  });
  return envelope.data;
}

export async function fetchReport(runId: string): Promise<ReportData> {
  const envelope = await pitRequest<{ data: ReportData }>(`/v1/research-runs/${runId}/report`);
  return envelope.data;
}

export interface AgentsStatus {
  ficha_available?: boolean;
  reason?: string;
  anthropic_configured?: boolean;
}

export async function fetchAgentsStatus(): Promise<AgentsStatus> {
  const envelope = await pitRequest<{ data: AgentsStatus }>("/v1/agents/status");
  return envelope.data;
}

export interface FichaResult {
  dossier_markdown: string;
}

export async function generateFicha(
  runId: string,
  body: { segment?: string; stage?: string } = {},
): Promise<FichaResult> {
  const envelope = await pitRequest<{ data: FichaResult }>(`/v1/research-runs/${runId}/ficha`, {
    method: "POST",
    body: JSON.stringify(body),
  });
  return envelope.data;
}

export function reportPdfUrl(runId: string): string {
  return `${getApiBase()}/v1/research-runs/${runId}/report.pdf`;
}

export const RECOMMENDATION_LABELS: Record<string, { label: string; tone: "go" | "conditional" | "flag" | "insufficient" }> = {
  Investigate: { label: "Investigar", tone: "go" },
  Validate: { label: "Validar", tone: "conditional" },
  Deprioritize: { label: "Depriorizar", tone: "insufficient" },
  "Insufficient evidence": { label: "Evidencia insuficiente", tone: "flag" },
};

export const MARKET_COVERAGE: Record<string, { tier: "strong" | "partial" | "none"; note: string }> = {
  PE: { tier: "strong", note: "Cobertura fuerte de CLI Market — multi-tienda, validada con productos agro/frescos." },
  MX: { tier: "strong", note: "Cobertura fuerte de CLI Market — multi-tienda, validada con productos agro/frescos." },
  AR: { tier: "strong", note: "Cobertura fuerte de CLI Market — multi-tienda, validada con productos agro/frescos." },
  CO: { tier: "partial", note: "Cobertura parcial de CLI Market — una tienda verificada." },
  BR: { tier: "partial", note: "Cobertura parcial de CLI Market — una tienda verificada." },
  US: { tier: "none", note: "Sin datos de góndola de CLI Market para categorías agro/frescos (catálogo orientado a DTC/wellness)." },
  CL: { tier: "none", note: "Sin datos de góndola de CLI Market confirmados para categorías agro/frescos." },
};

export interface RecentRun {
  id: string;
  query: string;
  target_market: string;
  score: number | null;
}

const RECENT_RUNS_KEY = "pit_recent_runs";
const RECENT_RUNS_MAX = 8;

export function loadRecentRuns(): RecentRun[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(window.localStorage.getItem(RECENT_RUNS_KEY) || "[]");
  } catch {
    return [];
  }
}

export function saveRecentRun(entry: RecentRun): RecentRun[] {
  const runs = loadRecentRuns().filter((run) => run.id !== entry.id);
  runs.unshift(entry);
  const trimmed = runs.slice(0, RECENT_RUNS_MAX);
  if (typeof window !== "undefined") {
    window.localStorage.setItem(RECENT_RUNS_KEY, JSON.stringify(trimmed));
  }
  return trimmed;
}

export interface AuthSession {
  token: string;
  csrf_token: string;
  email: string;
  tier: string;
}

export interface MeResponse {
  email: string;
  tier: string;
  csrf_token: string;
  email_verified: boolean;
  tier_expires_at: string | null;
  usage: { used: number; limit: number | null; period: string };
}

export async function signup(email: string, password: string, locale: "es" | "en" = "es"): Promise<AuthSession> {
  const envelope = await pitRequest<{ data: AuthSession }>("/v1/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password, locale }),
  });
  rememberCsrfToken(envelope.data.csrf_token);
  return envelope.data;
}

export async function login(email: string, password: string): Promise<AuthSession> {
  const envelope = await pitRequest<{ data: AuthSession }>("/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  rememberCsrfToken(envelope.data.csrf_token);
  return envelope.data;
}

export async function logout(): Promise<void> {
  await pitRequest("/v1/auth/logout", { method: "POST" });
  cachedCsrfToken = null;
}

export async function getMe(): Promise<MeResponse> {
  const envelope = await pitRequest<{ data: MeResponse }>("/v1/auth/me");
  rememberCsrfToken(envelope.data.csrf_token);
  return envelope.data;
}

export async function verifyEmail(token: string): Promise<{ email: string; email_verified: boolean }> {
  // POST with the token in the body, not a query param — keeps it out of
  // server access logs.
  const envelope = await pitRequest<{ data: { email: string; email_verified: boolean } }>("/v1/auth/verify", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
  return envelope.data;
}

export async function resendVerificationEmail(): Promise<void> {
  await pitRequest("/v1/auth/resend-verification", { method: "POST" });
}
