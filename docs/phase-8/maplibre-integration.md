# MapLibre GL JS Integration Architecture

## 1. Overview
AgriDrone AutoMap utilizes **MapLibre GL JS** (v6.14.0) as its dedicated web-based vector and raster mapping engine. MapLibre GL JS provides hardware-accelerated WebGL rendering, smooth client-side reprojection, fluid zooming/panning, and dynamic layer styling without vendor lock-in or recurring map tile fees.

---

## 2. Map Container Architecture & Lifecycle
To prevent memory leaks and context loss in modern Next.js React 18/19 environments, the MapLibre instance is wrapped in a dedicated component lifecycle:

```typescript
// Initializing MapLibre safely in React
useEffect(() => {
  if (!mapContainerRef.current || mapRef.current) return;

  const map = new maplibregl.Map({
    container: mapContainerRef.current,
    style: OSM_RASTER_STYLE,
    center: [74.585, 18.155],
    zoom: 15,
    maxZoom: 22,
    pitchWithRotate: false,
  });

  map.on('load', () => {
    mapRef.current = map;
    setIsMapLoaded(true);
  });

  return () => {
    map.remove();
    mapRef.current = null;
  };
}, []);
```

### Key Lifecycle Safeguards:
1. **Singleton Map Reference**: `mapRef.current` guards against duplicate map initializations during React StrictMode re-renders.
2. **Explicit Cleanup**: `map.remove()` is called in the `useEffect` cleanup return to destroy the WebGL canvas, detach event listeners, and clear internal tile caches.
3. **Marker Tracking**: Interactive point-probing markers (`probeMarkerRef.current`) are cleanly removed before map destruction.

---

## 3. Basemap Configuration
The map defaults to an accessible, high-performance OpenStreetMap raster basemap styled for agricultural context:

```typescript
const OSM_RASTER_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    "osm-tiles": {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "&copy; OpenStreetMap Contributors",
    },
  },
  layers: [
    {
      id: "osm-base-layer",
      type: "raster",
      source: "osm-tiles",
      minzoom: 0,
      maxzoom: 19,
    },
  ],
};
```

---

## 4. Layer Ordering & Draw Hierarchy
To ensure boundaries remain visible over orthomosaics and vegetation index rasters, layers are strictly arranged in the following z-order:

| Layer ID | Type | Z-Index / Order | Visual Style |
|---|---|---|---|
| `osm-base-layer` | Raster | Base (Lowest) | Neutral geographic background |
| `drone-raster-layer` | Raster | Middle | Dynamic 256x256 XYZ slippy tiles with opacity slider |
| `field-boundary-fill` | Fill | Upper Middle | Translucent emerald `#10b981` (12% opacity) |
| `field-boundary-line` | Line | Top | High-contrast emerald `#059669` (width 2.5, dashed `[3, 2]`) |

When `map.addLayer` is called for the drone raster, `beforeLayerId` is explicitly set to `'field-boundary-line'`, guaranteeing that the field perimeter is never occluded by high-density raster pixels.

---

## 5. Viewport Synchronization & Bounds Fitting
Map bounds are derived directly from PostGIS geometries (`FieldBoundaryGeoJSON.bbox`) or raster metadata (`MapLayerVisualization.bounds`).
- When a field boundary is loaded:
  ```typescript
  map.fitBounds([[minX, minY], [maxX, maxY]], {
    padding: 50,
    maxZoom: 18,
    duration: 1200,
  });
  ```
- This automatically centers the drone survey regardless of farm geographic location.
