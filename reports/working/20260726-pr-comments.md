# PRコメント投稿用下書き

以下の各見出しから次の見出しの直前までを、1件のPRコメントとして投稿する。

## コメント1: 主要画面のdesktop／mobile

採用したワイヤー `6b + 5a + 4a`のうち、6bのPCサイドバー、5aの検索UI、4aの統合検索フローを主要画面へ対応付けました。desktopは220px sidebar＋main、mobileは375px単一カラム＋固定下タブです。

![ホーム desktop](__RAW_BASE__/docs/evidence/ui-rewrite-20260726/home-normal-desktop.png)

ホームdesktopは、6bの220pxサイドバーと動画グリッド、カードの罫線・角丸を示す証拠です。

![ホーム mobile](__RAW_BASE__/docs/evidence/ui-rewrite-20260726/home-normal-mobile.png)

ホームmobileは、検索ファーストの単一カラム、動画カード、固定下タブを示す証拠です。

![ホーム mobile 最下部viewport](__RAW_BASE__/docs/evidence/ui-rewrite-20260726/home-bottom-viewport-mobile.png)

最下部viewportは375×812・`fullPage: false`で撮影し、規約・プライバシー・削除窓口リンクが固定下タブの上に可視であることを示します。通常のfull-page画像では固定要素がスクロール位置に描画されるため、この点の根拠には使いません。

![検索結果 desktop](__RAW_BASE__/docs/evidence/ui-rewrite-20260726/search-results-desktop.png)

検索結果desktopは、5a／4aの検索バー、条件行、件数、動画行を本文へ集約した構成の証拠です。

![検索結果 mobile](__RAW_BASE__/docs/evidence/ui-rewrite-20260726/search-results-mobile.png)

検索結果mobileは、375pxで動画行のメタ情報と条件行を表示する構成の証拠です。

![動画詳細 desktop](__RAW_BASE__/docs/evidence/ui-rewrite-20260726/detail-normal-desktop.png)

動画詳細desktopは、YouTube導線、保存、派生情報、関連動画をPC本文へ表示する構成の証拠です。

![動画詳細 mobile](__RAW_BASE__/docs/evidence/ui-rewrite-20260726/detail-normal-mobile.png)

動画詳細mobileは、サムネイルから派生情報までを上から順に表示し、投稿日・長さを利用者向けに整形した表示の証拠です。

## コメント2: 検索条件のinteraction

条件UIは別画面へ遷移させず、mobileではボトムシート、desktopでは右パネルとして表示します。カレンダーはその内部を差し替えるため、検索条件と現在のrouteを保ったまま戻れます。

![条件パネル desktop](__RAW_BASE__/docs/evidence/ui-rewrite-20260726/search-conditions-desktop.png)

desktop右パネルは、検索結果の上にタグ・長さ・投稿日とCTAを表示する構成の証拠です。

![条件シート mobile](__RAW_BASE__/docs/evidence/ui-rewrite-20260726/search-conditions-mobile.png)

mobile条件シートは、背景オーバーレイ上に下から開き、タグ節を表示する構成の証拠です。

![カレンダー desktop](__RAW_BASE__/docs/evidence/ui-rewrite-20260726/search-calendar-desktop.png)

desktopカレンダーは、右パネルに「条件に戻る」、月移動、クリア、7列gridを表示する証拠です。

![カレンダー mobile](__RAW_BASE__/docs/evidence/ui-rewrite-20260726/search-calendar-mobile.png)

mobileカレンダーは、375pxのシート内に「条件に戻る」、月移動、曜日、日付grid、CTAを表示する証拠です。視覚セル40pxと日付buttonのhit領域44px以上は、`design-measurements.spec.ts`の「カレンダー日付セルの視覚寸法と操作領域を実要素で測定する」で別々に実測します。

## コメント3: 状態の出し分け

状態を成功や0件に誤変換しないことを確認するため、loading、公開artifact未検出、retryable error、派生artifact未作成、未同意を個別に撮影しました。特に「未作成」と「0件」は別の意味として表示しています。

![読み込み中](__RAW_BASE__/docs/evidence/ui-rewrite-20260726/home-loading-mobile.png)

読み込み中は、視覚的に3本のストライプplaceholderを表示する証拠です。状態メッセージは画像には表示せず、`LoadingState`の`role=status`で支援技術へ通知します。これは`comprehensive-coverage.spec.ts`の「公開データの遅延中はloadingを表示する」で確認します。

![公開artifact未検出](__RAW_BASE__/docs/evidence/ui-rewrite-20260726/search-data-not-found-mobile.png)

公開artifact未検出は、利用不可理由と再取得導線を表示する証拠です。

![503エラー mobile](__RAW_BASE__/docs/evidence/ui-rewrite-20260726/home-server-error-mobile.png)

503エラーmobileは、日本語の説明、技術情報の開閉、再取得操作を表示する証拠です。

![503エラー desktop](__RAW_BASE__/docs/evidence/ui-rewrite-20260726/home-server-error-desktop.png)

503エラーdesktopは、PCサイドバーとエラー時の再取得操作を表示する証拠です。

![派生artifact未作成](__RAW_BASE__/docs/evidence/ui-rewrite-20260726/detail-artifact-not-generated-mobile.png)

派生artifact未作成は、チャット等の欠落を「未作成」と表示する証拠です。

![未同意詳細](__RAW_BASE__/docs/evidence/ui-rewrite-20260726/detail-without-consent-mobile.png)

未同意詳細は、同意・規約導線を表示し、画像内にYouTube導線、派生情報、同意取り下げ操作がない状態の証拠です。

## コメント4: 実測による適合検証

`design-measurements.spec.ts`はCSS変数の値だけで判定せず、実要素の`getComputedStyle()`または`getBoundingClientRect()`を測定します。カレンダーは開いた状態で視覚セルと日付buttonの操作領域を別々に測定します。実行結果は適合29、不適合0、未検証0でした。

| 測定項目 | 実測値 |
| --- | --- |
| primary button背景／selected chip背景／link色 | `rgb(124, 92, 191)`／`rgb(237, 231, 248)`／`rgb(111, 79, 180)` |
| display／caption／label | `24px`／`12.5px`／`11px / 700 / 1.32px` |
| video title | `16px / 700` |
| chip／button／card／input角丸 | `999px`／`12px`／`12px`／`14px` |
| sheet角丸／sheet影 | mobile `20px`、desktop panel `0px`／`rgba(33,29,43,.16) 0px 8px 28px` |
| card影／標準罫線 | `none`／`1px` |
| input・chip・button罫線 | CSS指定`1.5px`、mobile Chromeのcomputed値`1px`、cssRules`1.5px` |
| focus outline | `3px solid` |
| 横padding／list gap／section margin | mobile `16px`・desktop `24px`／`12px`／`32px` |
| search bar／primary button高さ | `44px`／`48px` |
| mobile tab高さ | Link `56px`、safe-areaを含むnav `57px` |
| sidebar幅／右panel幅 | `220px`／`320px` |
| sidebar項目の視覚高／hit領域 | 疑似要素背景`40px`／Link矩形`44px` |
| sidebar radius | 疑似要素`10px` |
| カレンダー日付セルの視覚高／hit領域 | 疑似要素`40px`／button矩形`44px × 44px` |
| visible button・link | 全件`44px × 44px`以上 |

実測で見つけて修正した主な不適合は、投稿日・長さの生値、503時の英語技術文字列、未同意詳細のリンク重なりと取り下げ操作、skip link `43.80px`・footer link `22.09px`、sidebarの40px／44pxの仕様衝突、`artifactFlags.chat=false`でのチャット数表示です。修正後は、sidebarを視覚40px＋hit領域44pxに分離し、公開値がないチャット数は表示しない仕様にしています。

補足として、frontend E2Eはdesktop-chrome 30件とmobile-chrome 30件の計60件が終了コード0で完走し、axeはcritical 0・serious 0でした。screen reader実機確認とChrome以外の追加browser matrixは未実施です。
