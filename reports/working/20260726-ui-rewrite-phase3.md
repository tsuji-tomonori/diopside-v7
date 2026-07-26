# UI 全面書き直し Phase 3a — 検索画面・ホーム画面

## 指示と適用範囲

- 対象は `frontend/src/pages/SearchPage.tsx`、`HomePage.tsx`、ページテスト、およびそれらを成立させる最小の共通UI/CSS調整である。
- 正本は `docs/design/wireframes.md` の検索フロー4aとホーム節、`component-implementation.md`、`design-system.md`、`20260726-ui-rewrite-plan.md` の既存契約とした。
- route、`contract/policy/schemas/search/storage` の公開API・schema・永続化形式、`PublicDataContext` 公開API、新規依存追加、`.workspace`、commit/push は対象外とした。

## 実装内容と判断

- `SearchPage` を `SearchBar`、`SuggestList`、`ConditionRow`、`ConditionPanel`、`LengthSlider`、`RangeCalendar`、`VideoListItem`、状態componentで構成した。
  - 入力中だけ、実 `tagIndex` の表示名部分一致・実count降順によるタグ候補を最大2件と、入力語をそのまま検索する候補1件を出す。日付解釈データは既存contractに無いため、架空候補は出さない。
  - 条件ゼロでは追加chip、条件ありでは解除chipと条件actionを表示する。条件変更時に `search.ts` の `buildSearchParams` でURLを更新し、location変更時には `parseSearchParamsWithReport` で復元・正規化する。
  - 検索indexまたはrelease artifactが欠ける場合は `DataErrorState` とし、0件状態にはしない。loading、retryable/permanent error、emptyを分けた。
  - 条件パネル内でカレンダーを差し替え、初期節指定時には対象節までスクロールして一時ハイライトする。
- `HomePage` を検索起点に変更し、実tagIndexのクイックタグ、最新動画、空状態でも残る検索/タグ入口を実装した。CSSでmobile listと768px以上の3列gridを切り替える。
- `SearchPage.test.tsx`（6件）と`HomePage.test.tsx`（2件）を追加した。候補上限、キーボード選択、status通知、条件chip、CTA/live region、URL同期、loading/empty/artifact欠落/retryable・permanent error、ホームの入口と空状態を検証する。

## 実行結果

| command | result |
| --- | --- |
| `cd frontend && npm test -- SearchPage.test.tsx HomePage.test.tsx` | 合格: 2 files / 8 tests |
| `cd frontend && npm run typecheck` | 合格 |
| `cd frontend && npm test` | 合格: 20 files / 56 tests（Phase 2完了時48件から8件増） |
| `cd frontend && npm run build` | 合格: Vite production build完了 |
| `git diff --check` | 合格 |

Taskfileは確認したが、本変更はfrontend pageのため、対象受入条件に指定されたfrontend commandを直接実行した。deploy、外部通信を要する検証、commit/pushは実行していない。

## SWEBOK セルフチェック

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | pass | task受入条件、上記56 test/typecheck/build | 完了基準を成果物と実行結果で判定した | 変更要求時にtaskを更新 |
| PRC-001 | pass | taskの対象/非対象/実施順、本report | Phase 3aの工程・境界を記録した | 後続phaseで再評価 |
| SCM-001 | pass | `git status --short`、`git diff --check`、非変更contract | 変更対象と既存dirty worktreeを区別し、`.workspace`非変更を維持した | commitはユーザー判断 |
| QUA-001 | pass | 正本照合、page test、実行結果 | UI製品品質と手順/検証記録を別証跡で確認した | peer reviewは別gate |
| REQ-102 | pass | Search/Homeの8 page tests | 指定された受入観点を自動検証へ対応付けた | e2e追加時に補完 |
| DES-001 | pass | wireframe 4a、component仕様、Search/Home構成 | 要求から既存UI component組合せへ追跡できる | 視覚レビューは後続で実施 |
| CON-080 | pass | `SearchPage.test.tsx`、`HomePage.test.tsx`、全Vitest | 変更した表示/状態/分岐をunit testで検証した | 将来のpage変更にも更新 |
| TST-001 | pass | taskの対象/非対象、narrow→aggregate実行記録 | テスト範囲と実行順を明示・実施した | e2eは別phaseで実施 |
| TST-801 | pass | 受入command全件合格、56件の実数 | 終了基準の達成結果を個別記録した | peer reviewは実装完了と分離 |

対象ID数9、判定数9。未解決failはない。

## 未対応・残余リスク

- PC/mobileの実ブラウザ幅での視覚差と、シートの下スワイプは今回のVitestでは検証していない。既存`ConditionSheet`はEsc・背景click・focus trapをcomponent test済みであり、視覚/gesture確認はe2eまたは手動レビューが必要である。
- 同義語・日付自然言語解釈は既存public data/APIにないため未実装である。捏造を避け、実tagIndex由来の部分一致のみを表示する。
- 外部peer review/approvalは本reportに証跡がないため合格扱いにしていない。

---

## Phase 3b — 詳細・保存・履歴・静的ページ

### 指示と適用範囲

- 対象は `DetailPage`、`SavedPage`、`HistoryPage`、`TermsPage`、`PrivacyPage`、`NotFoundPage`、`App.tsx`、`VideoCard.tsx` と各ページtestである。
- 正本は `wireframes.md` の保存・履歴、動画詳細、not found節、`component-implementation.md`、`design-system.md`、Phase 1 reportの既存契約とした。
- `contract/policy/schemas/search/storage` の公開API・Zod schema・localStorage形式、`PublicDataContext`、route、依存関係は変更していない。`.workspace`は読取りのみで、commit/push/deployも実行していない。

### 実装内容と判断

- Detailは、同意前に規約・同意導線のみを先に表示し、同意後にサムネイル、タイトル、投稿日・長さ・実在するチャット数、タグ、YouTube CTA、保存操作、派生情報の順で表示するよう再構成した。
  - 同意、同意取り下げ、`releaseMode === normal` による派生情報の制御、detail load成功時のみの履歴追加、error `role=alert` の「公開データサーバーでエラー」文言を維持した。
  - artifactが存在しない場合は各節と総覧に「未作成」を表示し、0件へ置換していない。関連動画は実release内の共有tagに限り、同意済みかつnormal releaseでだけ `VideoGridCard` として表示する。
- 保存・履歴は `VideoListItem` に統一し、空状態では `EmptyState` に理由と`/search`導線を置いた。履歴の全削除・個別削除を維持し、保存画面にあった「先頭を保存」の動作確認用UIは架空操作のため削除した。
  - storage write/removeの失敗時に発火する既存 `diopside:storage-error` eventの形式・処理を変えず、ページtestで削除操作とeventの継続を確認した。
- 規約・プライバシーは本文・linkを変えず、静かな本文幅、見出し、余白だけを追加した。`プライバシー・削除窓口` と `削除・訂正を依頼` の既存linkを維持した。
- Not Foundを独立pageへ寄せ、h1とホーム・検索への導線を実装した。`App.tsx`はこのpageをcatch-all routeに接続し、`/admin`のreplace redirectとshell navigationは維持した。
- `VideoCard.tsx` は参照がすべて `VideoListItem`/`VideoGridCard` へ移ったため削除した。`rg -n "VideoCard|components/VideoCard" frontend/src frontend/e2e` の参照確認は出力なしだった。

### 追加テスト

- `DetailPage.test.tsx`: 未同意のCTA/派生非表示、同意後表示、artifact未作成、公開データserver error。
- `SavedPage.test.tsx`、`HistoryPage.test.tsx`: 一覧、emptyの検索導線、全削除または個別削除、storage failure event。
- `NotFoundPage.test.tsx`: h1、次導線、shellのdesktop/mobile navigation。
- `StaticPages.test.tsx`: 規約本文・外部規約link、プライバシーの削除窓口・依頼link。

### 実行結果

| command | result |
| --- | --- |
| `cd frontend && npm run typecheck` | 合格 |
| `cd frontend && npm test -- --run src/pages/DetailPage.test.tsx src/pages/SavedPage.test.tsx src/pages/HistoryPage.test.tsx src/pages/NotFoundPage.test.tsx src/pages/StaticPages.test.tsx` | 初回: 13 tests中1件失敗（未作成表示が複数あることを単一要素と仮定したtest期待）。testを実態に合わせ修正。 |
| `cd frontend && npm test` | 合格: 25 files / 69 tests（Phase 3aの56件から13件増） |
| `cd frontend && npm run typecheck && npm test && npm run build` | 指定順で全件合格: typecheck合格、25 files / 69 tests合格、Vite production build合格 |
| `rg -n "VideoCard|components/VideoCard" frontend/src frontend/e2e` | 合格: 参照なし |
| `git diff --check` | 合格 |

Taskfileは確認済みであり、今回の受入条件が指定するfrontend commandを直接実行した。Taskfileのaggregate `verify` はbackend/infra/e2eまで対象を広げるため、実行していない。未実行を合格とは扱わない。

### SWEBOK セルフチェック

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | pass | Phase 3b task、指定順のtypecheck/test/build | 成果物と完了基準を対応付けて実績化した | 変更要求時にtaskを更新 |
| PRC-001 | pass | taskの対象/非対象/実施順、本Phase節 | 工程・境界・終了条件を記録した | 後続変更で再評価 |
| SCM-001 | pass | path一覧、`git diff --check`、VideoCard参照検査 | 構成変更と非変更contractを識別した | commitはユーザー判断 |
| QUA-001 | pass | 正本照合、13 page tests、aggregate検証 | 品質要求と検証結果を別証跡で確認した | 外部reviewは別gate |
| REQ-102 | pass | 画面別受入条件と13 page tests | 全指定状態を自動検証へ追跡した | 視覚レビュー時に補完 |
| DES-001 | pass | 詳細順序、list/grid、empty/static/not found構造 | wireframe/component設計をpageへ反映した | responsive視覚確認を別途実施 |
| CON-080 | pass | 追加5 test files、全Vitest | 変更したpolicy/storage/route表示分岐を検証した | 将来のpage変更にも更新 |
| TST-001 | pass | narrow失敗の分類・修正、aggregate実行記録 | narrowからaggregateの手順を実施した | e2eは別scope |
| TST-801 | pass | 指定3 command全件合格、69 tests実数 | 完了基準を実行結果で満たした | peer reviewは実装完了と分離 |

対象ID数9、判定数9。未解決failはない。

### 未対応・残余リスク

- desktop/mobileの実ブラウザ幅による詳細関連グリッド、固定mobile nav、静的ページの視覚確認はVitestだけではしていない。仕様上必須のtypecheck/test/buildは完走済みであり、視覚reviewは別途必要である。
- 外部peer review/approvalの証跡はないため、実装・ローカル検証の完了とは区別する。
