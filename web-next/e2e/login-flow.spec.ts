import { test, expect } from "@playwright/test";
import { getVerificationToken } from "./helpers/db";

// Runs against a real, disposable local backend (see playwright.config.ts's
// second webServer entry) — not mocked/intercepted like the other auth
// specs — so this is the one place that actually proves signup, email
// verification, login, session persistence via the pit_session cookie, and
// logout/session-revocation all work together end to end.

function uniqueEmail(): string {
  return `e2e-${Date.now()}-${Math.floor(Math.random() * 1e6)}@example.com`;
}

const PASSWORD = "Testpass123!";

test.describe("Complete login flow (real backend)", () => {
  test("signup, verify, explicit login, session persistence, and logout all work", async ({ page }) => {
    const email = uniqueEmail();

    // 1. Sign up.
    await page.goto("/signup");
    await page.locator('input[type="email"]').fill(email);
    await page.locator('input[type="password"]').fill(PASSWORD);
    await page.getByRole("button", { name: /crear cuenta|create/i }).click();
    await page.waitForURL(/\/analyze\/?/);

    // 2. Verify the account — read the token straight from the E2E DB
    // instead of a real email, since RESEND_API_KEY is unset for this
    // backend on purpose.
    const token = await getVerificationToken(email);
    await page.goto(`/verify?token=${token}`);

    // 3. Log out of the auto-login session from signup, so the next step
    // genuinely exercises the login form (not just signup's session).
    await page.goto("/account");
    await page.getByRole("button", { name: /cerrar sesión|log out/i }).click();
    await page.waitForURL(/\/login\/?/);

    // Session should now be dead: /account must show the logged-out state.
    await page.goto("/account");
    await expect(page.getByText(/no has iniciado sesión|not logged in/i)).toBeVisible();

    // 4. Explicit login with the same credentials.
    await page.goto("/login");
    await page.locator('input[type="email"]').fill(email);
    await page.locator('input[type="password"]').fill(PASSWORD);
    await page.getByRole("button", { name: /inicia sesión|sign in/i }).click();
    await page.waitForURL(/\/analyze\/?/);

    // 5. Session persistence: /account must reflect the logged-in user via
    // the pit_session cookie set at login — this is the real proof the
    // cookie-based session survives a fresh navigation, not just an
    // in-memory client state.
    await page.goto("/account");
    await expect(page.getByText(email)).toBeVisible();
    await expect(page.getByText(/correo verificado|email verified/i)).toBeVisible();

    // 6. Logout kills the session again (also covers the token_version
    // revocation fix — a live session must actually die, not just have its
    // cookie deleted client-side).
    await page.getByRole("button", { name: /cerrar sesión|log out/i }).click();
    await page.waitForURL(/\/login\/?/);
    await page.goto("/account");
    await expect(page.getByText(/no has iniciado sesión|not logged in/i)).toBeVisible();
  });

  test("login with the wrong password is rejected with an error, not a redirect", async ({ page }) => {
    const email = uniqueEmail();
    await page.goto("/signup");
    await page.locator('input[type="email"]').fill(email);
    await page.locator('input[type="password"]').fill(PASSWORD);
    await page.getByRole("button", { name: /crear cuenta|create/i }).click();
    await page.waitForURL(/\/analyze\/?/);

    await page.goto("/account");
    await page.getByRole("button", { name: /cerrar sesión|log out/i }).click();
    await page.waitForURL(/\/login\/?/);

    await page.goto("/login");
    await page.locator('input[type="email"]').fill(email);
    await page.locator('input[type="password"]').fill("DefinitelyWrongPass123!");
    await page.getByRole("button", { name: /inicia sesión|sign in/i }).click();

    // Must stay on /login with a visible error — never redirect to /analyze/.
    // The backend doesn't localize error messages, so this is always English.
    await expect(page).toHaveURL(/\/login\/?/);
    await expect(page.getByText(/invalid email or password/i)).toBeVisible();
  });
});
