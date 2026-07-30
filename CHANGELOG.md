# Changelog

All notable changes to this project are documented in this file.

## 2026-07-30

Full audit of PIT's 8 evidence-source connectors and scoring pipeline: 22 completed research runs existed in production, but every single one was scored "Insufficient evidence" (coverage_factor 0.4–0.52). Traced this to most external connectors being broken, plus a scoring gap that silently dropped nearly half the evidence domains from the final score. Fixed both, then extended coverage with two new sources.

### Fixed — connectors (each confirmed live against the real API before merging)
- **GDELT**: had zero retry logic — a single 429/5xx aborted the whole trend domain. Added the same retry/backoff pattern already proven in `semanticscholar.py`.
- **OpenFDA**: query was an unscoped bare phrase (OpenFDA requires `field:value` Lucene syntax) with hyphenated ISO dates instead of `report_date:[YYYYMMDD TO ...]`. Fixed both. Separately, discovered OpenFDA returns HTTP 404 with `{"error":{"code":"NOT_FOUND"}}` for a genuine zero-recalls query — the normal case for most food products, not a failure — which was tanking the whole `regulatory` pipeline step on almost every run; now treated as an empty result.
- **NIH RePORTER**: was sending a GET with query-string params against a POST-only, JSON-body API. Rewrote the request entirely.
- **NSF Awards**: wrong base URL, wrong param names (`startDate`/`endDate`/`limit` → `dateStart`/`dateEnd` MM/DD/YYYY + `rpp` capped at 25), and parsed a top-level `award` key that doesn't exist (real shape is nested under `response.award`).
- **UN Comtrade**: complete rewrite — real endpoint is `comtradeapi.un.org/data/v1/get/...` with an `Ocp-Apim-Subscription-Key` header (Azure APIM), `period` as a CSV year list (not a hyphenated range), and real field names (`primaryValue`/`netWgt`, not `tradeValue`/`netWeight`).
- **Climatiq**: real endpoint is `/data/v1/search` (not `/v2/search`), requires a `data_version` param, and nests results under `results` with a `factor` field (not `data`/`co2e_factor`).
- **EPO OPS**: OAuth host (`oauth.epo.org`) has no DNS record at all; the token endpoint actually lives on `ops.epo.org`. Search path needed a `/published-data/` segment. Pagination is the `X-OPS-Range` header, not a query param — date filtering is CQL embedded in `q`. A quoted search term or an open-ended future date both 500 on EPO's side; fixed to unquoted terms and a capped date range. A non-English query with zero matches returns HTTP 404 `EntityNotFound` — a legitimate empty result, not an error.
- **EPO OPS biblio enrichment**: the `/search` endpoint never carries title/applicant/IPC data — every result previously showed patent counts with no qualitative detail. Added a follow-up batch call to the `/biblio` endpoint (all matched patents in one request) that fills in real titles, applicant/assignee names, and IPC classification codes; falls back to the bare results if the batch call fails.
- **CORDIS**: `cordis.europa.eu/api/search` 404s with the site's own SPA shell, not a JSON error — it was never a real endpoint. Found the actual one (`/api/search/results`, with a `contenttype='project'` filter) by capturing the CORDIS website's own network calls in a live browser session. No API key required.

### Added
- **WITS (World Integrated Trade Solution / UNCTAD TRAINS)**: new connector for tariff barriers, a gap Comtrade's flow data never covered — what tariff a Peru-origin export actually pays entering the target market (e.g. cocoa powder into the US: 13.64% MFN vs 0% preferential under the Peru-US trade agreement). Folded into the existing `trade` domain rather than given its own scoring weight. WITS's WAF returns HTTP 403 for any request with no `User-Agent` header and occasionally times out under repeated calls — both handled (custom UA + retry/backoff).
- **USDA FAS (PSD database)**: global production/supply/demand context. Its ~55 tracked commodities are bulk agricultural goods (grains, oilseeds, dairy) — confirmed live this covers only 3 of PIT's ~24 specialty products (café, uva, limón); scoped to match only those rather than guess a commodity code for the rest.

### Fixed — scoring
- `ScoringEngine.weights` only ever covered 5 of 9 evidence domains (`science`, `patent`, `trend`, `trade`, `commerce`). `macro` (BCRP), `regulatory` (OpenFDA/EFSA/FoodData Central), `sustainability` (Climatiq), and `technology_scout` (CORDIS/NIH/NSF) — 8 of 16 connectors — were being fetched, stored as real evidence, and even shown in the report UI, but silently dropped before scoring (`build_domain_scores` skips any domain not in `weights`). Confirmed live: one real run had domain summaries for 8 of 9 domains but `domain_scores` rows for only 5. Rebalanced weights across all 9 domains and added the missing `estimate_coverage`/`estimate_score` branches for `macro`.
- Re-ran the "arándano orgánico" PE case end to end after the connector fixes: `coverage_factor` went from 0.52 (patent + trade domains entirely missing) to 0.76 — crossing the 0.60 threshold for the first time in this dataset's history and producing a real "Deprioritize" recommendation instead of "Insufficient evidence."

### Fixed — landing page
- The "Integrations" grid showed a single fixed export corridor per product (e.g. "PE→US"), when most of these are genuinely multi-market exports — updated to show the top two real destinations per product (US/EU are consistently the largest for Peru's agroexport lines).
- The "real case" metrics section (13/17/48) was a hardcoded constant tied to blueberry→US that never reflected any live pipeline run. Swapped the featured case to high-flavanol cacao→EU (the best real result among 3 candidates tested live against the fixed pipeline) and refreshed the figures from an actual run: 38 real science evidence records, 11 PE retail stores compared, 136 real shelf products found. Renamed "Commercial references" → "Stores compared" to match what the number actually is.
- The infrastructure section's source/domain counters ("15 fuentes", "8 dominios") were the same kind of stale hardcoded constant — updated to 18 sources / 9 domains, recomputed from the real connector list, with the per-category breakdown (5 ciencia / 6 mercado / 3 regulatorio / 4 I+D y proyectos) and the domain list (added the missing "macro") to match.

### Security
- Closed PR #4 ("technical specs for 17 public API connectors") without merging: it planned to add FAOSTAT (`CC BY-NC-SA 3.0`, non-commercial license, unresolved commercial-use question) and Google Trends via headless-Chrome scraping (the spec itself acknowledged this risks Google's Terms of Service) to a paid commercial product. Deleted the associated branch.

### Added — public example report
- `/report/` with no `run_id` showed an empty placeholder — there was no unauthenticated way to view any report, since every report route requires a logged-in owner. Added `/v1/public/example-report`, a single hardcoded run_id (not a general auth bypass, so it can never expose a real user's data), and wired the frontend to use it when no `run_id` is given, with a banner making clear it's an example.

### Fixed — more real bugs found while building the example report
- **Comtrade silently returned zero trade data on every single run.** `reporter_country` defaulted to `"0"` ("World" aggregate); confirmed live this returns zero HS6-level records from the real API. `enrich_with_trade()` never overrode it, so the "trade" domain (0.20 weight, tied for highest) had been contributing nothing to any score since Comtrade was fixed earlier today. Defaulted to Peru (604) — PIT's whole premise is Peru's export potential.
- **Every one of the 17 connectors could crash the entire pipeline run on a timeout.** `urlopen`'s socket timeout surfaces as a bare `TimeoutError`, not wrapped in `URLError` — every connector's `except` clause only covered `HTTPError`/`URLError`, so a single slow connector could take down a real user's whole research run instead of just failing its own domain. Reproduced live (GDELT). Fixed across all 17 connectors.
- **Shelf-price comparison showed the wrong currency.** The frontend hardcoded "S/" (Peruvian sol) on every price regardless of which market was actually queried — a Mexico analysis displayed Mexican peso prices labeled as soles. Now maps the symbol from the commerce domain's actual target market.

### Documented — real coverage gaps, not bugs (left as-is)
- **EPO OPS and Climatiq barely match Spanish or multi-word qualified queries.** Confirmed live: `"cacao alto flavanol"` → 0 EPO patents, but `"high flavanol cocoa"` → 5; `"high flavanol cocoa"` → 0 Climatiq matches, but `"cocoa"` alone → 5. Both APIs want short, simple, English terms — this silently weakens the patent and sustainability domains on any real Spanish-language query, which is most of them.
- **CLI Market's shelf-price domain reflects the *target* market, not Peru's domestic market.** For non-LatAm targets (US, EU) CLI Market has little to no relevant grocery-retailer coverage (only a handful of generic lifestyle e-commerce brands), so "Retail/góndola" comes back empty even when the same product has rich real data in Peru's own market. Not a bug — CLI Market's real retail coverage is concentrated in Peru + a few LatAm markets.
- **The regulatory domain (OpenFDA, EFSA/EUR-Lex, FoodData Central) only covers the US and EU.** All three connectors explicitly skip any other `target_market` (confirmed in code: OpenFDA/FoodDataCentral require `target_market == "US"`, EFSA requires an EU market). Any analysis targeting Mexico, Chile, Colombia, Argentina, Brazil, etc. will always show an empty regulatory panel — there's no real LatAm equivalent to OpenFDA wired in yet (e.g. Mexico's COFEPRIS).

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
- **No CSRF defense (HIGH):** the cross-subdomain session cookie (`SameSite=None`, required since frontend and backend live on different Fly.io subdomains) had zero CSRF protection anywhere in the codebase — a hostile page could silently ride a logged-in user's session to drain their quota or log them out. Added a double-submit `pit_csrf` cookie plus an `X-CSRF-Token` header check on every cookie-authenticated state-changing route; `Authorization: Bearer` requests (non-browser clients, this project's own test suite) are correctly exempt, since they aren't cookie-authenticated and so aren't CSRF-exposed. **Superseded a few hours later — see below, this specific design turned out to be broken in production.**
- **No server-side session revocation on logout (MEDIUM, follow-up from the IDOR/CSRF review):** logout only ever deleted the `pit_session`/`pit_csrf` cookies client-side; the underlying JWT stayed fully valid via `Authorization: Bearer` for its full 7-day TTL, so a token captured before logout (XSS, a copied Bearer value, a shared device) survived the user clicking "log out." Added a `token_version` counter on `users`; every JWT carries a `tv` claim, `get_current_user` rejects any mismatch, and logout bumps `token_version` — invalidating every session for that account everywhere, not just the one used to log out. Logout was made best-effort so an already-invalid session still gets its cookies cleared (a real regression caught by `code-reviewer` in the first pass and fixed before merge).
- **CSRF was actually broken in production (HIGH, self-discovered within hours of the fix above):** the double-submit `pit_csrf` cookie fix looked correct in code review and passed the backend test suite, but a cookie set by the backend's origin (`cli-market-pit-backend.fly.dev`) is invisible to frontend JS via `document.cookie` on a *different* origin (`cli-market-pit.fly.dev`) regardless of `httpOnly` — basic cookie same-origin-storage rules, not something `SameSite` changes. Net effect: `X-CSRF-Token` never got attached client-side, so every cookie-authenticated mutating request (create research run, enrich, ficha generation, resend-verification, logout) was silently returning 403 in production from the moment that fix deployed. Neither the earlier `code-reviewer`/`security-reviewer` passes (static analysis, no live browser) nor the pytest suite (`httpx`'s `TestClient` doesn't model real cross-origin cookie visibility) could have caught this — it was caught by a genuine end-to-end Playwright test that logs in through a real Chromium browser against a real local backend (see Added, below). Redesigned as a stateless HMAC token (`hmac_sha256(PIT_JWT_SECRET, f"{user_id}:{token_version}")`) delivered in the JSON body of signup/login/me instead of a cookie, cached in memory by the frontend, with no cross-origin dependency left anywhere in the verification path.
- Every fix in this list went through independent `code-reviewer` and `security-reviewer` passes before merge; no CRITICAL/HIGH issues remained unresolved.

### Added (continued)
- Real end-to-end Playwright test for the complete login flow (`web-next/e2e/login-flow.spec.ts`): signup → email verification (token read directly from a disposable local SQLite DB, since `RESEND_API_KEY` is deliberately unset for this test backend) → explicit login → session persistence across a fresh page load via the `pit_session` cookie → logout → wrong-password rejection. Backed by a second `webServer` entry in `playwright.config.ts` that boots the real FastAPI app for the test run — this is the only E2E spec that talks to a genuine backend instead of intercepted/mocked routes, and it's what caught the CSRF production break above.
- CI's `frontend` job now also installs the Python backend package, since the new login-flow E2E test needs a real `pit.api` server to boot alongside the frontend dev server.
