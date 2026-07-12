# full implementation rebaseline

状態: in_progress

## 背景

既存実装を完成済みとみなさず、仕様正本から要求、実装、検証の対応を再構成する。外部承認が必要なproduction gateと、ローカルで実装・検証できる範囲を分離する。

## 対象

- npm/Pythonの検証可能なモノレポ基盤
- canonical public release contractと境界テスト
- collector、processor、tagging、export、frontend、infraの段階実装
- `.workspace/tags.zip` と `.workspace/scripts.zip` を入力・移行資料として参照するYouTube collector/tagging実装
- requirements/acceptance/gapに対する検証証跡

## 非対象

- AWSへのdeploy/bootstrap/destroy
- production YouTube API projectの設定変更、quota申請、credential作成
- GATE-001〜005の人による承認代行
- 受領資料や既存ユーザー変更の削除

## 受け入れ条件

- [ ] `.workspace` がGit対象外である。
- [ ] ルートworkspaceのinstall/typecheck/test/buildが成功する。
- [ ] backendのruff/pyright/pytestとcanonical contract検証が成功する。
- [ ] frontendの主要route、query、local state、error、accessibility要件が自動検証される。
- [ ] collector/processor/tagging/exportがversion付きcontractを再現可能に生成する。
- [ ] YouTube Data API collectorがmetadata、uploads、comments、live chatをquota/checkpoint付きで取得できる。
- [ ] infraがrag-assistの構成・規約に沿うCDK synth/test可能なstackを持つ。
- [ ] local verification結果と未達gateが作業レポートに事実どおり記録される。
- [ ] deployを実行しない。

## 検証方法

- `task verify`
- `task export:check`
- 後続マイルストーンで追加するcollector/processor/tagging/IaCのfixture test

## リスク

- GATE-001〜005は外部承認・最新価格・実quotaを必要とし、ローカル実装だけでは合格しない。
- `.git` metadataが空で、現時点ではcommit/push不能である。
