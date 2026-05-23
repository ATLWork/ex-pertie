const { defineConfig, devices } = require('@playwright/test');
module.exports = defineConfig({
  testDir: './features',
  use: {
    baseURL: 'http://localhost:3000',
    browserName: 'chromium',
    headless: true,
    viewport: { width: 1920, height: 1080 },
    ignoreHTTPSErrors: true,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } }
  ]
});
