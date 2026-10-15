"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Layers,
  Play,
  RotateCw,
  XCircle,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Terminal,
  Cpu,
  ArrowRight,
  Sliders,
  FileCheck,
  Check,
} from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import { AlertBanner } from "@/components/AlertBanner";

export default function PhotogrammetryPage() {
  const [selectedSurvey, setSelectedSurvey] = useState("SURV-2026-101 (North Pivot 4, 348 photos)");
  const [preset, setPreset] = useState<"fast" | "precision" | "custom">("fast");
  const [targetGsd, setTargetGsd] = useState(2.5);
  const [generateDsm, setGenerateDsm] = useState(true);
  const [radiometricCal, setRadiometricCal] = useState(true);

  // Simulation state
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(64);
  const [currentStage, setCurrentStage] = useState("OpenSfM Feature Matching & Bundle Adjustment");

  const simulatedLogs = [
    "[2026-10-14 12:20:01] INFO: Initializing WebODM task worker for survey SURV-2026-101",
    "[2026-10-14 12:20:05] INFO: Reading EXIF/XMP tags from 348 aerial images",
    "[2026-10-14 12:20:18] INFO: Camera sensor identified: MicaSense RedEdge-P (5 bands, focal length 5.5mm)",
    "[2026-10-14 12:21:45] INFO: Downwelling Light Sensor (DLS-2) solar irradiance calibration applied",
    "[2026-10-14 12:23:12] INFO: Running OpenSfM feature extraction (SIFT algorithm, quality: HIGH)...",
    "[2026-10-14 12:26:40] INFO: 342 / 348 images successfully aligned in bundle adjustment (98.3%)",
    "[2026-10-14 12:31:05] INFO: Generating sparse point cloud (reprojection error: 0.84 pixels)",
    "[2026-10-14 12:35:50] INFO: Executing OpenMVS dense surface point cloud reconstruction...",
    "[2026-10-14 12:41:20] INFO: Generating 2.5cm/px orthophoto GeoTIFF with UTM Zone 32N projection...",
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 mb-1">
            <span>Page 2 of 5</span>
            <span>&bull;</span>
            <span className="text-emerald-700 font-bold">Photogrammetry Center</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            WebODM Photogrammetry Processing
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Submit compatible raw aerial survey photos to WebODM, configure photogrammetry options, and track live reconstruction.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/admin/algorithms"
            className="btn-primary text-xs"
          >
            <span>Proceed to Algorithms</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Row 1: Task Configuration & Node Health */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Card 1: Configuration Panel (2 cols) */}
        <div className="card-base p-6 lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2 font-semibold text-sm text-slate-800">
              <Sliders className="w-4 h-4 text-emerald-600" />
              <span>Photogrammetry Pipeline Configuration</span>
            </div>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
              NodeODM Connected
            </span>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Target Flight Survey</label>
              <select
                value={selectedSurvey}
                onChange={(e) => setSelectedSurvey(e.target.value)}
                className="input-base w-full text-xs"
              >
                <option>SURV-2026-101 (North Pivot 4, 348 photos - Eligible)</option>
                <option>SURV-2026-084 (East Pasture 1, 120 photos - Re-run)</option>
              </select>
            </div>

            {/* Presets */}
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-2">Processing Presets</label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <button
                  type="button"
                  onClick={() => setPreset("fast")}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    preset === "fast"
                      ? "border-emerald-600 bg-emerald-50/50 shadow-xs"
                      : "border-slate-200 hover:border-slate-300 bg-white"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-xs text-slate-900">Agricultural Fast</span>
                    {preset === "fast" && <Check className="w-3.5 h-3.5 text-emerald-600" />}
                  </div>
                  <p className="text-[11px] text-slate-500">Lower densification, rapid 2D orthomosaic generation (~15-30 min).</p>
                </button>

                <button
                  type="button"
                  onClick={() => setPreset("precision")}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    preset === "precision"
                      ? "border-emerald-600 bg-emerald-50/50 shadow-xs"
                      : "border-slate-200 hover:border-slate-300 bg-white"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-xs text-slate-900">High Precision</span>
                    {preset === "precision" && <Check className="w-3.5 h-3.5 text-emerald-600" />}
                  </div>
                  <p className="text-[11px] text-slate-500">Full point-cloud densification, digital surface &amp; terrain models.</p>
                </button>

                <button
                  type="button"
                  onClick={() => setPreset("custom")}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    preset === "custom"
                      ? "border-emerald-600 bg-emerald-50/50 shadow-xs"
                      : "border-slate-200 hover:border-slate-300 bg-white"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-xs text-slate-900">Custom Options</span>
                    {preset === "custom" && <Check className="w-3.5 h-3.5 text-emerald-600" />}
                  </div>
                  <p className="text-[11px] text-slate-500">Specify manual feature matching thresholds and camera flags.</p>
                </button>
              </div>
            </div>

            {/* Sliders & Toggles */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Target GSD (cm/pixel)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={targetGsd}
                  onChange={(e) => setTargetGsd(Number(e.target.value))}
                  className="input-base w-full text-xs"
                />
              </div>

              <div className="flex items-center gap-2 pt-6">
                <input
                  type="checkbox"
                  id="dsm-toggle"
                  checked={generateDsm}
                  onChange={(e) => setGenerateDsm(e.target.checked)}
                  className="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500"
                />
                <label htmlFor="dsm-toggle" className="text-xs font-semibold text-slate-700">
                  Generate Elevation Model (DSM)
                </label>
              </div>

              <div className="flex items-center gap-2 pt-6">
                <input
                  type="checkbox"
                  id="rad-toggle"
                  checked={radiometricCal}
                  onChange={(e) => setRadiometricCal(e.target.checked)}
                  className="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500"
                />
                <label htmlFor="rad-toggle" className="text-xs font-semibold text-slate-700">
                  Reflectance Panel Calibration
                </label>
              </div>
            </div>

            <div className="pt-2">
              <button className="btn-primary text-xs">
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Start Photogrammetry Reconstruction</span>
              </button>
            </div>
          </div>
        </div>

        {/* Card 2: Cluster Node Health (1 col) */}
        <div className="card-base p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2 font-semibold text-sm text-slate-800">
              <Cpu className="w-4 h-4 text-emerald-600" />
              <span>NodeODM Compute Cluster</span>
            </div>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500">Service Status</span>
              <span className="font-semibold text-emerald-700 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 pulse-active" />
                Online &amp; Responsive
              </span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500">Assigned Nodes</span>
              <strong className="text-slate-900 font-mono">1 Active (Worker-01)</strong>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500">Available RAM</span>
              <strong className="text-slate-900 font-mono">18.4 GB / 32.0 GB</strong>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500">Node API Endpoint</span>
              <strong className="text-slate-700 font-mono text-[10px]">http://nodeodm:3000</strong>
            </div>
          </div>

          <AlertBanner
            type="info"
            message="Dedicated Celery queue (photogrammetry_queue) prevents heavy photogrammetry runs from blocking fast GIS raster operations."
          />
        </div>
      </div>

      {/* Row 2: Live Task Progress & Terminal */}
      <div className="card-base p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm text-slate-900">Active Task: WebODM-Task-4829</span>
              <StatusBadge status="PROCESSING" />
            </div>
            <p className="text-xs text-slate-500 mt-0.5">Stage: {currentStage}</p>
          </div>
          <div className="flex items-center gap-2">
            <button className="btn-secondary text-xs text-rose-600 border-rose-200 hover:bg-rose-50">
              <XCircle className="w-3.5 h-3.5 text-rose-500" />
              <span>Cancel Job</span>
            </button>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-medium text-slate-600">
            <span>Overall Task Progress</span>
            <span>{progress}% (Elapsed: 18m 42s | Remaining: ~9m)</span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden">
            <div
              className="bg-emerald-600 h-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Monospace Log Terminal */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
            <span className="flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5 text-slate-500" />
              <span>Real-Time Diagnostic Log Feed</span>
            </span>
            <span className="text-[11px] font-mono text-slate-400">stdout | Auto-Scroll Enabled</span>
          </div>
          <div className="bg-slate-900 text-slate-200 p-4 rounded-xl font-mono text-xs h-60 overflow-y-auto space-y-1 shadow-inner border border-slate-800">
            {simulatedLogs.map((log, idx) => (
              <div key={idx} className="leading-relaxed hover:bg-slate-800/50 px-1 rounded transition-colors">
                <span className="text-emerald-400">{log.slice(0, 21)}</span>
                <span className="text-slate-300">{log.slice(21)}</span>
              </div>
            ))}
            <div className="flex items-center gap-2 text-emerald-400 pt-2 font-bold animate-pulse">
              <span>&gt; Processing point cloud tiles...</span>
            </div>
          </div>
        </div>
      </div>

      {/* Row 3: Generated Artifacts Ledger */}
      <div className="card-base p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Generated Photogrammetry Deliverables</h2>
            <p className="text-xs text-slate-500">Stitched orthomosaics and surface models available for registration.</p>
          </div>
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
            2 Products Ready
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border border-slate-200 rounded-lg overflow-hidden">
            <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-4">Artifact Name</th>
                <th className="py-2.5 px-4">Spatial Format</th>
                <th className="py-2.5 px-4">Resolution (GSD)</th>
                <th className="py-2.5 px-4">File Size</th>
                <th className="py-2.5 px-4">Storage Container</th>
                <th className="py-2.5 px-4 text-right">Registration Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              <tr className="hover:bg-slate-50/60 transition-colors">
                <td className="py-3 px-4 font-bold text-slate-900 flex items-center gap-2">
                  <FileCheck className="w-4 h-4 text-emerald-600" />
                  <span>orthophoto_micasense_5band.tif</span>
                </td>
                <td className="py-3 px-4 font-mono">GeoTIFF (EPSG:32632)</td>
                <td className="py-3 px-4 font-mono">2.4 cm/px</td>
                <td className="py-3 px-4">1.8 GB</td>
                <td className="py-3 px-4 font-mono text-slate-500">azure://surveys/101/ortho/</td>
                <td className="py-3 px-4 text-right">
                  <Link
                    href="/admin/algorithms"
                    className="btn-primary text-xs py-1 px-3"
                  >
                    <span>Register &amp; Open in Page 3</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </td>
              </tr>

              <tr className="hover:bg-slate-50/60 transition-colors">
                <td className="py-3 px-4 font-bold text-slate-900 flex items-center gap-2">
                  <FileCheck className="w-4 h-4 text-blue-600" />
                  <span>digital_surface_model_dsm.tif</span>
                </td>
                <td className="py-3 px-4 font-mono">GeoTIFF (Elevation)</td>
                <td className="py-3 px-4 font-mono">5.0 cm/px</td>
                <td className="py-3 px-4">640 MB</td>
                <td className="py-3 px-4 font-mono text-slate-500">azure://surveys/101/dsm/</td>
                <td className="py-3 px-4 text-right">
                  <span className="badge-done">Archived in Azure</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
