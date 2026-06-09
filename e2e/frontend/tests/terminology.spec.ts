import { test, expect } from '@playwright/test';
import { TerminologyPage } from '../page-objects';

test.describe('术语库管理测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/terminology');
  });

  test('term-001: 术语库表格加载', async ({ page }) => {
    const terminologyPage = new TerminologyPage(page);
    await expect(terminologyPage.glossaryTable).toBeVisible();
  });

  test('term-002: 添加术语按钮可见', async ({ page }) => {
    const terminologyPage = new TerminologyPage(page);
    await expect(terminologyPage.addButton).toBeVisible();
  });
});
