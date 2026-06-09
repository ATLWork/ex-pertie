import { Page, Locator, expect } from '@playwright/test';

export class RulesPage {
  readonly page: Page;
  readonly rulesTable: Locator;
  readonly addButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.rulesTable = page.locator('table');
    this.addButton = page.getByRole('button', { name: '添加规则' });
  }

  async goto() {
    await this.page.goto('/rules');
  }

  async expectTableVisible() {
    await expect(this.rulesTable).toBeVisible();
  }
}
