import { expect, test } from '@playwright/test';

test('all public routes render without console errors', async ({ page }) => {
  const errors: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text());
  });

  for (const route of ['/', '/search', '/saved', '/history', '/videos/rY4A7Lxk12Q']) {
    await page.goto(route);
    await expect(page.locator('main')).toBeVisible();
    await expect(page.locator('main'), route).not.toContainText('失敗しました');
    await expect(page.locator('h1')).toBeVisible();
  }
  expect(errors).toEqual([]);
});

test('search query is canonicalized and results remain available', async ({ page }) => {
  await page.goto('/search?tag=tag-002&tag=tag-002&lmin=-1&sort=unknown');
  await expect(page).toHaveURL(/\/search\?sort=newest$/);
  await expect(page.getByText(/件$/).first()).toBeVisible();
});

test('keyboard user can skip to main content', async ({ page }) => {
  await page.goto('/');
  await page.keyboard.press('Tab');
  const skip = page.getByText('本文へスキップ');
  await expect(skip).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('#main-content')).toBeFocused();
});

test('admin route is not exposed and redirects home', async ({ page }) => {
  await page.goto('/admin');
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole('link', { name: '管理' })).toHaveCount(0);
});
