# 公開releaseのrollback

## 起動条件

- latest取得失敗、schema/join/hash不整合、source/policy失効、重大UI回帰。

## 手順

1. 新規exportを停止し、correlation IDとactive releaseIdを記録する。
2. release catalogからpolicy-compliantな直前2版を確認する。削除・失効対象を含む版は除外する。
3. candidateを`ReleaseValidator`で再検証し、versioned artifactをread-backする。
4. operator承認後、latest pointerだけを条件付き更新する。
5. 15分以内にhealth、latest、index、代表detailを確認する。
6. 原因releaseをrollback候補から除外し、incident/reportへ記録する。

## ローカル訓練

`backend/tests/test_atomic_publisher.py`のvalid A、invalid B、latest不変を実行する。production pointerは変更しない。
