import { expect, test } from '@playwright/test';

// 全公開routeがconsole errorなしで表示されることを検証する。
test('全公開routeをconsole errorなしで表示する', async ({ page }) => {
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

// 検索queryの正規化後も結果が利用可能なことを検証する。
test('検索queryを正規化して結果を維持する', async ({ page }) => {
  await page.goto('/search?tag=tag-002&tag=tag-002&lmin=-1&sort=unknown');
  await expect(page).toHaveURL(/\/search\?sort=newest$/);
  await expect(page.getByText(/件$/).first()).toBeVisible();
});

// タグ候補をkeyboardで選択でき、即時feedbackを得られることを検証する。
test('タグ候補のkeyboard選択と即時feedbackを提供する', async ({ page }) => {
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

// 詳細取得のserver失敗を分類し、履歴へ残さないことを検証する。
test('詳細取得のserver失敗を分類して履歴から除外する', async ({ page }) => {
  await page.route('**/videos/rY4A7Lxk12Q.json', async (route) => {
    await route.fulfill({ status: 503, contentType: 'application/json', body: '{}' });
  });
  await page.goto('/videos/rY4A7Lxk12Q');
  await expect(page.getByRole('alert')).toContainText('公開データサーバーでエラー');
  const history = await page.evaluate(() => localStorage.getItem('diopside_history_v1'));
  expect(history).toBeNull();
});

// keyboard利用者が本文へskipできることを検証する。
test('keyboard操作で本文へskipできる', async ({ page }) => {
  await page.goto('/');
  await page.keyboard.press('Tab');
  const skip = page.getByText('本文へスキップ');
  await expect(skip).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('#main-content')).toBeFocused();
});

// admin routeを公開せず、homeへredirectすることを検証する。
test('admin routeを非公開にしてhomeへredirectする', async ({ page }) => {
  await page.goto('/admin');
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole('link', { name: '管理' })).toHaveCount(0);
});

// policyと削除窓口へ到達できることを検証する。
test('policyと削除窓口へ到達できる', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('link', { name: 'プライバシー・削除窓口' }).click();
  await expect(page).toHaveURL(/\/privacy$/);
  await expect(page.getByRole('link', { name: /削除・訂正を依頼/ })).toHaveAttribute('href', /github\.com/);
});
