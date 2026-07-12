# frontend browser E2E

## 実施

- Vite `/data` proxyをFastAPIへ接続。
- Playwrightを既存Chromeでdesktop/mobileの2 projectに設定。
- `/`、`/search`、`/saved`、`/history`、direct detailを検証。
- query canonicalization、skip link keyboard focus、admin非露出を検証。
- runtime fixture schema testを全public artifactへ拡張。
- DetailPageのconditional hook呼出しを修正。
- data URI faviconを追加しresource 404を解消。

## 検証

- TypeScript typecheck: pass
- Vitest: 11 tests pass
- Playwright Chrome: 8 tests pass
- desktop/mobile全route: console error 0
- Vite production build: pass（直前変更前。集約検証で再実行対象）

## 残るmanual/performance検証

- color contrast実測。
- Lighthouse 3回中央値。
- 2,500動画・代表20検索benchmark。
