# getReleaseTagsContract sequence (generated)

```mermaid
sequenceDiagram
    actor Client
    participant Router
    participant Functions
    participant Loader as Contract loader
    participant Storage as Public contract directory
    Client->>Router: GET /api/contracts/releases/{release_id}/tags
    Router->>Router: Resolve typed contract directory dependency
    Router->>Functions: read_tags_contract(...) 
    Functions->>Loader: contract_loader.read_taxonomy(...) 
    Loader->>Storage: Read and parse canonical JSON
    Storage-->>Loader: JSON bytes or missing file
    Loader-->>Functions: Validated payload or classified HTTP error
    Functions->>Loader: contract_loader.read_tag_index(...) 
    Loader->>Storage: Read and parse canonical JSON
    Storage-->>Loader: JSON bytes or missing file
    Loader-->>Functions: Validated payload or classified HTTP error
    Functions->>Loader: contract_loader.read_alias_index(...) 
    Loader->>Storage: Read and parse canonical JSON
    Storage-->>Loader: JSON bytes or missing file
    Loader-->>Functions: Validated payload or classified HTTP error
    Functions-->>Router: typed TagsContractResponse response
    Router-->>Client: 200 JSON
```

## Error sequence

- Missing artifact is classified as 404 by the contract loader.
- Invalid stored JSON or a path/payload invariant failure is classified as 500.
- Framework path validation is classified as 422 where applicable.
- The router catches no broad exception; classified errors propagate through FastAPI.
