import { mkdir } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { chromium } from '@playwright/test';

const root = new URL('..', import.meta.url).pathname;
const outputDir = `${root}reports/private/ui-rewrite-20260726`;
const consent = { schemaVersion: 1, policyMajor: '1', acceptedAt: '2026-07-13T00:00:00Z' };

function start(command, args, cwd) {
  return spawn(command, args, { cwd, stdio: 'ignore' });
}

async function waitFor(url) {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // 起動中は再試行する。
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  throw new Error(`Timed out waiting for ${url}`);
}

async function capture(browser, name, viewport, prepare) {
  const context = await browser.newContext({ viewport });
  await context.addInitScript((value) => {
    localStorage.setItem('diopside_consent_v1', JSON.stringify(value));
  }, consent);
  const page = await context.newPage();
  await prepare(page);
  await page.screenshot({ path: `${outputDir}/${name}.png`, fullPage: true });
  await context.close();
}

async function searchResults(page) {
  await page.goto('http://127.0.0.1:5173/search', { waitUntil: 'networkidle' });
  const query = page.getByRole('combobox', { name: 'キーワード' });
  await query.fill('雑談');
  await query.press('ArrowDown');
  await query.press('Enter');
}

await mkdir(outputDir, { recursive: true });
const backend = start('.venv/bin/uvicorn', ['app.main:app', '--app-dir', 'src', '--host', '127.0.0.1', '--port', '8000'], `${root}backend`);
const frontend = start('npm', ['run', 'dev', '--', '--host', '127.0.0.1', '--port', '5173'], `${root}frontend`);

try {
  await waitFor('http://127.0.0.1:8000/health');
  await waitFor('http://127.0.0.1:5173');
  const browser = await chromium.launch({ channel: 'chrome' });
  const mobile = { width: 375, height: 812 };
  const desktop = { width: 1280, height: 900 };

  await capture(browser, 'home-mobile', mobile, (page) => page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle' }));
  await capture(browser, 'home-desktop', desktop, (page) => page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle' }));
  await capture(browser, 'search-empty-mobile', mobile, (page) => page.goto('http://127.0.0.1:5173/search', { waitUntil: 'networkidle' }));
  await capture(browser, 'search-empty-desktop', desktop, (page) => page.goto('http://127.0.0.1:5173/search', { waitUntil: 'networkidle' }));
  await capture(browser, 'search-results-mobile', mobile, searchResults);
  await capture(browser, 'search-results-desktop', desktop, searchResults);
  await capture(browser, 'condition-sheet-mobile', mobile, async (page) => {
    await page.goto('http://127.0.0.1:5173/search', { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: '＋タグ' }).click();
  });
  await capture(browser, 'condition-panel-desktop', desktop, async (page) => {
    await page.goto('http://127.0.0.1:5173/search', { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: '＋タグ' }).click();
  });
  await capture(browser, 'calendar-mobile', mobile, async (page) => {
    await page.goto('http://127.0.0.1:5173/search', { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: '＋タグ' }).click();
    await page.getByRole('dialog', { name: '検索条件' }).getByRole('button', { name: 'カレンダー' }).click();
  });
  await capture(browser, 'detail-mobile', mobile, (page) => page.goto('http://127.0.0.1:5173/videos/rY4A7Lxk12Q', { waitUntil: 'networkidle' }));
  await capture(browser, 'detail-desktop', desktop, (page) => page.goto('http://127.0.0.1:5173/videos/rY4A7Lxk12Q', { waitUntil: 'networkidle' }));
  await capture(browser, 'saved-empty-mobile', mobile, (page) => page.goto('http://127.0.0.1:5173/saved', { waitUntil: 'networkidle' }));
  await capture(browser, 'history-mobile', mobile, async (page) => {
    await page.goto('http://127.0.0.1:5173/videos/rY4A7Lxk12Q', { waitUntil: 'networkidle' });
    await page.goto('http://127.0.0.1:5173/history', { waitUntil: 'networkidle' });
  });
  await browser.close();
  console.log(`Captured 14 screenshots in ${outputDir}`);
} finally {
  backend.kill('SIGTERM');
  frontend.kill('SIGTERM');
}
