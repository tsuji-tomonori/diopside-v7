# yt-dlpによるタイムスタンプ入力回復の実測

## 指示と対象

`gpt-5.6-sol`の利用許可を受け、前回入力取得で停止した白雪巴出演アーカイブについて、`yt-dlp`で字幕または音声を取得できるか再検証した。対象は通常公開・字幕なし・年齢制限を代表する3本とした。

## 判断

- `yt-dlp`のメタデータ抽出、字幕保存、音声URL解決、音声実体保存を別gateとして扱う。
- 終了コード0でも保存物がHTMLの場合があるため、ファイル種別・サイズ・再生時間が確認できない音声をASR入力にしない。
- 年齢制限動画はCookieなしで回避を試みず、認証済み入力待ちとする。
- 字幕の全編coverageと独立レビューが完了するまで、公開releaseの`timestamps.status`を生成済みにしない。

## 実測結果

| 動画ID | 区分 | yt-dlp結果 | 判定 |
| --- | --- | --- | --- |
| `UZcmZzKQWYc` | 通常公開・字幕あり | `ja-orig` VTT 644,441 bytes、SHA-256 `46898109f6b9b7113b0e268e32e57b3ec7ddf955746b01f452e3ce609c5e53a9`、正規化1,493 cue、raw timing gap 0件 | 入力品質gate合格。意味マッピングと独立レビューへ進める |
| `ajB1VeIsrlc` | 通常公開・字幕なし | 音声format 251とURLは解決。保存物は195 bytesの`Site Unavailable` HTML | 入力品質gate不合格。全編ASR音声未取得 |
| `gl5UkwS_jmM` | 年齢制限 | `Sign in to confirm your age` | 入力品質gate不合格。認証済み入力待ち |

## 実行した検証

- `yt-dlp 2026.07.04 --list-subs`: 3本の字幕・availabilityを確認した。
- `yt-dlp -f bestaudio --get-url`: 公開2本では音声URL解決、年齢制限1本では認証要求を確認した。
- `yt-dlp --write-auto-subs --sub-langs ja-orig,ja --skip-download`: `UZcmZzKQWYc`のVTT保存に成功した。
- `yt-dlp -f bestaudio`: `ajB1VeIsrlc`はexit 0だが、`file`判定でHTML、内容は`Site Unavailable`だった。
- 添付skillの`parse_vtt_with_timing`: `UZcmZzKQWYc`で1,493 cue、raw timing 119.079〜5,113.159秒、10秒以上のgap 0件を確認した。
- Google Sheets `対象動画` 37行、179行、1807行を更新し、書戻し結果を再読した。

## fitと未対応

yt-dlpで公開字幕の取得経路は回復したが、字幕なし動画のメディアCDN遮断と、年齢・会員制限の認証入力不足は解消していない。`UZcmZzKQWYc`も独立レビュー前のため作成済みにはしていない。全体601本の完了条件は未達である。

## セルフチェック

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | blocked | 1,813本の台帳と未作成601本 | 完了基準は数値化されているが未達 | 動画単位gateを継続する |
| MGT-060 | pass | 本レポートの3種実測 | 原因、事象、影響、次の対応を分離した | CDN・認証制限を継続監視する |
| PRC-001 | pass | 3種の代表動画と非対象判断 | yt-dlp検証の適用範囲が一意 | 公開字幕ありへ拡張する |
| SCM-001 | pass | PR #3の既存branchと本記録 | 重複PRを作らず変更履歴を維持 | branchのremote SHAを照合する |
| QUA-001 | blocked | 字幕coverageは合格、独立レビューは未実施 | 入力品質と最終製品品質を混同していない | 2レビューとvalidatorを実施する |
| AI-001 | blocked | 字幕hash、cue、timing根拠 | 生成目的と入力評価は追跡できるが、公開評価未完了 | `UZcmZzKQWYc`の意味・レビュー工程を完了する |
