# Roles and Permissions Specification

**Document:** Security Model — Phase 9  
**Status:** Implemented & Verified  
**Date:** October 2026  

---

## 1. Role Taxonomy

AgriDrone AutoMap defines three explicit user roles in `backend/app/models/user.py`:

```python
class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    AGRONOMIST = "AGRONOMIST"
    FARMER = "FARMER"
```

1. **ADMIN (System Administrator / Operator)**
   - Responsible for drone fleet operations, platform configuration, farm creation, raw image ingestion, WebODM photogrammetry pipeline triggers, and user onboarding.
   - Has global read and write privileges across all farms, fields, and jobs.
2. **AGRONOMIST (Agronomic Specialist)**
   - Responsible for analyzing spectral indices, validating vegetation health, setting colormaps, and writing agronomic field recommendations.
   - Has access to processing workflows and diagnostic tools across assigned regions.
3. **FARMER (Tenant / Landowner)**
   - Landowner or farm manager who accesses actionable intelligence for their specific agricultural property.
   - **Strictly constrained by resource-level ownership:** Can only see, probe, and download maps, surveys, and reports for farms where `farm.owner_id == user.id`.

---

## 2. Permission Matrix by Functional Area

| Operation / Endpoint | ADMIN | AGRONOMIST | FARMER | Authorization Guard |
| :--- | :---: | :---: | :---: | :--- |
| **User & Account Management** | | | | |
| Register new farmer account | Yes | No | No | `get_current_active_admin` |
| Assign farm to farmer | Yes | No | No | `get_current_active_admin` |
| Update account status (disable/enable)| Yes | No | No | `get_current_active_admin` |
| View own user profile (`/auth/me`)| Yes | Yes | Yes | `get_current_user` |
| **Farm & Field Management** | | | | |
| Create new farm or field | Yes | Yes | No | `get_current_active_admin` |
| List farms (`GET /farms`) | All | All | Owned Only | `farms.py` ownership filter |
| View farm details (`GET /farms/{id}`)| Yes | Yes | Owned Only | `verify_farm_access` |
| View field boundary (`GET /fields/{id}/boundary`)| Yes | Yes | Owned Only | `verify_field_access` |
| **Drone Image Ingestion** | | | | |
| Upload raw drone files (`POST /ingestion/surveys/{id}/files`)| Yes | Yes | **No (403)**| `get_current_active_admin` |
| Delete survey file | Yes | Yes | **No (403)**| `get_current_active_admin` |
| View survey files list | Yes | Yes | Owned Only | `verify_survey_access` |
| Download raw drone file | Yes | Yes | Owned Only | `verify_survey_access` |
| **Photogrammetry & Reconstruction** | | | | |
| Trigger WebODM task (`POST /photogrammetry/tasks`)| Yes | Yes | **No (403)**| `get_current_active_admin` |
| List photogrammetry tasks | All | All | Owned Only | `photogrammetry.py` ownership filter |
| View task status & outputs | Yes | Yes | Owned Only | `verify_task_access` |
| **Algorithms & Raster Generation** | | | | |
| Submit algorithm batch (`POST /algorithms/batch`)| Yes | Yes | **No (403)**| `get_current_active_admin` |
| List algorithm jobs | All | All | Owned Only | `algorithms.py` ownership filter |
| View algorithm job status | Yes | Yes | Owned Only | `verify_algorithm_job_access` |
| View map product details | Yes | Yes | Owned Only | `verify_map_product_access` |
| **Interactive Maps & Diagnostics** | | | | |
| Render XYZ map tiles (`GET /maps/tiles/...`)| Yes | Yes | Owned Only | Dual Header/Query Token Guard |
| Probe point spectral value (`GET /maps/products/{id}/probe`)| Yes | Yes | Owned Only | `verify_map_product_access` |
| View scientific diagnostics (`GET /maps/products/{id}/diagnostics`)| Yes | Yes | Owned Only | `verify_map_product_access` |
| **Deliverables & Reports** | | | | |
| List reports (`GET /reports`)| All | All | Owned Only | `reports.py` ownership filter |
| View report details (`GET /reports/{id}`)| Yes | Yes | Owned Only | `verify_report_access` |
| Download PDF report (`GET /reports/{id}/download`)| Yes | Yes | Owned Only | `verify_report_access` |

---

## 3. Resource Ownership Guard Implementation

Role checks alone are insufficient for tenant security because multiple users share the `FARMER` role. Every resource access function in `backend/app/api/deps.py` navigates the relational database hierarchy to verify tenant ownership:

```python
def verify_farm_access(
    farm_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Farm:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found or does not exist.")

    # Admins and Agronomists have system-wide access
    if current_user.role in [UserRole.ADMIN, UserRole.AGRONOMIST]:
        return farm

    # Farmers may only access farms they own
    if farm.owner_id != current_user.id:
        # Privacy-preserving 404 to prevent resource enumeration
        raise HTTPException(status_code=404, detail="Farm not found or does not exist.")

    return farm
```

When an unauthorized farmer attempts to access another farmer's farm, field, survey, job, or map layer by changing the ID in the URL, the system responds with an identical **HTTP 404 Not Found**, ensuring zero data leakage regarding the existence of competitor assets.
