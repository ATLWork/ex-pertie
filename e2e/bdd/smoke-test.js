const { chromium } = require('@playwright/test');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('http://localhost:3000');
  const title = await page.title();
  console.log(`✅ 页面标题：${title}`);
  console.log("✅ Playwright环境运行正常");
  await browser.close();
})();
