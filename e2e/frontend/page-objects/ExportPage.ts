import { Page, Locator, expect } from '@playwright/test';

export class ExportPage {
  readonly page: Page;
  readonly newExportBtn: Locator;
  readonly formatSelect: Locator;
  readonly historyTable: Locator;

  constructor(page: Page) {
    this.page = page;
    this.newExportBtn = page.getByRole('button', { name: '新建导出' });
    this.formatSelect = page.locator('select');
    this.historyTable = page.locator('table');
  }

  async goto() {
    await this.page.goto('/export');
  }

  async expectFormVisible() {
    await expect(this.newExportBtn).toBeVisible();
  }

  async expectHistoryTableVisible() {
    await expect(this.historyTable).toBeVisible();
  }
}
