# タイムスタンプ移植のPR用視覚証跡

PR #4を取り込んだUIで、release `20260729-001`を読み込んだ実画面から5枚を再撮影した。撮影は
`http://127.0.0.1:5173`の開発サーバーと`backend/data/public`の正規releaseに対して行い、同意状態は
`diopside_consent_v1`を設定して再現した。desktopは1440×900、mobileは375×812 CSS pxである。
外部サムネイルは通信に依存しないよう遮断し、アプリのfallback表示も含めて確認した。

| ファイル | 画面・状態 | 示していること |
| --- | --- | --- |
| `detail-timestamps-desktop.png` | 動画詳細・desktop | PR #4のDetail UI内で、移植した実データの章立てを時刻、信頼度、YouTube deep linkつきで一覧表示する |
| `detail-timestamps-mobile.png` | 動画詳細・mobile | 同じ章立てをmobile幅で表示し、長い日本語の章題が横方向へはみ出さないことを示す |
| `detail-no-timestamps-mobile.png` | 動画詳細・タイムスタンプ未生成 | タイムスタンプが無い動画では見どころ候補カードを描画せず、「未作成」も表示しない。反応集計など既存表示は維持する |
| `search-daigojinkaku-desktop.png` | 検索結果・desktop | 移植した動画がキーワード検索で実際に見つかる。`第五人格`で3件を返す |
| `home-mobile.png` | ホーム・mobile | 1209本を読み込んだ状態のホームで、実タイトルが省略表示され、mobile幅の破綻がない |

信頼度は生成元の`high`／`medium`／`low`を日本語の高／中／低へ写像して表示する。数値へ変換していない。
生成元`get_archives_info_v1`は利用者向けに「アーカイブ情報生成」と表示し、存在しない生成日時は推測していない。
