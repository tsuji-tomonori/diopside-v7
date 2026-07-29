# タイムスタンプ移植のPR用視覚証跡

release `20260729-001` を読み込んだ実際の画面から5枚を撮影した。合計は約1.4MiBである。撮影は
`http://127.0.0.1:5173` の開発サーバーと `backend/data/public` の正規releaseに対して行い、同意状態は
`diopside_consent_v1` を設定して再現した。desktopは1280×860、mobileはPixel 7相当である。

| ファイル | 画面・状態 | 示していること |
| --- | --- | --- |
| `detail-timestamps-desktop.png` | 動画詳細・desktop | 移植した実データの章立てを、時刻とYouTube deep linkつきで一覧表示する。派生情報の識別子は`get_archives_info_v1`、作成日は生成元の`completedAt`を表示する |
| `detail-timestamps-mobile.png` | 動画詳細・mobile | 同じ章立てをmobile幅で表示し、長い日本語の章題が横方向へはみ出さないことを示す |
| `detail-no-timestamps-mobile.png` | 動画詳細・タイムスタンプ未生成 | タイムスタンプが無い動画では節そのものを描画せず、「未作成」も表示しない。チャット、コメント、ワードクラウドの既存表示は変えていない |
| `search-daigojinkaku-desktop.png` | 検索結果・desktop | 移植した動画がキーワード検索で実際に見つかる。`第五人格`で3件を返す |
| `home-mobile.png` | ホーム・mobile | 1209本を読み込んだ状態のホームで、実タイトルが省略表示され、mobile幅の破綻がない |

信頼度は生成元の`high`／`medium`／`low`を日本語の高／中／低へ写像して表示する。数値へ変換していない。
