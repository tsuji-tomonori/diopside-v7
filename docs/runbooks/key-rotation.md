# Credential and HMAC key rotation

1. 対象key、owner、利用job、最終利用、rotation reasonを確認する。
2. 新versionをSecrets Manager等へ作成し、旧keyを上書きしない。
3. non-productionで取得、署名、HMAC video間非一致、log非露出を確認する。
4. operator承認後にconsumerを新versionへ切り替える。
5. overlap中の成功率とquotaを監視する。
6. rollback window後に旧credentialを失効する。
7. author HMAC keyは対応token/derived outputの削除完了後に破棄する。

API key/token値をcommand line、commit、report、logへ記載しない。
