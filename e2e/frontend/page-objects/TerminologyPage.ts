import { Page, Locator, expect } from '@playwright/test';

export class TerminologyPage {
  readonly page: Page;
  readonly glossaryTable: Locator;
  readonly addButton: Locator;
  readonly categoryFilter: Locator;

  constructor(page: Page) {
    this.page = page;
    this.glossaryTable = page.locator('table');
    this.addButton = page.getByRole('button', { name: '添加术语' });
    this.categoryFilter = page.locator('select');
  }

  async goto() {
    await this.page.goto('/terminology');
  }

  async expectTableVisible() {
    await expect(this.glossaryTable).toBeVisible();
  }

  async clickAddButton() {
    await this.addButton.click();
  }
}
