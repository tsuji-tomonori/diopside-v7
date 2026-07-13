# getLatestContract detail design (generated)

- Stable contract slug: `public/get-latest-contract`
- Business function: `read_latest_contract`
- Authentication: public
- Permissions: none
- Idempotency: safe read
- Transaction boundary: none
- External effects: reads the configured public contract directory

## Source ownership

| Concern | Source |
| --- | --- |
| contract | `src/app/apis/public/get_latest/contract.py` |
| router | `src/app/apis/public/get_latest/router.py` |
| functions | `src/app/apis/public/get_latest/functions.py` |
| schemas | `src/app/apis/public/get_latest/schemas.py` |
| samples | `src/app/apis/public/get_latest/samples.py` |

## Resource boundaries

- Contract-loader calls: `contract_loader.read_latest`
- Database/SQL: not applicable; this operation reads versioned filesystem artifacts.
- Provider SDK: not applicable; the operation layer imports no provider adapter.
- Mutation/rollback: not applicable; this is a safe read with no transaction.

## Compatibility

- Operation identity `getLatestContract` and path `/api/contracts/latest` are stable.
- Response payload validation remains owned by canonical public contract models.
- Non-backward-compatible public schema changes require a major schema/path migration.
