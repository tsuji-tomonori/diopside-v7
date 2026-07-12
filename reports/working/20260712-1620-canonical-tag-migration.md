# canonical tag migration

## 指示

`.workspace/tags.zip` と `.workspace/scripts.zip` を参考に、taggingを完全実装へ進める。

## 実施

- NFKC、空白、case、先頭`#`を扱う照合正規化を実装。
- category/subcategory/canonical nameから決定論的stable `tagId`を生成。
- exact aliasをcanonical名へ解決してからIDを付与。
- reason/source/evidence/confidenceを保持したv3 assignmentへ移行。
- primary/media/channelの単一基数、duplicate ID、unknown/review値を拒否。
- taxonomyVersion、aliasVersion、algorithmVersion、scopeDecisionVersionをsnapshotへ追加。
- 異なるvideoId数に基づくpublic tag count/indexを生成。
- ZIPを直接読むpreview CLIとTaskfile commandを追加。

## 検証

- Ruff: pass
- Pyright strict: pass
- Pytest: 11 tests pass
- 実snapshot migration: pass
- videoCount: 2,062
- assignmentCount: 15,997
- 本人1,378件と外部684件の重複: 0

## 未対応

- 受領snapshotに残るsemantic/provenance gapのデータ修正。
- review ledgerと人手承認CLI。
- v1 integer/flat/composite key migration fixture。
- canonical v3 snapshotからatomic public releaseを生成・publishするexporter。
