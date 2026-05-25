const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // 监听所有请求和响应
  page.on('request', req => {
    if (req.url().includes('/api/')) {
      console.log(`请求: ${req.method()} ${req.url()}`);
    }
  });

  page.on('response', res => {
    if (res.url().includes('/api/')) {
      console.log(`响应: ${res.status()} ${res.url()}`);
    }
  });

  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log(`控制台错误: ${msg.text().substring(0, 200)}`);
    }
  });

  console.log('访问登录页...');
  await page.goto('http://localhost:3000/login');
  await page.waitForLoadState('networkidle');

  console.log('填写表单...');
  await page.fill('#username', 'adminuser');
  await page.fill('#password', 'Admin123456');

  console.log('提交...');
  await page.click('button[type="submit"]');

  console.log('等待响应...');
  await page.waitForTimeout(5000);

  console.log(`URL: ${page.url()}`);
  const token = await page.evaluate(() => localStorage.getItem('token'));
  console.log(`Token: ${token ? '存在' : '不存在'}`);

  await browser.close();
})();