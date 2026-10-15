"use client";

import React, { useState } from "react";
import {
  Layers,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Sliders,
  Crosshair,
  Download,
  Info,
  Check,
  Eye,
  Columns,
} from "lucide-react";

interface InteractiveMapPreviewProps {
  fieldName: string;
  surveyDate: string;
  activeLayer: "ortho" | "ndvi" | "ndre" | "savi";
  onLayerChange: (layer: "ortho" | "ndvi" | "ndre" | "savi") => void;
  opacity: number;
  onOpacityChange: (opacity: number) => void;
  splitMode: boolean;
  onToggleSplit: () => void;
}

export function InteractiveMapPreview({
  fieldName,
  surveyDate,
  activeLayer,
  onLayerChange,
  opacity,
  onOpacityChange,
  splitMode,
  onToggleSplit,
}: InteractiveMapPreviewProps) {
  const [splitPos, setSplitPos] = useState(50);
  const [probedPoint, setProbedPoint] = useState<{
    x: number;
    y: number;
    lat: number;
    lon: number;
    val: number;
  } | null>({
    x: 48,
    y: 52,
    lat: 45.1842,
    lon: 9.3218,
    val: 0.72,
  });

  const handleMapClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const xPct = ((e.clientX - rect.left) / rect.width) * 100;
    const yPct = ((e.clientY - rect.top) / rect.height) * 100;

    // Simulate realistic index value based on location
    const simulatedVal = parseFloat((0.2 + (Math.sin(xPct / 10) * 0.3 + 0.35)).toFixed(2));
    const lat = parseFloat((45.18 + (yPct / 1000)).toFixed(4));
    const lon = parseFloat((9.32 + (xPct / 1000)).toFixed(4));

    setProbedPoint({
      x: xPct,
      y: yPct,
      lat,
      lon,
      val: Math.min(Math.max(simulatedVal, -0.1), 0.88),
    });
  };

  return (
    <div className="relative w-full h-[620px] rounded-xl overflow-hidden border border-slate-200 bg-slate-900 shadow-md flex flex-col">
      {/* Top Map Control Bar */}
      <div className="absolute top-4 left-4 z-20 flex items-center gap-2">
        <div className="bg-white/95 backdrop-blur-md rounded-lg shadow-sm border border-slate-200 p-1 flex items-center gap-1">
          <button
            onClick={() => onLayerChange("ortho")}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
              activeLayer === "ortho"
                ? "bg-emerald-600 text-white shadow-xs"
                : "text-slate-700 hover:bg-slate-100"
            }`}
          >
            True Color RGB
          </button>
          <button
            onClick={() => onLayerChange("ndvi")}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
              activeLayer === "ndvi"
                ? "bg-emerald-600 text-white shadow-xs"
                : "text-slate-700 hover:bg-slate-100"
            }`}
          >
            NDVI Vigor
          </button>
          <button
            onClick={() => onLayerChange("ndre")}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
              activeLayer === "ndre"
                ? "bg-emerald-600 text-white shadow-xs"
                : "text-slate-700 hover:bg-slate-100"
            }`}
          >
            NDRE Chlorophyll
          </button>
          <button
            onClick={() => onLayerChange("savi")}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
              activeLayer === "savi"
                ? "bg-emerald-600 text-white shadow-xs"
                : "text-slate-700 hover:bg-slate-100"
            }`}
          >
            SAVI Soil-Adj
          </button>
        </div>

        {/* Split Comparison Toggle */}
        <button
          onClick={onToggleSplit}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold shadow-sm border transition-all ${
            splitMode
              ? "bg-blue-600 text-white border-blue-700 shadow-xs"
              : "bg-white/95 backdrop-blur-md text-slate-700 hover:bg-slate-50 border-slate-200"
          }`}
          title="Toggle Split-Screen Comparison (RGB vs Index)"
        >
          <Columns className="w-3.5 h-3.5" />
          <span>{splitMode ? "Split Active" : "Compare Split"}</span>
        </button>
      </div>

      {/* Map Zoom / Fullscreen Utilities (Top Right) */}
      <div className="absolute top-4 right-4 z-20 flex flex-col gap-1.5">
        <div className="bg-white/95 backdrop-blur-md rounded-lg shadow-sm border border-slate-200 p-1 flex flex-col">
          <button className="p-2 text-slate-700 hover:bg-slate-100 rounded-md transition-colors" title="Zoom In">
            <ZoomIn className="w-4 h-4" />
          </button>
          <button className="p-2 text-slate-700 hover:bg-slate-100 rounded-md transition-colors border-t border-slate-100" title="Zoom Out">
            <ZoomOut className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Interactive Map Visual Viewport */}
      <div
        onClick={handleMapClick}
        className="relative w-full flex-1 cursor-crosshair overflow-hidden select-none"
        style={{
          background: "radial-gradient(circle at 50% 50%, #1e293b 0%, #0f172a 100%)",
        }}
      >
        {/* Simulated Satellite Landscape Background */}
        <div
          className="absolute inset-0 opacity-80"
          style={{
            backgroundImage: `radial-gradient(#334155 1.5px, transparent 1.5px), radial-gradient(#1e293b 1.5px, #0f172a 1.5px)`,
            backgroundSize: "30px 30px",
            backgroundPosition: "0 0, 15px 15px",
          }}
        />

        {/* Simulated Field Boundary Polygon */}
        <div className="absolute inset-0 flex items-center justify-center p-8 pointer-events-none">
          <div
            className="w-[82%] h-[82%] rounded-2xl relative border-2 border-emerald-400/90 shadow-2xl overflow-hidden transition-all"
            style={{
              clipPath: "polygon(6% 12%, 88% 4%, 96% 82%, 14% 94%)",
            }}
          >
            {/* Base Layer: RGB True Color Orthomosaic Simulation */}
            <div
              className="absolute inset-0 transition-opacity duration-300"
              style={{
                background: "linear-gradient(135deg, #2d5a27 0%, #3e6b32 25%, #4a7c3b 50%, #2f5323 75%, #1e3a17 100%)",
                filter: "contrast(1.15) saturate(1.2)",
              }}
            >
              {/* Field Crop Rows Texture Simulation */}
              <div
                className="w-full h-full opacity-35"
                style={{
                  backgroundImage: "repeating-linear-gradient(45deg, rgba(0,0,0,0.2) 0px, rgba(0,0,0,0.2) 4px, transparent 4px, transparent 16px)",
                }}
              />
            </div>

            {/* Overlay Layer: False Color Index Layer */}
            {activeLayer !== "ortho" && (
              <div
                className="absolute inset-0 transition-opacity duration-300"
                style={{
                  opacity: opacity / 100,
                  clipPath: splitMode ? `polygon(0 0, ${splitPos}% 0, ${splitPos}% 100%, 0 100%)` : undefined,
                  background:
                    activeLayer === "ndvi"
                      ? "radial-gradient(ellipse at 40% 45%, #1b5e20 0%, #4caf50 35%, #ffeb3b 65%, #ff9800 80%, #d32f2f 100%)"
                      : activeLayer === "ndre"
                      ? "radial-gradient(ellipse at 50% 50%, #0d47a1 0%, #1976d2 30%, #4caf50 60%, #ffeb3b 85%, #f44336 100%)"
                      : "radial-gradient(ellipse at 45% 45%, #2e7d32 0%, #81c784 40%, #fff176 70%, #e57373 100%)",
                  filter: "saturate(1.3) contrast(1.1)",
                }}
              >
                {/* Simulated Canopy Stress Patch */}
                <div
                  className="absolute w-36 h-28 rounded-full blur-md opacity-90"
                  style={{
                    top: "35%",
                    left: "25%",
                    background: "#d32f2f",
                  }}
                />
              </div>
            )}

            {/* Split Slider Divider Line */}
            {splitMode && (
              <div
                className="absolute top-0 bottom-0 z-30 w-1 bg-white cursor-ew-resize shadow-lg"
                style={{ left: `${splitPos}%` }}
              >
                <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-white shadow-md border border-slate-300 flex items-center justify-center text-slate-700 text-xs font-bold">
                  &#8644;
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Probed Pixel Marker and Tooltip */}
        {probedPoint && (
          <div
            className="absolute z-30 -translate-x-1/2 -translate-y-full pointer-events-none transition-all duration-150"
            style={{ left: `${probedPoint.x}%`, top: `${probedPoint.y}%` }}
          >
            <div className="bg-slate-900/95 text-white backdrop-blur-md border border-slate-700 rounded-lg p-2.5 shadow-xl text-xs space-y-1 mb-2">
              <div className="flex items-center justify-between gap-3 border-b border-slate-700 pb-1">
                <span className="font-bold text-emerald-400 uppercase text-[10px] tracking-wider">
                  Pixel Inspection
                </span>
                <span className="text-[10px] text-slate-400">
                  {probedPoint.lat}, {probedPoint.lon}
                </span>
              </div>
              <div className="flex items-center justify-between gap-4 pt-0.5">
                <span className="text-slate-300 capitalize">{activeLayer} Value:</span>
                <span className="font-mono font-bold text-sm text-emerald-300">
                  {activeLayer === "ortho" ? "RGB (48, 86, 38)" : probedPoint.val}
                </span>
              </div>
              <p className="text-[10px] text-slate-400 italic">
                {probedPoint.val > 0.6
                  ? "Dense Vigorous Canopy"
                  : probedPoint.val > 0.4
                  ? "Moderate Vegetation"
                  : "Stressed / Soil Background"}
              </p>
            </div>
            {/* Pin Target */}
            <div className="w-3 h-3 rounded-full bg-emerald-400 border-2 border-slate-950 mx-auto shadow-md animate-ping" />
          </div>
        )}
      </div>

      {/* Bottom Map Metadata & Status Footer */}
      <div className="h-10 bg-slate-950/90 border-t border-slate-800 px-4 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-4">
          <span>Field: <strong className="text-slate-200">{fieldName}</strong></span>
          <span className="hidden sm:inline">Flight Date: <strong className="text-slate-200">{surveyDate}</strong></span>
          <span className="hidden md:inline">GSD: <strong className="text-slate-200">2.4 cm/px</strong></span>
        </div>
        <div className="flex items-center gap-2 text-[11px]">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span>Interactive Click-to-Probe Active</span>
        </div>
      </div>
    </div>
  );
}
