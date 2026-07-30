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
  await expect(page.locator('.result-count')).toHaveText(/^\d+件$/);
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

// 最小対応幅でも横overflowや固定navigationによる操作領域不足がないことを検証する。
test('320px幅で主要画面とnavigationを利用できる', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 568 });
  await page.goto('/');
  const viewport = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(viewport.scrollWidth).toBeLessThanOrEqual(viewport.clientWidth);

  for (const link of await page.getByRole('navigation', { name: 'mobile navigation' }).getByRole('link').all()) {
    const box = await link.boundingBox();
    expect(box?.height).toBeGreaterThanOrEqual(44);
  }
});

// mobile条件sheetがbuttonから開き、Escapeで閉じてfocusを戻すことを検証する。
test('mobile検索条件sheetをkeyboardで閉じてfocusを戻す', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto('/search');
  const trigger = page.getByRole('button', { name: /^条件/ });
  await trigger.click();
  await expect(page.getByRole('complementary', { name: '検索条件' })).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('complementary', { name: '検索条件' })).toBeHidden();
  await expect(trigger).toBeFocused();
});

// production UIに動作確認専用の操作を公開しないことを検証する。
test('保存画面に動作確認用controlを公開しない', async ({ page }) => {
  await page.goto('/saved');
  await expect(page.getByText(/動作確認/)).toHaveCount(0);
  await expect(page.getByRole('link', { name: 'アーカイブを探す' })).toBeVisible();
});

// mobileのsection actionが一行を保ち、主要見出しの視線を分断しないことを検証する。
test('375px幅でquick searchのactionを一行表示する', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto('/');
  const action = page.getByRole('link', { name: 'すべての条件を見る' });
  await expect(action).toBeVisible();
  const metrics = await action.evaluate((element) => {
    const range = document.createRange();
    range.selectNodeContents(element);
    return {
      lineRects: range.getClientRects().length,
      right: element.getBoundingClientRect().right,
      viewportWidth: document.documentElement.clientWidth,
    };
  });
  expect(metrics.lineRects).toBe(1);
  expect(metrics.right).toBeLessThanOrEqual(metrics.viewportWidth);
});

// desktopの検索条件panelで主要actionが初期viewport内に収まることを検証する。
test('desktop検索条件panelの主要actionを初期viewport内に表示する', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/search');
  const action = page.getByRole('button', { name: /^\d+件を見る$/ });
  await expect(action).toBeVisible();
  const box = await action.boundingBox();
  expect(box).not.toBeNull();
  expect((box?.y ?? 0) + (box?.height ?? 0)).toBeLessThanOrEqual(900);
});

// 外部thumbnailが取得できない場合もvideoとして識別できるfallbackを検証する。
test('thumbnail取得失敗時にvideo fallbackを表示する', async ({ page }) => {
  await page.route('https://picsum.photos/**', async (route) => {
    await route.abort();
  });
  await page.goto('/');
  await expect(page.locator('.video-thumb-fallback').first()).toBeVisible();
  await expect(page.getByText('サムネイルを表示できません').first()).toBeAttached();
});

// 詳細heroでthumbnail取得に失敗しても壊れた画像を残さず再生導線を維持する。
test('詳細thumbnail取得失敗時にvideo面と再生導線を維持する', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('diopside_consent_v1', JSON.stringify({
      schemaVersion: 1,
      policyMajor: '1',
      acceptedAt: '2026-07-31T00:00:00Z',
    }));
  });
  await page.route('https://picsum.photos/**', async (route) => {
    await route.abort();
  });
  await page.goto('/videos/rY4A7Lxk12Q');
  await expect(page.locator('.detail-media')).toBeVisible();
  await expect(page.locator('.detail-thumb')).toHaveCount(0);
  await expect(page.getByRole('link', { name: 'YouTubeで再生' })).toBeVisible();
});
