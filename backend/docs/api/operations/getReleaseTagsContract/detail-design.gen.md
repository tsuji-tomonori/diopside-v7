# getReleaseTagsContract detail design (generated)

- Stable contract slug: `public/get-release-tags-contract`
- Business function: `read_tags_contract`
- Authentication: public
- Permissions: none
- Idempotency: safe read
- Transaction boundary: none
- External effects: reads the configured public contract directory

## Source ownership

| Concern | Source |
| --- | --- |
| contract | `src/app/apis/public/get_tags/contract.py` |
| router | `src/app/apis/public/get_tags/router.py` |
| functions | `src/app/apis/public/get_tags/functions.py` |
| schemas | `src/app/apis/public/get_tags/schemas.py` |
| samples | `src/app/apis/public/get_tags/samples.py` |

## Resource boundaries

- Contract-loader calls: `contract_loader.read_taxonomy`, `contract_loader.read_tag_index`, `contract_loader.read_alias_index`
- Database/SQL: not applicable; this operation reads versioned filesystem artifacts.
- Provider SDK: not applicable; the operation layer imports no provider adapter.
- Mutation/rollback: not applicable; this is a safe read with no transaction.

## Compatibility

- Operation identity `getReleaseTagsContract` and path `/api/contracts/releases/{release_id}/tags` are stable.
- Response payload validation remains owned by canonical public contract models.
- Non-backward-compatible public schema changes require a major schema/path migration.
