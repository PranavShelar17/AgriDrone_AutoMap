# Advanced Visualization — 3D Models, Point Clouds, Media & Colormaps

This document details the architecture and implementation of WebODM 3.3.1's advanced visualization capabilities integrated into AgriDrone AutoMap: 3D textured meshes, dense point clouds, 3D Gaussian splatting, panoramas, and dynamic raster colormaps.

---

## 1. 3D Textured Models & Meshes

WebODM executes multi-view stereo reconstruction and texturing using OpenMVS, generating:
- **`textured_model.glb`**: Binary glTF format containing geometry, UV coordinates, and embedded textures. glTF is the industry-standard 3D web transmission format.
- **`textured_model.obj`** and material library (`.mtl`).

### 1.1 WebGL 3D Viewer Integration
AgriDrone AutoMap integrates interactive 3D model visualization directly within the Photogrammetry Workspace:
- **Technology**: Three.js / `@google/model-viewer` WebGL canvas embedded in the workspace.
- **Controls**: Orbit, pan, zoom, wireframe toggle, ambient lighting, and auto-rotation.
- **Lazy Loading**: 3D assets are **never loaded automatically** upon page render. The user must explicitly click "Load 3D Model" to fetch the asset, saving bandwidth and client GPU memory.
- **Verification Rule**: The 3D viewer is rendered **only** when `textured_model.glb` is listed in the task's `available_assets`. No fabricated or mock 3D geometry is ever displayed.

---

## 2. Dense Point Clouds & Potree Integration

WebODM generates dense point clouds in LAS/LAZ format (`georeferenced_model.laz`):
- **Point Attributes**: X, Y, Z, RGB color, classification (ground vs vegetation), return number, and intensity.
- **Potree Octree**: WebODM builds a hierarchical LOD Octree for point cloud streaming.
- **AgriDrone Point Cloud Interface**:
  - Displays point cloud metadata: Total point count, point density (pts/m²), bounding box, and CRS.
  - Direct download endpoint: `GET /api/v1/photogrammetry/tasks/{task_id}/download/georeferenced_model.laz`.
  - For advanced inspection, authorized users can launch WebODM's embedded Potree point cloud viewer in a dedicated secure modal.

---

## 3. 3D Gaussian Splatting (WebODM 3.3 Experimental)

WebODM 3.3 introduces experimental support for 3D Gaussian Splatting (`/api/projects/{p}/tasks/{t}/splats/`):
- **Mechanism**: Radiance field reconstruction producing photorealistic novel-view synthesis.
- **Resource Requirements**: Requires GPU-enabled NodeODM workers (NVIDIA CUDA Compute Capability >= 7.0) with >= 8GB VRAM.
- **AgriDrone Status**: Flagged as **Experimental**. Enabled only when connected to a GPU-accelerated processing node. If running on a CPU-only NodeODM instance, Gaussian splatting options are hidden to prevent task crashes.

---

## 4. Media & Panorama Workflows

Audited in `app/api/media.py`:
- **Equirectangular 360 Panoramas**: Drone surveys conducted with spherical 360 cameras can be ingested to generate interactive panoramic tours.
- **Media Thumbnails**: Automated thumbnail generation for quick visual review of aerial captures.
- **Camera Pose Visualization**: WebODM exports `cameras.json` indicating latitude, longitude, altitude, yaw, pitch, and roll of each camera exposure station, rendered as frustums along the flight path.

---

## 5. Dynamic Colormaps, Hillshading & Raster Styling

WebODM's tiler (`app/classes/tiler.py`) supports dynamic on-the-fly raster styling for elevation and agricultural vegetation products:

| Colormap Token | Best Use Case | Visual Characteristics |
|:---|:---|:---|
| **`viridis`** (Default) | Digital Surface Models (DSM) | Perceptually uniform blue-to-green-to-yellow gradient |
| **`terrain`** | Digital Terrain Models (DTM) | Conventional cartographic brown-green-white elevation ramp |
| **`plasma`** / **`magma`** | Thermal & canopy temperature | High-contrast purple-orange-yellow palette |
| **`greys`** | Bare elevation / Raw height | Grayscale representation (black=low, white=high) |

- **Hillshading (`hillshade=1`)**: Computes shaded relief using illumination azimuth and sun elevation, dramatically highlighting micro-topography, drainage paths, and irrigation furrows.
