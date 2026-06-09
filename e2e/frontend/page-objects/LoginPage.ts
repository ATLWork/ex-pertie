import { Page, Locator, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly ssoButton: Locator;
  readonly guestButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.ssoButton = page.getByRole('button', { name: '使用 SSO 登录' });
    this.guestButton = page.getByRole('button', { name: '游客访问' });
  }

  async goto() {
    await this.page.goto('/login');
  }

  async loginWithGuest() {
    await this.guestButton.click();
  }

  async loginWithSSO() {
    await this.ssoButton.click();
  }

  async expectErrorMessage() {
    // No traditional error message on SSO login page
    // Check for toast or alert if available
    const alert = this.page.locator('[role="alert"], [role="status"]');
    await expect(alert).toBeVisible();
  }
}
