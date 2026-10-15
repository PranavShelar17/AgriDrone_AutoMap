# AgriDrone AutoMap — Security & Access Boundaries (Phase 5)
## Document Reference: `docs/phase-5/security-and-access-boundaries.md`
**Phase**: Phase 5 — Admin Dashboard, Farm/Survey Management & Drone Image Ingestion  
**Status**: APPROVED SECURITY SPECIFICATION  
**Version**: 1.0.0  

---

## 1. Security Architecture Principles

Full production authentication and role-based access control (RBAC) across the multi-tenant Farmer Portal are scheduled for **Phase 9**. However, Phase 5 establishes strict architectural security boundaries to ensure no insecure practices or secret leakages are introduced.

### Core Security Rules:
1. **No Client-Supplied Authorization**: The backend never accepts client-provided user IDs, role strings, or ownership assertions as proof of access.
2. **Environment-Enforced Authorization Boundary**:
   - In `ENVIRONMENT=development`, the system automatically resolves or provisions a scoped local administrator account (`admin@agridrone.local`).
   - In non-development environments (`staging`, `production`), unauthenticated requests are strictly rejected with HTTP 401 Unauthorized, failing closed.
3. **Storage Credential Isolation**:
   - Azure Storage connection strings and account keys never touch the browser, source control, client-side configuration, or application logs.
   - All object storage operations are routed through the backend storage abstraction.
4. **Path Traversal & Safe Object Naming**:
   - Filenames are sanitized via regex (`sanitize_filename()`), stripping directory markers (`/`, `\`, `..`).
   - Local development storage paths are strictly verified using `os.path.abspath` boundary checks against the storage root directory.
5. **No Anonymous Public Storage**:
   - Containers are strictly private. Public URL generation is disallowed.
   - When Azure is active, time-limited SAS tokens (60-minute duration) are issued only to authenticated backend requests.

---

## 2. Protected Operations in Phase 5

| Operation | Method & Route | Protection Mechanism |
| :--- | :--- | :--- |
| **Register Farm / Field** | `POST /farms`, `POST /farms/{id}/fields` | Scoped to authenticated administrator; PostGIS polygon topology checks |
| **Delete Farm / Field** | `DELETE /farms/{id}`, `DELETE /fields/{id}`| Destructive operation; requires admin privilege and confirms relational cascade |
| **Create Survey Flight** | `POST /surveys` | Requires valid `field_id`; unique survey code validation |
| **Ingest File** | `POST /ingestion/upload/{id}` | Enforces size limits, magic byte check, and virus/malware path isolation |
| **Delete File** | `DELETE /ingestion/files/{id}` | Deletes both database record and underlying object in Azure/local storage |
