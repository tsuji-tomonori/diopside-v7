import { expect, Page, test, TestInfo } from '@playwright/test';

const consentStorageKey = 'diopside_consent_v1';
const fixtureVideoTitle = '【歌枠】深夜リクエスト大会！';

const deterministicThumbnail = `
<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360">
  <rect width="640" height="360" fill="#EDE7F8" />
  <circle cx="320" cy="150" r="72" fill="#7C5CBF" />
  <path d="M292 105h48c40 0 68 19 68 45s-28 45-68 45h-48z" fill="#FFFFFF" />
  <text x="320" y="270" text-anchor="middle" font-family="Arial, sans-serif" font-size="34" fill="#211D2B">diopside archive</text>
</svg>`;

function observeRuntimeErrors(page: Page): () => void {
  const errors: string[] = [];

  page.on('pageerror', (error) => {
    errors.push(`pageerror: ${error.message}`);
  });
  page.on('console', (message) => {
    if (message.type() === 'error') {
      errors.push(`console: ${message.text()}`);
    }
  });

  return () => expect(errors).toEqual([]);
}

async function prepareDeterministicBrowser(page: Page): Promise<void> {
  await page.addInitScript(() => {
    Math.random = () => 0.25;
  });
  await page.route('https://picsum.photos/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'image/svg+xml',
      body: deterministicThumbnail,
    });
  });
}

async function seedConsent(page: Page): Promise<void> {
  await page.addInitScript(([key]) => {
    window.localStorage.setItem(
      key,
      JSON.stringify({
        schemaVersion: 1,
        policyMajor: '1',
        acceptedAt: '2026-07-26T00:00:00.000Z',
      }),
    );
  }, [consentStorageKey]);
}

async function captureUi(page: Page, testInfo: TestInfo, name: string): Promise<void> {
  const screenshotPath = testInfo.outputPath(`${testInfo.project.name}-${name}.png`);
  await page.screenshot({
    path: screenshotPath,
    fullPage: true,
    animations: 'disabled',
  });
  await testInfo.attach(`${testInfo.project.name}-${name}`, {
    path: screenshotPath,
    contentType: 'image/png',
  });
}

test.describe('critical public user journeys', () => {
  test.beforeEach(async ({ page }) => {
    await prepareDeterministicBrowser(page);
  });

  test('home and primary navigation adapt to the viewport', async ({ page }, testInfo) => {
    const assertNoRuntimeErrors = observeRuntimeErrors(page);

    await page.goto('/');

    await expect(page.getByRole('heading', { name: 'diopside', level: 1 })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'newest archives', level: 2 })).toBeVisible();
    await expect(page.getByRole('link', { name: new RegExp(fixtureVideoTitle) }).first()).toBeVisible();

    const isMobile = testInfo.project.name.includes('mobile');
    await expect(page.locator('.sidebar')).toBeVisible({ visible: !isMobile });
    await expect(page.locator('.bottom-nav')).toBeVisible({ visible: isMobile });

    await captureUi(page, testInfo, 'home');

    await page.getByRole('link', { name: '検索', exact: true }).click();
    await expect(page).toHaveURL(/\/search\?sort=newest$/);
    await expect(page.getByRole('heading', { name: 'search', level: 1 })).toBeVisible();

    assertNoRuntimeErrors();
  });

  test('keyboard search selects a suggestion and persists a canonical condition', async ({ page }, testInfo) => {
    const assertNoRuntimeErrors = observeRuntimeErrors(page);
    await seedConsent(page);

    await page.goto('/search');
    await expect(page.getByText('3 件', { exact: true })).toBeVisible();

    const query = page.getByRole('combobox', { name: 'キーワード' });
    await query.fill('歌枠');

    const suggestion = page.getByRole('option', { name: '歌枠' });
    await expect(suggestion).toBeVisible();
    await query.press('ArrowDown');
    await expect(suggestion).toHaveAttribute('aria-selected', 'true');
    await query.press('Enter');

    await expect(page).toHaveURL(/\/search\?q=%E6%AD%8C%E6%9E%A0&tag=tag-001&sort=newest$/);
    await expect(page.getByText('1 件', { exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: '歌枠 深夜 リクエスト 大会', level: 3 })).toBeVisible();
    await expect(page.getByRole('button', { name: 'recent search 歌枠 を再適用' })).toBeVisible();

    await captureUi(page, testInfo, 'search-result');
    assertNoRuntimeErrors();
  });

  test('detail consent, save, and history form one complete journey', async ({ page }, testInfo) => {
    const assertNoRuntimeErrors = observeRuntimeErrors(page);

    await page.goto('/videos/rY4A7Lxk12Q');

    await expect(page.getByRole('heading', { name: 'video detail', level: 1 })).toBeVisible();
    await expect(page.getByText('YouTube/API由来の情報・派生表示は同意後に有効です。')).toBeVisible();
    await captureUi(page, testInfo, 'detail-consent');

    await page.getByRole('button', { name: '同意して進む' }).click();
    await expect(page.getByRole('heading', { name: fixtureVideoTitle, level: 2 })).toBeVisible();
    await expect(page.getByRole('link', { name: 'YouTubeで見る' })).toHaveAttribute(
      'href',
      'https://www.youtube.com/watch?v=rY4A7Lxk12Q',
    );
    await expect(page.getByRole('heading', { name: 'derived artifacts', level: 3 })).toBeVisible();
    await captureUi(page, testInfo, 'detail-consented');

    await page.getByRole('button', { name: '保存する' }).click();
    await expect(page.getByRole('status')).toHaveText('保存しました。');

    await page.getByRole('link', { name: '保存', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'saved', level: 1 })).toBeVisible();
    await expect(page.getByRole('heading', { name: fixtureVideoTitle, level: 3 })).toBeVisible();
    await captureUi(page, testInfo, 'saved');

    await page.getByRole('link', { name: '履歴', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'history', level: 1 })).toBeVisible();
    await expect(page.getByRole('heading', { name: fixtureVideoTitle, level: 3 })).toBeVisible();
    await captureUi(page, testInfo, 'history');

    assertNoRuntimeErrors();
  });
});
