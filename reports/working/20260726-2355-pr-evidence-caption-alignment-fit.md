# Phase 8b PR証拠キャプション整合の適合報告

## 指示と判断

公開予定のPR本文・コメント・視覚証拠について、画像またはE2Eで直接裏付けられない主張を是正した。`gh`、commit、push、PR操作は行っていない。

- 問題1は(a)を採用した。375×812で最下部までスクロールした`fullPage: false`の`home-bottom-viewport-mobile.png`を追加し、規約・プライバシー・削除窓口リンクが固定下タブの上に可視であることを示した。撮影scriptへ再現手順を追加し、READMEにはfull-page撮影でのfixed要素の読み方を注記した。
- 問題2は(a)を採用した。calendar日付buttonの44×44px hit領域を維持し、選択・範囲の視覚セルを`::before`の40×40pxへ分離した。calendarを開いた状態で両値を別々に測るE2Eを追加し、適合表とPR下書きの集計を29項目／60 E2Eへ更新した。
- 問題3は実装を確認した。`LoadingState`の文言は`.sr-only`内にあり、視覚的には3本のplaceholderだけである。キャプションは視覚証拠と、`role=status`を確認する`公開データの遅延中はloadingを表示する` E2Eを分けて記載した。

## 全画像の再点検

READMEとPRコメントの17 PNGを目視した。画像だけで確定できない`sticky`、`fixed`、画面遷移の有無、内部flag、数値寸法、行全体リンク、横スクロール、CTAの固定はキャプションから除外した。画像に可視な構成・文言に限定し、calendar寸法とloadingの支援技術通知はテスト名を併記した。PR本文のE2E件数も58件から実行済みの60件へ修正した。

## 実行結果

| command | 結果 |
| --- | --- |
| `node tools/capture-ui-rewrite-screenshots.mjs` | 合格。最下部viewportを含む53枚を再生成。 |
| `cd frontend && npm run test:e2e` | 合格、60 passed、40.3秒。desktop/mobile各30件。 |
| `cd backend && .venv/bin/python -m pytest -q` | 合格、63 passed、2.95秒。 |
| `task verify` | 合格、終了コード0。内包E2E 60 passed、40.3秒。 |
| PNG容量 | 合格、17枚・2,178,132 bytes（2.077 MiB、2.5MB以内）。 |

## SWEBOKセルフチェック

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- |
| MGT-003 | pass | task受け入れ条件、17 PNG、指定3 command終了結果 | 完了基準を成果物・容量・実測・終了コードで確認した | 次回の証跡追加時も容量を再計測する |
| MGT-060 | pass | 本report「全画像の再点検」 | 根拠不足の主張を公開するとレビュー誤認を招くリスクを、証拠追加または主張弱化で解消した | PR更新時に同じ画像単位の確認を行う |
| PRC-001 | pass | README、PR本文、PRコメント、撮影script | 公開対象とprivate再現用撮影を分離し、対象外のPR投稿を行わなかった | 視覚証拠の追加時にREADMEへ追記する |
| SCM-001 | pass | `git diff --check`、evidence README、capture script | PNGの生成手順・公開選定・容量を構成として追跡可能にした | 親agentがcommit時に対象ファイルを確認する |
| QUA-001 | pass | 目視PNG、calendar E2E、loading E2E | 製品の視覚品質とprocess／programmatic証拠を混同しないよう記述を分離した | screen reader実機確認は未実施のまま残す |
| REQ-102, DES-001 | pass | design-system 6.8、RangeCalendar、追加測定E2E | 視覚40pxとhit領域44px以上を実装・測定・適合表へ追跡した | calendar UI変更時は両測定を再実行する |
| CON-080, TST-701, TST-801 | pass | E2E 60 passed、backend 63 passed、task verify exit 0 | 変更したCSS・E2Eと集約検証を完走した | browser matrix拡張は別途実施する |

残余risk: screen reader実機確認とChrome以外のbrowser matrixは未実施であり、合格とは扱っていない。
