# getLatestContract interface (generated)

- Method: `GET`
- Path: `/api/contracts/latest`
- Summary: Read the active canonical release pointer.
- Authentication: public
- Permissions: none
- Security requirement: none (public read)

## Parameters

| Name | In | Required | Schema |
| --- | --- | --- | --- |
| — | — | — | — |

## Responses

| Status | Description | Schema |
| ---: | --- | --- |
| 200 | Successful Response | `#/components/schemas/LatestContractResponse` |
| 404 | The requested canonical contract artifact was not found. | `none` |
| 500 | The stored canonical contract is invalid or inconsistent. | `none` |

## Traceability

- Requirements: CON-003, FR-EXP-001, FR-EXP-005
- Specifications: SPEC-DATA-PUB-001, SPEC-OPS-PUBLISH-001
- Acceptance: AC-DATA-01, AC-EXP-01
