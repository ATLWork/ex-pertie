const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    baseURL: 'http://localhost:3000',
    ignoreHTTPSErrors: true
  });
  const page = await context.newPage();

  // 1. 获取 token
  console.log('1. 获取 token...');
  const loginData = await fetch('http://localhost:8000/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'adminuser', password: 'Admin123456' })
  }).then(r => r.json());
  const token = loginData.data.access_token;
  console.log(`Token: ${token.substring(0, 30)}...`);

  // 2. 先清除旧的
  console.log('2. 设置 token 并访问 /import...');
  await page.goto('about:blank');
  await page.context().addInitScript((t) => {
    localStorage.setItem('token', t);
  }, token);

  await page.goto('http://localhost:3000/import');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000);

  console.log(`URL: ${page.url()}`);
  const hasToken = await page.evaluate(() => !!localStorage.getItem('token'));
  console.log(`Has token: ${hasToken}`);

  // 3. 检查是否有 redirect 发生
  const url = page.url();
  if (url.includes('/login')) {
    console.log('被重定向到登录页!');
    // 检查 localStorage 是否被清除
    const clearedToken = await page.evaluate(() => localStorage.getItem('token'));
    console.log(`Token after redirect: ${clearedToken ? 'still exists' : 'cleared'}`);
  } else {
    console.log('成功访问 /import');
    const content = await page.content();
    console.log(`包含 "Import": ${content.includes('Import')}`);
    console.log(`包含 "Data": ${content.includes('Data')}`);
  }

  await browser.close();
})();