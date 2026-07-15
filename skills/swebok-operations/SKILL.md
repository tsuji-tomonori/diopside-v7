---
name: swebok-operations
description: 運用に関する計画、作成、変更、レビュー、完了判定を、repository同梱のSWEBOK/Well-Architectedチェックリストで証跡ベースに自己検査する。運用設計・運用の作業、関連成果物の更新、工程gateの判定時に使用する。
---

# 運用のAI駆動セルフチェック

## 正本を読む

1. repository rootの`AGENTS.md`と対象taskの受け入れ条件を読む。
2. `docs/spec/`、該当設計、既存実装・testから現在状態を確認する。
3. [チェックリスト](references/checklist.md)を読み、対象範囲に適用するIDを選ぶ。

## AI駆動で進める

1. 作業前に、対象ID、期待する証跡、検証方法をtaskへ記録する。Critical/Highを先に評価する。
2. 可観測性、インシデント、継続性、リリース、SLO、Runbookを、正本、contract、test、docsと同じ変更単位で実装する。
3. 設計判断や生成物を推測で補わず、ファイル、command出力、runtime挙動、承認記録など再確認可能な証跡へ結びつける。
4. 計画完了、実装完了、検証完了、報告前の各gateで、適用IDを再評価する。変更により適用範囲が増えた場合は対象IDを追加する。
5. 関連KAへ影響する場合は、対応skillも読む。少なくとも要件→設計→実装→テスト→運用・保守の下流影響を確認する。

## 判定を記録する

taskまたは`reports/working`に次の列を持つ表を作る。

```text
ID | status | evidence | rationale | follow-up
```

- `pass`: 合格基準を直接証明する証跡がある場合だけ使う。
- `fail`: 合格基準への反証、欠落、または回帰がある場合に使い、修正後に再評価する。
- `not-applicable`: 対象外である具体的理由とスコープ根拠がある場合だけ使う。
- `blocked`: 外部approval、credential、環境などが不足し、ローカルで証明不能な場合に使う。
- 未確認、未実行、timeout、skipped、間接証拠は`pass`にしない。

## gateを閉じる

1. 適用IDがすべて`pass`、または根拠付き`not-applicable`か確認する。
2. `fail`を修正し、同じ検証を再実行する。`blocked`は実装完了と外部gateを分離して残す。
3. 実行commandと結果、未対応、残余riskを`reports/working`へ記録する。
4. 対象IDの件数と判定件数が一致しない場合、工程完了を宣言しない。
