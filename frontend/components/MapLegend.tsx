"use client";

import React, { useState } from "react";
import { Info, ChevronDown, ChevronUp } from "lucide-react";
import type { MapLegend as MapLegendType } from "@/lib/api";

interface MapLegendProps {
  legend: MapLegendType | null;
  productType?: string;
  className?: string;
}

export function MapLegend({ legend, productType, className = "" }: MapLegendProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  if (!legend) {
    return (
      <div className={`bg-white/95 backdrop-blur-md rounded-lg shadow-md border border-slate-200 p-3 text-xs text-slate-500 ${className}`}>
        No active product selected
      </div>
    );
  }

  // Construct gradient CSS string from stops
  const gradientStops = legend.stops
    .map((s, idx) => {
      const pct = Math.round((idx / Math.max(legend.stops.length - 1, 1)) * 100);
      return `${s.color} ${pct}%`;
    })
    .join(", ");

  return (
    <div
      className={`bg-white/95 backdrop-blur-md rounded-xl shadow-lg border border-slate-200 p-3.5 transition-all text-xs ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-2 mb-2.5">
        <div className="flex items-center gap-1.5 min-w-0">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 shrink-0" />
          <h4 className="font-semibold text-slate-800 truncate" title={legend.title}>
            {legend.title}
          </h4>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-slate-400 hover:text-slate-600 p-0.5 rounded transition"
          aria-label={isExpanded ? "Collapse legend" : "Expand legend"}
        >
          {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {isExpanded && (
        <div className="space-y-3">
          {/* Continuous Gradient Bar for continuous indices and elevation */}
          {legend.colormap_type !== "RGB" && (
            <div>
              <div
                className="h-3 w-full rounded border border-slate-300 shadow-inner"
                style={{
                  background: `linear-gradient(to right, ${gradientStops})`,
                }}
              />
              <div className="flex justify-between items-center text-[10px] text-slate-500 font-mono mt-1">
                <span>{legend.min_value} {legend.unit !== "dimensionless" ? legend.unit : ""}</span>
                <span className="text-slate-400">Unit: {legend.unit}</span>
                <span>{legend.max_value} {legend.unit !== "dimensionless" ? legend.unit : ""}</span>
              </div>
            </div>
          )}

          {/* Discrete Color Stops / Analytical Zones */}
          <div className="space-y-1.5 pt-1">
            {legend.stops.map((stop, i) => (
              <div key={i} className="flex items-center justify-between gap-2 text-[11px]">
                <div className="flex items-center gap-2 min-w-0">
                  <span
                    className="w-3.5 h-3.5 rounded shrink-0 border border-slate-300 shadow-xs"
                    style={{ backgroundColor: stop.color }}
                  />
                  <span className="text-slate-700 truncate">{stop.label}</span>
                </div>
                <span className="text-slate-400 font-mono text-[10px] shrink-0">
                  {stop.value}
                </span>
              </div>
            ))}
          </div>

          {/* NoData Transparent Badge */}
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <div className="flex items-center gap-2">
              <span
                className="w-3.5 h-3.5 rounded shrink-0 border border-slate-300 shadow-xs relative overflow-hidden"
                style={{
                  backgroundImage:
                    "repeating-linear-gradient(45deg, #cbd5e1 0, #cbd5e1 2px, #f8fafc 0, #f8fafc 6px)",
                }}
              />
              <span>NoData / Masked</span>
            </div>
            <span className="text-[10px] text-slate-400 font-mono">100% Alpha</span>
          </div>

          <div className="text-[10px] text-slate-400 italic flex items-center gap-1">
            <Info className="w-3 h-3 shrink-0 text-slate-400" />
            <span>Values represent spectral indices, not diagnostic claims.</span>
          </div>
        </div>
      )}
    </div>
  );
}
