# UI全面書き直し計画 — Phase 1

- 作成日: 2026-07-26
- 対象: `frontend/src/**` のUI再構築（本Phaseはdocs/reportのみ、実装コード変更なし）
- 正本: `docs/design/design-system.md`、`docs/design/wireframes.md`、`docs/design/component-implementation.md`、`docs/spec/22.system-specifications.md`

## 調査範囲と制約

SSR抽出済みの `.workspace/design-reference/design-spec.html`（45,090 bytes / 1,025 lines）、`wireframe.html`（69,219 bytes / 1,386 lines）、`components.html`（75,407 bytes / 1,564 lines）を全量確認した。`.workspace` はread-onlyでGit対象外。本Phaseでは `frontend/src/**`、契約・testを変更しない。採用targetは wireframe `6b + 5a + 4a` である。

## gap分析 — 画面

| 画面 | 現行 | target | 差分の内容 | 影響度 |
| --- | --- | --- | --- | --- |
| App shell | mobile下タブと非表示sidebar、本文16px | 375px下タブ＋PC w220 sidebar、safe-area、design typography | PC shell・アイコン・font・active表示を再構築 | High |
| Home | リスト中心の簡易ページ | 検索起点、quick tags、PC 3〜4列grid | 情報階層とresponsive表示を追加 | High |
| Search input | label/input/select form | natural language + tag token、h44/r14 | token化、候補選択、URL同期UIが不足 | Critical |
| Search suggestions | listboxは存在 | 最大4行・タグ/日付/keyword分類、件数、120ms | visual/情報構造/日付解釈を追加 | High |
| Search results | 通常フォーム＋一覧 | sticky条件行、chip一行、live count、sort | 条件表示と操作導線を全面変更 | Critical |
| Filter | select中心 | mobile sheet / PC w320 panel、タグ・range・calendar | 条件編集モデルが未実装 | Critical |
| Saved | 簡易VideoCard一覧 | target VideoListItem、empty導線 | empty/target card/stylingを整備 | Medium |
| History | 簡易VideoCard一覧 | target VideoListItem、clear/empty導線 | target cardと状態表現を整備 | Medium |
| Detail | 同意、artifact、保存を縦列挙 | hero media、metadata/tags/CTA、派生状態を視覚整理 | policy/derivedの既存条件を保った再配置 | High |
| Terms/Privacy | テキスト主体 | shell内の静かな情報ページ | typography/spacingのみ、内容とリンクは維持 | Low |
| NotFound | `p.status`のみ | 見出し、次導線、shell維持 | h1・empty state化 | Medium |
| Data states | status文字列、alert card | skeleton、empty、retryable/permanentを視覚・programmaticに区別 | missing artifact≠0件の扱いを共通化 | High |

## gap分析 — コンポーネント

| コンポーネント | 現行 | target | 差分の内容 | 影響度 |
| --- | --- | --- | --- | --- |
| tokens/styles | `styles.css` 331行、Arial/Georgia、部分token | デザインtoken、3段elevation、指定font、motion | token層とresponsive utilitiesが不足 | High |
| Button | 全button共通h44/r10 | primary/secondary/text、h48/r12、state | variant/state contractがない | High |
| Chip | 表示用span、11px | 5 variant、h32/44-hit、remove/action | 操作/a11y/状態がない | Critical |
| SearchBar | input単体 | token list + input + icon | DOM構造・focus/closeがない | Critical |
| SuggestList | existing listbox | classified 4-row list、keyboard/live | date/keyword rows、表示値が不足 | High |
| ConditionRow | なし | sticky add/removable/action chips | 常設入口・URL条件の可視化がない | Critical |
| ConditionSheet/Panel | なし | dialog/focus trap、PC panel | modal semantics、responsive entryなし | Critical |
| LengthSlider | なし | dual slider / 15min / 5h+ | state・keyboard操作なし | High |
| RangeCalendar | なし | 2tap range、dot、future disabled | state・grid a11yなし | High |
| VideoCard | 128×72/r12、外部link別 | list120×68/r8 / grid、whole link、badge | target layout・loading/hover差 | High |
| AppShell nav | テキストリンク、mobile active top border | Material Symbols、filled active、PC item state | icon/Nav visual contract差 | Medium |
| DataErrorState | generic status-card | typed error + retry + focus-preserving UI | target visual state不足 | Medium |

件数: Critical **5**、High **13**、Medium **5**、Low **1**（計24）。

## 維持すべき既存契約

### ルーティング・データ・ポリシー（routing / data / policy）

- routesを維持する: `/`、`/search`、`/saved`、`/history`、`/videos/:id`、`/terms`、`/privacy`。`/admin` は `/` へreplaceし、公開DOMに「管理」linkを置かない。
- `src/lib/contract.ts`、`policy.ts`、`schemas.ts` の公開data、policy link、Zod schemaを変更しない。`src/lib/search.ts` のquery正規化・`tag`反復・sort既定、`src/lib/storage.ts` のversioned localStorage/失敗eventも維持する。
- `PublicDataContext` の `loading, release, refresh, error, errorKind, tagIndex, latest` APIを維持する。policy同意、releaseModeによるderived data非表示、artifact欠落と空データの区別を保持する。

### 現行testが依存するDOM契約

- `#main-content`、skip text `本文へスキップ` とhref、`main navigation` / `mobile navigation` のaccessible name。
- Search: combobox name `キーワード`、`role=listbox`、keyboard ArrowDown/Enter、条件追加後の`role=status`文言 `検索条件へ追加しました`。
- Detail error: `role=alert`と「公開データサーバーでエラー」。
- 全routeの`main`と`h1`、error文言`失敗しました`を不要に出さないこと。
- privacy link `プライバシー・削除窓口`、privacy内の`削除・訂正を依頼` link、`/admin`に`管理` linkが無いこと。

## 書き直し計画

### Phase 2 — token、shell、共通コンポーネント

- 変更: `frontend/src/styles.css`, `frontend/src/components/AppShell.tsx`, `frontend/src/components/VideoCard.tsx`, `frontend/src/components/DataErrorState.tsx`。
- 新規: `frontend/src/components/ui/Icon.tsx`, `Button.tsx`, `Chip.tsx`, `SearchBar.tsx`, `SuggestList.tsx`, `ConditionRow.tsx`, `ConditionSheet.tsx`, `ConditionPanel.tsx`, `LengthSlider.tsx`, `RangeCalendar.tsx`, `VideoListItem.tsx`, `VideoGridCard.tsx`, `EmptyState.tsx`, `LoadingState.tsx`。
- props案: `Chip({variant, selected?, label, count?, onClick?, onRemove?})`; `SearchBar({query,tokens,onQueryChange,onTokenRemove,onKeyDown})`; `SuggestList({items,activeIndex,onSelect})`; `ConditionSheet({open,initialSection?,condition,onChange,onClose,resultCount})`; `VideoListItem({video,tagNames,chatCount?})`。
- AppShellの既存landmark/testid相当DOM・routingを維持し、mobile/PCをCSS media queryで切替える。

### Phase 3 — 全ページ移植

- 変更: `frontend/src/pages/HomePage.tsx`, `SearchPage.tsx`, `SavedPage.tsx`, `HistoryPage.tsx`, `DetailPage.tsx`, `TermsPage.tsx`, `PrivacyPage.tsx`, `NotFoundPage.tsx`, `frontend/src/App.tsx`。
- 必要なら新規: `frontend/src/hooks/useSearchCondition.ts`, `frontend/src/lib/format.ts`（既存contractを変えず表示整形だけを置く）。
- SearchPageは既存`search.ts`のnormalizationとstorage recent searchを唯一の状態境界にし、URL→UI→URLの一方向同期を実装する。DetailPageはconsent/policy/derived gatingとhistory更新の条件をそのまま保持する。

### Phase 4 — testと検証

- 変更: `frontend/src/components/AppShell.test.tsx`、各新規componentの`*.test.tsx`、`frontend/e2e/public-routes.spec.ts`。
- 追加対象: button/chip states、SearchBar token/keyboard、suggest list、sheet focus trap/Esc/focus return、range/calendar keyboard、responsive nav、loading/empty/error、policy gating、existing route/role/text契約。
- 実行順: targeted Vitest → `npm run typecheck` → `npm test` → `npm run build` → Playwright。未実行・timeout・skippedはpassにしない。

## 未決事項とリスク

1. Material Symbolsと指定Google fontsの読み込み方式（外部読み込みか自己hostか）はPhase 2開始前に決める。CSP/オフライン要件は現行仕様にない。
2. `tagId`の同名tagをsub-category付きで表示するデータ整形の位置は、現在のtag taxonomy fixtureを確認して決める。
3. カレンダーの実装方式（ライブラリなしのARIA gridか軽量依存追加か）は依存追加の判断を要する。targetの44px/keyboardを満たすことが必須。
4. targetは未認証管理を非表示だが、参照componentsの古い説明にはdisabled例がある。現行public contractとdesign-system v1.1に従い**非表示**を採用する。

## SWEBOKセルフチェック

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| REQ-002 | pass | 本reportの対象・正本・制約、成果物header | 文書目的・scope・読者を明示 | Phase 2でacceptanceをtaskへ引継ぐ |
| REQ-102 | pass | Phase 4のcommand/検証対象 | 後続要求を検証可能な形で計画 | 実装後に実行結果を追記 |
| REQ-202 | pass | design-system、spec、参照HTML、現行contractの読合せ | 本Phaseのtarget/現行差異を同一reportに追跡 | 仕様改定時に再確認 |
| DES-001 | pass | `wireframes.md`、`component-implementation.md` | UI構造・数値・状態を設計成果物化 | Phase 2 code review |
| DES-018 | pass | component DOM/a11y節 | interactionとa11yをcomponent単位で定義 | 実装testを追加 |
| CON-001 | pass | Phase 2/3の具体的pathとprops | 実装単位とreuse境界を明示 | 実装時に契約を維持 |
| TST-001 | pass | Phase 4 narrow→aggregate順 | test scopeと実行順を定義 | 実行自体はPhase 4 |
| SCM-001 | pass | git diff対象=docs/report、`.workspace` read-only | 構成品目と非対象を識別 | parent review後にcommit判断 |
| MGT-001 | pass | scope、3 phase、risk/未決事項 | 計画・リスクを明示 | 未決事項をPhase 2 gateで決定 |
| PRC-001 | pass | Phase 1〜4分割、gate記録 | 工程と完了基準を定義 | 各phaseで更新 |
| QUA-090 | blocked | peer review記録なし | 文書レビューは外部実施待ち | parent agent reviewで判定更新 |
| QUA-100 | pass | static文書照合 + Phase 4 dynamic test計画 | Verification/Validationを分離して計画 | Phase 4で実行証跡を追加 |

本Phaseでtest/buildは実行していない（実装コードを変更しない調査・文書化phaseのため）。これは検証passを主張しない。`QUA-090` は外部レビュー待ちであり、実装完了とは区別する。

## 実行記録・指示適合

- 実行: `wc -l -c .workspace/design-reference/*.html`、`rg --files frontend/src frontend/e2e`、`sed`/`rg`による正本・現行実装・test・SWEBOK checklistの静的読合せ、`git diff --name-only -- frontend/src`。
- 結果: 設計移植2文書と本計画を作成し、`frontend/src` のdiffは0件。テスト、typecheck、build、e2eは未実行。
- fit: 指定された3成果物、画面別・component別gap、Phase 2〜4のpath/props、契約維持、SWEBOK判定を記録した。commitは行っていない。
- 残余: peer review、fonts/icon供給、calendar実装方式、同名tag表示をPhase 2の判断・検証対象として残す。
