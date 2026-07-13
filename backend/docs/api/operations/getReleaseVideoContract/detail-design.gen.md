# getReleaseVideoContract detail design (generated)

- Stable contract slug: `public/get-release-video-contract`
- Business function: `read_video_contract`
- Authentication: public
- Permissions: none
- Idempotency: safe read
- Transaction boundary: none
- External effects: reads the configured public contract directory

## Source ownership

| Concern | Source |
| --- | --- |
| contract | `src/app/apis/public/get_video/contract.py` |
| router | `src/app/apis/public/get_video/router.py` |
| functions | `src/app/apis/public/get_video/functions.py` |
| schemas | `src/app/apis/public/get_video/schemas.py` |
| samples | `src/app/apis/public/get_video/samples.py` |

## Resource boundaries

- Contract-loader calls: `contract_loader.read_video`
- Database/SQL: not applicable; this operation reads versioned filesystem artifacts.
- Provider SDK: not applicable; the operation layer imports no provider adapter.
- Mutation/rollback: not applicable; this is a safe read with no transaction.

## Compatibility

- Operation identity `getReleaseVideoContract` and path `/api/contracts/releases/{release_id}/videos/{video_id}` are stable.
- Response payload validation remains owned by canonical public contract models.
- Non-backward-compatible public schema changes require a major schema/path migration.
