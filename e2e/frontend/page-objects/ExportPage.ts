import { Page, Locator, expect } from '@playwright/test';

export class ExportPage {
  readonly page: Page;
  readonly exportButton: Locator;
  readonly formatSelect: Locator;
  readonly historyTable: Locator;

  constructor(page: Page) {
    this.page = page;
    this.exportButton = page.locator('button:has-text("导出"), button:has-text("Export")');
    this.formatSelect = page.locator('.ant-select');
    this.historyTable = page.locator('.ant-table');
  }

  async goto() {
    await this.page.goto('/export');
  }

  async expectFormVisible() {
    await expect(this.exportButton.or(this.formatSelect)).toBeVisible();
  }

  async expectHistoryTableVisible() {
    await expect(this.historyTable).toBeVisible();
  }
}
