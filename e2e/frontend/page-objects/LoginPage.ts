import { Page, Locator, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly registerLink: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.usernameInput = page.locator('input[type="text"], input[name="username"]');
    this.passwordInput = page.locator('input[type="password"], input[name="password"]');
    this.submitButton = page.locator('button[type="submit"]');
    this.registerLink = page.locator('a:has-text("注册"), a:has-text("Register")');
    this.errorMessage = page.locator('.ant-alert, .ant-message-error, [role="alert"]');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(username: string, password: string) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async expectErrorMessage() {
    await expect(this.errorMessage).toBeVisible();
  }
}
