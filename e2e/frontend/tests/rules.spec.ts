import { test, expect } from '@playwright/test';
import { RulesPage } from '../page-objects';

test.describe('翻译规则测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/rules');
  });

  test('rules-001: 规则表格加载', async ({ page }) => {
    const rulesPage = new RulesPage(page);
    await expect(rulesPage.rulesTable).toBeVisible();
  });

  test('rules-002: 添加规则按钮可见', async ({ page }) => {
    const rulesPage = new RulesPage(page);
    await expect(rulesPage.addButton).toBeVisible();
  });
});
