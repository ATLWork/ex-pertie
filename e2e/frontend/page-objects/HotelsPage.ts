import { Page, Locator, expect } from '@playwright/test';

export class HotelsPage {
  readonly page: Page;
  readonly hotelTable: Locator;
  readonly addButton: Locator;
  readonly searchInput: Locator;

  constructor(page: Page) {
    this.page = page;
    this.hotelTable = page.locator('table');
    this.addButton = page.getByRole('button', { name: '添加酒店' });
    this.searchInput = page.getByPlaceholder('搜索酒店...');
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
