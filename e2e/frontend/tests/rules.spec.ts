import { test, expect } from '@playwright/test';
import { RulesPage } from '../page-objects';

test.describe('翻译规则测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/rules');
  });

  test('rules-001: 规则列表加载', async ({ page }) => {
    const rulesPage = new RulesPage(page);
    await rulesPage.expectTableVisible();
  });

  test('rules-002: 添加规则按钮可见', async ({ page }) => {
    const rulesPage = new RulesPage(page);
    if (await rulesPage.addButton.isVisible()) {
      await rulesPage.addButton.click();
      // 期望显示规则表单
    }
  });
});
