import { test, expect } from '@playwright/test';
import { ImportPage, ExportPage, LoginPage } from '../page-objects';

test.describe('数据导入测试', () => {
  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.loginWithGuest();
  });

  test('import-001: 导入页面加载', async ({ page }) => {
    const importPage = new ImportPage(page);
    await importPage.goto();
    await importPage.expectUploadAreaVisible();
  });

  test('import-002: 导入历史记录表格可见', async ({ page }) => {
    const importPage = new ImportPage(page);
    await importPage.goto();
    await importPage.expectHistoryTableVisible();
  });
});

test.describe('导出功能测试', () => {
  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.loginWithGuest();
  });

  test('export-001: 导出页面加载', async ({ page }) => {
    const exportPage = new ExportPage(page);
    await exportPage.goto();
    await exportPage.expectFormVisible();
  });

  test('export-002: 导出历史记录表格可见', async ({ page }) => {
    const exportPage = new ExportPage(page);
    await exportPage.goto();
    await exportPage.expectHistoryTableVisible();
  });
});
