# diopside基準実装の初期構築

状態: in_progress

## 受け入れ条件

- [ ] backend が public static契約（latest.json + release配下）を公開できる。
- [ ] frontend が `/`, `/search`, `/saved`, `/history`, `/videos/:id` を提供できる。
- [ ] Policy同意後に派生データを表示する動線を持つ。
- [ ] localStorage が保存・履歴・recent searchで version key を持つ。
- [ ] `/admin` route は public ナビに露出しない。
- [ ] `task verify` で実行コマンドが定義される。

## 実施内容

- backend: FastAPI + static契約サーバを追加。
- frontend: React + route shell + 保存/履歴/検索を追加。
- infra: プレースホルダ（plan/report）を追加。
- 作業ログ: tasks と reports の最小骨格を追加。
