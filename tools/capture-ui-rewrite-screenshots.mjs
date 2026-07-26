import { mkdir } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { chromium } from '@playwright/test';

const root = new URL('..', import.meta.url).pathname;
const outputDir = `${root}reports/private/ui-verification-20260726`;
const baseURL = 'http://127.0.0.1:5174';
const consent = { schemaVersion: 1, policyMajor: '1', acceptedAt: '2026-07-13T00:00:00Z' };
const viewports = { mobile: { width: 375, height: 812 }, desktop: { width: 1280, height: 900 } };

function start(command, args, cwd) {
  return spawn(command, args, { cwd, stdio: 'ignore' });
}

async function waitFor(url) {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    try {
      if ((await fetch(url)).ok) return;
    } catch {
      // 起動中は再試行する。
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  throw new Error(`Timed out waiting for ${url}`);
}

async function capture(browser, screen, state, kind, prepare = async () => {}) {
  const context = await browser.newContext({ viewport: viewports[kind] });
  await context.addInitScript((value) => localStorage.setItem('diopside_consent_v1', JSON.stringify(value)), consent);
  const page = await context.newPage();
  await prepare(page);
  await page.screenshot({ path: `${outputDir}/${screen}-${state}-${kind}.png`, fullPage: true });
  await context.close();
}

async function both(browser, screen, state, prepare) {
  for (const kind of Object.keys(viewports)) await capture(browser, screen, state, kind, prepare);
}

async function normalRoute(path) {
  return (page) => page.goto(`${baseURL}${path}`, { waitUntil: 'networkidle' });
}

async function errorRoute(path, status) {
  return async (page) => {
    await page.route('**/data/latest.json', (route) => route.fulfill({ status, contentType: 'application/json', body: '{}' }));
    await page.goto(`${baseURL}${path}`, { waitUntil: 'networkidle' });
  };
}

async function artifactNotGeneratedRoute(page) {
  const noArtifacts = { chat: false, comments: false, timestamps: false, wordcloudChat: false, wordcloudComments: false, wordcloudBoth: false };
  await page.route('**/data/releases/20260711-001/index.json', async (route) => {
    const value = await (await route.fetch()).json();
    const video = value.videos.find((item) => item.videoId === 'rY4A7Lxk12Q');
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
  await page.goto(`${baseURL}/videos/rY4A7Lxk12Q`, { waitUntil: 'networkidle' });
}

await mkdir(outputDir, { recursive: true });
const backend = start('.venv/bin/uvicorn', ['app.main:app', '--app-dir', 'src', '--host', '127.0.0.1', '--port', '8000'], `${root}backend`);
const frontend = start('npm', ['run', 'dev', '--', '--host', '127.0.0.1', '--port', '5174'], `${root}frontend`);

try {
  await waitFor('http://127.0.0.1:8000/health');
  await waitFor(baseURL);
  const browser = await chromium.launch({ channel: 'chrome' });

  for (const [screen, path] of Object.entries({ home: '/', search: '/search', saved: '/saved', history: '/history', detail: '/videos/rY4A7Lxk12Q', terms: '/terms', privacy: '/privacy', 'not-found': '/not-defined', admin: '/admin' })) {
    await both(browser, screen, 'normal', await normalRoute(path));
  }
  await both(browser, 'search', 'results', async (page) => {
    await page.goto(`${baseURL}/search`, { waitUntil: 'networkidle' });
    await page.getByRole('combobox', { name: 'キーワード' }).fill('雑談');
    await page.getByRole('combobox', { name: 'キーワード' }).press('ArrowDown');
    await page.getByRole('combobox', { name: 'キーワード' }).press('Enter');
  });
  await both(browser, 'search', 'conditions', async (page) => {
    await page.goto(`${baseURL}/search`, { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: '＋タグ' }).click();
  });
  await capture(browser, 'search', 'calendar', 'mobile', async (page) => {
    await page.goto(`${baseURL}/search`, { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: '＋タグ' }).click();
    await page.getByRole('button', { name: 'カレンダー' }).click();
  });
  await capture(browser, 'search', 'calendar', 'desktop', async (page) => {
    await page.goto(`${baseURL}/search`, { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: '＋タグ' }).click();
    await page.getByRole('button', { name: 'カレンダー' }).click();
  });
  for (const [screen, path] of Object.entries({ home: '/', search: '/search', saved: '/saved', history: '/history', detail: '/videos/rY4A7Lxk12Q' })) {
    await both(browser, screen, 'server-error', await errorRoute(path, 503));
    await both(browser, screen, 'data-not-found', await errorRoute(path, 404));
  }
  await both(browser, 'detail', 'artifact-not-generated', artifactNotGeneratedRoute);
  for (const kind of Object.keys(viewports)) {
    await capture(browser, 'home', 'loading', kind, async (page) => {
      await page.route('**/data/latest.json', async (route) => { await new Promise((resolve) => setTimeout(resolve, 1200)); await route.continue(); });
      await page.goto(`${baseURL}/`);
      await page.getByText('データを読み込んでいます…').waitFor();
    });
    await capture(browser, 'detail', 'without-consent', kind, async (page) => {
      await page.addInitScript(() => localStorage.removeItem('diopside_consent_v1'));
      await page.goto(`${baseURL}/videos/rY4A7Lxk12Q`, { waitUntil: 'networkidle' });
    });
    await capture(browser, 'saved', 'populated', kind, async (page) => {
      await page.addInitScript(() => localStorage.setItem('diopside_saved_v1', JSON.stringify(['rY4A7Lxk12Q'])));
      await page.goto(`${baseURL}/saved`, { waitUntil: 'networkidle' });
    });
  }
  await browser.close();
  console.log(`Captured ${Object.keys(viewports).length * 2 * 5 + 18 + 4 + 4 + 6} screenshots in ${outputDir}`);
} finally {
  backend.kill('SIGTERM');
  frontend.kill('SIGTERM');
}
