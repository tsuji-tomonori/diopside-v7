# 削除とCDN purge

## 起動条件

source削除/非公開、30日refresh不能、policy/permission失効、privacy deletion、retention期限。

## 手順

1. target identity、source、理由、期限、actorをdeletion eventへ固定する。
2. publicから除外する`compliance_purge` candidateをbase latestから減算生成する。
3. processed、raw、author ID/token/key、object version、replica/backupの順に対象を削除またはcryptographic erasureする。
4. purge release検証後にlatestを切り替える。新video/tag/derived field追加は禁止する。
5. 対象versioned URLとCloudFront pathをinvalidate/denyする。
6. 5分以内にorigin/CDN取得成功0、7日以内にprivacy対象全layer 0をread-backする。
7. 各layer、CDN、結果、時刻を監査記録へ保存する。

削除は再現性、versioning、backup保持より優先する。
