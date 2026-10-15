# Known Limitations & Operational Considerations

## 1. WebODM / NodeODM Local Availability in Development

1. **Local NodeODM Container Requirement**:
   - In development environments where the Docker container for NodeODM is not actively running on `http://localhost:3001`, the cluster health check reports `cluster_status: "OFFLINE"`.
   - The AgriDrone AutoMap platform handles this gracefully:
     - The UI displays an amber/red status badge indicating the node is offline.
     - The Diagnostics tab lists the exact command required to start the local container:
       ```bash
       docker run -p 3001:3000 opendronemap/nodeodm:latest
       ```
     - Mocked testing and worker safety guards prevent unexpected crashes when the container is stopped.

---

## 2. WebODM Lightning Commercial Cloud Service

1. **External Paid Dependency**:
   - WebODM Lightning is an external, commercial cloud GPU processing network hosted by OpenDroneMap (`cloud.webodm.net`).
   - It requires paid subscription credits or API token authorization.
   - **AgriDrone AutoMap does not fake or simulate WebODM Lightning**.
   - The platform documents this transparently in the Administration tab, providing an informational runbook for agricultural cooperatives that wish to configure cloud bursting during peak harvest periods.

---

## 3. High-Resolution Photogrammetry Compute & Storage Demands

1. **RAM and CPU Requirements**:
   - Reconstructing raw surveys with over 300 high-resolution aerial photographs at full resolution requires at least **16 GB of system RAM** and multi-core CPU/GPU acceleration.
   - For low-resource development laptops, users should select the **Fast Orthophoto Preset** (`5.0 cm/px GSD`, dense point cloud disabled) to ensure rapid completion without hitting host Out-of-Memory (OOM) limits.
2. **Azure Storage Transfer**:
   - When configured with Azure Blob Storage, raw image uploads and resulting COG GeoTIFFs are streamed using block-blob chunks. In offline/local environments without Azure credentials, the system automatically falls back to `LocalStorageService` in `backend/storage/`.
