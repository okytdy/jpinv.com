const { defineConfig, devices } = require('@playwright/test');

const PORT = process.env.PORT || 4173;
const externalBaseURL = process.env.BASE_URL || process.env.PLAYWRIGHT_BASE_URL;
const baseURL = externalBaseURL || `http://127.0.0.1:${PORT}`;

module.exports = defineConfig({
  testDir: './tests',
  timeout: 30_000,
  expect: {
    timeout: 5_000,
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.01,
      threshold: 0.2,
      animations: 'disabled'
    }
  },
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    bypassCSP: true
  },
  ...(externalBaseURL
    ? {}
    : {
        webServer: {
          command: `npm run build && python3 -m http.server ${PORT} --bind 127.0.0.1 --directory dist`,
          url: baseURL,
          reuseExistingServer: !process.env.CI,
          timeout: 10_000
        }
      }),
  projects: [
    {
      name: 'chromium-desktop',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 1400 } }
    },
    {
      name: 'chromium-mobile',
      use: { ...devices['Pixel 5'], viewport: { width: 390, height: 844 } }
    }
  ]
});
