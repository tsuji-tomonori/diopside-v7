# getReleaseTagsContract test factors (generated)

| ID | Type | Input/condition | Expected |
| --- | --- | --- | --- |
| TF-001 | normal | Existing canonical artifact | 200 and response schema match |
| TF-002 | missing-data | Artifact path does not exist | 404 without fallback data |
| TF-003 | invalid-data | Stored JSON is malformed or violates its canonical model | 500 without private content exposure |
| TF-004 | compatibility | Stable method/path/operationId are compared with manual contract | Generation fails on drift |
| TF-005 | security | Public read without credentials | No authentication requirement or provider credential exposure |
| TF-006 | boundary/validation | Invalid release_id path value | Declared 422 when framework validation applies; otherwise 404; traversal cannot escape contract root |

## Required assertions

- Declared error statuses: 404, 422, 500.
- Missing optional values remain missing; no fabricated zero, date, count, or metadata.
- Repeated reads are byte/semantic stable for the same release artifact.
- Generated interface and runtime OpenAPI have the same method, path, operation ID, and errors.
