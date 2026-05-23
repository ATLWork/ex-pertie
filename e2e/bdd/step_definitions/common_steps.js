const { Given, When, Then, Before, After } = require('@cucumber/cucumber');
const { chromium } = require('@playwright/test');
const { expect } = require('@playwright/test');

Before(async function () {
  this.browser = await chromium.launch({ headless: true });
  this.context = await this.browser.newContext();
  this.page = await this.context.newPage();
});

After(async function () {
  await this.page.close();
  await this.context.close();
  await this.browser.close();
});

Given('系统服务运行正常', async function () {
  const response = await this.page.goto('http://localhost:8000/api/v1/health');
  expect(response.ok()).toBeTruthy();
});

When('用户访问系统登录页', async function () {
  await this.page.goto('/login');
  await expect(this.page).toHaveTitle(/登录/);
});

When('输入邮箱 {string}，密码 {string}', async function (email, password) {
  if (email && email !== '""') {
    await this.page.fill('input[name="email"]', email);
  }
  if (password && password !== '""') {
    await this.page.fill('input[name="password"]', password);
  }
});

When('点击登录按钮', async function () {
  await Promise.all([
    this.page.waitForNavigation({ waitUntil: 'networkidle' }),
    this.page.click('button[type="submit"]')
  ]);
});

Then('系统登录成功，跳转至首页', async function () {
  await expect(this.page).toHaveURL(/dashboard/);
});

Then('页面显示错误提示 {string}', async function (message) {
  const errorMsg = this.page.locator(`text="${message}"`);
  await expect(errorMsg).toBeVisible();
});
