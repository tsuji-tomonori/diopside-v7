# UI 全面書き直し Phase 3a: 検索・ホーム

状態: done

## 対象と受入条件

- `SearchPage.tsx` と `HomePage.tsx` を Phase 2 UI component と wireframe 4a に移植する。
- URL は `search.ts` の parse/build を唯一の正規化経路として双方向同期する。公開 contract、route、storage 形式は変更しない。
- 検索候補は実 `tagIndex` に由来する最大4行だけとし、artifact 欠落を空結果として表示しない。
- Search/Home の Vitest を追加し、指定状態・a11y DOM契約・URL同期を検証する。
- `cd frontend && npm run typecheck`、`npm test`、`npm run build` を順に実行し、結果を report に記録する。

## スコープ外・制約・リスク

- Saved/History/Detail、route、公開 contract、Zod schema、localStorage 形式、npm dependency は変更しない。
- `.workspace` は読取り専用、commit/push/deploy はしない。
- responsive 表示は CSS media query に委ねる。jsdom での実画面幅切替は component 実装の既存 contract に従う。
- 外部の peer review/approval は本作業の完了と区別する。

## 実施順と証跡

1. 正本・既存 component/data contract を照合し、page/hook/test の設計を確定する。
2. 検索条件 hook と Search/Home を実装し、unit test を追加する。
3. 狭い Vitest、typecheck、aggregate Vitest、build を実行する。
4. `reports/working/20260726-ui-rewrite-phase3.md` に command 結果と SWEBOK 判定を記録する。

## 適用 SWEBOK セルフチェック（計画時）

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | pass | 本taskの受入条件・実行command | 成功/完了を成果物と検証で判定可能にした | 実行後に結果へ更新 |
| PRC-001 | pass | 対象・除外・実施順 | 工程の適用範囲を明示した | reportで実績化 |
| SCM-001 | pass | 対象path、非変更contract、`.workspace`制約 | 構成識別と変更境界を固定した | diff確認 |
| QUA-001 | pass | product UI、process記録、validation command を分離 | 品質観点を混同しない | 実行結果を記録 |
| REQ-102 | pass | 受入条件と test 項目 | 検証可能な要求として追跡する | page testへ対応付け |
| DES-001 | pass | wireframes/component implementation と page構造 | 要求からUI設計への追跡を確保 | 実装後に照合 |
| CON-080 | pending | Search/Home testを追加予定 | 変更分岐をテストする | Vitest実行後に判定 |
| TST-001 | pass | 対象/非対象と narrow→aggregate の実行順 | テスト範囲を明示した | 実施統計をreportへ記録 |
| TST-801 | pending | 実行前 | 終了基準は未検証 | 全command後に判定 |

## 完了整理時の確認

- 実装と受入条件別の検証結果は`reports/working/20260726-ui-rewrite-phase3.md`に記録済みである。後続のPhase 4 E2EおよびPhase 7dの`task verify`終了コード0で、統合・aggregateの回帰も確認した。
- 計画時表の`pending`は実行前の記録であり、完了時の判定は上記reportを正本とする。
