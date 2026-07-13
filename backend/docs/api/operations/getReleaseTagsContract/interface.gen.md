# getReleaseTagsContract interface (generated)

- Method: `GET`
- Path: `/api/contracts/releases/{release_id}/tags`
- Summary: Read taxonomy, tag index, and alias projections.
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
| 200 | Successful Response | `#/components/schemas/TagsContractResponse` |
| 404 | The requested canonical contract artifact was not found. | `none` |
| 422 | A path parameter failed validation. | `none` |
| 500 | The stored canonical contract is invalid or inconsistent. | `none` |

## Traceability

- Requirements: FR-EXP-001, FR-TAG-012, FR-TAG-022
- Specifications: SPEC-DATA-PUB-001, SPEC-DATA-TAG-001
- Acceptance: AC-DATA-01, AC-TAG-03, AC-TAG-09
