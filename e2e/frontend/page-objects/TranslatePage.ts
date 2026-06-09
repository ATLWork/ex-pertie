import { Page, Locator, expect } from '@playwright/test';

export class TranslatePage {
  readonly page: Page;
  readonly sourceTextarea: Locator;
  readonly targetTextarea: Locator;
  readonly translateButton: Locator;
  readonly batchTranslateButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.sourceTextarea = page.getByPlaceholder('输入要翻译的文本...');
    this.targetTextarea = page.getByPlaceholder('翻译结果将显示在这里...');
    this.translateButton = page.getByRole('button', { name: /^翻译$/ });
    this.batchTranslateButton = page.getByRole('button', { name: '全部翻译' });
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
