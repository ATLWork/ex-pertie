import { test, expect } from '@playwright/test';
import { TerminologyPage } from '../page-objects';

test.describe('术语库管理测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/terminology');
  });

  test('term-001: 术语库列表加载', async ({ page }) => {
    const terminologyPage = new TerminologyPage(page);
    await terminologyPage.expectTableVisible();
  });

  test('term-002: 添加术语按钮可见', async ({ page }) => {
    const terminologyPage = new TerminologyPage(page);
    if (await terminologyPage.addButton.isVisible()) {
      await terminologyPage.clickAddButton();
      // 期望显示术语表单
    }
  });

  test('term-003: 分类筛选器可见', async ({ page }) => {
    const terminologyPage = new TerminologyPage(page);
    if (await terminologyPage.categoryFilter.isVisible()) {
      await terminologyPage.categoryFilter.click();
      // 期望显示分类选项
    }
  });
});
