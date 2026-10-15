# Raster Comparison Workflow

## 1. Overview
Evaluating agricultural development over time or inspecting the correlation between different spectral channels requires comparing geospatial products side-by-side. Phase 8 implements a synchronized dual-map comparison interface powered by dual MapLibre GL JS instances.

---

## 2. Comparison Modes & User Interaction
Users can switch between **Single Layer Map Mode** and **Dual Split Comparison Mode** using the "Compare Layers" toggle on Page 4.

### Features of Dual Comparison Mode:
1. **Independent Product Selection**:
   - **Left Map**: Displays Product A (e.g., RGB Orthophoto or Early Vegetative NDVI).
   - **Right Map**: Displays Product B (e.g., Red-Edge NDRE or Late Season NDVI).
2. **Camera Synchronization**:
   - Map A and Map B are programmatically synchronized using bidirectional `move` event listeners.
   - Panning, zooming, or rotating Map A immediately updates Map B to the exact same center coordinates, zoom level, pitch, and bearing, and vice versa.
   - Circular synchronization loops are prevented via mutual motion flags (`isMovingA`, `isMovingB`).
3. **Independent Opacity Sliders**:
   - Each view maintains an independent opacity controller (0–100%).
4. **Independent Dynamic Legends**:
   - Each map displays its own color ramp and metric scale at the bottom-left corner.

---

## 3. Comparison Compatibility Validation (`/api/v1/maps/compare-compatibility`)
Before presenting two products side-by-side, the backend evaluates whether the comparison is scientifically and spatially defensible:

```
GET /api/v1/maps/compare-compatibility?product_a={id}&product_b={id}
```

### Compatibility Evaluation Logic:
1. **Exact Survey Match (100% Overlap)**:
   - If both products belong to the exact same drone flight (e.g., comparing NDVI vs NDRE of the same date), `is_compatible = true`, overlap = 100%. Direct multi-spectral comparison is approved.
2. **Same Field, Different Survey Dates (Multi-Temporal)**:
   - If products originate from different flight surveys of the same field, `is_compatible = true`, overlap = 95%.
   - A multi-temporal development advisory is provided: *"Compare canopy development across flight dates with awareness of differing weather and illumination."*
3. **Different Fields (0% Overlap)**:
   - If products belong to entirely different farms or fields, `is_compatible = false`.
   - A clear incompatibility warning banner instructs the user to select products sharing field boundaries.

---

## 4. Scientific Disclaimers in Comparison
Visual difference between two dates or layers does not automatically prove a single cause (such as disease, insect damage, or specific fertilizer deficiency). Comparison maps highlight spatial variation to guide targeted field scouting.
