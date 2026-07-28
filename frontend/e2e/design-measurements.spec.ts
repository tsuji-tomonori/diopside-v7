import { expect, test } from '@playwright/test';

const consent = { schemaVersion: 1, policyMajor: '1', acceptedAt: '2026-07-13T00:00:00Z' };

async function enableConsent(page: import('@playwright/test').Page) {
  await page.addInitScript((value) => localStorage.setItem('diopside_consent_v1', JSON.stringify(value)), consent);
}

async function openConditions(page: import('@playwright/test').Page) {
  await page.goto('/search');
  await page.getByRole('button', { name: '＋タグ' }).click();
  return page.getByRole('dialog', { name: '検索条件' });
}

async function computed(page: import('@playwright/test').Page, selector: string, properties: string[]) {
  return page.locator(selector).first().evaluate((element, names) => {
    const style = getComputedStyle(element);
    return Object.fromEntries(names.map((name) => [name, style.getPropertyValue(name)]));
  }, properties);
}

// 適用済みの色を実要素で検証する。
test('色を実要素のcomputed styleで測定する', async ({ page }) => {
  // 1. 初期化
  await enableConsent(page);
  const dialog = await openConditions(page);
  await dialog.getByRole('button', { name: '雑談' }).click();
  await page.mouse.move(0, 0);

  // 2. テストの実行
  const colors = {
    primary: await computed(page, '.dio-condition-sheet__cta', ['background-color', 'color']),
    selectedChip: await computed(page, '.dio-chip.is-selected', ['background-color']),
    link: await computed(page, '.site-footer a', ['color']),
  };

  // 3. アサーション
  expect(colors.primary).toEqual({ 'background-color': 'rgb(124, 92, 191)', color: 'rgb(255, 255, 255)' });
  expect(colors.selectedChip['background-color']).toBe('rgb(237, 231, 248)');
  expect(colors.link.color).toBe('rgb(111, 79, 180)');
});

// 表示・caption・label・動画titleの文字組を実要素で検証する。
test('文字組を実要素のcomputed styleで測定する', async ({ page }) => {
  // 1. 初期化
  await enableConsent(page);
  await page.goto('/');
  await page.getByRole('heading', { name: 'diopside' }).waitFor();
  await expect(page.locator('.dio-display')).toHaveCSS('font-size', '24px');
  await page.goto('/search');

  // 2. テストの実行
  const typography = {
    caption: await computed(page, '.dio-video-list-item .dio-caption', ['font-size']),
    label: await computed(page, '.dio-label', ['font-size', 'font-weight', 'letter-spacing']),
    title: await computed(page, '.dio-video-list-item h3', ['font-size', 'font-weight']),
  };

  // 3. アサーション
  expect(typography.caption['font-size']).toBe('12.5px');
  expect(typography.label).toEqual({ 'font-size': '11px', 'font-weight': '700', 'letter-spacing': '1.32px' });
  expect(typography.title).toEqual({ 'font-size': '16px', 'font-weight': '700' });
});

// 角丸、罫線、focus ring、elevationを実要素で検証する。
test('形状とfocusを実要素のcomputed styleで測定する', async ({ page }, testInfo) => {
  // 1. 初期化
  await enableConsent(page);
  const dialog = await openConditions(page);
  await dialog.getByRole('button', { name: '雑談' }).click();
  await page.keyboard.press('Tab');
  await page.keyboard.press('Tab');

  // 2. テストの実行
  const values = {
    chip: await computed(page, '.dio-chip.is-selected', ['border-radius', 'border-top-width']),
    button: await computed(page, '.dio-condition-sheet__cta', ['border-radius', 'border-top-width']),
    card: await computed(page, '.dio-video-list-item', ['border-radius', 'border-top-width', 'box-shadow']),
    input: await computed(page, '.dio-search-bar', ['border-radius', 'border-top-width']),
    sheet: await computed(page, '.dio-condition-sheet', ['border-top-left-radius', 'box-shadow']),
    focus: await page.evaluate(() => {
      const element = document.activeElement as HTMLElement;
      const style = getComputedStyle(element);
      return { outlineWidth: style.outlineWidth, outlineStyle: style.outlineStyle };
    }),
    declaredBorderWidths: await page.evaluate(() => {
      const rules = Array.from(document.styleSheets)
        .flatMap((sheet) => Array.from(sheet.cssRules))
        .filter((rule): rule is CSSStyleRule => rule instanceof CSSStyleRule);
      const readBorderWidth = (selector: string) => {
        const style = rules.find((rule) => rule.selectorText.includes(selector))?.style;
        return style?.borderTopWidth || style?.border.split(' ')[0];
      };
      return {
        button: readBorderWidth('.dio-button'),
        chip: readBorderWidth('.dio-chip'),
        input: readBorderWidth('.dio-search-bar'),
        devicePixelRatio: window.devicePixelRatio,
      };
    }),
  };

  // 3. アサーション
  expect(values.chip).toEqual({ 'border-radius': '999px', 'border-top-width': '1px' });
  expect(values.button).toEqual({ 'border-radius': '12px', 'border-top-width': '1px' });
  expect(values.card).toEqual({ 'border-radius': '12px', 'border-top-width': '1px', 'box-shadow': 'none' });
  expect(values.input).toEqual({ 'border-radius': '14px', 'border-top-width': '1px' });
  expect(values.declaredBorderWidths).toMatchObject({ button: '1.5px', chip: '1.5px', input: '1.5px' });
  expect(values.declaredBorderWidths.devicePixelRatio).toBe(testInfo.project.name === 'mobile-chrome' ? 2.625 : 1);
  expect(values.focus).toEqual({ outlineWidth: '3px', outlineStyle: 'solid' });
  if (testInfo.project.name === 'mobile-chrome') {
    expect(values.sheet).toEqual({ 'border-top-left-radius': '20px', 'box-shadow': 'rgba(33, 29, 43, 0.16) 0px 8px 28px 0px' });
  } else {
    expect(values.sheet).toEqual({ 'border-top-left-radius': '0px', 'box-shadow': 'rgba(33, 29, 43, 0.16) 0px 8px 28px 0px' });
  }
});

// padding、gap、marginを実要素のcomputed styleで検証する。
test('余白を実要素のcomputed styleで測定する', async ({ page }, testInfo) => {
  // 1. 初期化
  await enableConsent(page);
  await page.goto('/');
  await page.getByRole('heading', { name: 'diopside' }).waitFor();

  // 2. テストの実行
  const spacing = {
    main: await computed(page, '.main-content', ['padding-left']),
    list: await computed(page, '.dio-home-page__mobile-videos', ['row-gap']),
    section: await computed(page, '.section', ['margin-top']),
  };

  // 3. アサーション
  expect(spacing.main['padding-left']).toBe(testInfo.project.name === 'mobile-chrome' ? '16px' : '24px');
  expect(spacing.list['row-gap']).toBe('12px');
  expect(spacing.section['margin-top']).toBe('32px');
});

// navigation、search、panel、buttonの寸法を実要素で検証する。
test('寸法を実要素のbounding rectで測定する', async ({ page }, testInfo) => {
  // 1. 初期化
  await enableConsent(page);
  const dialog = await openConditions(page);
  const rect = async (selector: string) => page.locator(selector).first().evaluate((element) => {
    const box = element.getBoundingClientRect();
    return { width: box.width, height: box.height };
  });

  // 2. テストの実行
  const dimensions = {
    search: await rect('.dio-search-bar'),
    primary: await rect('.dio-condition-sheet__cta'),
    panel: await rect('.dio-condition-sheet'),
    navigation: testInfo.project.name === 'mobile-chrome'
      ? await rect('.bottom-nav')
      : await rect('.sidebar'),
    navigationItem: testInfo.project.name === 'mobile-chrome'
      ? await rect('.bottom-nav a')
      : await rect('.sidebar a'),
    sidebarItemVisual: testInfo.project.name === 'mobile-chrome'
      ? null
      : await page.locator('.sidebar a.is-active').evaluate((element) => {
        const style = getComputedStyle(element, '::before');
        const box = element.getBoundingClientRect();
        return {
          height: box.height - Number.parseFloat(style.top) - Number.parseFloat(style.bottom),
          radius: style.borderTopLeftRadius,
        };
      }),
  };

  // 3. アサーション
  expect(dimensions.search.height).toBe(44);
  expect(dimensions.primary.height).toBe(48);
  if (testInfo.project.name === 'mobile-chrome') {
    expect(dimensions.navigation.height).toBe(57);
    expect(dimensions.navigationItem.height).toBe(56);
    expect(dimensions.panel.width).toBe(412);
  } else {
    expect(dimensions.navigation.width).toBe(220);
    expect(dimensions.navigationItem.height).toBe(44);
    expect(dimensions.sidebarItemVisual).toEqual({ height: 40, radius: '10px' });
    expect(dimensions.panel.width).toBe(320);
  }
});

// 可視buttonとlinkの操作領域を実要素のbounding rectで検証する。
test('操作領域を実要素のbounding rectで測定する', async ({ page }) => {
  // 1. 初期化
  await enableConsent(page);
  await page.goto('/search');

  // 2. テストの実行
  const controls = await page.evaluate(() => Array.from(document.querySelectorAll<HTMLElement>('button, a[href]'))
    .filter((element) => {
      const style = getComputedStyle(element);
      const box = element.getBoundingClientRect();
      return style.visibility !== 'hidden' && box.width > 0 && box.height > 0;
    })
    .map((element) => {
      const box = element.getBoundingClientRect();
      return { name: element.getAttribute('aria-label') ?? element.textContent?.trim() ?? element.tagName, width: box.width, height: box.height };
    }));

  // 3. アサーション
  expect(controls.filter((control) => control.width < 44 || control.height < 44), JSON.stringify(controls)).toEqual([]);
});

// カレンダーを開いた状態で、視覚セルと操作領域を別々に測定する。
test('カレンダー日付セルの視覚寸法と操作領域を実要素で測定する', async ({ page }) => {
  // 1. 初期化
  await enableConsent(page);
  const dialog = await openConditions(page);
  await dialog.getByRole('button', { name: 'カレンダー' }).click();
  const date = dialog.locator('.dio-calendar__row > button:not(:disabled)').first();

  // 2. テストの実行
  const dimensions = await date.evaluate((element) => {
    const hitArea = element.getBoundingClientRect();
    const visual = getComputedStyle(element, '::before');
    return {
      hitHeight: hitArea.height,
      hitWidth: hitArea.width,
      visualHeight: visual.height,
      visualWidth: visual.width,
    };
  });

  // 3. アサーション
  expect(dimensions.visualWidth).toBe('40px');
  expect(dimensions.visualHeight).toBe('40px');
  expect(dimensions.hitWidth).toBeGreaterThanOrEqual(44);
  expect(dimensions.hitHeight).toBeGreaterThanOrEqual(44);
});
