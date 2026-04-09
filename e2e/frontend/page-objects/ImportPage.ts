import { Page, Locator, expect } from '@playwright/test';

export class ImportPage {
  readonly page: Page;
  readonly uploadButton: Locator;
  readonly fileInput: Locator;
  readonly historyTable: Locator;
  readonly uploadProgress: Locator;

  constructor(page: Page) {
    this.page = page;
    this.uploadButton = page.locator('button:has-text("上传"), button:has-text("Upload"), button:has-text("导入")');
    this.fileInput = page.locator('input[type="file"]');
    this.historyTable = page.locator('.ant-table');
    this.uploadProgress = page.locator('.ant-progress');
  }

  async goto() {
    await this.page.goto('/import');
  }

  async expectUploadAreaVisible() {
    await expect(this.uploadButton.or(this.fileInput)).toBeVisible();
  }

  async expectHistoryTableVisible() {
    await expect(this.historyTable).toBeVisible();
  }
}
