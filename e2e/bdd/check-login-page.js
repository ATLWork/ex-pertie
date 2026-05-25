const { chromium } = require('@playwright/test');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ baseURL: 'http://localhost:3000' });
  await page.goto('/login');
  console.log("=== 登录页所有输入框 ===");
  const inputs = await page.locator('input').all();
  for (const input of inputs) {
    const type = await input.getAttribute('type');
    const name = await input.getAttribute('name');
    const placeholder = await input.getAttribute('placeholder');
    const id = await input.getAttribute('id');
    console.log(`输入框：type=${type}, name=${name}, placeholder=${placeholder}, id=${id}`);
  }
  console.log("\n=== 登录页所有按钮 ===");
  const buttons = await page.locator('button').all();
  for (const btn of buttons) {
    const text = await btn.textContent();
    const type = await btn.getAttribute('type');
    console.log(`按钮：type=${type}, text=${text?.trim()}`);
  }
  await browser.close();
})();
