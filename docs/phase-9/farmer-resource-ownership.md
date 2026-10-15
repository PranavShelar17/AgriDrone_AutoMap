# Farmer Resource Ownership & Anti-IDOR Architecture

**Document:** Security Specification — Phase 9  
**Status:** Implemented & Verified  
**Date:** October 2026  

---

## 1. The IDOR Vulnerability in Geospatial Multi-Tenancy

In multi-tenant agricultural mapping systems, Insecure Direct Object Reference (IDOR) represents a critical security risk. If a system relies solely on UUID parameters (e.g. `GET /api/v1/maps/products/e4a132e6-768f-4318-ba20-2f98150ea2fe/probe`) without verifying that the requesting user owns the underlying agricultural land, a competitor farmer or unauthorized party could enumerate or guess IDs to inspect:
- Confidential crop vigor diagnostics (NDVI/NDRE distributions).
- High-resolution drone orthomosaics revealing private land structures.
- Historical flight dates, yield estimates, and agronomic reports.

Phase 9 completely eliminates IDOR vulnerabilities by enforcing strict, server-side relational hierarchy validation on every protected route.

---

## 2. Relational Hierarchy Traversal

All agricultural resources derive their tenant ownership from `Farm.owner_id`. When a request arrives from a user with `role == FARMER`, the backend navigates the relational graph backwards to verify ownership:

```
MapProduct (id)
   │
   ▼
Survey (survey_id)
   │
   ▼
Field (field_id)
   │
   ▼
Farm (farm_id) ────► Farm.owner_id == current_user.id ?
                         │
                         ├── YES ──► Grant Access (HTTP 200)
                         └── NO  ──► Privacy-Preserving Rejection (HTTP 404)
```

### Hierarchy Traversal Reference

| Resource | Primary Key | Foreign Key Path to Farm Owner | Dependency Guard in `deps.py` |
| :--- | :--- | :--- | :--- |
| **Farm** | `farm.id` | `farm.owner_id` | `verify_farm_access` |
| **Field** | `field.id` | `field.farm.owner_id` | `verify_field_access` |
| **Survey** | `survey.id` | `survey.field.farm.owner_id` | `verify_survey_access` |
| **SurveyFile** | `file.id` | `file.survey.field.farm.owner_id` | `verify_survey_access` |
| **PhotogrammetryTask** | `task.id` | `task.survey.field.farm.owner_id` | `verify_task_access` |
| **AlgorithmJob** | `job.id` | `job.survey.field.farm.owner_id` | `verify_algorithm_job_access` |
| **MapProduct** | `product.id` | `product.survey.field.farm.owner_id` | `verify_map_product_access` |
| **Report** | `report.id` | `report.survey.field.farm.owner_id` | `verify_report_access` |

---

## 3. Privacy-Preserving HTTP 404 Policy

When an unauthorized farmer requests a resource owned by another tenant, returning an `HTTP 403 Forbidden` response confirms to an attacker that the resource exists and belongs to someone else.

To prevent resource enumeration and reconnaissance, AgriDrone AutoMap adopts a strict **privacy-preserving HTTP 404 policy**:
- **Non-existent ID:** Returns `HTTP 404 Not Found` (`"Resource not found or does not exist."`).
- **Existent ID owned by Another Farmer:** Returns **identical `HTTP 404 Not Found`** (`"Resource not found or does not exist."`).

An attacker cannot differentiate between an invalid UUID and a competitor's private asset.

---

## 4. Multi-Farm Support

A farmer may own or lease multiple distinct parcels of agricultural land. The AgriDrone AutoMap schema natively supports 1-to-Many farm ownership:

- In `backend/app/models/farm.py`, `Farm.owner_id` is a foreign key to `users.id`.
- Multiple `Farm` records can point to the same `owner_id`.
- When `GET /api/v1/farms` is called by a farmer, the endpoint queries:
  ```python
  farms = db.query(Farm).filter(Farm.owner_id == current_user.id).all()
  ```
- The frontend `UserProfileResponse` includes `assigned_farm_ids: List[str]`, allowing the farmer portal selector to switch seamlessly between multiple assigned farms.

---

## 5. Handling Unassigned Farmer Accounts

When a new farmer account is provisioned before physical drone flights or boundary surveying occur, the farmer has zero assigned farms (`assigned_farm_ids == []`):
- `GET /api/v1/farms` returns `{ items: [], total: 0 }`.
- `GET /api/v1/surveys` returns `{ items: [], total: 0 }`.
- The Farmer Portal (`/portal/surveys`) displays a dedicated empty state:
  > *"No Maps or Fields Available Yet — No farms or fields are currently assigned to your account. When your agricultural administrator registers and maps your fields, your survey rasters and diagnostics will appear here automatically."*
- No unhandled exceptions or blank screens occur.
