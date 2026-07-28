import axe from 'axe-core';
import { expect, test } from '@playwright/test';

const consent = {
  schemaVersion: 1,
  policyMajor: '1',
  acceptedAt: '2026-07-13T00:00:00Z',
};

async function enableSearchFeatures(page: import('@playwright/test').Page) {
  await page.addInitScript((value) => {
    localStorage.setItem('diopside_consent_v1', JSON.stringify(value));
  }, consent);
}

async function openConditions(page: import('@playwright/test').Page) {
  const trigger = page.getByRole('button', { name: '＋タグ' });
  await trigger.click();
  const dialog = page.getByRole('dialog', { name: '検索条件' });
  await expect(dialog).toBeVisible();

  return { dialog, trigger };
}

function localDateKey(offset: number): string {
  const value = new Date();
  value.setDate(value.getDate() + offset);
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

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
  await enableSearchFeatures(page);
  await page.goto('/search');
  const query = page.getByRole('combobox', { name: 'キーワード' });
  await query.fill('雑談');
  await query.press('ArrowDown');
  await expect(page.getByRole('listbox')).toBeVisible();
  await query.press('Enter');
  await expect(page.getByRole('status').last()).toContainText('検索条件へ追加しました');
});

// viewportごとにナビゲーションが一意に切り替わることを検証する。
test('viewportごとにmobile navigationとPCサイドバーを切り替える', async ({ page }, testInfo) => {
  await page.goto('/');
  const isMobile = testInfo.project.name === 'mobile-chrome';

  if (isMobile) {
    await expect(page.getByRole('navigation', { name: 'mobile navigation' })).toBeVisible();
    await expect(page.locator('.sidebar')).toBeHidden();
  } else {
    await expect(page.getByRole('navigation', { name: 'mobile navigation' })).toBeHidden();
    await expect(page.locator('.sidebar')).toBeVisible();
  }
});

// 条件UIが幅に応じた形状を持ち、閉じた後に開いた操作へ戻ることを検証する。
test('条件sheetまたはright panelはEscapeで閉じ、triggerへfocusを戻す', async ({ page }, testInfo) => {
  await enableSearchFeatures(page);
  await page.goto('/search');
  const { dialog, trigger } = await openConditions(page);

  if (testInfo.project.name === 'mobile-chrome') {
    await expect(dialog).toHaveClass(/dio-condition-sheet/);
    const placement = await dialog.evaluate((element) => {
      const bounds = element.getBoundingClientRect();
      return { bottom: Math.round(bounds.bottom), viewportBottom: window.innerHeight };
    });
    expect(placement.bottom).toBe(placement.viewportBottom);
  } else {
    await expect(page.locator('.dio-condition-panel .dio-condition-sheet')).toBeVisible();
    await expect(page.locator('.dio-condition-panel .dio-condition-sheet')).toHaveCSS('width', '320px');
  }

  await page.keyboard.press('Escape');
  await expect(dialog).toBeHidden();
  await expect(trigger).toBeFocused();
});

// 条件が変わった結果件数をCTAが即時に表し、空結果を区別することを検証する。
test('条件変更に合わせてCTA件数を更新し、0件時に緩和表示を出す', async ({ page }) => {
  await enableSearchFeatures(page);
  await page.goto('/search');
  const { dialog } = await openConditions(page);
  const cta = dialog.getByRole('button', { name: /件を表示/ });
  const before = await cta.textContent();

  await dialog.getByRole('button', { name: '雑談' }).click();
  await expect.poll(() => cta.textContent()).not.toBe(before);

  const query = page.getByRole('combobox', { name: 'キーワード' });
  await query.fill('__e2e_no_matching_video__');
  await query.press('Enter');
  await expect(dialog.getByRole('button', { name: '0件 — 条件をゆるめる' })).toBeVisible();
});

// カレンダーが遷移せずに日付範囲を反映し、未来日を禁止することを検証する。
test('カレンダーはsheet内で範囲を確定し、未来日を選択できない', async ({ page }) => {
  await enableSearchFeatures(page);
  await page.goto('/search');
  const { dialog } = await openConditions(page);
  await dialog.getByRole('button', { name: 'カレンダー' }).click();
  await expect(dialog.getByRole('heading', { name: '投稿日' })).toBeVisible();
  await expect(dialog.locator('#tags')).toHaveCount(0);
  await expect(page).toHaveURL(/\/search(?:\?|$)/);

  const start = localDateKey(-2);
  const end = localDateKey(-1);
  const future = localDateKey(1);

  await expect(dialog.locator(`[data-date="${future}"]`)).toBeDisabled();
  await dialog.locator(`[data-date="${start}"]`).click();
  await dialog.locator(`[data-date="${end}"]`).click();
  await expect(page).toHaveURL(new RegExp(`from=${start}.*to=${end}|to=${end}.*from=${start}`));
  await dialog.getByRole('button', { name: '条件に戻る' }).click();
  await expect(page.getByRole('button', { name: `${start}〜${end}`, exact: true })).toBeVisible();
});

// pointerを使わず、Tabと候補選択だけで検索結果へ到達できることを検証する。
test('Tab・矢印・Enterだけでタグ条件を追加して結果へ到達できる', async ({ page }) => {
  await enableSearchFeatures(page);
  await page.goto('/search');
  await page.keyboard.press('Tab');
  await expect(page.getByText('本文へスキップ')).toBeFocused();
  const query = page.getByRole('combobox', { name: 'キーワード' });
  for (let index = 0; index < 12; index += 1) {
    await page.keyboard.press('Tab');
    if (await query.evaluate((element) => document.activeElement === element)) {
      break;
    }
  }
  await expect(query).toBeFocused();
  await page.keyboard.type('雑談');
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/tag=tag-/);
  await expect(page.getByRole('status').last()).toContainText('検索条件へ追加しました');
  await expect(page.getByText(/件$/).first()).toBeVisible();
});

// 主要公開画面に重大度critical/seriousの自動検出a11y違反がないことを検証する。
test('主要routeでaxe critical/serious違反がない', async ({ page }) => {
  await enableSearchFeatures(page);
  for (const route of ['/', '/search', '/videos/rY4A7Lxk12Q']) {
    await page.goto(route);
    await page.addScriptTag({ content: axe.source });
    const violations = await page.evaluate(async () => {
      const results = await (window as typeof window & { axe: typeof axe }).axe.run(document);
      return results.violations
        .filter((violation) => violation.impact === 'critical' || violation.impact === 'serious')
        .map(({ id, impact, nodes }) => ({ id, impact, nodes: nodes.length }));
    });
    expect(violations, `${route} axe critical/serious`).toEqual([]);
  }
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
