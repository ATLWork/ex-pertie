const { Given, When, Then } = require('@cucumber/cucumber');
const { expect } = require('@playwright/test');

Given('系统运行正常，用户已使用admin账号登录', async function () {
  await this.page.goto('/login');
  const usernameInput = this.page.locator('#username');
  await usernameInput.waitFor({ state: 'visible' });
  await usernameInput.fill('adminuser');  // 使用 conftest.py 中的用户名

  const passwordInput = this.page.locator('#password');
  await passwordInput.waitFor({ state: 'visible' });
  await passwordInput.fill('Admin123456');

  const loginBtn = this.page.locator('button[type="submit"]');
  await loginBtn.click();
  await this.page.waitForURL(/\/(dashboard|import|$)/, { timeout: 10000 }).catch(() => {});
});

// 系统已导入测试酒店数据 - 使用 common_steps.js 中的定义

When('用户进入"数据导入"页面', async function () {
  await this.page.goto('/import');
  await expect(this.page).toHaveURL(/import/);
});

When('选择标准有效Excel文件上传', async function () {
  // 创建一个模拟的Excel文件
  const testFile = Buffer.from('测试Excel内容');
  await this.page.setInputFiles('input[type="file"]', {
    name: 'test-hotels.xlsx',
    mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    buffer: testFile
  });
});

Then('文件上传成功，系统解析完成后显示数据预览', async function () {
  const previewArea = this.page.locator('.import-preview, .data-preview');
  await expect(previewArea).toBeVisible({ timeout: 10000 });
});

When('用户点击"确认导入"按钮', async function () {
  const confirmBtn = this.page.locator('button:has-text("确认导入")').or(
    this.page.locator('button:has-text("导入")')
  );
  await confirmBtn.click();
});

Then('数据导入成功，提示导入成功信息', async function () {
  const successMsg = this.page.locator('.ant-message-success, .notification-success');
  await expect(successMsg).toBeVisible({ timeout: 10000 });
});

Then('酒店列表页显示导入的数据', async function () {
  await this.page.goto('/hotels');
  const table = this.page.locator('table');
  await expect(table).toBeVisible();
});

When('选择文件 {string} 上传', async function (filename) {
  // 根据不同的错误文件名，设置对应的模拟内容
  let buffer;
  switch (filename) {
    case 'empty_file.xlsx':
      buffer = Buffer.from('');
      break;
    case 'invalid_format.docx':
      buffer = Buffer.from('这不是Excel文件');
      break;
    case 'missing_required_field.xlsx':
      // 创建一个缺少必填字段的Excel
      buffer = Buffer.from('酒店名称\n'); // 只有表头，缺少必填字段
      break;
    default:
      buffer = Buffer.from('测试内容');
  }
  await this.page.setInputFiles('input[type="file"]', {
    name: filename,
    mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    buffer
  });
});

Then('导入失败，显示错误提示 {string}', async function (expectedError) {
  const errorMsg = this.page.locator(`.ant-message-error, .ant-alert, text="${expectedError}"`);
  await expect(errorMsg).toBeVisible({ timeout: 10000 });
});
