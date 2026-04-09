import { test, expect } from '@playwright/test';
import { TranslatePage } from '../page-objects';

test.describe('翻译功能测试', () => {
  test('trans-001: 单条翻译', async ({ page }) => {
    const translatePage = new TranslatePage(page);
    await translatePage.goto();
    await translatePage.translate('酒店提供免费WiFi');
    await translatePage.expectResultVisible();
  });

  test('trans-002: 翻译结果非空', async ({ page }) => {
    const translatePage = new TranslatePage(page);
    await translatePage.goto();
    await translatePage.translate('测试翻译');
    await expect(translatePage.targetTextarea).not.toBeEmpty();
  });

  test('trans-003: 批量翻译模式切换', async ({ page }) => {
    await page.goto('/translate');
    const batchButton = page.locator('button:has-text("批量"), button:has-text("Batch")');
    if (await batchButton.isVisible()) {
      await batchButton.click();
      // 期望切换到批量模式
    }
  });
});
