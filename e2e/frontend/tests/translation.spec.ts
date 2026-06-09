import { test, expect } from '@playwright/test';
import { TranslatePage } from '../page-objects';

test.describe('翻译功能测试', () => {
  test('trans-001: 单条翻译页面加载', async ({ page }) => {
    const translatePage = new TranslatePage(page);
    await translatePage.goto();
    await expect(translatePage.sourceTextarea).toBeVisible();
  });

  test('trans-002: 翻译按钮可见', async ({ page }) => {
    const translatePage = new TranslatePage(page);
    await translatePage.goto();
    await expect(translatePage.translateButton).toBeVisible();
  });

  test('trans-003: 批量翻译按钮可见', async ({ page }) => {
    const translatePage = new TranslatePage(page);
    await translatePage.goto();
    await expect(translatePage.batchTranslateButton).toBeVisible();
  });
});
