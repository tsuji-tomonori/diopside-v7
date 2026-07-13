# Gate証拠の失効と置換

1. GATE-001〜006 evidenceのscope、project/account、effectiveAt、expiresAt、ownerを日次確認する。
2. 失効/不一致時はnormal生成・公開を停止する。
3. GATE-001/002失効では禁止dataを減らすcompliance purgeを優先する。
4. replacement evidenceは旧recordを変更せず、単方向supersedes linkで追加する。
5. scopeがcollector、retention、public projection、IaCと一致するまでnormalを再開しない。
6. Product Owner/operatorの判断、根拠、時刻を監査記録へ残す。

metadata-only containmentやpurgeをnormal/product acceptanceとして数えない。
