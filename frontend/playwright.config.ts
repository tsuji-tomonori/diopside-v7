import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  // WSL2ではデフォルト並列実行時にworkerプロセスがexit code 144でkillされるため、既定は直列実行とする。
  // CIなど並列実行が安定している環境ではPLAYWRIGHT_WORKERSで明示的に上書きできる。
  workers: process.env.PLAYWRIGHT_WORKERS ? Number.parseInt(process.env.PLAYWRIGHT_WORKERS, 10) : 1,
  retries: 0,
  reporter: 'line',
  use: {
    baseURL: 'http://127.0.0.1:5173',
    channel: 'chrome',
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'desktop-chrome', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 7'] } },
  ],
  webServer: [
    {
      command: '../backend/.venv/bin/uvicorn app.main:app --app-dir ../backend/src --host 127.0.0.1 --port 8000',
      url: 'http://127.0.0.1:8000/health',
      reuseExistingServer: true,
      timeout: 30_000,
    },
    {
      command: 'npm run dev -- --host 127.0.0.1 --port 5173',
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: true,
      timeout: 30_000,
    },
  ],
});
