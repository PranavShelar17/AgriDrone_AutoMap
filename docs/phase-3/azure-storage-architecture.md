# AgriDrone AutoMap — Azure Blob Storage Architecture
## Document Reference: `docs/phase-3/azure-storage-architecture.md`
**Phase**: Phase 3 — System Architecture, Technical Validation & Implementation Blueprint  
**Status**: APPROVED ARCHITECTURE BLUEPRINT  
**Version**: 1.0.0  

---

## 1. Storage Philosophy & Platform Selection

**Microsoft Azure Blob Storage** is the sole approved primary object store for AgriDrone AutoMap. In strict adherence to project constraints:
- Amazon S3, Google Cloud Storage, and self-hosted MinIO are **excluded**.
- Neither PostgreSQL nor container local disks are used as durable binary stores.
- Storage account credentials, master keys, and connection strings are **strictly server-side** and never exposed to the client browser.
- All client uploads and downloads are mediated through **ephemeral, narrowly scoped Shared Access Signature (SAS) tokens** with a 15-minute expiration.

---

## 2. Logical Container Architecture

Storage is partitioned into five dedicated containers based on data lifecycle, access patterns, and security classification:

| Container Name | Content Category | Typical File Types | Default Access Tier | Public Access |
| :--- | :--- | :--- | :--- | :--- |
| **`raw-surveys`** | Uploaded raw aerial photos, ZIP/TAR survey bundles, EXIF JPEGs | `.zip`, `.tar.gz`, `.jpg`, `.tif` | Hot | Disabled |
| **`orthomosaics`** | Full-resolution stitched true-color orthomosaics, DSM, DTM | `.tif` (GeoTIFF / COG) | Hot | Disabled |
| **`vegetation-indices`** | Derived index rasters (NDVI, VARI, etc.) and colormap preview tiles | `.tif` (COG), `.png` | Hot | Disabled |
| **`reports`** | Compiled agronomic audit PDF reports | `.pdf` | Hot / Cool | Disabled |
| **`temp-scratch`** | Intermediate WebODM tiles, temporary download caches | `.tmp`, `.part` | Hot (7-day lifecycle purge) | Disabled |

---

## 3. Blob Naming Conventions & Hierarchy

To prevent namespace collisions, ensure auditable provenance, and facilitate bucket prefix partitioning, all blob paths follow a predictable hierarchical scheme:

```
raw-surveys/
└── {survey_id}/
    └── raw_upload_{upload_id}_{sanitized_filename}

orthomosaics/
└── {survey_id}/
    ├── orthophoto_full_{task_id}.tif          # Original WebODM export
    ├── orthophoto_cog_{task_id}.tif           # Cloud-Optimized GeoTIFF with internal overviews
    ├── dsm_surface_cog_{task_id}.tif          # Digital Surface Model (Elevation)
    └── dtm_terrain_cog_{task_id}.tif          # Digital Terrain Model (Ground)

vegetation-indices/
└── {survey_id}/
    ├── index_vari_{job_id}_cog.tif            # Floating-point VARI index COG
    ├── index_ndvi_{job_id}_cog.tif            # Floating-point NDVI index COG (multispectral)
    └── previews/
        └── {job_id}_thumb_rdylgn.png          # Quick-look colorized overview thumbnail

reports/
└── {survey_id}/
    └── agronomic_report_{report_number}_{timestamp}.pdf
```

### Database Reference Integrity
- The database **never stores transient SAS URLs** (which expire after 15 minutes).
- The database stores **only the relative blob path** (e.g., `vegetation-indices/srv-001/index_vari_job901_cog.tif`).
- The backend FastAPI `StorageService` dynamically resolves relative paths to signed 15-minute SAS URLs upon authorized client request.

---

## 4. Upload & Download Data Flow

### 4.1. Direct Chunked Upload Flow (Page 1)
To allow multi-gigabyte drone survey uploads (up to 5GB) without exhausting FastAPI server memory or blocking worker processes:
1. **Initiation**: The Next.js frontend calls `POST /api/v1/surveys/{survey_id}/uploads/initiate`.
2. **Authorization & SAS Minting**: FastAPI validates user permissions on the survey, calculates the target blob path, and uses the Azure SDK (`azure.storage.blob`) to generate a temporary `PutBlob` / `PutBlock` SAS token valid for 15 minutes.
3. **Direct Browser Upload**: The browser uses the Azure Storage Blob client library (`@azure/storage-blob`) to upload the file directly to Azure via parallel chunked blocks (e.g. 8 MB blocks).
4. **Commit & Finalize**: Once all blocks are committed (`PutBlockList`), the browser notifies FastAPI via `POST /api/v1/surveys/.../finalize`.
5. **Backend Verification**: FastAPI calls `get_blob_properties()` to confirm file existence, verifies the reported file size matches the uploaded byte count, updates the database status to `UPLOADED`, and dispatches the background validation task.

### 4.2. Secure Download Flow (Pages 4 & 5)
1. The farmer or agronomist clicks "Download Orthophoto (GeoTIFF)" or "Download Diagnostic Report (PDF)".
2. The frontend calls `GET /api/v1/portal/products/{product_id}/sas-url`.
3. FastAPI verifies that the requesting user's tenant owns the parent farm.
4. If authorized, FastAPI mints a temporary `Read` SAS token scoped exclusively to that single blob with a 15-minute lifetime (`BlobSasPermissions(read=True)`).
5. The browser initiates a direct HTTPS download from Azure Blob Storage.

---

## 5. Security & Access Control

1. **Service Identity**:
   - In production (Azure App Service / AKS / Container Apps), backend services authenticate using **Managed Identity (Microsoft Entra ID)** with the `Storage Blob Data Contributor` RBAC role. No shared access keys exist in application configuration files.
   - In local development, an Azure Storage connection string or Azurite local emulator is injected via `.env`.
2. **Network Isolation**:
   - Public anonymous read access is explicitly disabled (`AllowBlobPublicAccess = false`) across all storage containers.
   - Cross-Origin Resource Sharing (CORS) rules strictly whitelist the approved application domains (`http://localhost:3000`, `http://localhost:3005`, and production domains) for `GET`, `PUT`, `HEAD`, and `OPTIONS` operations.

---

## 6. Lifecycle Management, Retention & Cost Optimization

1. **Automated Scratch Pruning**:
   - Azure Lifecycle Management rules automatically delete any blob in `temp-scratch/` older than 7 days.
2. **Tier Transitioning (Cold Storage)**:
   - Raw drone survey archives (`raw-surveys/`) are transitioned from **Hot** to **Cool** tier after 30 days of inactivity, reducing storage expenses by up to 50% while preserving raw flight provenance for reprocessing.
   - Orthomosaic and index COGs remain on the **Hot** tier to ensure fast tile read latencies for interactive map exploration.
3. **Soft Delete & Disaster Recovery**:
   - Container-level soft delete is enabled with a 14-day retention window to safeguard against accidental operator or administrative deletion.
   - Point-in-time restore is enabled for production storage accounts.
