# UI全面書き直し Phase 1: 設計参照の解析と計画策定

状態: done

## 対象

- `.workspace/design-reference/{design-spec,wireframe,components}.html` を全量読了し、設計参照をMarkdownへ忠実に移植する。
- 現行 `frontend/src/**`、`docs/spec/**`、既存testを読み、後続3フェーズの実装計画と契約維持事項を記録する。
- `docs/design/wireframes.md`、`docs/design/component-implementation.md`、`reports/working/20260726-ui-rewrite-plan.md` のみを作成・更新する。`frontend/src/**` は変更しない。

## 受け入れ条件

- [x] 参照HTML 3本を全量確認した証跡を残す。
- [x] ワイヤーフレームとコンポーネント実装を日本語Markdownへ移植し、実DOM・数値・状態・a11yを記録する。
- [x] 画面別・コンポーネント別のgap表、Phase 2〜4の具体的なファイル計画、既存契約をレポートに記録する。
- [x] `frontend/src/**` を変更しない。
- [x] 適用SWEBOKチェックの判定、直接証拠、未実行検証を事実どおりレポートへ記録する。

## 適用SWEBOK（計画前選定）

| ID | 期待する証跡 | 検証方法 |
| --- | --- | --- |
| 要件定義: REQ-001, REQ-012 | 正本仕様とのtraceability表 | 仕様・設計・現行コードの読合せ |
| 詳細設計: DES-001, DES-018, DES-032 | wireframe/component移植、DOM・a11y設計 | 参照HTML全量読了と文書review |
| 実装: CON-001, CON-020 | 既存contractを保護するPhase計画 | `frontend/src`・testの静的調査 |
| テスト: TST-001, TST-014 | Phase 4のnarrow→aggregate計画 | test/e2eとpackage scriptsの静的調査 |
| 構成管理: SCM-001, SCM-012 | 変更対象・非対象と成果物識別 | `git diff`、成果物存在確認 |
| マネジメント: MGT-001, MGT-022 | scope、リスク、未決事項、フェーズ計画 | 本task・report review |
| プロセス: PRC-001, PRC-020 | Phase gateと記録 | task/report review |
| 品質保証: QUA-001, QUA-016 | 検証境界と残余risk | report review |

チェックIDは各KA checklistの実IDを確認して、成果物作成時に正規化する。Critical/Highが存在すればそれを優先する。
