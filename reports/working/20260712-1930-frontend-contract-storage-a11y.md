# frontend契約、storage、アクセシビリティ

## 実施

- Zod strict runtime schemaをlatest/index/search/tag/taxonomy/alias/detailへ追加。
- HTTP 404、timeout、5xx、network、schema、release mismatchを型付き分類。
- valid empty dataとfetch/schema errorを分離。
- localStorage破損時に当該keyだけを初期化。
- write失敗をevent通知し、成功扱いせず例外で画面を破壊しない。
- consent payloadのschemaVersion、major、acceptedAtを検証。
- skip link、main focus target、`:focus-visible`を追加。
- desktop/mobile navigation landmark labelを修正。
- Testing Library + axe-core構造検査を追加。

## 検証

- TypeScript typecheck: 合格
- Vitest: 10件のtestが合格
- axe-core: violation 0（jsdom非対応のcolor contrastは除外）
- Vite production build: 合格
- npm audit: 脆弱性0件

## 未対応

- Playwrightによる全route keyboard/browser E2E。
- 実ブラウザでのcolor contrast、focus return、44px hit-area manual確認。
- Lighthouse 3回中央値と2,500動画search benchmark。
