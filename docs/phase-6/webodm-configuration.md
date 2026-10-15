# AgriDrone AutoMap — WebODM Configuration Specification
## Document Reference: `docs/phase-6/webodm-configuration.md`
**Phase**: Phase 6 — WebODM / OpenDroneMap Integration & Drone Photogrammetry Processing  
**Status**: APPROVED CONFIGURATION SPECIFICATION  
**Version**: 1.0.0  

---

## 1. Server-Side Configuration Parameters

All WebODM integration parameters are defined in `backend/app/core/config.py` and read from the environment or `.env` file:

| Variable Name | Default Value | Description |
| :--- | :--- | :--- |
| `WEBODM_API_URL` | `http://localhost:3001` | Base URL of the WebODM or NodeODM instance. In Docker Compose internal networks, this can be set to `http://nodeodm:3000`. |
| `WEBODM_USERNAME` | `admin` | WebODM administration account username for JWT token authentication. |
| `WEBODM_PASSWORD` | `admin` | WebODM administration account password. |
| `WEBODM_PROJECT_ID` | `None` (auto-detected) | Optional target project ID. When empty, AgriDrone automatically finds or provisions a project named `"AgriDrone AutoMap"`. |
| `WEBODM_TOKEN` | `None` | Pre-shared static JWT authentication token (bypasses username/password auth when provided). |
| `WEBODM_TIMEOUT_SECONDS` | `30` | Maximum timeout in seconds for standard WebODM REST HTTP queries. |
| `WEBODM_POLL_INTERVAL_SECONDS` | `10` | Worker status polling interval in seconds during active photogrammetric reconstruction. |
| `WEBODM_MAX_RETRIES` | `3` | Maximum retry attempts for failed HTTP dispatches. |

---

## 2. Processing Presets & Options Mapping

AgriDrone AutoMap translates user selections into validated, injection-safe WebODM options:

```json
[
  {"name": "auto-boundary", "value": true},
  {"name": "dsm", "value": true},
  {"name": "dtm", "value": true},
  {"name": "orthophoto-resolution", "value": 2.5},
  {"name": "feature-quality", "value": "high"},
  {"name": "pc-quality", "value": "medium"},
  {"name": "radiometric-calibration", "value": "camera+sun"}
]
```

### Parameter Whitelist:

1. **`resolution_preset`**:
   - `FAST`: Maps to `orthophoto-resolution: 5.0` cm/px, `fast-orthophoto: true`, `dtm: false`, `feature-quality: low`, `pc-quality: low`. Intended for rapid turnaround (~15-30 mins).
   - `HIGH_RES` (Default): Maps to `orthophoto-resolution: 2.5` cm/px, `dsm: true`, `dtm: true`, `feature-quality: high`, `pc-quality: medium`. Generates dense point cloud and precision elevation rasters.
   - `CUSTOM`: Allows user-defined GSD (0.5 to 50.0 cm/px) and custom feature extraction / point cloud densification quality settings.
2. **`feature_quality`**: Whitelisted to `ultra`, `high`, `medium`, `low`, or `lowest`. Prevents arbitrary string injection.
3. **`pc_quality`**: Whitelisted to `ultra`, `high`, `medium`, `low`, or `lowest`.
4. **`radiometric_calibration`**: When enabled, applies sun sensor and reflectance panel irradiance normalization (`camera+sun`).

---

## 3. Resource & Memory Requirements

Photogrammetry resource consumption scales with image count, sensor megapixel resolution, and quality preset:

| Preset | Image Count | Recommended RAM | CPU Cores | Est. Runtime |
| :--- | :--- | :--- | :--- | :--- |
| **Agricultural Fast** | 100 – 300 | 8 GB | 4 cores | 15 – 25 mins |
| **High Precision** | 100 – 300 | 16 – 32 GB | 8 cores | 45 – 90 mins |
| **High Precision** | 300 – 800 | 32 – 64 GB | 16 cores | 2 – 4 hours |

> [!WARNING]
> If a worker machine lacks sufficient RAM during dense point cloud generation, the OpenMVS process may be terminated by the OS Out-Of-Memory (OOM) killer. For datasets over 400 photos on development machines with under 16 GB RAM, the `Agricultural Fast` preset is recommended.
