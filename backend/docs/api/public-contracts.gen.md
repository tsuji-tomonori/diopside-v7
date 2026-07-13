# Public API inventory (generated)

> Generated from `public-contracts.manual.json`; do not edit manually.

| Operation ID | Method | Path | Auth | Success | Errors | Summary |
| --- | --- | --- | --- | ---: | --- | --- |
| `getLatestContract` | GET | `/api/contracts/latest` | public | 200 | 404, 500 | Read the active canonical release pointer. |
| `getReleaseContract` | GET | `/api/contracts/release/{release_id}` | public | 200 | 404, 422, 500 | Read one canonical release index. |
| `getReleaseSearchContract` | GET | `/api/contracts/releases/{release_id}/search` | public | 200 | 404, 422, 500 | Read one release search index. |
| `getReleaseTagsContract` | GET | `/api/contracts/releases/{release_id}/tags` | public | 200 | 404, 422, 500 | Read taxonomy, tag index, and alias projections. |
| `getReleaseVideoContract` | GET | `/api/contracts/releases/{release_id}/videos/{video_id}` | public | 200 | 404, 422, 500 | Read one public video detail. |

## Operation boundaries

### `getLatestContract`

- Contract: `public/get-latest-contract`
- Permissions: none
- Idempotency: safe read
- Transaction: none
- External effects: reads the configured public contract directory

### `getReleaseContract`

- Contract: `public/get-release-contract`
- Permissions: none
- Idempotency: safe read
- Transaction: none
- External effects: reads the configured public contract directory

### `getReleaseSearchContract`

- Contract: `public/get-release-search-contract`
- Permissions: none
- Idempotency: safe read
- Transaction: none
- External effects: reads the configured public contract directory

### `getReleaseTagsContract`

- Contract: `public/get-release-tags-contract`
- Permissions: none
- Idempotency: safe read
- Transaction: none
- External effects: reads the configured public contract directory

### `getReleaseVideoContract`

- Contract: `public/get-release-video-contract`
- Permissions: none
- Idempotency: safe read
- Transaction: none
- External effects: reads the configured public contract directory
