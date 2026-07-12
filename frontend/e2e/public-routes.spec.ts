import { expect, test } from '@playwright/test';

test('all public routes render without console errors', async ({ page }) => {
  const errors: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text());
  });

  for (const route of ['/', '/search', '/saved', '/history', '/videos/rY4A7Lxk12Q', '/terms', '/privacy']) {
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

test('tag suggestions support keyboard selection and live feedback', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('diopside_consent_v1', JSON.stringify({
      schemaVersion: 1,
      policyMajor: '1',
      acceptedAt: '2026-07-13T00:00:00Z',
    }));
  });
  await page.goto('/search');
  const query = page.getByRole('combobox', { name: 'キーワード' });
  await query.fill('雑談');
  await query.press('ArrowDown');
  await expect(page.getByRole('listbox')).toBeVisible();
  await query.press('Enter');
  await expect(page.getByRole('status').last()).toContainText('検索条件へ追加しました');
});

test('detail server failure is classified and never enters history', async ({ page }) => {
  await page.route('**/videos/rY4A7Lxk12Q.json', async (route) => {
    await route.fulfill({ status: 503, contentType: 'application/json', body: '{}' });
  });
  await page.goto('/videos/rY4A7Lxk12Q');
  await expect(page.getByRole('alert')).toContainText('公開データサーバーでエラー');
  const history = await page.evaluate(() => localStorage.getItem('diopside_history_v1'));
  expect(history).toBeNull();
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

test('policy and deletion contact are reachable', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('link', { name: 'プライバシー・削除窓口' }).click();
  await expect(page).toHaveURL(/\/privacy$/);
  await expect(page.getByRole('link', { name: /削除・訂正を依頼/ })).toHaveAttribute('href', /github\.com/);
});
