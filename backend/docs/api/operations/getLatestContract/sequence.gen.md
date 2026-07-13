# getLatestContract sequence (generated)

```mermaid
sequenceDiagram
    actor Client
    participant Router
    participant Functions
    participant Loader as Contract loader
    participant Storage as Public contract directory
    Client->>Router: GET /api/contracts/latest
    Router->>Router: Resolve typed contract directory dependency
    Router->>Functions: read_latest_contract(...) 
    Functions->>Loader: contract_loader.read_latest(...) 
    Loader->>Storage: Read and parse canonical JSON
    Storage-->>Loader: JSON bytes or missing file
    Loader-->>Functions: Validated payload or classified HTTP error
    Functions-->>Router: typed LatestContractResponse response
    Router-->>Client: 200 JSON
```

## Error sequence

- Missing artifact is classified as 404 by the contract loader.
- Invalid stored JSON or a path/payload invariant failure is classified as 500.
- Framework path validation is classified as 422 where applicable.
- The router catches no broad exception; classified errors propagate through FastAPI.
