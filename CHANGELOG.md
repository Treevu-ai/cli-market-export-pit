# Changelog

All notable changes to this project are documented in this file.

## 2026-07-28

### Added
- ES/EN language toggle (client-side, localStorage-based) across the whole site.
- Light/dark/system theme toggle (`next-themes`) on every route except the landing page, which stays permanently dark by design.
- Mandatory email verification on signup (via Resend): new accounts can't run analyses until they click the link sent to their inbox. Existing accounts were grandfathered as verified.
- Automatic downgrade for Pro/Enterprise accounts: admin-granted tiers now carry an expiry date (default 30 days, overridable), and the next authenticated request after expiry silently reverts the account to Free — no cron/scheduler needed.
- Password strength requirements on signup: uppercase, lowercase, digit, symbol, no spaces.
- Rate limiting on `/v1/auth/signup` (5/IP/hour), `/v1/auth/login` (10/IP/hour), and `/v1/auth/resend-verification` (3/account/hour) — closes the account-farming gap that let anyone bypass the Free-tier quota with disposable emails.
- `/verify` page and a "verify your email" banner (with resend action) in the analysis console.
- Verification status and plan-expiry date shown on the account page.
- "8 domains evaluated" stat on the landing now lists the actual 8 PIT scoring domains, disambiguating it from the unrelated 4-category source breakdown next to it.
- The "+N more sources" ticker on the landing is now a real expand/collapse control listing all 11 additional connectors (was static text with a stale count).

### Changed
- Pro plan pricing CTA now says "Solicitar Pro" (mailto) instead of "Crear cuenta gratis" — there's no self-serve billing yet, so the old copy was misleading for a $49/mo plan.
- Removed the GitHub link from the footer (pointed at a private repo).
- Rewrote the security-section landing headline ("Sin fingir ser el IPC") to drop the implied comparison to Peru's official INEI price index.

### Fixed
- Two real mobile-viewport overlap bugs introduced by longer English translation strings (`developers-section.tsx` unbounded-width column + missing grid breakpoint; `security-section.tsx` license badges absolutely pinned over content that can grow taller).
- Legal pages (`/legal/privacy`, `/legal/terms`) had lost their `mailto:`/`/pricing` hyperlinks when their body text was flattened into translated strings — restored as real anchors.
- `fly.api.toml` had no explicit `dockerfile` set, so `fly deploy` silently built the repo-root (frontend) Dockerfile for the backend app instead of `Dockerfile.api`, taking the backend down after a deploy. Pinned explicitly; this class of failure can't recur.

### Security
- Fixed a TOCTOU race in the new signup rate limiter and switched it to trust only Fly's `Fly-Client-Ip` header (dropped the spoofable `X-Forwarded-For` fallback).
- Fixed a race where a verification token issued in a follow-up write (rather than the same INSERT as account creation) could leave an account in a state the grandfather migration would silently auto-verify after a process restart; token issuance is now atomic with user creation.
- Added `_transaction()` rollback-on-exception (previously only committed on success, leaving the shared Postgres connection poisoned after any error).

## 2026-07-29

### Added
- Four new verified export categories: páprika (HS 090422), aguaymanto/goldenberry (HS 081090, basket code — documented as such), cúrcuma (HS 091030), higo (HS 080420), and maracuyá (HS 200899, basket code) — bringing the landing's analyzable-product set to 24. Each verified live against the UN Comtrade public API and cross-checked for real CLI Market retail coverage before being added.
- Regrouped the landing's flat 24-card product grid into 6 collapsible families (Frutas frescas, Especias y aromáticas, Granos y semillas, Vegetales y raíces, Bebidas y estimulantes, Derivados y funcionales) with a new "HS específico"/"HS compartido" badge per product — surfaces the exclusive-vs-basket-code distinction that was previously tracked internally but invisible in the UI.
- Playwright E2E suite (`web-next/e2e/`) — the project had no frontend test framework at all until now. Covers the landing smoke test, the new integrations accordion, the ES/EN language toggle, signup client-side validation, `/analyze/` auth gating, and a mobile-viewport (375px) horizontal-overflow regression guard.
- CI now runs a `frontend` job (build + Playwright E2E) — previously CI only covered the Python backend.

### Fixed
- CI's Python `test` job had been silently failing on every push since the páprika commit — not from anything those commits changed, but because `ruff` was pinned as `>=0.5` with no explicit rule config, so CI always installed the latest ruff and inherited whatever rules it had just promoted to default-enabled (ruff 0.16 added several). Pinned `ruff>=0.9,<0.17`, fixed the newly-surfaced findings, and fixed one real (unrelated, pre-existing) mypy gap that had never actually run in CI because ruff failing earlier in the same job always short-circuited it.
- `storage.py`'s `_execute()` only converted the `_ph()` placeholder token on the SQLite branch, never on PostgreSQL — every `create_run()` call would have thrown a SQL syntax error against a real Postgres database. Production currently runs SQLite so this was dormant, but `psycopg2-binary` is a live dependency; fixed while extending this exact statement for the ownership migration below.

### Security
- **Research-run IDOR (HIGH):** `research_runs` had no ownership column at all, and 5 endpoints — get run, enrich, report, report.pdf, and the Anthropic-backed ficha generator — had zero authentication. Anyone who obtained a `run_id` could read another user's research data or trigger a real paid AI call for free, with no auth, quota, or rate limit. Added a `user_id` column, threaded it through run creation, and gated all 5 endpoints behind an ownership check (404, not 403, on mismatch — avoids leaking whether a run exists). Also gated `/v1/connectors/status` and `/metrics` (internal ops data, no legitimate frontend consumer) behind the existing admin-secret dependency.
- **No CSRF defense (HIGH):** the cross-subdomain session cookie (`SameSite=None`, required since frontend and backend live on different Fly.io subdomains) had zero CSRF protection anywhere in the codebase — a hostile page could silently ride a logged-in user's session to drain their quota or log them out. Added a double-submit `pit_csrf` cookie plus an `X-CSRF-Token` header check on every cookie-authenticated state-changing route; `Authorization: Bearer` requests (non-browser clients, this project's own test suite) are correctly exempt, since they aren't cookie-authenticated and so aren't CSRF-exposed.
- Both fixes went through independent `code-reviewer` and `security-reviewer` passes before merge; no CRITICAL/HIGH issues remained after fixes.
