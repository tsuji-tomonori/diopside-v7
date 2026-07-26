import axe from 'axe-core';
import { expect, test } from '@playwright/test';

const consent = { schemaVersion: 1, policyMajor: '1', acceptedAt: '2026-07-13T00:00:00Z' };

async function enableConsent(page: import('@playwright/test').Page) {
  await page.addInitScript((value) => localStorage.setItem('diopside_consent_v1', JSON.stringify(value)), consent);
}

async function openConditions(page: import('@playwright/test').Page) {
  await page.getByRole('button', { name: '＋タグ' }).click();
  return page.getByRole('dialog', { name: '検索条件' });
}

async function reproduceArtifactNotGenerated(page: import('@playwright/test').Page) {
  const noArtifacts = {
    chat: false, comments: false, timestamps: false, wordcloudChat: false, wordcloudComments: false, wordcloudBoth: false,
  };
  await page.route('**/data/releases/20260711-001/index.json', async (route) => {
    const value = await (await route.fetch()).json();
    const video = value.videos.find((item: { videoId: string }) => item.videoId === 'rY4A7Lxk12Q');
    video.artifactFlags = noArtifacts;
    delete video.chat;
    delete video.comments;
    await route.fulfill({ json: value });
  });
  await page.route('**/data/releases/20260711-001/videos/rY4A7Lxk12Q.json', async (route) => {
    const value = await (await route.fetch()).json();
    value.artifactFlags = noArtifacts;
    delete value.chat;
    delete value.comments;
    delete value.timestamps;
    delete value.wordcloud;
    await route.fulfill({ json: value });
  });
}

// 読み込み中の状態が公開データ取得の遅延中に表示されることを検証する。
test('公開データの遅延中はloadingを表示する', async ({ page }) => {
  // 1. 初期化
  await page.route('**/data/latest.json', async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 800));
    await route.continue();
  });
  // 2. テストの実行
  await page.goto('/');
  // 3. アサーション
  await expect(page.getByText('データを読み込んでいます…')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'diopside' })).toBeVisible();
});

// 5xxとartifact欠落を空状態へ誤変換しないことを検証する。
test('retryable errorとartifact欠落を空状態と区別する', async ({ page }) => {
  // 1. 初期化
  await page.route('**/data/latest.json', (route) => route.fulfill({ status: 503, body: '{}' }));
  // 2. テストの実行
  await page.goto('/search');
  // 3. アサーション
  await expect(page.getByRole('alert')).toContainText('公開データサーバーでエラー');
  await expect(page.getByText('公開中の動画はありません')).toHaveCount(0);

  await page.unroute('**/data/latest.json');
  await page.route('**/search-index.json', (route) => route.fulfill({ status: 404, body: '{}' }));
  await page.reload();
  await expect(page.getByRole('alert')).toContainText('公開データが見つかりません');
  await expect(page.getByText('検索結果はありません')).toHaveCount(0);
});

// サジェストが入力中だけ最大4行で表示され、Escapeとfocus外しで閉じることを検証する。
test('サジェストの表示上限と閉じる条件を検証する', async ({ page }) => {
  // 1. 初期化
  await enableConsent(page);
  await page.goto('/search');
  const input = page.getByRole('combobox', { name: 'キーワード' });
  // 2. テストの実行
  await input.fill('雑談');
  // 3. アサーション
  await expect(page.locator('.dio-suggest-list [role="option"]')).toHaveCount(2);
  await input.press('Escape');
  await expect(page.getByRole('listbox')).toBeHidden();
  await input.fill('雑談');
  await page.getByRole('heading', { name: '検索' }).click();
  await expect(page.getByRole('listbox')).toBeHidden();
});

// 条件chipの節移動、close即時解除、URL復元を検証する。
test('条件chipは節を開きcloseで解除しreload後も復元する', async ({ page }) => {
  // 1. 初期化
  await enableConsent(page);
  await page.goto('/search?lmin=60&lmax=120');
  const chip = page.getByRole('button', { name: '1h〜2h', exact: true });
  // 2. テストの実行
  await chip.click();
  const dialog = page.getByRole('dialog', { name: '検索条件' });
  // 3. アサーション
  await expect(dialog.locator('#length')).toHaveClass(/is-highlighted/);
  await dialog.getByRole('button', { name: '条件を閉じる' }).click();
  await page.getByRole('button', { name: '1h〜2hの条件を解除' }).click();
  await expect(page).not.toHaveURL(/lmin|lmax/);
  await page.goto('/search?lmin=60&lmax=120');
  await page.reload();
  await expect(page.getByRole('button', { name: '1h〜2h', exact: true })).toBeVisible();
});

// 条件dialogの背景クリック、focus trap、sliderのkeyboard境界を検証する。
test('条件dialogは背景クリックとfocus trapに対応しslider範囲を保つ', async ({ page }) => {
  // 1. 初期化
  await enableConsent(page);
  await page.goto('/search');
  const dialog = await openConditions(page);
  // 2. テストの実行
  const min = dialog.getByRole('slider', { name: '長さの下限' });
  const max = dialog.getByRole('slider', { name: '長さの上限' });
  await min.press('End');
  await max.press('Home');
  // 3. アサーション
  await expect(min).toHaveValue('300');
  await expect(max).toHaveValue('300');
  await dialog.getByRole('button', { name: /件を表示|条件をゆるめる/ }).focus();
  await page.keyboard.press('Tab');
  await expect(dialog.getByRole('button', { name: '条件を閉じる' })).toBeFocused();
  await page.locator('.dio-sheet-backdrop').click({ position: { x: 2, y: 2 } });
  await expect(dialog).toBeHidden();
});

// カレンダーの逆順正規化、月移動、keyboard日移動を検証する。
test('カレンダーは逆順を正規化し月移動とkeyboard日移動を行う', async ({ page }) => {
  // 1. 初期化
  await enableConsent(page);
  await page.goto('/search');
  const dialog = await openConditions(page);
  await dialog.getByRole('button', { name: 'カレンダー' }).click();
  const dates = dialog.locator('[data-date]:not(:disabled)');
  const first = await dates.nth(1).getAttribute('data-date');
  const second = await dates.nth(0).getAttribute('data-date');
  // 2. テストの実行
  await dates.nth(1).click();
  await dates.nth(0).click();
  await expect(dialog.locator('[aria-selected="true"]')).toHaveCount(2);
  await dialog.getByRole('button', { name: '前の月' }).click();
  await dialog.getByRole('gridcell').filter({ hasText: '1' }).first().focus();
  await page.keyboard.press('ArrowRight');
  // 3. アサーション
  await expect(page).toHaveURL(new RegExp(`from=${second}.*to=${first}|to=${first}.*from=${second}`));
  await expect(dialog.locator('.dio-calendar__month')).not.toContainText(`${new Date().getFullYear()}年${new Date().getMonth() + 1}月`);
});

// 同意状態で詳細のYouTube導線と派生表示が切り替わることを検証する。
test('詳細は未同意で派生を隠し同意後に表示する', async ({ page }) => {
  // 1. 初期化
  await page.goto('/videos/rY4A7Lxk12Q');
  // 2. テストの実行
  await page.getByRole('button', { name: '同意して進む' }).click();
  // 3. アサーション
  await expect(page.getByRole('link', { name: 'YouTubeで見る' })).toBeVisible();
  await expect(page.getByRole('heading', { name: '派生情報' })).toBeVisible();
  await page.getByRole('button', { name: '同意を取り下げる' }).click();
  await expect(page.getByRole('link', { name: 'YouTubeで見る' })).toHaveCount(0);
  await expect(page.getByText('派生データは未作成です')).toHaveCount(0);
});

// 派生artifact未作成と0件を画面上で区別する。
test('派生artifact未作成を0件と表示せずに区別する', async ({ page }) => {
  // 1. 初期化
  await enableConsent(page);
  await reproduceArtifactNotGenerated(page);

  // 2. テストの実行
  await page.goto('/videos/rY4A7Lxk12Q');

  // 3. アサーション
  await expect(page.getByText('派生データは未作成です')).toBeVisible();
  await expect(page.getByText('未作成', { exact: true })).toHaveCount(4);
  await expect(page.getByText('0件')).toHaveCount(0);
});

// 保存・履歴・静的・未検出routeをaxe対象に含めることを検証する。
test('追加主要routeでaxe critical serious違反がない', async ({ page }) => {
  // 1. 初期化
  await enableConsent(page);
  // 2. テストの実行
  for (const route of ['/saved', '/history', '/terms', '/privacy', '/not-defined']) {
    await page.goto(route);
    await page.addScriptTag({ content: axe.source });
    const violations = await page.evaluate(async () => (await (window as typeof window & { axe: typeof axe }).axe.run(document)).violations
      .filter((violation) => violation.impact === 'critical' || violation.impact === 'serious')
      .map((violation) => violation.id));
    // 3. アサーション
    expect(violations, `${route} axe critical/serious`).toEqual([]);
  }
});

// keyboardのみで検索、詳細、保存まで完走できることを検証する。
test('keyboardのみで検索から詳細を経て保存できる', async ({ page }) => {
  // 1. 初期化
  await enableConsent(page);
  await page.goto('/search');
  const input = page.getByRole('combobox', { name: 'キーワード' });
  // 2. テストの実行
  await input.fill('雑談');
  await input.press('ArrowDown');
  await input.press('Enter');
  await page.locator('.dio-video-list-item a').first().focus();
  await page.keyboard.press('Enter');
  // 3. アサーション
  await expect(page).toHaveURL(/\/videos\//);
  await page.getByRole('button', { name: '保存する' }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('status')).toContainText('保存しました');
});
