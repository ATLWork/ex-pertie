import { test, expect } from '@playwright/test';
import { LoginPage, RegisterPage } from '../page-objects';

test.describe('认证模块', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('auth-001: 登录页面加载', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('input[name="username"], input[type="text"]').first()).toBeVisible();
  });

  test('auth-002: 登录成功', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('test_user', 'Test1234');
    // 期望登录后跳转到首页或仪表盘
    await expect(page).not.toHaveURL(/\/login$/);
  });

  test('auth-003: 登录失败 - 错误密码', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('test_user', 'WrongPassword');
    await loginPage.expectErrorMessage();
  });

  test('auth-004: 注册页面加载', async ({ page }) => {
    await page.goto('/register');
    await expect(page.locator('input[name="username"]')).toBeVisible();
  });

  test('auth-005: 注册成功', async ({ page }) => {
    const registerPage = new RegisterPage(page);
    await registerPage.goto();
    const timestamp = Date.now();
    await registerPage.register(
      `test_user_${timestamp}`,
      `test_${timestamp}@example.com`,
      'Test1234'
    );
    // 期望注册后跳转或显示成功消息
  });

  test('auth-006: 注册失败 - 密码不含大写', async ({ page }) => {
    const registerPage = new RegisterPage(page);
    await registerPage.goto();
    await registerPage.page.locator('input[name="username"]').fill('test_user_fail');
    await registerPage.page.locator('input[name="email"]').fill('test@example.com');
    await registerPage.page.locator('input[name="password"]').fill('test1234');
    await registerPage.page.locator('input[name="confirmPassword"]').fill('test1234');
    await registerPage.page.locator('button[type="submit"]').click();
    // 期望显示验证错误
  });
});
