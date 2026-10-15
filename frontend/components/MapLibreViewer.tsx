"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import * as maplibregl from "maplibre-gl";
import {
  Layers,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Crosshair,
  Sliders,
  Eye,
  EyeOff,
  RefreshCw,
  Loader2,
  MapPin,
  X,
} from "lucide-react";
import { api, FieldBoundaryGeoJSON, MapLayerVisualization, PointProbeResponse } from "@/lib/api";
import { MapLegend } from "@/components/MapLegend";

export interface MapLibreViewerProps {
  boundaryGeoJson: FieldBoundaryGeoJSON | null;
  activeProductId: string | null;
  visualizationMeta: MapLayerVisualization | null;
  opacity: number;
  onOpacityChange?: (val: number) => void;
  className?: string;
  onProbe?: (point: PointProbeResponse | null) => void;
}

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

export function MapLibreViewer({
  boundaryGeoJson,
  activeProductId,
  visualizationMeta,
  opacity,
  onOpacityChange,
  className = "",
  onProbe,
}: MapLibreViewerProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const probeMarkerRef = useRef<maplibregl.Marker | null>(null);

  const [isMapLoaded, setIsMapLoaded] = useState(false);
  const [isLayerVisible, setIsLayerVisible] = useState(true);
  const [isProbing, setIsProbing] = useState(false);
  const [probeData, setProbeData] = useState<PointProbeResponse | null>(null);

  // Initialize MapLibre GL JS Map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const initialCenter: [number, number] = visualizationMeta?.center || [74.585, 18.155];
    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: OSM_RASTER_STYLE,
      center: initialCenter,
      zoom: 15,
      maxZoom: 22,
      pitchWithRotate: false,
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

    map.on("load", () => {
      mapRef.current = map;
      setIsMapLoaded(true);
    });

    // Cleanup on unmount
    return () => {
      if (probeMarkerRef.current) {
        probeMarkerRef.current.remove();
        probeMarkerRef.current = null;
      }
      map.remove();
      mapRef.current = null;
      setIsMapLoaded(false);
    };
  }, []);

  // Update Field Boundary GeoJSON
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isMapLoaded) return;

    const sourceId = "field-boundary-source";
    const fillLayerId = "field-boundary-fill";
    const lineLayerId = "field-boundary-line";

    if (!boundaryGeoJson || !boundaryGeoJson.geometry) {
      if (map.getLayer(fillLayerId)) map.removeLayer(fillLayerId);
      if (map.getLayer(lineLayerId)) map.removeLayer(lineLayerId);
      if (map.getSource(sourceId)) map.removeSource(sourceId);
      return;
    }

    const featureCollection = {
      type: "FeatureCollection",
      features: [boundaryGeoJson],
    };

    const existingSource = map.getSource(sourceId) as maplibregl.GeoJSONSource | undefined;
    if (existingSource) {
      existingSource.setData(featureCollection as any);
    } else {
      map.addSource(sourceId, {
        type: "geojson",
        data: featureCollection as any,
      });

      map.addLayer({
        id: fillLayerId,
        type: "fill",
        source: sourceId,
        paint: {
          "fill-color": "#10b981",
          "fill-opacity": 0.12,
        },
      });

      map.addLayer({
        id: lineLayerId,
        type: "line",
        source: sourceId,
        paint: {
          "line-color": "#059669",
          "line-width": 2.5,
          "line-dasharray": [3, 2],
        },
      });
    }

    // Fit map to field bbox if available
    if (boundaryGeoJson.bbox && boundaryGeoJson.bbox.length === 4) {
      const [minX, minY, maxX, maxY] = boundaryGeoJson.bbox;
      map.fitBounds(
        [
          [minX, minY],
          [maxX, maxY],
        ],
        { padding: 50, maxZoom: 18, duration: 1200 }
      );
    }
  }, [boundaryGeoJson, isMapLoaded]);

  // Update Raster Tile Layer when activeProductId or visualizationMeta changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isMapLoaded) return;

    const rasterSourceId = "drone-raster-source";
    const rasterLayerId = "drone-raster-layer";

    // Clean up previous raster
    if (map.getLayer(rasterLayerId)) {
      map.removeLayer(rasterLayerId);
    }
    if (map.getSource(rasterSourceId)) {
      map.removeSource(rasterSourceId);
    }

    if (!activeProductId || !visualizationMeta) {
      return;
    }

    // Absolute or relative tile URL template
    const tileUrl = `${window.location.origin}/api/v1/maps/tiles/${activeProductId}/{z}/{x}/{y}.png`;

    map.addSource(rasterSourceId, {
      type: "raster",
      tiles: [tileUrl],
      tileSize: 256,
      bounds: visualizationMeta.bounds,
    });

    // Place raster layer just below field-boundary-line for clear perimeter visibility
    const beforeLayerId = map.getLayer("field-boundary-line") ? "field-boundary-line" : undefined;

    map.addLayer(
      {
        id: rasterLayerId,
        type: "raster",
        source: rasterSourceId,
        paint: {
          "raster-opacity": isLayerVisible ? opacity : 0,
          "raster-resampling": "linear",
        },
      },
      beforeLayerId
    );

    // If no field boundary fitted the map, fit to raster bounds
    if (!boundaryGeoJson?.bbox && visualizationMeta.bounds) {
      const [minLon, minLat, maxLon, maxLat] = visualizationMeta.bounds;
      map.fitBounds(
        [
          [minLon, minLat],
          [maxLon, maxLat],
        ],
        { padding: 60, maxZoom: 19, duration: 1000 }
      );
    }
  }, [activeProductId, visualizationMeta, isMapLoaded]);

  // Handle Opacity Changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isMapLoaded) return;

    const rasterLayerId = "drone-raster-layer";
    if (map.getLayer(rasterLayerId)) {
      map.setPaintProperty(rasterLayerId, "raster-opacity", isLayerVisible ? opacity : 0);
    }
  }, [opacity, isLayerVisible, isMapLoaded]);

  // Click-to-Probe Value Handler
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isMapLoaded || !activeProductId) return;

    const handleMapClick = async (e: maplibregl.MapMouseEvent) => {
      const { lng, lat } = e.lngLat;
      setIsProbing(true);

      try {
        const probed = await api.probeMapPoint(activeProductId, lat, lng);
        setProbeData(probed);
        if (onProbe) onProbe(probed);

        // Update or create probing marker on the map
        if (!probeMarkerRef.current) {
          const el = document.createElement("div");
          el.className = "w-4 h-4 rounded-full bg-emerald-500 border-2 border-white shadow-lg animate-ping";
          probeMarkerRef.current = new maplibregl.Marker({ color: "#10b981" })
            .setLngLat([lng, lat])
            .addTo(map);
        } else {
          probeMarkerRef.current.setLngLat([lng, lat]);
        }
      } catch (err) {
        console.warn("Probe request error:", err);
      } finally {
        setIsProbing(false);
      }
    };

    map.on("click", handleMapClick);

    return () => {
      map.off("click", handleMapClick);
    };
  }, [activeProductId, isMapLoaded, onProbe]);

  // Zoom to extent
  const handleZoomToExtent = useCallback(() => {
    const map = mapRef.current;
    if (!map) return;

    if (boundaryGeoJson?.bbox) {
      const [minX, minY, maxX, maxY] = boundaryGeoJson.bbox;
      map.fitBounds(
        [
          [minX, minY],
          [maxX, maxY],
        ],
        { padding: 50, duration: 1000 }
      );
    } else if (visualizationMeta?.bounds) {
      const [minLon, minLat, maxLon, maxLat] = visualizationMeta.bounds;
      map.fitBounds(
        [
          [minLon, minLat],
          [maxLon, maxLat],
        ],
        { padding: 50, duration: 1000 }
      );
    }
  }, [boundaryGeoJson, visualizationMeta]);

  return (
    <div className={`relative w-full h-[620px] rounded-xl overflow-hidden border border-slate-200 bg-slate-900 shadow-md ${className}`}>
      {/* MapLibre WebGL Canvas Container */}
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* Top Left: Quick Action Controls */}
      <div className="absolute top-4 left-4 z-20 flex flex-wrap items-center gap-2">
        <div className="bg-white/95 backdrop-blur-md rounded-lg shadow-sm border border-slate-200 p-1 flex items-center gap-1.5 text-xs">
          <button
            onClick={() => setIsLayerVisible(!isLayerVisible)}
            className={`px-2.5 py-1.5 rounded-md font-medium flex items-center gap-1.5 transition ${
              isLayerVisible
                ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                : "text-slate-500 hover:bg-slate-100"
            }`}
            title="Toggle raster visibility"
          >
            {isLayerVisible ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
            <span>{isLayerVisible ? "Layer Visible" : "Layer Hidden"}</span>
          </button>

          <button
            onClick={handleZoomToExtent}
            className="px-2.5 py-1.5 rounded-md font-medium text-slate-700 hover:bg-slate-100 flex items-center gap-1.5 transition"
            title="Fit view to field or raster boundary"
          >
            <Maximize2 className="w-3.5 h-3.5 text-slate-500" />
            <span>Fit Extent</span>
          </button>
        </div>

        {/* Opacity Slider */}
        {onOpacityChange && (
          <div className="bg-white/95 backdrop-blur-md rounded-lg shadow-sm border border-slate-200 px-3 py-1.5 flex items-center gap-2 text-xs">
            <Sliders className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-slate-600 font-medium text-[11px]">Opacity:</span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={opacity}
              onChange={(e) => onOpacityChange(parseFloat(e.target.value))}
              className="w-20 accent-emerald-600 cursor-pointer h-1.5 bg-slate-200 rounded-lg"
              title="Adjust layer transparency"
            />
            <span className="font-mono text-slate-700 font-semibold text-[11px] w-8 text-right">
              {Math.round(opacity * 100)}%
            </span>
          </div>
        )}
      </div>

      {/* Value Probe Floating Tooltip */}
      {probeData && (
        <div className="absolute top-4 right-16 z-20 bg-slate-900/90 text-white backdrop-blur-md rounded-lg shadow-lg border border-slate-700 px-3 py-2 text-xs flex items-center gap-3 animate-fadeIn">
          <div className="flex items-center gap-1.5 text-emerald-400">
            <Crosshair className="w-4 h-4 shrink-0 animate-pulse" />
            <span className="font-semibold">Probed Value:</span>
          </div>
          <div className="font-mono font-bold text-sm text-white">
            {probeData.is_valid && probeData.value !== undefined ? (
              <span>
                {probeData.value}{" "}
                <span className="text-xs font-normal text-slate-300">{probeData.unit}</span>
              </span>
            ) : (
              <span className="text-amber-300 text-xs font-normal">NoData / Outside</span>
            )}
          </div>
          <div className="text-[10px] text-slate-400 font-mono">
            {probeData.lat.toFixed(5)}, {probeData.lon.toFixed(5)}
          </div>
          <button
            onClick={() => {
              setProbeData(null);
              if (probeMarkerRef.current) {
                probeMarkerRef.current.remove();
                probeMarkerRef.current = null;
              }
            }}
            className="text-slate-400 hover:text-white transition p-0.5"
            title="Dismiss probe"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Bottom Left: Dynamic Legend */}
      <div className="absolute bottom-4 left-4 z-20 max-w-xs w-72">
        <MapLegend
          legend={visualizationMeta?.legend || null}
          productType={visualizationMeta?.product_type}
        />
      </div>

      {/* Bottom Right: Probing Hint Badge */}
      <div className="absolute bottom-4 right-4 z-20 bg-white/90 backdrop-blur-md rounded-md shadow-sm border border-slate-200 px-2.5 py-1 text-[11px] text-slate-600 flex items-center gap-1.5 pointer-events-none">
        {isProbing ? (
          <>
            <Loader2 className="w-3 h-3 text-emerald-600 animate-spin" />
            <span>Sampling pixel...</span>
          </>
        ) : (
          <>
            <MapPin className="w-3 h-3 text-slate-500" />
            <span>Click map to probe pixel value</span>
          </>
        )}
      </div>
    </div>
  );
}
