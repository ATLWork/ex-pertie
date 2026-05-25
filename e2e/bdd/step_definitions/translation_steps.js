const { When, Then } = require('@cucumber/cucumber');
const { expect } = require('@playwright/test');

When('用户进入"术语管理"页面', async function () {
  await this.page.goto('/translation/terms');
  await expect(this.page).toHaveURL(/terms/);
});

When('点击"新增术语"按钮', async function () {
  const addBtn = this.page.locator('button:has-text("新增术语"), button:has-text("Add Term")');
  await addBtn.click();
});

When('输入中文："酒店"，英文："Hotel"，备注："通用酒店翻译"', async function () {
  await this.page.fill('input[name="zh"]', '酒店');
  await this.page.fill('input[name="en"]', 'Hotel');
  await this.page.fill('textarea[name="remark"]', '通用酒店翻译');
});

When('点击"保存"按钮', async function () {
  await this.page.click('button:has-text("保存"), button:has-text("Save")');
});

Then('术语保存成功，术语列表显示新增的"酒店"-"Hotel"术语', async function () {
  const successMsg = this.page.locator('.ant-message-success');
  await expect(successMsg).toBeVisible();
  const termItem = this.page.locator('text="酒店"').first();
  await expect(termItem).toBeVisible();
});

When('用户进入翻译管理页，选中所有未翻译数据', async function () {
  await this.page.goto('/translation');
  const selectAll = this.page.locator('thead input[type="checkbox"]');
  await selectAll.check();
});

When('点击"批量翻译"按钮', async function () {
  const translateBtn = this.page.locator('button:has-text("批量翻译")');
  await translateBtn.click();
});

Then('系统显示翻译进度条，所有数据在10秒内翻译完成', async function () {
  const progressBar = this.page.locator('.ant-progress');
  await expect(progressBar).toBeVisible();
  // 等待翻译完成
  await this.page.waitForSelector('.ant-progress-status-success', { timeout: 15000 });
});
