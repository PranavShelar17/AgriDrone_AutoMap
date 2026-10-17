# Processing Node Management & Cluster Telemetry

This document details the monitoring, telemetry, options discovery, and security controls for photogrammetry processing nodes (NodeODM and ClusterODM) in AgriDrone AutoMap.

---

## 1. NodeODM Architecture & WebODM Cluster Models

WebODM delegates heavy Structure-from-Motion (SfM) computation to processing nodes:
1. **NodeODM**: A lightweight, standalone REST microservice wrapping OpenDroneMap. Exposes `/info`, `/task/new`, `/task/{uuid}/info`, and `/task/{uuid}/output`.
2. **ClusterODM**: An intelligent load-balancer and reverse proxy that distributes tasks across multiple NodeODM worker nodes based on RAM capacity and queue depth.
3. **WebODM ProcessingNode Entity** (`app/models/processingnode.py`):
   - Stores node connection configuration (`hostname`, `port`, `token`, `queue_count`, `available_memory`).

---

## 2. Cluster Telemetry & Capacity Monitoring

AgriDrone AutoMap provides real-time cluster telemetry via `GET /api/v1/photogrammetry/nodes`:

### 2.1 Monitored Metrics
- **Node Identifier & Label**: Friendly node name and cluster ID.
- **Online Status**: Boolean flag indicating successful socket ping and HTTP probe.
- **Queue Depth (`task_queue_count`)**: Number of tasks currently waiting or executing on the node.
- **Available RAM (`available_memory_gb`)**: Free memory reported by NodeODM. Used to prevent OOM errors on high-resolution surveys (> 500 photos).
- **Engine Version**: Upstream ODM and NodeODM release tag.
- **Last Checked Timestamp**: Time of the most recent diagnostic probe.

### 2.2 Dynamic NodeODM Options Schema
Every NodeODM engine exposes its complete CLI parameter schema via `GET /api/processingnodes/{id}/options/`. AgriDrone AutoMap queries this schema dynamically to:
- Discover supported flags (e.g. `feature-quality`, `pc-quality`, `radiometric-calibration`, `auto-boundary`).
- Populate dropdowns and validation ranges in the Custom Preset configuration drawer.
- Avoid hardcoding CLI arguments that may vary across ODM versions.

---

## 3. Security & Administrative Access Restrictions

Processing node management is strictly restricted to **Platform Administrators**:
1. **Role-Based Access Control (RBAC)**:
   - `GET /api/v1/photogrammetry/nodes` requires `get_current_active_admin`.
   - Ordinary farmers attempting to access node endpoints receive `HTTP 403 Forbidden`.
2. **Redaction of Infrastructure Details**:
   - Internal cluster IP addresses, private hostnames, and WebODM administrative tokens are **redacted** from client payloads.
   - Farmers only see high-level service status (`ONLINE` or `OFFLINE`) on the general health indicator.
3. **Audit Logging**:
   - Any administrative modifications to processing nodes are recorded in PostgreSQL `audit_logs` with the administrator's ID and IP address.
