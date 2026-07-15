# SWEBOK KA別AI駆動チェックリスト

`.workspace/swebok_checklist.xlsx`のKAシートを、AI agentが工程ごとに利用できるMarkdownへ同期した索引。元Excelはread-only入力でありGitへ追加しない。

元Excel SHA-256: `37a0a2d91c9ffc16955bd1f736605554c178d10144a5dc174587d47f9ac12ab7`

同期対象: 18 KA / 1673チェック項目

元ブックの[サマリ](source-summary.md)と[抜け漏れ分析](gap-analysis.md)も同期対象とする。

| KA | 元シート | 件数 | Skill | Agent | Checklist |
| --- | --- | ---: | --- | --- | --- |
| 要件定義 | `01_要件定義` | 88 | [`swebok-requirements`](../../../skills/swebok-requirements/SKILL.md) | [`swebok-requirements.toml`](../../../agents/swebok-requirements.toml) | [checklist](../../../skills/swebok-requirements/references/checklist.md) |
| アーキテクチャ | `02_アーキテクチャ` | 82 | [`swebok-architecture`](../../../skills/swebok-architecture/SKILL.md) | [`swebok-architecture.toml`](../../../agents/swebok-architecture.toml) | [checklist](../../../skills/swebok-architecture/references/checklist.md) |
| 詳細設計 | `03_詳細設計` | 97 | [`swebok-design`](../../../skills/swebok-design/SKILL.md) | [`swebok-design.toml`](../../../agents/swebok-design.toml) | [checklist](../../../skills/swebok-design/references/checklist.md) |
| 実装 | `04_実装` | 85 | [`swebok-construction`](../../../skills/swebok-construction/SKILL.md) | [`swebok-construction.toml`](../../../agents/swebok-construction.toml) | [checklist](../../../skills/swebok-construction/references/checklist.md) |
| テスト | `05_テスト` | 90 | [`swebok-testing`](../../../skills/swebok-testing/SKILL.md) | [`swebok-testing.toml`](../../../agents/swebok-testing.toml) | [checklist](../../../skills/swebok-testing/references/checklist.md) |
| 運用 | `06_運用` | 105 | [`swebok-operations`](../../../skills/swebok-operations/SKILL.md) | [`swebok-operations.toml`](../../../agents/swebok-operations.toml) | [checklist](../../../skills/swebok-operations/references/checklist.md) |
| 保守 | `07_保守` | 86 | [`swebok-maintenance`](../../../skills/swebok-maintenance/SKILL.md) | [`swebok-maintenance.toml`](../../../agents/swebok-maintenance.toml) | [checklist](../../../skills/swebok-maintenance/references/checklist.md) |
| 構成管理 | `08_構成管理` | 96 | [`swebok-configuration-management`](../../../skills/swebok-configuration-management/SKILL.md) | [`swebok-configuration-management.toml`](../../../agents/swebok-configuration-management.toml) | [checklist](../../../skills/swebok-configuration-management/references/checklist.md) |
| マネジメント | `09_マネジメント` | 93 | [`swebok-engineering-management`](../../../skills/swebok-engineering-management/SKILL.md) | [`swebok-engineering-management.toml`](../../../agents/swebok-engineering-management.toml) | [checklist](../../../skills/swebok-engineering-management/references/checklist.md) |
| プロセス | `10_プロセス` | 95 | [`swebok-engineering-process`](../../../skills/swebok-engineering-process/SKILL.md) | [`swebok-engineering-process.toml`](../../../agents/swebok-engineering-process.toml) | [checklist](../../../skills/swebok-engineering-process/references/checklist.md) |
| 品質保証 | `12_品質保証` | 91 | [`swebok-quality`](../../../skills/swebok-quality/SKILL.md) | [`swebok-quality.toml`](../../../agents/swebok-quality.toml) | [checklist](../../../skills/swebok-quality/references/checklist.md) |
| セキュリティ | `13_セキュリティ` | 104 | [`swebok-security`](../../../skills/swebok-security/SKILL.md) | [`swebok-security.toml`](../../../agents/swebok-security.toml) | [checklist](../../../skills/swebok-security/references/checklist.md) |
| クラウド | `14_クラウド` | 64 | [`swebok-cloud`](../../../skills/swebok-cloud/SKILL.md) | [`swebok-cloud.toml`](../../../agents/swebok-cloud.toml) | [checklist](../../../skills/swebok-cloud/references/checklist.md) |
| AWS | `15_AWS` | 129 | [`swebok-aws`](../../../skills/swebok-aws/SKILL.md) | [`swebok-aws.toml`](../../../agents/swebok-aws.toml) | [checklist](../../../skills/swebok-aws/references/checklist.md) |
| Google Cloud | `16_GoogleCloud` | 122 | [`swebok-google-cloud`](../../../skills/swebok-google-cloud/SKILL.md) | [`swebok-google-cloud.toml`](../../../agents/swebok-google-cloud.toml) | [checklist](../../../skills/swebok-google-cloud/references/checklist.md) |
| Azure | `17_Azure` | 115 | [`swebok-azure`](../../../skills/swebok-azure/SKILL.md) | [`swebok-azure.toml`](../../../agents/swebok-azure.toml) | [checklist](../../../skills/swebok-azure/references/checklist.md) |
| OCI | `18_OCI` | 80 | [`swebok-oci`](../../../skills/swebok-oci/SKILL.md) | [`swebok-oci.toml`](../../../agents/swebok-oci.toml) | [checklist](../../../skills/swebok-oci/references/checklist.md) |
| AI | `19_AI` | 51 | [`swebok-ai`](../../../skills/swebok-ai/SKILL.md) | [`swebok-ai.toml`](../../../agents/swebok-ai.toml) | [checklist](../../../skills/swebok-ai/references/checklist.md) |

## 同期と検証

```bash
python3 tools/sync_swebok_ka.py --write
python3 tools/sync_swebok_ka.py --check
task swebok:check
```

`--check`は元シート、ID、件数、生成済みskill/agent/checklistの完全一致を検証する。
