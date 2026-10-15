# AgriDrone AutoMap — Security Architecture & Threat Mitigation
## Document Reference: `docs/phase-3/security-architecture.md`
**Phase**: Phase 3 — System Architecture, Technical Validation & Implementation Blueprint  
**Status**: APPROVED ARCHITECTURE BLUEPRINT  
**Version**: 1.0.0  

---

## 1. Security Philosophy & Trust Boundaries

AgriDrone AutoMap handles proprietary agricultural cadastral boundaries, commercial aerial drone imagery, and sensitive diagnostic yield data across multiple farm enterprises.

### Core Security Mandates:
1. **Never Trust Client-Side Parameters**: A farmer client providing a `farm_id`, `survey_id`, or `report_id` in a URL or payload is never trusted. The backend FastAPI service independently validates tenant ownership before executing any query or action.
2. **Zero Storage Secrets in Browser**: Azure Storage account names, master keys, and connection strings are strictly kept server-side. Clients interact with Azure Blob Storage exclusively through short-lived (15-minute) SAS tokens minted after server-side authorization.
3. **No Direct Container Blob Public Access**: Anonymous public read access is permanently disabled across all storage containers.
4. **Isolated Processing Boundaries**: Asynchronous workers and WebODM cluster nodes execute in isolated subnets with no public inbound ports.

---

## 2. Authentication & Authorization Architecture

### 2.1. Authentication Architecture (Decoupled Design)
As established in Phase 1 and preserved through Phase 2, the final production authentication provider (e.g. self-hosted JWT Bearer, Azure AD B2C, or OAuth2/OIDC) remains an open decision.

The architecture implements a decoupled **`AuthManager`** interface in `backend/app/core/security.py`:
- In local development and prototyping, standard Bearer JWT tokens (`HS256` / `RS256`) validate the `sub` (User UUID) and `role` claims.
- The interface easily plugs into enterprise OIDC / OAuth2 providers in production without requiring changes to business logic or database models.

### 2.2. Role-Based Access Control (RBAC) & Multi-Tenancy Matrix

| System Action | Admin | Agronomist | Farmer |
| :--- | :---: | :---: | :---: |
| **Manage Farms & Field Boundaries** | Global | Assigned Farms | Own Farm Only |
| **Page 1: Upload Raw Imagery & Pre-Stitched GeoTIFFs** | Yes | Assigned Surveys | No |
| **Page 2: Configure & Dispatch WebODM Reconstruction** | Yes | No | No |
| **Page 3: Select Algorithms & Compute Vegetation Indices** | Yes | Assigned Surveys | No |
| **Page 3: Publish Map Layers to Farmer Portal** | Yes | Assigned Surveys | No |
| **Page 4: View Interactive Map & Inspect Vegetation Layers** | Yes | Assigned Farms | Own Farm Only |
| **Page 4: Download Published GeoTIFF Assets (SAS Link)** | Yes | Assigned Farms | Own Farm Only |
| **Page 5: Generate & Download PDF Diagnostic Reports** | Yes | Assigned Farms | Own Farm Only |

### 2.3. Multi-Tenant Query Scoping Pattern
FastAPI endpoints inject a scoped database dependency that automatically appends ownership filters:
```python
# Conceptual FastAPI dependency
def get_authorized_survey(survey_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Survey).join(Field).join(Farm)
    if current_user.role == UserRole.FARMER:
        query = query.filter(Farm.owner_id == current_user.id)
    elif current_user.role == UserRole.AGRONOMIST:
        query = query.filter(Farm.assigned_agronomist_id == current_user.id)
    
    survey = query.filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=403, detail="Access denied to requested survey.")
    return survey
```

---

## 3. Threat Model & OWASP Mitigation Matrix

| Threat Category | Potential Attack Vector | Platform Mitigation Architecture |
| :--- | :--- | :--- |
| **Malicious File Upload / Zip Bomb** | Attacker uploads a 42KB ZIP that expands into a 500GB disk-filling payload, or contains `../` path traversal (Zip Slip). | 1. Direct upload to Azure Blob Storage bypasses application web server memory.<br/>2. Celery unzipping worker checks uncompressed size ratio (max 10x) and forbids archive extraction exceeding 10GB.<br/>3. File path sanitization strictly strips `..` and leading `/`. |
| **Insecure Direct Object Reference (IDOR)** | Farmer changes `survey_id` in the URL to view a competing farm's drone survey and diagnostic data. | Server-side ownership verification is enforced on every single `/api/v1` route. SAS tokens are generated only after verified database query match. |
| **Server-Side Request Forgery (SSRF)** | Attacker exploits WebODM node communication or tile proxy to probe internal cloud metadata (`169.254.169.254`). | 1. FastAPI communicates only with hardcoded, container-network WebODM endpoints.<br/>2. Dynamic tile endpoints strictly validate that target URLs match approved Azure Blob storage hostnames. |
| **Denial of Service via Heavy Computation** | Attacker floods WebODM or GDAL raster math queues with dozens of concurrent 4K drone reconstructions. | 1. Role-gated dispatch (only Admins can trigger WebODM).<br/>2. Redis task rate-limiting (max 2 concurrent photogrammetry jobs per tenant).<br/>3. Celery task timeouts automatically kill tasks exceeding 4 hours. |
| **Credential & Secret Exposure** | Azure storage account keys or database passwords committed to Git or leaked via client bundle. | 1. Zero storage keys in frontend code.<br/>2. Environment variable separation with Pydantic BaseSettings.<br/>3. Git pre-commit hooks scan for credential patterns. |

---

## 4. Audit Logging & Compliance

All security-sensitive operations are logged to the immutable `audit_logs` table in PostgreSQL:
```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    ip_address INET NOT NULL,
    user_agent TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Operations tracked:
- User authentication events (Login, Token Refresh, Password Change)
- Raw survey upload finalization
- WebODM task dispatch and cancellation
- Vegetation index computation
- Layer publication status changes
- Farmer report and GeoTIFF download SAS token generations
