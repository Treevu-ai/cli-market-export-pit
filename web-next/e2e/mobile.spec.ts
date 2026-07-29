import { test, expect } from "@playwright/test";

test.describe("Mobile viewport (375px) — no horizontal overflow", () => {
  test.use({ viewport: { width: 375, height: 812 } });

  test("landing page renders without horizontal overflow", async ({ page }) => {
    // Arrange
    await page.goto("/");

    // Act
    const { scrollWidth, clientWidth } = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
    }));

    // Assert
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth);
  });

  test("integrations accordion renders without horizontal overflow, including corner badges", async ({ page }) => {
    // Arrange
    await page.goto("/");
    const section = page.locator("#integrations");
    await section.scrollIntoViewIfNeeded();

    // Act — expand a second family so multiple product cards (with their
    // corner HS-quality / category badges) are visible at once.
    await section.getByRole("button", { name: /Especias y aromáticas/ }).click();
    await expect(section.getByRole("link", { name: /Páprika/ })).toBeVisible();

    const { scrollWidth, clientWidth } = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
    }));

    // Assert
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth);
  });
});
