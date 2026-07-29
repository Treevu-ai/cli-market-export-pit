import { test, expect } from "@playwright/test";

test.describe("Language toggle", () => {
  test("switches the hero headline and nav label from Spanish to English", async ({ page }) => {
    // Arrange
    await page.goto("/");
    const heading = page.locator("h1");
    await expect(heading).toContainText("Antes de exportar");
    const nav = page.locator("header nav");
    await expect(nav.getByRole("link", { name: "Iniciar sesión" })).toBeVisible();

    // Act
    await nav.getByRole("button", { name: "EN" }).click();

    // Assert
    await expect(heading).toContainText("Before you export");
    await expect(nav.getByRole("link", { name: "Log in" })).toBeVisible();
  });

  test("switches back to Spanish when ES is clicked again", async ({ page }) => {
    // Arrange
    await page.goto("/");
    const nav = page.locator("header nav");
    await nav.getByRole("button", { name: "EN" }).click();
    const heading = page.locator("h1");
    await expect(heading).toContainText("Before you export");

    // Act
    await nav.getByRole("button", { name: "ES" }).click();

    // Assert
    await expect(heading).toContainText("Antes de exportar");
  });
});
