import { test, expect } from '@playwright/test';
import { LoginPage } from '../page-objects';

test.describe('导航测试', () => {
  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.loginWithGuest();
  });

  test('nav-001: 首页仪表盘加载', async ({ page }) => {
    await page.goto('/import');
    await expect(page.locator('aside')).toBeVisible();
    await expect(page.locator('header')).toBeVisible();
  });

  test('nav-002: 侧边栏导航到酒店管理', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: '酒店管理' }).click();
    await expect(page).toHaveURL(/\/hotels/);
  });

  test('nav-003: 侧边栏导航到数据导入', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: '数据导入' }).click();
    await expect(page).toHaveURL(/\/import/);
  });

  test('nav-004: 侧边栏导航到翻译工具', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: '翻译工具' }).click();
    await expect(page).toHaveURL(/\/translate/);
  });
});

test.describe('页面功能测试', () => {
  test('page-001: 酒店列表页面加载', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.loginWithGuest();
    await page.goto('/hotels');
    await expect(page.locator('table')).toBeVisible();
  });

  test('page-002: 数据导入页面加载', async ({ page }) => {
    await page.goto('/import');
    await expect(page.locator('.border-dashed')).toBeVisible();
  });

  test('page-003: 翻译工作台页面加载', async ({ page }) => {
    await page.goto('/translate');
    await expect(page.getByPlaceholder('输入要翻译的文本...')).toBeVisible();
  });
});
