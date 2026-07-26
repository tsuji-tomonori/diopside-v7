# UI全面書き直し Phase 6 視覚レビュー不具合修正報告

## 指示と対象

Phase 4の視覚レビューで検出された表示整形、派生情報、条件パネル、カレンダー、LengthSlider、モバイル下タブの6件を対象にした。`src/lib/{contract,policy,schemas,search,storage}.ts`、データ契約、Zod schemaは変更していない。公開UIへ架空値・0件fallbackを追加していない。commit、push、deploy、新規依存追加も行っていない。

## 不具合ごとの対応

1. `frontend/src/lib/format.ts`を追加し、投稿日、動画長、件数、タイムスタンプ、派生情報の日時を集約して整形した。`VideoListItem`、`VideoGridCard`、`DetailPage`は`durationSec`と実在する集計値から表示する。集計がない動画はチャット数を表示せず、集計がある時だけ`12,480`形式で表示する。`format.test.ts`を追加した。
2. 詳細の派生情報を「データ更新日」「対象期間」「チャット」「コメント」「タイムスタンプ」「ワードクラウド」の日本語表示へ置換した。内部識別子は日本語の出所説明を主表示にし、識別子は補助表示に留めた。artifact自体がない時は既存通り「未作成」とし、0件には置換しない。consentとrelease modeの表示gateを維持した。
3. PC条件パネルは`width:min(320px,100vw)`とし、1280pxと1440pxで右端固定、内側288pxのスライダーとCTAがviewport内であることを実測した。
4. カレンダーの「条件に戻る」をRangeCalendarヘッダーへ統合した。375pxで戻る、前月、月表示、次月、クリアが横一列に収まり、曜日行と重ならないことを実測した。日付gridの計算には変更を加えていない。
5. 選択肢(a)を採用した。LengthSliderを単一トラック上のnative range 2つまみに戻した。理由は、設計正本が単一トラックの2つまみを明示しており、二本トラックを維持するより仕様追跡性を優先できるためである。下限・上限のclamp、15分step、キーボード、`aria-valuetext`、各inputの44px高hit areaを維持した。重なり時も両thumbはTabで個別に選択・調整でき、focus中のthumbを前面にする。
6. `.main-content`の既存`padding-bottom:calc(72px + env(safe-area-inset-bottom))`を確認した。375×812で末尾までscroll後、フッター下端が下タブ上端以下となることを実測したため追加変更は不要だった。

## 実行結果

| command | 結果 |
| --- | --- |
| `cd frontend && npm run typecheck` | 合格。`tsc -p tsconfig.json --noEmit`がexit 0。 |
| `cd frontend && npm test` | 合格。26 files、75 tests。Phase 4の69 testsから減少していない。 |
| `cd frontend && npm run build` | 合格。Vite production buildがexit 0。CSS構文警告を修正後に再実行した。 |
| `cd frontend && npm run test:e2e` | 初回は既存の投稿日heading期待が2環境で失敗。視覚を増やさない`sr-only`見出しを追加して再実行し、26 passed。 |
| `cd backend && .venv/bin/python -m pytest -q` | 合格。63 passed。日本語コンテンツgateを含む。 |
| `node tools/capture-ui-rewrite-screenshots.mjs` | 合格。14枚を再撮影した。 |

## viewport実測

| 条件 | 結果 |
| --- | --- |
| 1280×900 | panel `x=960, width=320`、CTA `x=976, width=288`、slider `x=976, width=288`。すべてviewport内。 |
| 1440×900 | panel `x=1120, width=320`、CTA `x=1136, width=288`、slider `x=1136, width=288`。すべてviewport内。 |
| 375×812 | カレンダーの戻る、前月、次月、クリアは幅82.7/44/44/59.0px、全て高さ44pxで右端359px以下。末尾scroll後のfooterは下タブ上に露出。 |

## 撮影済みスクリーンショット

`reports/private/ui-rewrite-20260726/`へ次の14枚を再作成した。`home-mobile.png`、`home-desktop.png`、`search-empty-mobile.png`、`search-empty-desktop.png`、`search-results-mobile.png`、`search-results-desktop.png`、`condition-sheet-mobile.png`、`condition-panel-desktop.png`、`calendar-mobile.png`、`detail-mobile.png`、`detail-desktop.png`、`saved-empty-mobile.png`、`history-mobile.png`。

## 適用SWEBOKセルフチェック

対象ID数13、判定数13。

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | pass | 本reportの6受入条件と実行結果 | 完了基準を第三者が判定できるcommandと成果物へ対応付けた | 親agentの視覚再評価を受ける |
| MGT-060 | pass | taskのリスクとviewport実測 | 原因→事象→影響と対策を事前記録し、表示崩れを実測した | 継続的にvisual regressionを確認する |
| PRC-001 | pass | taskの対象・非対象、report | 表示層を対象、契約・schemaを対象外として工程境界を維持した | 次変更時に範囲を再評価する |
| SCM-001 | pass | `git diff --check`、非commit制約 | 作業treeの既存変更を保持し、対象変更だけを追加した | commit/pushは依頼時だけ実施する |
| QUA-001 | pass | unit、build、E2E、backend、視覚実測 | 製品UI品質と工程品質を別々の証跡で確認した | 親agentの目視gateは別途残す |
| REQ-102 | pass | 不具合1〜6と各test/viewport結果 | 全要求を検査またはbrowser実測可能な条件へ対応付けた | なし |
| DES-001 | pass | design-system、component-implementation v1.1、実装 | カードcaption、range、calendar、navigation設計との追跡を維持した | なし |
| CON-080 | pass | `format.test.ts`、カード・詳細・slider test | 新規整形関数と変更分岐の単体テストを追加した | なし |
| TST-001 | pass | 対象と非対象、6 command | unitからbrowser、backend、撮影へ検証範囲を定義した | なし |
| TST-701 | pass | 75 unit tests、26 E2E、63 backend tests | 整形、状態分岐、a11y、viewportを受入条件に対応付けた | なし |
| TST-801 | pass | 実行結果表と再撮影14枚 | required commandごとの終了基準を個別に確認した | 親agentの目視評価は外部gateとして扱う |
| MNT-001 | pass | Phase 4視覚レビュー、Phase 6 task | UI回帰修正の対象範囲と対象外を明確にした | なし |

## 残余risk

実装とrequired commandはすべて合格した。再撮影PNGに対する親agentの最終視覚評価は、このreport作成時点では外部review gateとして未実施である。これは実装・検証完了とは区別する。
