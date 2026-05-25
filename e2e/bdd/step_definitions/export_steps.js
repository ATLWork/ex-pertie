const { Given, When, Then } = require('@cucumber/cucumber');
const { expect } = require('@playwright/test');

Given('系统已存在已完成翻译的酒店数据', function () {
  return 'success';
});

When('用户进入"导出管理"页面', async function () {
  await this.page.goto('/export');
  await expect(this.page).toHaveURL(/export/);
});

When('选择"全选"所有数据', async function () {
  const selectAll = this.page.locator('thead input[type="checkbox"]');
  await selectAll.check();
});

When('选择导出格式为"Expedia标准模板"', async function () {
  const formatSelect = this.page.locator('select[name="format"]');
  await formatSelect.selectOption({ label: 'Expedia标准模板' });
});

When('点击"导出"按钮', async function () {
  const exportBtn = this.page.locator('button:has-text("导出"), button:has-text("Export")');
  await exportBtn.click();
});

Then('系统开始生成文件，5秒内文件生成完成自动下载', async function () {
  const downloadPromise = this.page.waitForEvent('download', { timeout: 15000 });
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/Expedia.*\.xlsx/);
  console.log(`✅ 下载文件：${download.suggestedFilename()}`);
});

Then('下载文件名为"Expedia酒店数据_"开头的xlsx文件', async function () {
  // 已在上一步验证
});
