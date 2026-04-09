import { Page, Locator, expect } from '@playwright/test';

export class TerminologyPage {
  readonly page: Page;
  readonly glossaryTable: Locator;
  readonly addButton: Locator;
  readonly categoryFilter: Locator;
  readonly searchInput: Locator;

  constructor(page: Page) {
    this.page = page;
    this.glossaryTable = page.locator('.ant-table');
    this.addButton = page.locator('button:has-text("添加"), button:has-text("新建"), button:has-text("Create")');
    this.categoryFilter = page.locator('.ant-select');
    this.searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="search"]');
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
