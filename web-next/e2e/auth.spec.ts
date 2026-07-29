import { test, expect } from "@playwright/test";

test.describe("Signup form client-side validation", () => {
  test("shows a validation error for a weak password without contacting the network", async ({ page }) => {
    // Arrange
    let signupRequestFired = false;
    await page.route("**/auth/signup**", async (route) => {
      signupRequestFired = true;
      await route.abort();
    });
    await page.goto("/signup/");

    // Act
    // Note: the email/password <label> elements in SignupForm are not
    // programmatically associated (no htmlFor/id), so getByLabel is not
    // reliable here — fall back to input[type] selectors.
    // The password is 8+ chars (satisfies the native `minLength` constraint
    // so the browser lets the form submit) but has no uppercase letter, so
    // the app's own `validatePassword` should reject it.
    await page.locator('input[type="email"]').fill("valid-user@example.com");
    await page.locator('input[type="password"]').fill("abcdefgh");
    await page.getByRole("button", { name: /crear cuenta|creating/i }).click();

    // Assert — match the exact error string; a substring/regex match would
    // also hit the static password-hint text, which mentions "mayúscula" too.
    await expect(
      page.getByText("La contraseña debe tener al menos una mayúscula.", { exact: true })
    ).toBeVisible();
    expect(signupRequestFired).toBe(false);
  });

  test("blocks submission with an invalid email via native constraint validation", async ({ page }) => {
    // Arrange
    let signupRequestFired = false;
    await page.route("**/auth/signup**", async (route) => {
      signupRequestFired = true;
      await route.abort();
    });
    await page.goto("/signup/");
    const emailInput = page.locator('input[type="email"]');

    // Act
    await emailInput.fill("not-an-email");
    await page.locator('input[type="password"]').fill("Str0ng!Pass");
    await page.getByRole("button", { name: /crear cuenta|creating/i }).click();

    // Assert
    const isValid = await emailInput.evaluate((el: HTMLInputElement) => el.checkValidity());
    expect(isValid).toBe(false);
    expect(signupRequestFired).toBe(false);
  });
});

test.describe("Auth gating on /analyze/", () => {
  test("shows a login-required panel instead of the analysis form when logged out", async ({ page }) => {
    // Arrange / Act
    await page.goto("/analyze/");

    // Assert — this app gates in-place (no redirect): the console renders a
    // "sign in to analyze" panel and disables the submit button.
    await expect(page).toHaveURL(/\/analyze\/?/);
    await expect(page.getByText("Inicia sesión para analizar")).toBeVisible();
    await expect(page.getByRole("link", { name: "Crear cuenta" })).toBeVisible();
    await expect(page.getByRole("button", { name: /Analizar|Ejecutar/i })).toBeDisabled();
  });
});
