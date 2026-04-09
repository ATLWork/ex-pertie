import { Page, Locator, expect } from '@playwright/test';

export class TranslatePage {
  readonly page: Page;
  readonly sourceTextarea: Locator;
  readonly targetTextarea: Locator;
  readonly translateButton: Locator;
  readonly batchModeButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.sourceTextarea = page.locator('textarea[name="source"], textarea[name="text"], textarea').first();
    this.targetTextarea = page.locator('textarea[name="target"], textarea[readonly]');
    this.translateButton = page.locator('button:has-text("翻译"), button:has-text("Translate")');
    this.batchModeButton = page.locator('button:has-text("批量"), button:has-text("Batch")');
  }

  async goto() {
    await this.page.goto('/translate');
  }

  async translate(text: string) {
    await this.sourceTextarea.fill(text);
    await this.translateButton.click();
  }

  async expectResultVisible() {
    await expect(this.targetTextarea).toBeVisible();
  }
}
