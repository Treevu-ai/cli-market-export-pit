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
