# Database Safety, Backup & Disaster Recovery Plan

**Document:** PostgreSQL/PostGIS Backup & Disaster Recovery Standard  
**Phase:** Phase 10  
**Status:** Documented  
**Date:** October 2026  

---

## 1. Overview & Objectives

The AgriDrone AutoMap platform relies on a dual-tier persistence model:
1. **Relational & Spatial Database (PostgreSQL 16 + PostGIS 3.4):** Stores user accounts, farm boundaries, field geometries, survey flight metadata, photogrammetry task states, zonal statistics, and audit logs.
2. **Object Storage (Azure Blob Storage):** Stores heavy binary assets, including raw drone photos, orthomosaics, vegetation index GeoTIFFs, and PDF reports.

This plan outlines procedures to guarantee continuous data safety, zero-data-loss migrations, automated backups, and verifiable restoration procedures.

---

## 2. Proposed Recovery Objectives (Requires Operational Approval)

- **Recovery Point Objective (RPO):** Maximum 1 hour of potential transactional data loss.
- **Recovery Time Objective (RTO):** Maximum 2 hours to fully restore services from backup archives.

*Note: These targets represent proposed operational standards and depend on final infrastructure provisioning in Phase 10.*

---

## 3. Recommended Backup Schedule & Retention Policy

| Backup Type | Frequency | Tool / Mechanism | Retention Period | Storage Target |
| :--- | :--- | :--- | :--- | :--- |
| **Full Logical Backup** | Daily (02:00 UTC) | `pg_dump -Fc` (Compressed custom format) | 30 days | Encrypted Azure Blob / GCS Archive |
| **Transaction Logs (WAL)**| Continuous / Hourly | WAL-G / Cloud Provider Automated Archiving | 7 days | Private Blob Container |
| **Monthly Snapshot** | 1st of each month | Full schema + spatial vector archive | 365 days | Cold / Archive Tier Storage |

---

## 4. Logical Backup Procedure (`pg_dump`)

To execute a secure, non-destructive logical backup preserving all PostGIS geometry types and spatial indexes:

### Manual Backup Command
```bash
# Set credentials securely in environment
export PGPASSWORD="your_secure_db_password"

# Execute pg_dump with custom compressed format
pg_dump -h localhost -p 5434 -U agridrone_user -d agridrone_db -Fc -b -v -f "agridrone_backup_$(date +%Y%m%d_%H%M%S).dump"

unset PGPASSWORD
```

### Key Flags Explained:
- `-Fc`: Custom binary format (supports parallel restoration via `pg_restore`).
- `-b`: Includes large objects.
- `-v`: Verbose mode for verifiable logging.

---

## 5. Safe Restoration Procedure

Restorations must **never** be performed directly over an active production database without prior validation.

### Step 1: Create an Isolated Temporary Database
```bash
createdb -h localhost -p 5434 -U agridrone_user agridrone_restore_test
psql -h localhost -p 5434 -U agridrone_user -d agridrone_restore_test -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### Step 2: Restore from Dump Archive
```bash
pg_restore -h localhost -p 5434 -U agridrone_user -d agridrone_restore_test -v "agridrone_backup_20261015.dump"
```

### Step 3: Run Spatial & Relational Sanity Checks
```sql
-- 1. Verify PostGIS Extension
SELECT PostGIS_Full_Version();

-- 2. Verify Table Row Counts
SELECT 'users' as tbl, count(*) FROM users
UNION ALL SELECT 'farms', count(*) FROM farms
UNION ALL SELECT 'fields', count(*) FROM fields
UNION ALL SELECT 'surveys', count(*) FROM surveys
UNION ALL SELECT 'map_products', count(*) FROM map_products;

-- 3. Verify Geometry Validity
SELECT count(*) FROM fields WHERE ST_IsValid(boundary) = false;
-- Expected output: 0 invalid geometries
```

### Step 4: Promote Verified Database
Once validation passes, swap connections during an approved maintenance window.

---

## 6. Database and Cloud Storage Synchronization

Because database records reference blob paths in Azure Blob Storage (`blob_uri`), restoring an older database backup could create broken links if corresponding blobs were deleted in the interim.

### Recommended Safeguards:
1. **Azure Blob Soft Delete:** Enable 30-day soft delete on all Azure containers (`raw-surveys`, `orthomosaics`, `vegetation-indices`, `reports`) to prevent irreversible data loss.
2. **Immutable Retention / Versioning:** Enable blob versioning so that past raster artifacts referenced by historical database snapshots remain accessible.
3. **Coordinated Backups:** Schedule database dumps and storage synchronization snapshots at identical maintenance intervals.
