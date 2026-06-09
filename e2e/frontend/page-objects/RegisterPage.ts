import { Page } from '@playwright/test';

/**
 * RegisterPage - Stub
 * The /register route does not exist in the current application.
 * Registration is handled via SSO callback. This class exists only
 * for backward compatibility with existing test imports.
 */
export class RegisterPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto() {
    // Route does not exist - will redirect to login
    await this.page.goto('/register');
  }

  async register(_username: string, _email: string, _password: string) {
    // No-op: registration not available via UI
  }
}
