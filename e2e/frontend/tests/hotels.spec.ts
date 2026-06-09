import { test, expect } from '@playwright/test';
import { HotelsPage, LoginPage } from '../page-objects';

test.describe('酒店管理测试', () => {
  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.loginWithGuest();
    await page.goto('/hotels');
  });

  test('hotel-001: 酒店列表表格可见', async ({ page }) => {
    const hotelsPage = new HotelsPage(page);
    await expect(page.locator('table')).toBeVisible();
  });

  test('hotel-002: 搜索框可见', async ({ page }) => {
    const searchInput = page.getByPlaceholder('搜索酒店...');
    await expect(searchInput).toBeVisible();
  });

  test('hotel-003: 酒店搜索', async ({ page }) => {
    const hotelsPage = new HotelsPage(page);
    await hotelsPage.search('测试');
  });

  test('hotel-004: 新建酒店按钮可见', async ({ page }) => {
    const hotelsPage = new HotelsPage(page);
    await expect(hotelsPage.addButton).toBeVisible();
  });
});
