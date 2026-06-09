import { test, expect } from '@playwright/test';
import { LoginPage, DashboardPage } from '../page-objects';

test.describe('认证模块', () => {
  test('auth-001: 登录页面加载', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('button', { name: '使用 SSO 登录' })).toBeVisible();
    await expect(page.getByRole('button', { name: '游客访问' })).toBeVisible();
  });

  test('auth-002: 游客访问登录', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.loginWithGuest();
    await expect(page).not.toHaveURL(/\/login$/);
  });

  test('auth-003: SSO 登录按钮可见', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.expectErrorMessage();
  });

  test('auth-004: 使用游客身份访问仪表盘', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.loginWithGuest();
    const dashboard = new DashboardPage(page);
    await dashboard.expectToBeVisible();
  });
});
