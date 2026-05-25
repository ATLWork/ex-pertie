const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ baseURL: 'http://localhost:3000' });

  console.log('1. 访问登录页...');
  await page.goto('/login');
  await page.waitForLoadState('networkidle');

  // 点击 Register tab
  console.log('2. 点击 Register Tab...');
  await page.click('.ant-tabs-tab:has-text("Register")');
  await page.waitForTimeout(1000);

  // 列出 Register tab 内的所有输入框
  console.log('3. 查找 Register tab 内的输入框...');
  const inputs = await page.locator('.ant-tabs-tabpane-active input').all();
  console.log(`找到 ${inputs.length} 个输入框`);
  for (const input of inputs) {
    const name = await input.getAttribute('name');
    const type = await input.getAttribute('type');
    const id = await input.getAttribute('id');
    const placeholder = await input.getAttribute('placeholder');
    console.log(`  name=${name}, type=${type}, id=${id}, placeholder=${placeholder}`);
  }

  await browser.close();
})();