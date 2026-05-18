const { test, expect } = require('@playwright/test');
const { visualRoutes, rfqRoutes } = require('../qa/routes.cjs');
const { gotoRoute, screenshotName } = require('./helpers.cjs');

test.describe('key page visual regression', () => {
  for (const route of visualRoutes) {
    test(`${route.name} viewport matches baseline`, async ({ page }, testInfo) => {
      await gotoRoute(page, route.path);
      await expect(page).toHaveScreenshot(screenshotName(route.name, 'page', testInfo.project.name), {
        fullPage: false
      });
    });
  }
});

test.describe('RFQ flow visual regression', () => {
  for (const route of rfqRoutes) {
    test(`${route.name} RFQ CTA pre-fills form state`, async ({ page }, testInfo) => {
      await gotoRoute(page, route.path);

      const rfqCta = page.locator('[data-rfq-service], [data-rfq-document], [data-rfq-message]').first();
      await expect(rfqCta).toBeVisible();
      await rfqCta.click();
      await expect(page.locator('#inquiry-form')).toBeVisible();
      await expect(page.locator('#service_type')).not.toHaveValue('');
      await expect(page.locator('#document_type')).not.toHaveValue('');
      await expect(page.locator('#message')).not.toHaveValue('');

      await expect(page.locator('#contact')).toHaveScreenshot(screenshotName(route.name, 'rfq-flow', testInfo.project.name), {
        animations: 'disabled'
      });
    });
  }
});
