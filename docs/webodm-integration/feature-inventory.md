# WebODM Feature Inventory & Integration Matrix

This document provides a comprehensive inventory of all capabilities audited in **WebODM 3.3.1**, mapped across Feature Groups A through O, specifying their upstream source location, API dependency, permission requirements, implementation status in AgriDrone AutoMap, and architectural integration method.

---

## 1. Feature Groups Inventory Table

| Feature ID | Capability Name | Upstream WebODM Source Location | API / Service Dependency | AgriDrone Permission Level | AgriDrone AutoMap Status | Proposed Integration Method |
|:---|:---|:---|:---|:---|:---:|:---|
| **A.1** | List Projects | `app/api/projects.py:ProjectViewSet.list` | `GET /api/projects/` | Farmer (Scoped) / Admin | **IMPLEMENTED** | Synced via DB entity `photogrammetry_projects` & WebODM REST API |
| **A.2** | Create Project | `app/api/projects.py:ProjectViewSet.create` | `POST /api/projects/` | Farmer / Admin | **IMPLEMENTED** | Local PostgreSQL container with upstream WebODM project linkage |
| **A.3** | Update / Rename Project | `app/api/projects.py:ProjectViewSet.partial_update` | `PATCH /api/projects/{id}/` | Owner / Admin | **IMPLEMENTED** | Local metadata update with upstream WebODM API sync |
| **A.4** | Delete Project | `app/api/projects.py:ProjectViewSet.destroy` | `DELETE /api/projects/{id}/` | Owner / Admin | **IMPLEMENTED** | Cascade delete with explicit confirmation and upstream purge |
| **B.1** | Multi-Image Selection & Ingestion | `app/api/tasks.py:TaskViewSet.create` | `POST /api/projects/{p}/tasks/` | Farmer / Admin | **IMPLEMENTED** | Azure Blob Storage buffer dispatched via multipart streaming |
| **B.2** | Dataset Validation & Rejection | `app/classes/options.py` | FastAPI Validation Layer | Farmer / Admin | **IMPLEMENTED** | Strict rejection of GeoTIFFs, corrupted files, and non-aerial photos |
| **B.3** | Chunked Large Dataset Upload | `app/api/tasks.py:TaskViewSet.upload` | `POST /api/projects/{p}/tasks/{t}/upload/` | Admin Only | **SUPPORTED** | Available for >500 photo surveys using partial task workflow |
| **C.1** | GCP File Upload & Parsing | `app/classes/gcp.py:GCP` | `POST /api/v1/photogrammetry/gcp/validate` | Farmer / Admin | **IMPLEMENTED** | Regex parsing of CRS line, minimum 3 points check, pixel mapping |
| **C.2** | GCP Task Attachment | `app/api/tasks.py` | Multipart `gcp` file part | Farmer / Admin | **IMPLEMENTED** | Transmitted as `gcp_list.txt` in task creation multipart payload |
| **D.1** | Task Creation & Dispatch | `app/api/tasks.py:TaskViewSet.create` | `POST /api/projects/{p}/tasks/` | Farmer / Admin | **IMPLEMENTED** | Celery background task (`trigger_photogrammetry_task`) |
| **D.2** | Task Status & Progress Sync | `app/api/tasks.py:TaskViewSet.retrieve` | `GET /api/projects/{p}/tasks/{t}/` | Farmer (Scoped) / Admin | **IMPLEMENTED** | Polling engine synchronizing integer status codes (10–50) |
| **D.3** | Live Console Logs Tail | `app/api/tasks.py:TaskViewSet.output` | `GET /api/projects/{p}/tasks/{t}/output/` | Farmer (Scoped) / Admin | **IMPLEMENTED** | Terminal viewer with auto-scroll and log level formatting |
| **D.4** | Task Cancellation | `app/api/tasks.py:TaskViewSet.cancel` | `POST /api/projects/{p}/tasks/{t}/cancel/` | Owner / Admin | **IMPLEMENTED** | Forwards cancellation to WebODM, transitions task to `CANCELLED` |
| **D.5** | Task Retry / Re-run | `app/api/tasks.py:TaskViewSet.restart` | `POST /api/projects/{p}/tasks/{t}/restart/` | Owner / Admin | **IMPLEMENTED** | Resets status, increments retry counter, dispatches worker |
| **E.1** | Presets (Fast, High-Res, Multi) | `app/api/presets.py` | `GET /api/presets/` | Farmer / Admin | **IMPLEMENTED** | Curated agricultural presets: Fast, Field Precision, Multispectral |
| **E.2** | Dynamic NodeODM Options Schema | `app/api/processingnodes.py:options` | `GET /api/processingnodes/{id}/options/` | Admin Only | **INTEGRATING** | Proxied dynamic options schema for custom tuning |
| **F.1** | Orthophoto Tile Delivery | `app/api/tiler.py:TilerViewSet.tiles` | `GET /api/.../orthophoto/tiles/{z}/{x}/{y}.png` | Farmer (Scoped) / Admin | **INTEGRATING** | MapLibre GL JS raster tile proxy with bounds and TileJSON |
| **F.2** | DSM / DTM Elevation Viewing | `app/api/tiler.py:TilerViewSet.tiles` | `GET /api/.../dsm/tiles/{z}/{x}/{y}.png` | Farmer (Scoped) / Admin | **INTEGRATING** | Dynamic elevation color mapping (Viridis/Terrain) & Hillshading |
| **F.3** | Raster Bounds & Metadata | `app/api/tiler.py:TilerViewSet.bounds` | `GET /api/.../{type}/bounds/` | Farmer (Scoped) / Admin | **INTEGRATING** | Automatic map viewport fitting to photogrammetry deliverables |
| **G.1** | Asset Binary Downloads | `app/api/tasks.py:TaskViewSet.download` | `GET /api/projects/{p}/tasks/{t}/download/{asset}` | Farmer (Scoped) / Admin | **INTEGRATING** | Authorized downloads for `all.zip`, `orthophoto.tif`, `dsm.tif`, `report.pdf` |
| **G.2** | Azure Blob Deliverable Sync | N/A (AgriDrone Custom) | Azure Blob Storage SDK | Internal Worker | **IMPLEMENTED** | Automatic conversion of orthophoto to Cloud-Optimized GeoTIFF (COG) |
| **H.1** | Field Boundary GeoJSON Overlay | N/A (AgriDrone PostGIS) | PostGIS GeoJSON API | Farmer (Scoped) / Admin | **IMPLEMENTED** | Vector polygon overlays rendered atop WebODM orthophotos |
| **H.2** | WebODM GeoJSON Overlays | `app/api/overlays.py` | `GET /api/projects/{p}/tasks/{t}/overlays/` | Admin Only | **OPTIONAL** | Supported if task contains vector annotations |
| **I.1** | 3D Textured Mesh (.glb) | `app/templates/app/3d/` | `GET /api/.../download/textured_model.glb` | Farmer / Admin | **INTEGRATING** | Interactive Three.js / WebGL 3D model viewer |
| **I.2** | Point Cloud Metadata & LAZ | `app/models/task.py` | `GET /api/.../download/georeferenced_model.laz` | Farmer / Admin | **INTEGRATING** | Point count display, density stats, and direct LAZ export |
| **I.3** | 3D Gaussian Splats | `app/api/urls.py` (`/splats/`) | `GET /api/.../splats/` | Admin Only | **EXPERIMENTAL** | Optional WebODM 3.3 feature; requires GPU WebGL engine |
| **J.1** | Task Media & Panoramas | `app/api/media.py` | `GET /api/projects/{p}/tasks/{t}/media/` | Farmer / Admin | **SUPPORTED** | Available when 360 camera inputs or flight videos are ingested |
| **K.1** | Colormaps & Dynamic Hillshade | `app/classes/tiler.py` | Query params: `?colormap=viridis&hillshade=1` | Farmer / Admin | **INTEGRATING** | Frontend controls for live raster visualization adjustments |
| **L.1** | Processing Nodes Telemetry | `app/api/processingnodes.py` | `GET /api/processingnodes/` | Admin Only | **IMPLEMENTED** | Memory, queue count, version, online status monitoring |
| **M.1** | Cluster Health & Diagnostics | Multiple probe endpoints | `/api/cluster/nodes/` & `/info` | Admin Only | **IMPLEMENTED** | End-to-end diagnostics across WebODM, DB, Redis, and Storage |
| **N.1** | Tenant Isolation & RBAC | N/A (AgriDrone Architecture) | FastAPI Dependency Injection | All Users | **IMPLEMENTED** | Strict farmer data isolation; WebODM credentials hidden from clients |
| **O.1** | External Plugins & CloudODM | `plugins/` | Plugin manager | Admin Only | **EVALUATED** | Third-party plugins disabled by default to prevent vendor lock-in |

---

## 2. Capability Status Summary

- **Total Audited Capabilities**: 28
- **Fully Implemented & Active**: 18
- **Currently Being Extended / Enhanced in this Sprint**: 7 (Raster Tile Proxy, DSM Hillshade, Asset Downloads, 3D Mesh Viewer, Dynamic Options Schema)
- **Optional / Conditional**: 2 (Chunked Large Uploads, Task Media/Panoramas)
- **Experimental / Pending GPU Node**: 1 (3D Gaussian Splatting)
