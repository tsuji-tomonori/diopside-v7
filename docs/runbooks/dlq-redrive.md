# DLQ diagnosis and redrive

1. DLQ alertから30分以内にjobId、canonicalJobKey、inputVersion、attempt、errorCode、correlationIdを結合する。
2. secret、本文、author IDをlogへ出さず、分類済みreasonを確認する。
3. permanent errorは自動retryしない。retryableはattempt 4までの履歴を確認する。
4. immutable input manifest/hashを保存し、原因修正とoperator reasonを記録する。
5. original jobを変更せずchild jobとしてredriveする。
6. output集合hashと件数がsingle deliveryと一致し、重複0を確認する。
7. 30分以内のredrive成功、alertから60分以内の復旧を記録する。

redriveはpublic publishを直接起動せず、通常のvalidation/gateを通す。
