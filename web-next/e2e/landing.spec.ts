import { test, expect } from "@playwright/test";

test.describe("Landing page smoke test", () => {
  test("loads at / with a visible hero heading and nav", async ({ page }) => {
    // Arrange / Act
    await page.goto("/");

    // Assert
    await expect(page).toHaveTitle(/.+/);
    const heading = page.locator("h1");
    await expect(heading).toBeVisible();
    await expect(heading).toContainText("Antes de exportar");

    const nav = page.locator("header nav");
    await expect(nav).toBeVisible();
    await expect(nav.getByText("CLI MARKET")).toBeVisible();
  });

  test("renders the navigation links", async ({ page }) => {
    // Arrange
    await page.goto("/");

    // Act
    const nav = page.locator("header nav");

    // Assert
    await expect(nav.getByRole("link", { name: "Precios" })).toBeVisible();
    await expect(nav.getByRole("link", { name: "Iniciar sesión" })).toBeVisible();
  });
});
