# diopside デザインシステム

- 文書ID: DIO-DESIGN-001
- 版: v1.1
- 状態: UI design systemの正本
- 更新日: 2026-07-11
- 移植元: `.workspace/diopside デザイン仕様書 (standalone).html`
- Product scope: [docs/spec/10.use-cases-personas-value.md](../spec/10.use-cases-personas-value.md)
- Requirements: [docs/spec/20.requirements-definition.md](../spec/20.requirements-definition.md)
- UI specifications: [docs/spec/22.system-specifications.md](../spec/22.system-specifications.md)
- ベース: ワイヤー 6b(PCサイドバー)+ 5a(検索・条件UI)+ 4a(統合検索フロー)
- トークン実体: `apps/web/assets/css/main.css` の `@theme`

本文書がtoken、component、responsive、interaction、accessibilityのtarget正本である。要求／画面flowは`docs/spec`、実装値はCSS tokenを参照し、差がある場合はcurrent implementationをtarget仕様へ合わせるか、本文書を明示的にversion updateする。現行の44px、keyboard、live region、focus return差は`GAP-FE-A11Y-001`で追跡する。

## 1. デザイン原則

1. **モバイルファースト** — 375px・片手操作を基準に設計し、PC へ拡張する。ヒットターゲットは常に 44px 以上。
2. **説明なしで使える** — 入口(追加チップ等)は空状態でも常設し、機能を探させない。学習は1回で済む構造にする。
3. **候補は提示、判断は人** — サジェスト・解釈・タイムスタンプ候補は必ず可視化し、ユーザーが修正・解除できる。
4. **静かな上品さ** — 紫1色+無彩色で構成し、装飾よりも余白と階層で世界観を作る。彩度の高い色・絵文字は使わない。
5. **静的データ前提** — 全 UI は検証済みの静的 JSON（タグ index・検索 index）で成立させ、件数のライブ表示もクライアント側で完結する。targetはversioned release、現行3 pathは移行中のcompatibility contractとする。
6. **IDと表示を分離する** — tagのcomponent identity、URL、filter stateはstable `tagId`を使う。同じ表示名を持つ異なる分類軸はsubcategory contextで区別する。
7. **Policy失効時は安全に縮退する** — GATE-001が無効ならderived tag／分析をDOM、URL候補、sort／filterから除外し、未取得を0件と表示しない。

## 2. カラー

白雪巴さんのイメージカラー(菫)を唯一のアクセントに、雪白のニュートラルで支える。ライトテーマを正とし、ダークは将来拡張。

| トークン                      | 値                         | 用途                       |
| ----------------------------- | -------------------------- | -------------------------- |
| primary-500 菫 (`sumire-500`) | `#7C5CBF`                  | 主ボタン・選択状態・リンク |
| primary-600 (`sumire-600`)    | `#6F4FB4`                  | hover / pressed            |
| primary-100 (`sumire-100`)    | `#EDE7F8`                  | トークン背景・選択日レンジ |
| primary-50 (`sumire-50`)      | `#F5F2FB`                  | ハイライト面               |
| ink-900                       | `#211D2B`                  | 見出し・本文               |
| ink-600                       | `#5C5668`                  | メタ情報・補足             |
| bg 雪白 (`ink-50`)            | `#F7F6FA`                  | アプリ背景                 |
| surface / line                | `#FFFFFF` / `#E4E1EC`      | カード面 / 罫線            |
| success                       | `#3D7D5E`                  | 成功状態                   |
| danger                        | `#B84A5C`                  | 失敗・削除                 |
| warning                       | `#B9893A`                  | 実行中・注意               |
| focus ring                    | `rgba(124,92,191,.35)` 3px | フォーカス表示             |

ルール: アクセントは菫のみ。semantic 色は管理 UI と破壊的操作に限定。本文コントラストは 4.5:1 以上(ink-900/bg=13.9:1、ink-600/bg=6.5:1)。primary-500 上の白文字はボタンなど大きい要素のみ。

## 3. タイポグラフィ

| ロール                    | 指定                                              | CSS クラス      |
| ------------------------- | ------------------------------------------------- | --------------- |
| wordmark                  | Cormorant Garamond 600 / ls .1em                  | `.dio-wordmark` |
| display(見出し大)         | Shippori Mincho 600 / 24px / lh 1.4               | `.dio-display`  |
| title(動画タイトル)       | Zen Kaku Gothic New 700 / 16px / lh 1.5 / 2行省略 | `.dio-title`    |
| body(本文・チップ)        | 400–500 / 14px / lh 1.7                           | 既定            |
| caption(メタ情報)         | 400 / 12.5px / ink-600                            | `.dio-caption`  |
| label(セクション見出し小) | 700 / 11px / ls .12em / primary-500               | `.dio-label`    |

ルール: 明朝(Shippori Mincho)は画面見出し・空状態メッセージのみ。UI 操作要素はすべてゴシック。数字・時刻は等幅指定(`font-variant-numeric: tabular-nums` = `.dio-num`)。最小サイズはモバイル 11px。

## 4. 形状・余白・エレベーション

- **スペーシング(4px グリッド)**: inset(カード内) 16px / 画面左右 16px(mobile) 24px(PC) / 要素間 gap 8px(密) 12px(標準) 24px(セクション間) / リスト行間 12px / セクション余白 32px
- **角丸**: チップ・トークン 999px(full) / ボタン 12px / カード・サムネイル 12px / シート上部 20px / 入力欄 14px / カレンダー選択日 999px
- **罫線・枠**: 標準罫線 1px `#E4E1EC` / 入力・チップ枠 1.5px / フォーカス 3px ring
- **エレベーション(3段のみ)**: 0=なし(通常カード=罫線のみ) / 1=`0 2px 8px rgba(33,29,43,.08)`(sticky 条件行・ドロップダウン) / 2=`0 8px 28px rgba(33,29,43,.16)`(シート・右パネル)

## 5. アイコン

Material Symbols(Iconify `@iconify-json/material-symbols`、outlined 系)。サイズは 16(インライン)・20(ナビ・入力欄)・24(単独ボタン、ヒット領域44px)。色は常に隣接テキストと同色。絵文字は使用禁止。

主なアイコン: search / sell(タグ) / calendar_month(投稿日) / tune(条件) / home / star(保存) / history(履歴) / shuffle(ランダム) / chat_bubble(チャット数) / play_circle(YouTubeで見る) / settings(管理) / close(解除) / chevron_right(遷移)

## 6. コンポーネント対応表

| 仕様書 §                | Target component contract                                                                                                         | Current implementation／status                                              |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| 6.1 ボタン              | primary h48/radius12(1画面1つ)・secondary 枠1.5px・text                                                                           | 各 Screen 内                                                                |
| 6.2 チップ4種＋選択状態 | 選択可（selected stateあり）/ 適用中(removable) / 追加(dashed) / アクション(バッジ付き)                                           | `components/dio/DioChip.vue`                                                |
| 6.3 検索バー            | 自然言語+タグトークン、h44/radius14                                                                                               | `components/dio/SearchBar.vue`                                              |
| 6.4 サジェスト          | 最大4行=タグ≤2+日付≤1+キーワード1、行h44                                                                                          | `components/dio/SuggestList.vue` + `shared/search/suggest.ts`               |
| 6.5 条件行(sticky)      | 条件ゼロ=追加チップ3種、適用後=removable+条件(n)                                                                                  | `components/dio/ConditionRow.vue`                                           |
| 6.6 条件シート/右パネル | mobile ボトムシート / PC 右パネル w320、3セクション固定、CTA 件数ライブ                                                           | `components/dio/ConditionSheet.vue` + `ConditionPanel.vue`                  |
| 6.7 レンジスライダー    | 0〜5h+、15分スナップ、上限振り切り=上限なし                                                                                       | `components/dio/LengthSlider.vue`                                           |
| 6.8 カレンダー          | 2タップ範囲選択、配信ドット、visual cell 40px／hit area 44px以上、未来日disabled                                                  | `components/dio/RangeCalendar.vue`のhit areaはcurrent 40px。GAP-FE-A11Y-001 |
| 6.9 動画カード          | リスト行(サムネ120×68)/ グリッドカード、タグ最大2、チャット数は集計がある動画のみ                                                 | `components/dio/VideoListItem.vue` / `VideoGridCard.vue` / `VideoThumb.vue` |
| 6.10 ナビゲーション     | mobile 下タブ4項目 h56+safe-area / PC サイドバー w220。targetは未認証時に「管理」を表示しない。current disabled表示はGAP-AUTH-001 | `components/dio/AppShell.vue`                                               |

## 7. レイアウト・ブレークポイント

- `<768px`(mobile・基準375px): 単一カラム+下タブ。条件UI=ボトムシート。検索は「検索」タブの専用画面。
- `≥768px`(PC): サイドバー 220px+コンテンツ(リスト max-width 760px / グリッド 3〜4列)。条件UI=右スライドパネル 320px。

## 8. インタラクション・アクセシビリティ

- **モーション**: シート/パネル 240ms ease-out(下から/右から)。チップ・件数更新は即時。サジェスト開閉 120ms。`prefers-reduced-motion` 時は非本質的な移動・遷移を無効にし、本質的な状態変化はアニメーションなしで即時反映する。
- **フィードバック**: 条件変更→件数ライブ更新。0件時は CTA が「0件 — 条件をゆるめる」に変化し、直近条件の解除候補を1つ提示。
- **アクセシビリティ**: ヒット領域 44px 以上 / フォーカスリング 3px 必須 / コントラスト本文 4.5:1・大要素 3:1 / チップ解除は aria-label「◯◯の条件を解除」 / シートは focus trap + Esc で閉じる。
- **同名タグ**: 表示名が同じでも`tagId`をkeyとし、subcategoryを可視textまたはaccessible descriptionで伝える。選択件数の変更はpolite live regionでまとめて通知する。
- **状態**: loading / empty / partial / retryable error / permanent error / successを視覚・programmaticに区別し、focusを奪わない。欠落artifactは0件と表示しない。
- **状態の永続化**: お気に入り・履歴・最近の検索は localStorage。検索条件は URL クエリに反映し共有可能にする。
