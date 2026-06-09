import { Page, Locator, expect } from '@playwright/test';

export class ImportPage {
  readonly page: Page;
  readonly uploadZone: Locator;
  readonly fileInput: Locator;
  readonly historyTable: Locator;

  constructor(page: Page) {
    this.page = page;
    this.uploadZone = page.locator('.border-dashed.cursor-pointer').first();
    this.fileInput = page.locator('input[type="file"]');
    this.historyTable = page.locator('table');
  }

  async goto() {
    await this.page.goto('/import');
  }

  async expectUploadAreaVisible() {
    await expect(this.uploadZone).toBeVisible();
  }

  async expectHistoryTableVisible() {
    await expect(this.historyTable).toBeVisible();
  }
}
