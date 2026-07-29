import path from "node:path";
import { defineConfig, devices } from "@playwright/test";

const PORT = 3000;
const BASE_URL = `http://localhost:${PORT}`;

const API_PORT = 8000;
export const API_BASE_URL = `http://127.0.0.1:${API_PORT}`;

const REPO_ROOT = path.resolve(__dirname, "..");
const E2E_TMP_DIR = path.resolve(__dirname, "e2e", ".tmp");
export const E2E_DB_PATH = path.join(E2E_TMP_DIR, "e2e.db");
const E2E_RAW_DIR = path.join(E2E_TMP_DIR, "raw");

// Login E2E tests need a real backend, not just the frontend — this second
// webServer entry runs the FastAPI app against a disposable SQLite DB (wiped
// before each Playwright run) with no RESEND_API_KEY, so signup emails
// silently no-op instead of hitting the real Resend API; the verification
// token is instead read straight out of e2e.db (see e2e/helpers/db.ts).
const API_ENV = {
  PIT_DB_PATH: E2E_DB_PATH,
  PIT_RAW_DIR: E2E_RAW_DIR,
  PIT_CORS_ORIGINS: BASE_URL,
  PIT_FRONTEND_URL: BASE_URL,
  PIT_JWT_SECRET: "e2e-test-jwt-secret-not-for-production-use-only",
  PIT_ADMIN_SECRET: "e2e-test-admin-secret",
  // Explicitly blanked, not just omitted — without this, an ambient
  // RESEND_API_KEY from the parent shell would leak through (env is spread
  // from process.env below) and the E2E backend would fire real emails to
  // Resend for junk test addresses on every run.
  RESEND_API_KEY: "",
};

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  // Capped rather than left unbounded: these specs exercise the same shared
  // `next dev` server (webpack HMR compiles routes on demand), and higher
  // worker counts were observed to overload it and cause spurious timeouts.
  workers: process.env.CI ? 1 : 2,
  reporter: [
    ["html", { outputFolder: "playwright-report", open: "never" }],
    ["junit", { outputFile: "playwright-report/junit.xml" }],
    ["list"],
  ],
  use: {
    baseURL: BASE_URL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: [
        `node ${JSON.stringify(path.join(__dirname, "e2e", "helpers", "reset-db.cjs"))}`,
        `python -m uvicorn pit.api:app --host 127.0.0.1 --port ${API_PORT}`,
      ].join(" && "),
      url: `${API_BASE_URL}/v1/health`,
      cwd: REPO_ROOT,
      env: { ...process.env, ...API_ENV },
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: `npm run dev -- --port ${PORT}`,
      url: BASE_URL,
      env: { ...process.env, NEXT_PUBLIC_PIT_API_URL: API_BASE_URL },
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
});
