# UI全面書き直しのPR用視覚証跡

`reports/private/ui-verification-20260726/`で撮影した53枚から、PRでの確認に必要な17枚だけを選定した。主要画面のdesktop／mobile、条件UI、重要な状態分岐を優先し、合計は約2.08MiBである。選ばなかった通常画面、404、保存・履歴、規約・privacy、管理画面など36枚は、比較・再確認用として`reports/private/ui-verification-20260726/`に残しており、Git管理には含めない。

通常のPNGはfull-page撮影である。`position: fixed`の下タブはfull-page画像では撮影時のスクロール位置に描画されるため、本文との重なりの有無をfull-page画像から判断しない。この点は、375×812 viewport・最下部スクロール・`fullPage: false`で撮影した`home-bottom-viewport-mobile.png`で確認する。

| ファイル | 画面・状態 | 示していること | 対応する正本の項目 |
| --- | --- | --- | --- |
| `home-normal-desktop.png` | ホーム・desktop通常表示 | 220pxサイドバーと動画グリッドを持つPCホームであり、カードが罫線のみ・角丸12pxの画面構成になっている | `wireframes.md`「共通レイアウト」「ホーム」、`design-system.md` 4・7 |
| `home-normal-mobile.png` | ホーム・mobile通常表示 | 375pxで検索ファーストの単一カラム、動画カード、固定下タブを表示する | `wireframes.md`「共通レイアウト」「ホーム」、`design-system.md` 7・8 |
| `home-bottom-viewport-mobile.png` | ホーム・mobile最下部viewport | ページ最下部で、規約・プライバシー・削除窓口リンクが固定下タブの上に可視であることを示す（375×812、`fullPage: false`） | `wireframes.md`「共通レイアウト」、`design-system.md` 8 |
| `search-results-desktop.png` | 検索結果・desktop | 検索バー、条件行、件数、動画行を本文に表示し、サイドバーを含むPC構成を示す | `wireframes.md` 4a「検索結果」、`component-implementation.md`「SearchBar」「VideoListItem」 |
| `search-results-mobile.png` | 検索結果・mobile | 375pxで検索結果の動画行、日付・長さ、条件行を表示する | `wireframes.md` 4a「検索結果」、`component-implementation.md`「VideoListItem」 |
| `detail-normal-desktop.png` | 動画詳細・desktop通常表示 | YouTube導線、保存操作、派生情報、関連動画をPC本文に表示する | `wireframes.md`「動画詳細」、`component-implementation.md`「VideoGridCard」 |
| `detail-normal-mobile.png` | 動画詳細・mobile通常表示 | サムネイル、メタ、タグ、YouTube導線、保存、派生情報を上から順に表示し、投稿日・長さは日本語で整形されている | `wireframes.md`「動画詳細」、`component-implementation.md`「VideoListItem」 |
| `search-conditions-desktop.png` | 検索条件・desktop右パネル | 検索結果の上に右側の条件パネルを表示し、タグ・長さ・投稿日とCTAを表示する | `wireframes.md` 4a「条件シート／右パネル」、`design-system.md` 6.6・7 |
| `search-conditions-mobile.png` | 検索条件・mobileボトムシート | 375pxで背景オーバーレイと下から開いた条件シート、タグ節を表示する | `wireframes.md` 4a「条件シート／右パネル」、`design-system.md` 4・6.6・8 |
| `search-calendar-desktop.png` | 投稿日カレンダー・desktop右パネル | 右パネルに「条件に戻る」、月移動、クリア、7列の日付gridを表示する | `wireframes.md` 4a「カレンダー差し替え状態」、`component-implementation.md`「RangeCalendar」 |
| `search-calendar-mobile.png` | 投稿日カレンダー・mobileシート差し替え | 375pxのシート内に「条件に戻る」、月移動、曜日、日付grid、CTAを表示する。視覚セル40px／hit領域44px以上は`design-measurements.spec.ts`の「カレンダー日付セルの視覚寸法と操作領域を実要素で測定する」で測定する | `wireframes.md` 4a「カレンダー差し替え状態」、`design-system.md` 6.8・8 |
| `detail-artifact-not-generated-mobile.png` | 動画詳細・派生artifact未作成 | チャット、タイムスタンプ、ワードクラウドなどの欠落を「未作成」と表示する | `wireframes.md`「動画詳細」「読み込み・空・エラー・未検出」、`design-system.md` 8 |
| `detail-without-consent-mobile.png` | 動画詳細・未同意 | 同意ボタンと規約導線を表示し、画像内にYouTube導線・派生情報・同意取り下げ操作がない状態を示す | `wireframes.md`「動画詳細」、`docs/spec/22.system-specifications.md`の外部Policy・GATE優先 |
| `home-loading-mobile.png` | ホーム・loading | 視覚的には3本のストライプplaceholderを表示する。読み込み状態は`role=status`で支援技術へ通知し、`comprehensive-coverage.spec.ts`の「公開データの遅延中はloadingを表示する」で確認する | `wireframes.md`「読み込み・空・エラー・未検出」、`design-system.md` 8 |
| `search-data-not-found-mobile.png` | 検索・公開artifact未検出 | 「公開データが見つかりません」という利用不可理由と再取得操作を表示する | `wireframes.md`「読み込み・空・エラー・未検出」、`design-system.md` 8 |
| `home-server-error-mobile.png` | ホーム・503 retryable error | 日本語のエラー説明、技術情報の開閉、再取得操作を表示する | `wireframes.md`「読み込み・空・エラー・未検出」、`design-system.md` 8 |
| `home-server-error-desktop.png` | ホーム・503 retryable error・desktop | PCサイドバーと、日本語のエラー説明・再取得操作を表示する | `wireframes.md`「読み込み・空・エラー・未検出」、`design-system.md` 8 |
