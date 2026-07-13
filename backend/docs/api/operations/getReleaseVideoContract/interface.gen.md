# getReleaseVideoContract interface (generated)

- Method: `GET`
- Path: `/api/contracts/releases/{release_id}/videos/{video_id}`
- Summary: Read one public video detail.
- Authentication: public
- Permissions: none
- Security requirement: none (public read)

## Parameters

| Name | In | Required | Schema |
| --- | --- | --- | --- |
| `release_id` | path | true | `string` |
| `video_id` | path | true | `string` |

## Responses

| Status | Description | Schema |
| ---: | --- | --- |
| 200 | Successful Response | `#/components/schemas/VideoContractResponse` |
| 404 | The requested canonical contract artifact was not found. | `none` |
| 422 | A path parameter failed validation. | `none` |
| 500 | The stored canonical contract is invalid or inconsistent. | `none` |

## Traceability

- Requirements: FR-EXP-001, FR-FE-004, FR-FE-010
- Specifications: SPEC-DATA-PUB-001, SPEC-UI-DETAIL-001
- Acceptance: AC-DATA-01, AC-FE-03, AC-FE-05
