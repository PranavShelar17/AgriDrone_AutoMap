# AgriDrone AutoMap — Security & Error Handling Architecture
## Document Reference: `docs/phase-6/security-and-error-handling.md`
**Phase**: Phase 6 — WebODM / OpenDroneMap Integration & Drone Photogrammetry Processing  
**Status**: APPROVED SECURITY ARCHITECTURE  
**Version**: 1.0.0  

---

## 1. Security Architecture & Threat Mitigations

The photogrammetry processing tier implements multi-layer defense against injection, privilege escalation, and resource exhaustion:

### 1.1. Parameter Whitelisting & Command Injection Prevention
- Client inputs for photogrammetry configuration are strictly validated via Pydantic validators (`validate_preset`, `validate_fq`, `validate_pq`).
- User inputs **never become CLI shell arguments**. All options are structured as JSON arrays passed through WebODM's REST API.
- Custom target GSD is bounded between `0.5` and `100.0` cm/pixel to prevent negative numbers or excessive memory allocation.

### 1.2. Secret Isolation
- WebODM administrative credentials and storage connection strings remain server-side.
- The Next.js frontend has zero access to WebODM API tokens or private container endpoints.
- Task options and logs are scrubbed to ensure no credentials, tokens, or SAS signatures are persisted in `task_logs` or `photogrammetry_tasks.options`.

### 1.3. Concurrency Protection & Resource Throttling
- A database check constraint and API concurrency query ensure that no two photogrammetry tasks can execute simultaneously for the same survey.
- Conflicting requests return HTTP `409 Conflict` with clear instructions to wait for completion or cancel the running task.
- Celery worker prefetch multiplier is set to `1` with soft time limits (3h 50m) and hard time limits (4h) to avoid worker lockup.

### 1.4. Multi-Tenant Authorization Boundary
- In Phase 6 development mode, administrative actions are transparently attributed to `admin@agridrone.local`.
- In production environments, strict Bearer token authentication is enforced via `app.api.deps.get_current_user`.
- Foreign-key path checks guarantee that datasets must belong to the specified survey and field before processing can begin.

---

## 2. Standardized Error Handling

All Phase 6 endpoints utilize standard HTTP error codes:

| Scenario | HTTP Code | Error Response Message |
| :--- | :--- | :--- |
| **Non-existent survey** | `404 Not Found` | `"Survey with ID '...' not found."` |
| **Ineligible dataset (Rejected)** | `400 Bad Request` | `"Dataset cannot be processed because ingestion status is REJECTED."` |
| **Ineligible dataset (GeoTIFF)** | `400 Bad Request` | `"Pre-stitched GeoTIFF rasters cannot be submitted for WebODM photogrammetry. Use Phase 7 Direct GIS processing."` |
| **Active processing conflict** | `409 Conflict` | `"A photogrammetry task is already active for survey '...'. Wait for completion or cancel it before starting another run."` |
| **Invalid task cancellation** | `400 Bad Request` | `"Cannot cancel task in terminal state 'COMPLETED'."` |
| **Invalid task retry** | `400 Bad Request` | `"Cannot retry task in state 'RUNNING'. Only FAILED or CANCELLED tasks can be retried."` |
| **Pydantic schema validation error** | `422 Unprocessable Entity` | Field-level validation error details. |
