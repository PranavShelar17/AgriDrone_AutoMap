# AgriDrone AutoMap — Non-Functional Requirements Specification

## 1. Overview & Evaluation Methodology

This document specifies the non-functional requirements (NFRs) for the AgriDrone AutoMap platform. Because this platform handles computationally intensive raster operations, multi-gigabyte aerial datasets, and multi-tenant agricultural records, requirements are categorized across security, performance, reliability, resource management, and maintainability.

> [!NOTE]
> Numerical performance benchmarks, throughput rates, and SLAs are designated as **[PROPOSED — Requires Benchmarking & Approval]** to reflect real-world hardware, network bandwidth, and cloud resource sizing decisions.

---

## 2. Security Requirements (`NFR-SEC`)

- **NFR-SEC-01: Principle of Least Privilege (Azure Storage)**
  - All application access to Microsoft Azure Blob Storage must use the principle of least privilege.
  - Production deployments must leverage Azure Managed Identities or Microsoft Entra ID service principals. If connection strings or SAS tokens are utilized in development, they must reside strictly in server-side environment variables and never be exposed to client-side bundles.
- **NFR-SEC-02: Ephemeral Client Access Tokens**
  - Direct downloads of raster GeoTIFF files or PDF reports must be mediated via short-lived Azure Shared Access Signatures (SAS) with read-only permissions and an expiration lifespan not exceeding 15 minutes **[PROPOSED]**.
- **NFR-SEC-03: Multi-Tenant Data Isolation**
  - Database queries at the API layer must enforce tenant isolation by strictly validating user ownership against the target Farm/Survey UUIDs. No API route may accept a bare resource ID without performing ownership verification.
- **NFR-SEC-04: Secure Transport & Headers**
  - All external communication must occur over TLS 1.3 (with TLS 1.2 fallback). Standard security headers (HSTS, Content-Security-Policy, X-Content-Type-Options, X-Frame-Options) must be enforced across all FastAPI and Next.js responses.
- **NFR-SEC-05: Input Hardening & Path Traversal Prevention**
  - File upload endpoints must sanitize filenames, disallow directory traversal tokens (`../`, `~`), and validate file headers using magic number inspection rather than trusting MIME types or extensions.

---

## 3. Performance & Responsiveness (`NFR-PERF`)

- **NFR-PERF-01: Asynchronous Non-Blocking Backend**
  - Heavy computational tasks (WebODM photogrammetry, Rasterio/NumPy index calculations, ReportLab PDF assembly) must run inside decoupled Celery worker processes.
  - The FastAPI HTTP server must never perform synchronous raster crunching or block the event loop, maintaining an API latency target of $< 200\text{ ms}$ for standard CRUD operations **[PROPOSED]**.
- **NFR-PERF-02: Map Tile Streaming & Latency**
  - High-resolution raster overlays rendered in MapLibre GL JS must be tiled or served via HTTP range requests against Cloud Optimized GeoTIFFs (COGs).
  - Tiled map responses must achieve an initial viewport render target of $< 1.5\text{ seconds}$ on standard broadband connections **[PROPOSED — Requires Testing]**.
- **NFR-PERF-03: Resumable Upload Throughput**
  - The chunked upload pipeline must support chunk sizes between 5MB and 25MB, allowing network interruptions during multi-gigabyte uploads to resume from the last successful chunk without re-uploading the entire dataset.

---

## 4. Resource-Intensive Processing Considerations (`NFR-COMP`)

Photogrammetric reconstruction and geospatial raster operations have unique, high-demand hardware requirements:

- **NFR-COMP-01: WebODM Resource Allocation**
  - WebODM nodes require dedicated compute nodes. Recommended minimum baseline: 8 vCPUs, 32GB RAM, and high-speed NVMe scratch storage **[PROPOSED — Subject to deployment sizing]**.
  - Worker configurations must prevent concurrent job oversubscription on a single WebODM node to avoid out-of-memory (OOM) kernel terminations.
- **NFR-COMP-02: Memory-Efficient Raster Chunking**
  - All Rasterio and NumPy mathematical operations on multi-gigabyte orthomosaics must process rasters in windowed blocks (e.g., $1024 \times 1024$ or $2048 \times 2048$ pixel tiles) rather than loading entire multi-band rasters into system RAM at once.
- **NFR-COMP-03: Task Queue Isolation**
  - Celery must maintain separate queues for photogrammetry (`photogrammetry_queue`, long-running, hours) and raster algorithm calculations (`gis_queue`, short-running, seconds to minutes) to prevent fast GIS jobs from being blocked behind long photogrammetry runs.

---

## 5. Reliability & Availability (`NFR-REL`)

- **NFR-REL-01: Graceful Service Degradation**
  - In the event of WebODM node unavailability, all other platform functions (viewing existing surveys, running direct GIS operations on pre-stitched GeoTIFFs, downloading reports) must remain fully operational.
- **NFR-REL-02: Job State Persistence**
  - Task progress and state transitions must be persisted in PostgreSQL and synchronized via Redis pub/sub. If a Celery worker restarts unexpectedly, orphaned tasks must be detected, marked `FAILED` with diagnostic logs, and surfaced for operator retry.
- **NFR-REL-03: Mathematical Edge Case Resilience**
  - Division by zero in vegetation index equations (e.g., $\text{NIR} + \text{Red} == 0$), negative radiometric values, and floating-point overflow must be handled safely via NumPy masking without throwing unhandled runtime exceptions.

---

## 6. Maintainability & Code Quality (`NFR-MAINT`)

- **NFR-MAINT-01: Modular Architecture & Typing**
  - Frontend must be written in TypeScript with strict type checking enabled (`strict: true` in `tsconfig.json`).
  - Backend must be written in Python 3.11+ utilizing Pydantic v2 schemas for all request/response models and strict type annotations.
- **NFR-MAINT-02: Geospatial Abstraction Layer**
  - GIS raster computation functions must be encapsulated within a standalone Python service module (`services/gis/`), decoupled from FastAPI HTTP route controllers.
- **NFR-MAINT-03: Database Migrations**
  - All schema evolution in PostgreSQL/PostGIS must be managed via version-controlled Alembic migration scripts. Manual schema alterations are strictly prohibited.

---

## 7. Accessibility & Responsive Design (`NFR-A11Y`)

- **NFR-A11Y-01: Responsive Layout Standards**
  - The Five-Page application must support desktop ($1920 \times 1080$, $1440 \times 900$) and tablet ($1024 \times 768$) viewports using Tailwind CSS responsive breakpoints.
- **NFR-A11Y-02: Contrast & Color-Blindness in GIS Visualizations**
  - While agricultural false-color maps use conventional agronomic scales (Red-Yellow-Green), UI text, badges, and controls must satisfy WCAG 2.1 Level AA contrast ratios ($\ge 4.5:1$ for normal text).
  - Legends must pair color swatches with numerical intervals and descriptive text labels (e.g., "Dense Canopy", "Moderate Vigor") so color-blind users can interpret data.

---

## 8. Logging, Observability & Auditing (`NFR-LOG`)

- **NFR-LOG-01: Structured JSON Logging**
  - Backend logs must be emitted in structured JSON format, capturing `timestamp`, `log_level`, `correlation_id`, `tenant_id`, `service_name`, and `message`.
- **NFR-LOG-02: Credential & PII Redaction**
  - Logging interceptors must strictly scrub and redact sensitive fields (passwords, tokens, Azure connection strings, SAS tokens) from all stdout and error traces.
- **NFR-LOG-03: Processing Audit Trail**
  - Every calculation, photogrammetry run, and report download must generate an audit log entry in PostgreSQL capturing user ID, timestamp, parameters used, and input/output checksums.

---

## 9. Backup, Disaster Recovery & Retention (`NFR-DR`)

- **NFR-DR-01: Database Backup Policy [PROPOSED]**
  - PostgreSQL automated daily backups with Point-in-Time Recovery (PITR) enabled for a minimum 7-day retention period.
- **NFR-DR-02: Azure Storage Tiering & Lifecycle [PROPOSED]**
  - Raw drone photo batches can be moved to Azure Cool or Cold storage tiers 30 days after successful orthomosaic generation to optimize cloud storage expenditures.
  - Generated orthomosaics, index COGs, and PDF reports remain in Azure Hot storage for active portal querying.
