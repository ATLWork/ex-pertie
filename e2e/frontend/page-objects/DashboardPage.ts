import { Page, Locator, expect } from '@playwright/test';

export class DashboardPage {
  readonly page: Page;
  readonly sidebar: Locator;
  readonly header: Locator;
  readonly logoutButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.sidebar = page.locator('.ant-layout-sider, [class*="sider"]');
    this.header = page.locator('.ant-layout-header, [class*="header"]');
    this.logoutButton = page.locator('button:has-text("登出"), button:has-text("Logout")');
  }

  async goto() {
    await this.page.goto('/');
  }

  async expectToBeVisible() {
    await expect(this.sidebar).toBeVisible();
    await expect(this.header).toBeVisible();
  }
}
