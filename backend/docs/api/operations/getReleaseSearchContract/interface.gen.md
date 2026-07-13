# getReleaseSearchContract interface (generated)

- Method: `GET`
- Path: `/api/contracts/releases/{release_id}/search`
- Summary: Read one release search index.
- Authentication: public
- Permissions: none
- Security requirement: none (public read)

## Parameters

| Name | In | Required | Schema |
| --- | --- | --- | --- |
| `release_id` | path | true | `string` |

## Responses

| Status | Description | Schema |
| ---: | --- | --- |
| 200 | Successful Response | `#/components/schemas/SearchContractResponse` |
| 404 | The requested canonical contract artifact was not found. | `none` |
| 422 | A path parameter failed validation. | `none` |
| 500 | The stored canonical contract is invalid or inconsistent. | `none` |

## Traceability

- Requirements: FR-EXP-001, FR-FE-002, FR-FE-010
- Specifications: SPEC-DATA-PUB-001, SPEC-UI-SEARCH-001
- Acceptance: AC-DATA-01, AC-FE-02, AC-FE-05
