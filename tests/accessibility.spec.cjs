const { test, expect } = require('@playwright/test');
const { axeRoutes, redirectRoutes } = require('../qa/routes.cjs');
const { gotoRoute, runAxe, formatViolations } = require('./helpers.cjs');

test.describe('public route accessibility smoke tests', () => {
  for (const route of axeRoutes) {
    test(`${route.name} has no serious or critical axe blockers`, async ({ page }) => {
      await gotoRoute(page, route.path);
      await expect(page.locator('body')).toBeVisible();

      const results = await runAxe(page);
      const blockers = results.violations.filter((violation) => ['critical', 'serious'].includes(violation.impact));

      expect(formatViolations(blockers)).toBe('');
    });
  }
});

test.describe('redirect-only public routes', () => {
  for (const route of redirectRoutes) {
    test(`${route.name} keeps an accessible fallback link`, async ({ page }) => {
      await page.route('https://jpinv.com/**', (requestRoute) => requestRoute.abort());
      await page.goto(route.path, { waitUntil: 'domcontentloaded' }).catch(() => undefined);

      await expect(page.locator('main a')).toHaveAttribute('href', new RegExp(`${route.target.replace('/', '\\/')}$`));
    });
  }
});
