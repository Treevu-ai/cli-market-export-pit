import { test, expect } from "@playwright/test";

test.describe("Integrations accordion", () => {
  test("expands the Frutas frescas family by default and keeps others collapsed", async ({ page }) => {
    // Arrange
    await page.goto("/");
    const section = page.locator("#integrations");
    await section.scrollIntoViewIfNeeded();

    // Act / Assert
    const frutasTrigger = section.getByRole("button", { name: /Frutas frescas/ });
    await expect(frutasTrigger).toHaveAttribute("aria-expanded", "true");

    const especiasTrigger = section.getByRole("button", { name: /Especias y aromáticas/ });
    await expect(especiasTrigger).toHaveAttribute("aria-expanded", "false");
  });

  test("expands a collapsed family when its header is clicked", async ({ page }) => {
    // Arrange
    await page.goto("/");
    const section = page.locator("#integrations");
    await section.scrollIntoViewIfNeeded();
    const granosTrigger = section.getByRole("button", { name: /Granos y semillas/ });
    await expect(granosTrigger).toHaveAttribute("aria-expanded", "false");

    // Act
    await granosTrigger.click();

    // Assert
    await expect(granosTrigger).toHaveAttribute("aria-expanded", "true");
    await expect(section.getByRole("link", { name: /Quinua/ })).toBeVisible();
  });

  test("navigates to /analyze/ with the correct query params when a product card is clicked", async ({ page }) => {
    // Arrange
    await page.goto("/");
    const section = page.locator("#integrations");
    await section.scrollIntoViewIfNeeded();

    // The "derivadosFuncionales" family (which contains Cacao) is collapsed by
    // default, so expand it first.
    const derivadosTrigger = section.getByRole("button", { name: /Derivados y funcionales/ });
    await derivadosTrigger.click();
    const cacaoCard = section.getByRole("link", { name: /Cacao/ });
    await expect(cacaoCard).toBeVisible();

    // Act
    await cacaoCard.click();

    // Assert
    await expect(page).toHaveURL(/\/analyze\/\?query=cacao(\+|%20)alto(\+|%20)flavanol&market=US/);
  });
});
