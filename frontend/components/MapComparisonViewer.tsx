"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import * as maplibregl from "maplibre-gl";
import {
  Columns,
  Maximize2,
  Sliders,
  AlertTriangle,
  CheckCircle2,
  Info,
  RefreshCw,
} from "lucide-react";
import {
  api,
  FieldBoundaryGeoJSON,
  MapLayerVisualization,
  ComparisonCompatibilityResponse,
} from "@/lib/api";
import { MapLegend } from "@/components/MapLegend";

export interface MapComparisonViewerProps {
  boundaryGeoJson: FieldBoundaryGeoJSON | null;
  productAId: string | null;
  productBId: string | null;
  metaA: MapLayerVisualization | null;
  metaB: MapLayerVisualization | null;
  className?: string;
}

const OSM_STYLE: maplibregl.StyleSpecification = {
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

export function MapComparisonViewer({
  boundaryGeoJson,
  productAId,
  productBId,
  metaA,
  metaB,
  className = "",
}: MapComparisonViewerProps) {
  const containerARef = useRef<HTMLDivElement>(null);
  const containerBRef = useRef<HTMLDivElement>(null);
  const mapARef = useRef<maplibregl.Map | null>(null);
  const mapBRef = useRef<maplibregl.Map | null>(null);

  const [opacityA, setOpacityA] = useState(0.9);
  const [opacityB, setOpacityB] = useState(0.9);
  const [compatibility, setCompatibility] = useState<ComparisonCompatibilityResponse | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);

  // Check comparison compatibility when products change
  useEffect(() => {
    if (!productAId || !productBId) {
      setCompatibility(null);
      return;
    }

    let isMounted = true;
    api
      .checkComparisonCompatibility(productAId, productBId)
      .then((res) => {
        if (isMounted) setCompatibility(res);
      })
      .catch((err) => {
        console.warn("Failed to check compatibility:", err);
      });

    return () => {
      isMounted = false;
    };
  }, [productAId, productBId]);

  // Initialize both maps
  useEffect(() => {
    if (!containerARef.current || !containerBRef.current) return;
    if (mapARef.current || mapBRef.current) return;

    const initialCenter: [number, number] = metaA?.center || metaB?.center || [74.585, 18.155];

    // Left Map
    const mapA = new maplibregl.Map({
      container: containerARef.current,
      style: OSM_STYLE,
      center: initialCenter,
      zoom: 15,
      maxZoom: 22,
      pitchWithRotate: false,
    });

    // Right Map
    const mapB = new maplibregl.Map({
      container: containerBRef.current,
      style: OSM_STYLE,
      center: initialCenter,
      zoom: 15,
      maxZoom: 22,
      pitchWithRotate: false,
    });

    mapARef.current = mapA;
    mapBRef.current = mapB;

    // Synchronize movements between Map A and Map B
    let isMovingA = false;
    let isMovingB = false;

    const onMoveA = () => {
      if (isMovingB) return;
      isMovingA = true;
      mapB.jumpTo({
        center: mapA.getCenter(),
        zoom: mapA.getZoom(),
        bearing: mapA.getBearing(),
        pitch: mapA.getPitch(),
      });
      isMovingA = false;
    };

    const onMoveB = () => {
      if (isMovingA) return;
      isMovingB = true;
      mapA.jumpTo({
        center: mapB.getCenter(),
        zoom: mapB.getZoom(),
        bearing: mapB.getBearing(),
        pitch: mapB.getPitch(),
      });
      isMovingB = false;
    };

    mapA.on("move", onMoveA);
    mapB.on("move", onMoveB);

    return () => {
      mapA.off("move", onMoveA);
      mapB.off("move", onMoveB);
      mapA.remove();
      mapB.remove();
      mapARef.current = null;
      mapBRef.current = null;
    };
  }, []);

  // Update Field Boundaries on both maps
  const updateBoundaries = useCallback(
    (map: maplibregl.Map | null) => {
      if (!map || !map.isStyleLoaded()) return;

      const sourceId = "field-boundary-source";
      if (!boundaryGeoJson || !boundaryGeoJson.geometry) {
        if (map.getLayer("field-boundary-fill")) map.removeLayer("field-boundary-fill");
        if (map.getLayer("field-boundary-line")) map.removeLayer("field-boundary-line");
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
        map.addSource(sourceId, { type: "geojson", data: featureCollection as any });
        map.addLayer({
          id: "field-boundary-fill",
          type: "fill",
          source: sourceId,
          paint: { "fill-color": "#10b981", "fill-opacity": 0.1 },
        });
        map.addLayer({
          id: "field-boundary-line",
          type: "line",
          source: sourceId,
          paint: { "line-color": "#059669", "line-width": 2, "line-dasharray": [3, 2] },
        });
      }
    },
    [boundaryGeoJson]
  );

  useEffect(() => {
    const handleLoaded = () => {
      updateBoundaries(mapARef.current);
      updateBoundaries(mapBRef.current);
    };

    if (mapARef.current?.isStyleLoaded()) updateBoundaries(mapARef.current);
    else mapARef.current?.on("load", handleLoaded);

    if (mapBRef.current?.isStyleLoaded()) updateBoundaries(mapBRef.current);
    else mapBRef.current?.on("load", handleLoaded);
  }, [boundaryGeoJson, updateBoundaries]);

  // Update Raster Tile Layer A
  useEffect(() => {
    const map = mapARef.current;
    if (!map || !map.isStyleLoaded()) return;

    if (map.getLayer("raster-layer-a")) map.removeLayer("raster-layer-a");
    if (map.getSource("raster-source-a")) map.removeSource("raster-source-a");

    if (!productAId || !metaA) return;

    const tileUrl = `${window.location.origin}/api/v1/maps/tiles/${productAId}/{z}/{x}/{y}.png`;
    map.addSource("raster-source-a", {
      type: "raster",
      tiles: [tileUrl],
      tileSize: 256,
      bounds: metaA.bounds,
    });

    const beforeLayer = map.getLayer("field-boundary-line") ? "field-boundary-line" : undefined;
    map.addLayer(
      {
        id: "raster-layer-a",
        type: "raster",
        source: "raster-source-a",
        paint: { "raster-opacity": opacityA },
      },
      beforeLayer
    );
  }, [productAId, metaA, opacityA]);

  // Update Raster Tile Layer B
  useEffect(() => {
    const map = mapBRef.current;
    if (!map || !map.isStyleLoaded()) return;

    if (map.getLayer("raster-layer-b")) map.removeLayer("raster-layer-b");
    if (map.getSource("raster-source-b")) map.removeSource("raster-source-b");

    if (!productBId || !metaB) return;

    const tileUrl = `${window.location.origin}/api/v1/maps/tiles/${productBId}/{z}/{x}/{y}.png`;
    map.addSource("raster-source-b", {
      type: "raster",
      tiles: [tileUrl],
      tileSize: 256,
      bounds: metaB.bounds,
    });

    const beforeLayer = map.getLayer("field-boundary-line") ? "field-boundary-line" : undefined;
    map.addLayer(
      {
        id: "raster-layer-b",
        type: "raster",
        source: "raster-source-b",
        paint: { "raster-opacity": opacityB },
      },
      beforeLayer
    );
  }, [productBId, metaB, opacityB]);

  // Fit both maps to bounds
  const handleFitExtent = () => {
    const bbox = boundaryGeoJson?.bbox || metaA?.bounds || metaB?.bounds;
    if (!bbox) return;

    const [minX, minY, maxX, maxY] = bbox;
    mapARef.current?.fitBounds(
      [
        [minX, minY],
        [maxX, maxY],
      ],
      { padding: 40, duration: 1000 }
    );
  };

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Compatibility Banner */}
      {compatibility && (
        <div
          className={`p-3 rounded-lg border text-xs flex items-start gap-2.5 ${
            compatibility.is_compatible
              ? "bg-emerald-50 border-emerald-200 text-emerald-900"
              : "bg-amber-50 border-amber-200 text-amber-900"
          }`}
        >
          {compatibility.is_compatible ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          )}
          <div className="flex-1">
            <div className="font-semibold flex items-center justify-between">
              <span>
                {compatibility.is_compatible
                  ? `Compatible for Comparison (${compatibility.spatial_overlap_percentage}% Spatial Overlap)`
                  : "Limited Comparison Compatibility"}
              </span>
              <button
                onClick={handleFitExtent}
                className="text-[11px] underline hover:no-underline font-medium flex items-center gap-1"
              >
                <Maximize2 className="w-3 h-3" />
                <span>Sync Extents</span>
              </button>
            </div>
            <p className="mt-0.5 text-slate-700">{compatibility.reason}</p>
            <p className="mt-0.5 text-slate-500 italic text-[11px]">{compatibility.recommendation}</p>
          </div>
        </div>
      )}

      {/* Dual Split Map Container */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 h-[600px]">
        {/* Left Map: Product A */}
        <div className="relative rounded-xl overflow-hidden border border-slate-200 bg-slate-900 shadow-sm flex flex-col">
          <div className="absolute top-3 left-3 z-10 bg-white/95 backdrop-blur-md rounded-lg shadow-sm border border-slate-200 px-3 py-1.5 text-xs flex items-center justify-between gap-3">
            <span className="font-semibold text-slate-800">
              {metaA?.legend.title || "Layer A (Left)"}
            </span>
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] text-slate-500">Opacity:</span>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={opacityA}
                onChange={(e) => setOpacityA(parseFloat(e.target.value))}
                className="w-16 accent-emerald-600 cursor-pointer h-1.5 bg-slate-200 rounded"
              />
              <span className="font-mono text-[10px] text-slate-700 w-6 text-right">
                {Math.round(opacityA * 100)}%
              </span>
            </div>
          </div>

          <div ref={containerARef} className="w-full h-full" />

          {/* Left Legend */}
          <div className="absolute bottom-3 left-3 z-10 max-w-xs w-64 pointer-events-auto">
            <MapLegend legend={metaA?.legend || null} />
          </div>
        </div>

        {/* Right Map: Product B */}
        <div className="relative rounded-xl overflow-hidden border border-slate-200 bg-slate-900 shadow-sm flex flex-col">
          <div className="absolute top-3 left-3 z-10 bg-white/95 backdrop-blur-md rounded-lg shadow-sm border border-slate-200 px-3 py-1.5 text-xs flex items-center justify-between gap-3">
            <span className="font-semibold text-slate-800">
              {metaB?.legend.title || "Layer B (Right)"}
            </span>
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] text-slate-500">Opacity:</span>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={opacityB}
                onChange={(e) => setOpacityB(parseFloat(e.target.value))}
                className="w-16 accent-emerald-600 cursor-pointer h-1.5 bg-slate-200 rounded"
              />
              <span className="font-mono text-[10px] text-slate-700 w-6 text-right">
                {Math.round(opacityB * 100)}%
              </span>
            </div>
          </div>

          <div ref={containerBRef} className="w-full h-full" />

          {/* Right Legend */}
          <div className="absolute bottom-3 left-3 z-10 max-w-xs w-64 pointer-events-auto">
            <MapLegend legend={metaB?.legend || null} />
          </div>
        </div>
      </div>
    </div>
  );
}
