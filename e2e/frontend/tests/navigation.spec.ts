import { test, expect } from '@playwright/test';
import { DashboardPage, HotelsPage, ImportPage, TranslatePage } from '../page-objects';

test.describe('导航测试', () => {
  test('nav-001: 首页仪表盘加载', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.expectToBeVisible();
  });

  test('nav-002: 侧边栏导航到酒店管理', async ({ page }) => {
    await page.goto('/');
    await page.click('text=Hotels, text=酒店');
    await expect(page).toHaveURL(/\/hotels/);
  });

  test('nav-003: 侧边栏导航到数据导入', async ({ page }) => {
    await page.goto('/');
    await page.click('text=Data Import, text=导入');
    await expect(page).toHaveURL(/\/import/);
  });

  test('nav-004: 侧边栏导航到翻译工作台', async ({ page }) => {
    await page.goto('/');
    await page.click('text=Translation, text=翻译');
    await expect(page).toHaveURL(/\/translate/);
  });
});

test.describe('页面功能测试', () => {
  test('page-001: 酒店列表页面加载', async ({ page }) => {
    const hotelsPage = new HotelsPage(page);
    await hotelsPage.goto();
    await hotelsPage.expectTableVisible();
  });

  test('page-002: 数据导入页面加载', async ({ page }) => {
    const importPage = new ImportPage(page);
    await importPage.goto();
    await importPage.expectUploadAreaVisible();
  });

  test('page-003: 翻译工作台页面加载', async ({ page }) => {
    const translatePage = new TranslatePage(page);
    await translatePage.goto();
    await expect(translatePage.sourceTextarea).toBeVisible();
  });
});
