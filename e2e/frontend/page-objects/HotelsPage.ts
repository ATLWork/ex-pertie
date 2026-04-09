import { Page, Locator, expect } from '@playwright/test';

export class HotelsPage {
  readonly page: Page;
  readonly hotelTable: Locator;
  readonly addButton: Locator;
  readonly searchInput: Locator;
  readonly pagination: Locator;

  constructor(page: Page) {
    this.page = page;
    this.hotelTable = page.locator('.ant-table');
    this.addButton = page.locator('button:has-text("添加"), button:has-text("新建"), button:has-text("Create")');
    this.searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="search"]');
    this.pagination = page.locator('.ant-pagination');
  }

  async goto() {
    await this.page.goto('/hotels');
  }

  async expectTableVisible() {
    await expect(this.hotelTable).toBeVisible();
  }

  async clickAddButton() {
    await this.addButton.click();
  }

  async search(keyword: string) {
    await this.searchInput.fill(keyword);
    await this.searchInput.press('Enter');
  }
}
