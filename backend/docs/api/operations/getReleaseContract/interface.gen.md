# getReleaseContract interface (generated)

- Method: `GET`
- Path: `/api/contracts/release/{release_id}`
- Summary: Read one canonical release index.
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
| 200 | Successful Response | `#/components/schemas/ReleaseContractResponse` |
| 404 | The requested canonical contract artifact was not found. | `none` |
| 422 | A path parameter failed validation. | `none` |
| 500 | The stored canonical contract is invalid or inconsistent. | `none` |

## Traceability

- Requirements: CON-003, FR-EXP-001, FR-EXP-002
- Specifications: SPEC-DATA-PUB-001
- Acceptance: AC-DATA-01, AC-FE-05
