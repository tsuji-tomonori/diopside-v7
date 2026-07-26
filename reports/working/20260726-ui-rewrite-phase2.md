# UI全面書き直し Phase 2 実装記録

実施日: 2026-07-26

## 指示・判断

- `design-system.md`、`wireframes.md`、`component-implementation.md`、Phase 1計画を正本として、token、AppShell、共通UIを実装した。
- CDN font / Material Symbols webfont / npm依存は追加していない。指定font名を先頭にしたsystem fallbackと、`currentColor`のinline SVG icon setを採用した。
- カレンダーは新規依存を使わず、`role=grid`・44px cell・未来日disabledを実装した。
- 表示件数、chat count、video metadataはすべてprops/既存公開data由来とし、欠落値を0やfixtureで補完していない。
- routes、data/policy/storage API、既存landmark・skip link・search/error/privacyのDOM契約を変更していない。commit/pushはしていない。

## 実装ファイル

- 更新: `frontend/src/styles.css`
- 更新: `frontend/src/components/AppShell.tsx`
- 更新: `frontend/src/components/VideoCard.tsx`
- 更新: `frontend/src/components/DataErrorState.tsx`
- 追加: `frontend/src/components/ui/{Icon,Button,Chip,SearchBar,SuggestList,ConditionRow,ConditionSheet,ConditionPanel,LengthSlider,RangeCalendar,VideoListItem,VideoGridCard,EmptyState,LoadingState}.tsx`
- 追加: 上記各componentの `*.test.tsx`（14ファイル）
- 追加: `tasks/do/20260726-1100-ui-rewrite-phase2.md`

## 実行結果

1. `cd frontend && npm run typecheck`
   - 合格（TypeScript error 0）。初回はAppShellの余分な配列終端で失敗し、修正後に再実行して合格。
2. `cd frontend && npm test`
   - 合格。Test Files: **18 passed / 18**、Tests: **27 passed / 27**、failed 0。
   - 初回はSuggestList testが`role=option`にkey eventを送って1件失敗。実操作対象であるbuttonへ修正後、同じaggregate testを再実行して合格。
3. `cd frontend && npm run build`
   - 合格。Vite production buildで138 modules transformed、出力完了。
4. `git diff --check`
   - 合格（出力なし）。
5. PlaywrightによるE2E検証
   - 未実行。Phase 4対象であり、本Phaseの指示どおり実行していない。

## SWEBOK セルフチェック

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | pass | task受入条件、実行結果 | 完了基準と成果物を検証可能に記録 | parent評価時に確認 |
| MGT-060 | pass | taskのrisk表 | 原因・影響・対応を記録 | Phase 3で再評価 |
| PRC-013 | pass | Phase 1 plan、Phase 2 task | phase/gateと変更範囲が明記済み | Phase 3へ継続 |
| SCM-001 | blocked | git status、親agentのcommit判断待ち | 本Phaseはcommit/push禁止で承認記録を作れない | parent review/commit時に判定 |
| QUA-090 | blocked | peer review証跡なし | 外部レビューを実施済みと扱わない | parent review |
| QUA-100 | pass | typecheck, Vitest, build実出力 | 静的検証と動的検証を分けて実行 | e2eはPhase 4 |
| DES-018 | pass | UI component source、14 unit test files | DOM、ARIA、keyboard、focus/44px classをcomponent単位で実装 | Phase 3 integration test |
| CON-001 | pass | `components/ui` 14 component、typecheck | 再利用可能なprops境界で実装 | page移植はPhase 3 |
| TST-701 | pass | 14 UI component test、27 Vitest tests | component requirementの最低限の状態/ARIA/keyboardを検証 | e2eをPhase 4で追加 |
| TST-801 | pass | 本節の受入条件別実測結果 | typecheck/test/buildの終了基準を個別に記録 | e2eは本Phase対象外 |
| MNT-043 | pass | aggregate Vitest 18 files | 既存契約に対する回帰範囲を全Vitestへ拡張 | page統合変更後に再実行 |
| MNT-100 | pass | `npm test` 27/27 | 自動回帰を実行し結果を記録 | e2eはPhase 4 |

## 未対応・残余リスク

- Phase 3で既存ページを新しいSearchBar/Condition UIへ統合し、URL条件同期と同名tagのsubcategory表示を実データに接続する。本Phaseではページ構造を全面変更していない。
- Sheetのfocus trapはEsc、初期focus、focus returnを実装したが、Tab循環および下スワイプはPhase 3/4で統合E2Eを追加して強化する。
- 指定fontは外部CDN/CSP違反を避けるためsystem fallbackのみ。セルフホスト可否は将来のCSP・asset方針で判断する。
- e2eは未実行（Phase 4対象）。SCM承認とpeer reviewは外部gateであり、実装完了と区別する。

## Phase 2b 是正（2026-07-26）

- `components/ui`、同unit test、`styles.css`を通常の改行・ブロック形式へ是正した。CSSは1宣言1行へ展開し、condition control/calendar節を明示した。
- ConditionSheetはTab/Shift+Tabのfocus trapを実装し、初回のclosed mountではfocusを動かさず、実際に開いた後だけtriggerへfocusを戻すよう修正した。
- RangeCalendarは`grid > row > gridcell`、roving tabindex、Arrow/Home/End/PageUp/PageDown、Enter/Space、Escを実装した。未来日はdisabledのままで、視覚セルに対し44pxのhit areaを保持する。
- SearchBarはSuggestionList idと`aria-expanded`、`aria-controls`、`aria-activedescendant`を関連付けた。removable Chipは本体のsection移動とcloseの解除handlerを分離した。
- LengthSliderは重なったrange inputを廃止し、上下限を独立した44pxのnative rangeとして配置した。各sliderはブラウザ標準のArrow/PageUp/PageDown/Home/End操作と`aria-valuetext`を利用する。
- component testを **27 → 41** testsへ拡充した。Button variant/disabled、Chipの5 variantとhandler分離、SearchBarのcombobox状態、Sheetのfocus trap/focus return、Slider境界、Calendarのrange/row/roving tabindex/future日を追加で検証した。

### Phase 2b 実行結果

1. `cd frontend && npm run typecheck`
   - 合格（TypeScript error 0）。
2. `cd frontend && npm test`
   - 合格。Test Files: **18 passed / 18**、Tests: **41 passed / 41**、failed 0。
3. `cd frontend && npm run build`
   - 合格。138 modules transformed、production build完了。
4. `git diff --check`
   - 合格（出力なし）。

### Phase 2b SWEBOK 再判定

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | pass | taskのPhase 2b計画、上記実行結果 | 是正対象と検証可能な完了条件を記録 | parent review時に確認 |
| MGT-060 | pass | task risk表、独立sliderへの変更 | a11yリスクを実装とtestで低減 | 統合E2Eで再確認 |
| PRC-013 | pass | taskのPhase 2b節 | review指摘を変更単位として記録 | 次phaseへ継続 |
| SCM-001 | blocked | git status、commit/push禁止 | 構成品目は特定済みだが承認済みbaselineは作れない | parent review |
| QUA-090 | pass | parent review指摘、Phase 2b source/test | 指摘を再現可能なコードとtestへ反映 | peer reviewは外部gate |
| QUA-100 | pass | typecheck/Vitest/build実出力 | 静的・動的・production buildを実行 | e2eはPhase 4 |
| DES-018 | pass | Sheet/Calendar/SearchBar/Chip/Slider sourceとtests | ARIA、keyboard、focus contractを直接検証 | integration E2E |
| CON-001 | pass | readable components、typecheck | 再利用componentの可読性と型整合を確認 | page統合時に再確認 |
| TST-701 | pass | 41 Vitest tests | component contractの状態・操作・ARIAを拡充 | E2E追加 |
| TST-801 | pass | 上記3必須commandの成功 | 指定終了条件を個別に達成 | external gateは別管理 |
| MNT-043 | pass | aggregate 18 files/41 tests | 既存DOM契約を含む回帰suiteを実行 | page統合後に再実行 |
| MNT-100 | pass | npm test 41/41 | 自動回帰結果を実数で記録 | E2EはPhase 4 |

### 残余リスク

- desktop/mobile実機でのsheet swipeとCalendarの月境界focus遷移はunit test対象外であり、Phase 4のPlaywright/支援技術確認に残す。
- peer review、commit/push、E2Eは本作業では実施していない。未実行を合格とは扱わない。

## Phase 2c 是正（2026-07-26）

- 未是正だった `ConditionPanel.test.tsx`、`ConditionRow.test.tsx`、`EmptyState.test.tsx`、`Icon.test.tsx`、`LoadingState.test.tsx`、`SuggestList.test.tsx`、`VideoGridCard.test.tsx`、`VideoListItem.test.tsx` の8ファイルだけを、複数行・`describe`/`it`・AAA 3段の形式へ是正した。既に是正済みのtest filesは変更していない。
- 8 componentのDOM/ARIA/操作/状態contractを追加した。ConditionRowのzero/applied/sticky、ConditionPanelのdialog/name/close、SuggestListの4件上限/selection/click/Enter、EmptyStateの0件/未作成props、LoadingStateのstatus/placeholder、Iconの装飾/size/currentColor、video cardのwhole-link/thumbnail/tagを直接検証している。
- `VideoListItem.tsx` は、`chatCount`が渡されても `video.artifactFlags.chat === false` ならchat countを描画しないよう最小修正した。欠落した集計を0や別の値で補完していない。
- component test件数を **41 → 48** testsへ拡充した（対象8ファイルは 8 → 15 tests）。

### Phase 2c 実行結果

1. `cd frontend && npx vitest run src/components/ui/ConditionPanel.test.tsx src/components/ui/ConditionRow.test.tsx src/components/ui/EmptyState.test.tsx src/components/ui/Icon.test.tsx src/components/ui/LoadingState.test.tsx src/components/ui/SuggestList.test.tsx src/components/ui/VideoGridCard.test.tsx src/components/ui/VideoListItem.test.tsx`
   - 合格。Test Files: **8 passed / 8**、Tests: **15 passed / 15**。
2. `cd frontend && npm run typecheck`
   - 合格（TypeScript error 0）。
3. `cd frontend && npm test`
   - 合格。Test Files: **18 passed / 18**、Tests: **48 passed / 48**、failed 0。
4. `cd frontend && npm run build`
   - 合格。138 modules transformed、production build完了。

### Phase 2c SWEBOK 再判定

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | pass | taskのPhase 2c計画、8 files/15 tests、48/48 | 範囲と完了条件を検証可能な形で限定・記録 | parent review時に確認 |
| MGT-060 | pass | task risk表、artifactFlagsのcontract test | 欠落集計を表示するリスクをtestと実装で低減 | page統合時に再確認 |
| PRC-013 | pass | taskのPhase 2c節 | 是正対象・必要時のみの実装修正を変更単位で記録 | 次phaseへ継続 |
| SCM-001 | blocked | git status、commit/push禁止 | 構成品目は追跡したが承認済みbaselineは作れない | parent review |
| QUA-090 | pass | Phase 2cのcontract testと欠陥修正 | contractレビューで検出したchat表示の不整合を同じ変更単位で是正 | peer reviewは外部gate |
| QUA-100 | pass | typecheck、Vitest、build実出力 | 静的・動的・production buildを分けて実行 | e2eはPhase 4 |
| DES-018 | pass | 8 component source/test | DOM、ARIA、表示状態の契約を直接検証 | integration E2E |
| CON-001 | pass | `VideoListItem.tsx`、typecheck | 実装変更をartifact flagによる表示条件だけに限定 | page統合時に再確認 |
| TST-701 | pass | 8 files/15 tests、全48 tests | 指定されたcomponent contractをtestで網羅 | E2E追加 |
| TST-801 | pass | 指定3 commandの成功 | 終了条件を個別の実出力で確認 | external gateは別管理 |
| MNT-043 | pass | aggregate Vitest 18 files/48 tests | 既存DOM contractを含む回帰suiteを実行 | page統合後に再実行 |
| MNT-100 | pass | `npm test` 48/48 | 自動回帰結果を実数で記録 | E2EはPhase 4 |

### Phase 2c 未対応・外部gate

- Playwright E2EはPhase 4対象のため未実行。未実行を合格とは扱わない。
- peer review、commit、pushは本作業の対象外であり、実施していない。
