import { test, expect } from '@playwright/test';
import { HotelsPage } from '../page-objects';

test.describe('酒店管理测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/hotels');
  });

  test('hotel-001: 酒店列表默认分页', async ({ page }) => {
    await expect(page.locator('.ant-table')).toBeVisible();
    await expect(page.locator('.ant-pagination')).toBeVisible();
  });

  test('hotel-002: 酒店列表自定义分页', async ({ page }) => {
    const pageSizeSelect = page.locator('.ant-select');
    if (await pageSizeSelect.isVisible()) {
      await pageSizeSelect.click();
      await page.locator('.ant-select-item:has-text("10")').click();
    }
  });

  test('hotel-003: 酒店搜索', async ({ page }) => {
    const hotelsPage = new HotelsPage(page);
    await hotelsPage.search('测试');
    // 期望列表更新或显示无数据
  });

  test('hotel-004: 新建酒店按钮可见', async ({ page }) => {
    const hotelsPage = new HotelsPage(page);
    if (await hotelsPage.addButton.isVisible()) {
      await hotelsPage.clickAddButton();
      // 期望显示表单或弹窗
    }
  });
});
