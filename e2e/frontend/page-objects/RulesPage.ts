import { Page, Locator, expect } from '@playwright/test';

export class RulesPage {
  readonly page: Page;
  readonly rulesTable: Locator;
  readonly addButton: Locator;
  readonly activateButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.rulesTable = page.locator('.ant-table');
    this.addButton = page.locator('button:has-text("添加"), button:has-text("新建"), button:has-text("Create")');
    this.activateButton = page.locator('button:has-text("激活"), button:has-text("启用")');
  }

  async goto() {
    await this.page.goto('/rules');
  }

  async expectTableVisible() {
    await expect(this.rulesTable).toBeVisible();
  }
}
