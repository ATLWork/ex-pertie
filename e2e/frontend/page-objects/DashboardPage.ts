import { Page, Locator, expect } from '@playwright/test';

export class DashboardPage {
  readonly page: Page;
  readonly sidebar: Locator;
  readonly header: Locator;
  readonly logoutButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.sidebar = page.locator('aside');
    this.header = page.locator('header');
    this.logoutButton = page.getByRole('menuitem', { name: '退出登录' });
  }

  async goto() {
    // Default landing page after login is /import
    await this.page.goto('/import');
  }

  async expectToBeVisible() {
    await expect(this.sidebar).toBeVisible();
    await expect(this.header).toBeVisible();
  }
}
