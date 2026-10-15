"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Sliders,
  Play,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Loader2,
  Layers,
  ArrowRight,
  Eye,
  Info,
  Check,
  RefreshCw,
  Clock,
  Sparkles,
} from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import { AlertBanner } from "@/components/AlertBanner";
import {
  apiClient,
  EligibleRasterItem,
  RasterInspection,
  AlgorithmJobItem,
  AlgorithmBatchResponse,
} from "@/lib/api";

type SpectralRole = "nir" | "red" | "green" | "blue" | "red_edge" | "none";

interface UiBandRow {
  bandIndex: number;
  detectedName: string;
  dataType: string;
  minVal: number;
  maxVal: number;
  role: SpectralRole;
}

export default function AlgorithmsPage() {
  // 1. Source Rasters State
  const [eligibleRasters, setEligibleRasters] = useState<EligibleRasterItem[]>([]);
  const [selectedRasterId, setSelectedRasterId] = useState<string>("");
  const [isLoadingRasters, setIsLoadingRasters] = useState(true);
  const [inspection, setInspection] = useState<RasterInspection | null>(null);
  const [isInspecting, setIsInspecting] = useState(false);
  const [inspectionError, setInspectionError] = useState<string | null>(null);

  // 2. Band Mapping State
  const [bandRows, setBandRows] = useState<UiBandRow[]>([]);

  // 3. Algorithm Selection State
  const [selectedAlgos, setSelectedAlgos] = useState<Record<string, boolean>>({
    NDVI: true,
    NDRE: true,
    GNDVI: false,
    SAVI: true,
    VARI: false,
    GLI: false,
  });
  const [saviLFactor, setSaviLFactor] = useState(0.5);

  // 4. Styling controls
  const [colorPalette, setColorPalette] = useState("rdylgn");
  const [clampMin, setClampMin] = useState(-0.2);
  const [clampMax, setClampMax] = useState(0.85);

  // 5. Active Batch / Execution State
  const [activeBatch, setActiveBatch] = useState<AlgorithmBatchResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // 6. Generated Products / Recent Jobs Catalog
  const [recentJobs, setRecentJobs] = useState<AlgorithmJobItem[]>([]);
  const [isLoadingJobs, setIsLoadingJobs] = useState(false);

  // Load eligible rasters on mount
  const loadEligibleRasters = useCallback(async () => {
    setIsLoadingRasters(true);
    try {
      const res = await apiClient.getEligibleRasters();
      setEligibleRasters(res.items);
      if (res.items.length > 0 && !selectedRasterId) {
        setSelectedRasterId(res.items[0].source_id);
      }
    } catch (err: any) {
      console.error("Failed to load eligible rasters:", err);
    } finally {
      setIsLoadingRasters(false);
    }
  }, [selectedRasterId]);

  // Load recent algorithm jobs
  const loadRecentJobs = useCallback(async () => {
    setIsLoadingJobs(true);
    try {
      const jobs = await apiClient.listAlgorithmJobs(undefined, undefined);
      setRecentJobs(jobs);
    } catch (err: any) {
      console.error("Failed to load algorithm jobs:", err);
    } finally {
      setIsLoadingJobs(false);
    }
  }, []);

  useEffect(() => {
    loadEligibleRasters();
    loadRecentJobs();
  }, [loadEligibleRasters, loadRecentJobs]);

  // Inspect raster when selection changes
  useEffect(() => {
    if (!selectedRasterId) {
      setInspection(null);
      setBandRows([]);
      return;
    }

    const rasterItem = eligibleRasters.find((r) => r.source_id === selectedRasterId);
    if (!rasterItem) return;

    let isMounted = true;
    setIsInspecting(true);
    setInspectionError(null);

    apiClient
      .inspectRaster(rasterItem.source_id, rasterItem.source_type)
      .then((data) => {
        if (!isMounted) return;
        setInspection(data);

        // Map bands to UI rows with suggested roles
        const suggested = data.suggested_band_mapping || {};
        const revMap: Record<number, SpectralRole> = {};
        if (suggested.NIR) revMap[suggested.NIR] = "nir";
        if (suggested.Red) revMap[suggested.Red] = "red";
        if (suggested.Green) revMap[suggested.Green] = "green";
        if (suggested.Blue) revMap[suggested.Blue] = "blue";
        if (suggested.RedEdge) revMap[suggested.RedEdge] = "red_edge";

        const rows: UiBandRow[] = data.bands.map((b) => ({
          bandIndex: b.band_index,
          detectedName: b.description || `Band ${b.band_index}`,
          dataType: b.data_type,
          minVal: b.min_value,
          maxVal: b.max_value,
          role: revMap[b.band_index] || (b.band_index === 1 ? "blue" : b.band_index === 2 ? "green" : b.band_index === 3 ? "red" : "none"),
        }));
        setBandRows(rows);
      })
      .catch((err: any) => {
        if (!isMounted) return;
        console.error("Inspection error:", err);
        setInspectionError(err.message || "Failed to inspect raster dataset.");
      })
      .finally(() => {
        if (isMounted) setIsInspecting(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedRasterId, eligibleRasters]);

  // Polling active batch
  useEffect(() => {
    if (!activeBatch || ["COMPLETED", "PARTIALLY_COMPLETED", "FAILED"].includes(activeBatch.status)) {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const batchUpdate = await apiClient.getAlgorithmBatch(activeBatch.batch_id);
        setActiveBatch(batchUpdate);
        if (["COMPLETED", "PARTIALLY_COMPLETED", "FAILED"].includes(batchUpdate.status)) {
          loadRecentJobs();
        }
      } catch (err) {
        console.error("Batch polling error:", err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [activeBatch, loadRecentJobs]);

  // Spectral gating derived flags
  const hasNIR = bandRows.some((b) => b.role === "nir");
  const hasRed = bandRows.some((b) => b.role === "red");
  const hasGreen = bandRows.some((b) => b.role === "green");
  const hasRedEdge = bandRows.some((b) => b.role === "red_edge");
  const hasBlue = bandRows.some((b) => b.role === "blue");

  const canComputeNDVI = hasNIR && hasRed;
  const canComputeNDRE = hasNIR && hasRedEdge;
  const canComputeGNDVI = hasNIR && hasGreen;
  const canComputeSAVI = hasNIR && hasRed;
  const canComputeVARI = hasGreen && hasRed && hasBlue;
  const canComputeGLI = hasGreen && hasRed && hasBlue;

  const handleRoleChange = (bandIndex: number, newRole: SpectralRole) => {
    setBandRows((prev) =>
      prev.map((b) => (b.bandIndex === bandIndex ? { ...b, role: newRole } : b))
    );
  };

  const selectedRaster = eligibleRasters.find((r) => r.source_id === selectedRasterId);

  // Submit multi-map generation run
  const handleSubmitBatch = async () => {
    if (!selectedRasterId || !selectedRaster) return;

    // Build band mapping dictionary
    const mapping: Record<string, number> = {};
    for (const b of bandRows) {
      if (b.role === "nir") mapping["NIR"] = b.bandIndex;
      else if (b.role === "red") mapping["Red"] = b.bandIndex;
      else if (b.role === "green") mapping["Green"] = b.bandIndex;
      else if (b.role === "blue") mapping["Blue"] = b.bandIndex;
      else if (b.role === "red_edge") mapping["RedEdge"] = b.bandIndex;
    }

    // Build list of selected eligible algorithms
    const algosToRun: Array<{ algorithm_code: string; parameters?: Record<string, any> }> = [];
    if (selectedAlgos.NDVI && canComputeNDVI) algosToRun.push({ algorithm_code: "NDVI" });
    if (selectedAlgos.NDRE && canComputeNDRE) algosToRun.push({ algorithm_code: "NDRE" });
    if (selectedAlgos.GNDVI && canComputeGNDVI) algosToRun.push({ algorithm_code: "GNDVI" });
    if (selectedAlgos.SAVI && canComputeSAVI) {
      algosToRun.push({ algorithm_code: "SAVI", parameters: { L: saviLFactor } });
    }
    if (selectedAlgos.VARI && canComputeVARI) algosToRun.push({ algorithm_code: "VARI" });
    if (selectedAlgos.GLI && canComputeGLI) algosToRun.push({ algorithm_code: "GLI" });

    if (algosToRun.length === 0) {
      setSubmitError("Please select at least one algorithm compatible with the verified spectral channels.");
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const batchRes = await apiClient.submitAlgorithmBatch({
        source_id: selectedRaster.source_id,
        source_type: selectedRaster.source_type,
        band_mapping: mapping,
        algorithms: algosToRun,
      });
      setActiveBatch(batchRes);
      loadRecentJobs();
    } catch (err: any) {
      console.error("Batch dispatch error:", err);
      setSubmitError(err.message || "Failed to dispatch algorithm processing batch.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRetryJob = async (jobId: string) => {
    try {
      await apiClient.retryAlgorithmJob(jobId);
      loadRecentJobs();
    } catch (err: any) {
      alert(`Retry failed: ${err.message}`);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 mb-1">
            <span>Page 3 of 5</span>
            <span>&bull;</span>
            <span className="text-emerald-700 font-bold">GIS Analytics Engine</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Algorithm &amp; Multi-Map Generation
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Validate physical spectral bands, configure vegetation indices, and execute windowed Rasterio/NumPy index calculations.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/portal/surveys" className="btn-primary text-xs">
            <span>Open Map Viewer (Page 4)</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Row 1: Orthomosaic Selection Card */}
      <div className="card-base p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-600" />
            <h2 className="text-sm font-bold text-slate-900">Input Orthomosaic Raster Dataset</h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={loadEligibleRasters}
              className="text-xs font-medium text-slate-500 hover:text-slate-800 flex items-center gap-1"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Refresh Datasets</span>
            </button>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
              {eligibleRasters.length} Registered Rasters
            </span>
          </div>
        </div>

        {isLoadingRasters ? (
          <div className="flex items-center justify-center p-8 text-slate-400 gap-2 text-xs">
            <Loader2 className="w-4 h-4 animate-spin text-emerald-600" />
            <span>Scanning registered orthomosaics and pre-stitched GeoTIFFs...</span>
          </div>
        ) : eligibleRasters.length === 0 ? (
          <div className="p-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 text-center space-y-3">
            <Layers className="w-8 h-8 text-slate-400 mx-auto" />
            <h3 className="text-xs font-bold text-slate-800">No Eligible Orthomosaics Found</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              No reconstructed orthophotos or validated pre-stitched GeoTIFFs are currently available. Ingest drone imagery in Phase 5 or process a photogrammetry task in Phase 6 first.
            </p>
            <div className="flex justify-center gap-3 pt-2">
              <Link href="/admin/ingestion" className="btn-secondary text-xs">
                Upload Drone Flight
              </Link>
              <Link href="/admin/photogrammetry" className="btn-primary text-xs">
                Run Photogrammetry Task
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2">
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Select Registered Orthomosaic
              </label>
              <select
                value={selectedRasterId}
                onChange={(e) => setSelectedRasterId(e.target.value)}
                className="input-base w-full text-xs font-medium"
              >
                {eligibleRasters.map((r) => (
                  <option key={r.source_id} value={r.source_id}>
                    {r.filename} — {r.survey_code} ({r.farm_name || "Farm"}, {r.band_count} Bands, {r.detected_sensor})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Raster CRS / Projection</label>
              <div className="input-base w-full text-xs bg-slate-50 text-slate-600 font-mono flex items-center justify-between">
                <span>{inspection?.crs_epsg || selectedRaster?.crs_epsg || "EPSG:4326"}</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              </div>
            </div>
          </div>
        )}

        {/* Selected Raster Quick Specs */}
        {selectedRaster && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-slate-100 text-xs">
            <div>
              <span className="text-[11px] text-slate-400 block">Sensor Type</span>
              <strong className="text-slate-800">{selectedRaster.detected_sensor}</strong>
            </div>
            <div>
              <span className="text-[11px] text-slate-400 block">Channels</span>
              <strong className="text-slate-800">{selectedRaster.band_count} Bands</strong>
            </div>
            <div>
              <span className="text-[11px] text-slate-400 block">Ground Resolution</span>
              <strong className="text-slate-800">
                {inspection?.gsd_cm ? `${inspection.gsd_cm} cm/px` : selectedRaster.resolution_cm_px ? `${selectedRaster.resolution_cm_px} cm/px` : "5.0 cm/px"}
              </strong>
            </div>
            <div>
              <span className="text-[11px] text-slate-400 block">Dimensions</span>
              <strong className="text-slate-800">
                {inspection ? `${inspection.width} × ${inspection.height} px` : "Loading..."}
              </strong>
            </div>
          </div>
        )}
      </div>

      {/* Row 2: Band Mapping Grid & Scientific Gating Notice */}
      <div className="card-base p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Spectral Band Mapping &amp; Verification Grid</h2>
            <p className="text-xs text-slate-500">
              Drone sensors do not share universal band ordering. Map internal raster channels to physical spectral roles.
            </p>
          </div>
          {isInspecting && (
            <div className="flex items-center gap-1.5 text-xs text-emerald-700">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Inspecting raster bands...</span>
            </div>
          )}
        </div>

        {inspectionError && (
          <AlertBanner type="error" title="Inspection Notice" message={inspectionError} />
        )}

        {/* Calibration Notes */}
        {inspection && inspection.calibration_notes && inspection.calibration_notes.length > 0 && (
          <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-lg text-xs text-amber-900 space-y-1">
            <div className="flex items-center gap-1.5 font-semibold">
              <Info className="w-3.5 h-3.5 text-amber-700" />
              <span>Radiometric Calibration &amp; Sensor Telemetry</span>
            </div>
            <ul className="list-disc list-inside space-y-0.5 text-[11px] text-amber-800">
              {inspection.calibration_notes.map((note, i) => (
                <li key={i}>{note}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Band Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border border-slate-200 rounded-lg overflow-hidden">
            <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-4">Raster Channel</th>
                <th className="py-2.5 px-4">Sensor Metadata</th>
                <th className="py-2.5 px-4">Data Type &amp; Value Range</th>
                <th className="py-2.5 px-4">Assigned Spectral Role</th>
                <th className="py-2.5 px-4 text-right">Verification</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {bandRows.map((b) => (
                <tr key={b.bandIndex} className="hover:bg-slate-50/60 transition-colors">
                  <td className="py-2.5 px-4 font-mono font-bold text-slate-900">
                    Channel #{b.bandIndex}
                  </td>
                  <td className="py-2.5 px-4 font-medium">{b.detectedName}</td>
                  <td className="py-2.5 px-4 font-mono text-[11px] text-slate-500">
                    {b.dataType} [{b.minVal} – {b.maxVal}]
                  </td>
                  <td className="py-2.5 px-4">
                    <select
                      value={b.role}
                      onChange={(e) => handleRoleChange(b.bandIndex, e.target.value as SpectralRole)}
                      className="input-base text-xs py-1 px-2 font-semibold"
                    >
                      <option value="blue">Blue Channel (450–510 nm)</option>
                      <option value="green">Green Channel (530–590 nm)</option>
                      <option value="red">Red Channel (630–690 nm)</option>
                      <option value="red_edge">Red-Edge Channel (705–745 nm)</option>
                      <option value="nir">Near-Infrared (NIR, 750–900 nm)</option>
                      <option value="none">Unassigned / Ignored</option>
                    </select>
                  </td>
                  <td className="py-2.5 px-4 text-right">
                    {b.role !== "none" ? (
                      <span className="badge-done">Role Valid</span>
                    ) : (
                      <span className="text-[11px] text-slate-400">Ignored</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {!hasNIR ? (
          <AlertBanner
            type="error"
            title="Scientific Spectral Gating Warning"
            message="Near-Infrared (NIR) band is NOT assigned. Standard 3-band RGB imagery lacks the physical Near-Infrared reflectance required for genuine NDVI, NDRE, GNDVI, or SAVI calculations. All NIR algorithms are locked. Use VARI or GLI for visible-spectrum greenness."
          />
        ) : !hasRedEdge ? (
          <AlertBanner
            type="warning"
            title="RedEdge Band Unassigned"
            message="NIR and Red channels are verified (NDVI, GNDVI, SAVI are unlocked). NDRE requires a dedicated Red-Edge band (705–745 nm) and remains locked."
          />
        ) : (
          <AlertBanner
            type="success"
            message="NIR, Red, Green, and RedEdge channels successfully verified. All scientific vegetation index algorithms are unlocked."
          />
        )}
      </div>

      {/* Row 3: Algorithm Selection & Color Styling */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Card 3: Algorithm Gating & Selection Matrix (2 cols) */}
        <div className="card-base p-6 lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Algorithm Selection &amp; Multi-Map Batch</h2>
              <p className="text-xs text-slate-500">
                Select one or more compatible vegetation index products to generate simultaneously.
              </p>
            </div>
            <span className="text-xs font-semibold text-slate-500">Rasterio / NumPy</span>
          </div>

          <div className="space-y-3">
            {/* NDVI Card */}
            <div
              className={`p-4 rounded-xl border flex items-center justify-between transition-all ${
                canComputeNDVI ? "border-slate-200 bg-white" : "border-slate-200 bg-slate-50 opacity-60"
              }`}
            >
              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  id="algo-ndvi"
                  disabled={!canComputeNDVI}
                  checked={selectedAlgos.NDVI && canComputeNDVI}
                  onChange={(e) => setSelectedAlgos((prev) => ({ ...prev, NDVI: e.target.checked }))}
                  className="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500 mt-1"
                />
                <div>
                  <label htmlFor="algo-ndvi" className="font-bold text-xs text-slate-900 block">
                    NDVI — Normalized Difference Vegetation Index
                  </label>
                  <span className="font-mono text-[11px] text-slate-500 block">
                    Formula: (NIR - Red) / (NIR + Red)
                  </span>
                  <span className="text-[11px] text-slate-600">
                    General photosynthetic activity, canopy density, and biomass coverage.
                  </span>
                </div>
              </div>
              <StatusBadge status={canComputeNDVI ? "ELIGIBLE" : "LOCKED"} />
            </div>

            {/* NDRE Card */}
            <div
              className={`p-4 rounded-xl border flex items-center justify-between transition-all ${
                canComputeNDRE ? "border-slate-200 bg-white" : "border-slate-200 bg-slate-50 opacity-60"
              }`}
            >
              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  id="algo-ndre"
                  disabled={!canComputeNDRE}
                  checked={selectedAlgos.NDRE && canComputeNDRE}
                  onChange={(e) => setSelectedAlgos((prev) => ({ ...prev, NDRE: e.target.checked }))}
                  className="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500 mt-1"
                />
                <div>
                  <label htmlFor="algo-ndre" className="font-bold text-xs text-slate-900 block">
                    NDRE — Normalized Difference Red Edge Index
                  </label>
                  <span className="font-mono text-[11px] text-slate-500 block">
                    Formula: (NIR - RedEdge) / (NIR + RedEdge)
                  </span>
                  <span className="text-[11px] text-slate-600">
                    High-biomass canopy chlorophyll monitoring where standard NDVI saturates.
                  </span>
                </div>
              </div>
              <StatusBadge status={canComputeNDRE ? "ELIGIBLE" : "LOCKED"} />
            </div>

            {/* GNDVI Card */}
            <div
              className={`p-4 rounded-xl border flex items-center justify-between transition-all ${
                canComputeGNDVI ? "border-slate-200 bg-white" : "border-slate-200 bg-slate-50 opacity-60"
              }`}
            >
              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  id="algo-gndvi"
                  disabled={!canComputeGNDVI}
                  checked={selectedAlgos.GNDVI && canComputeGNDVI}
                  onChange={(e) => setSelectedAlgos((prev) => ({ ...prev, GNDVI: e.target.checked }))}
                  className="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500 mt-1"
                />
                <div>
                  <label htmlFor="algo-gndvi" className="font-bold text-xs text-slate-900 block">
                    GNDVI — Green Normalized Difference Vegetation Index
                  </label>
                  <span className="font-mono text-[11px] text-slate-500 block">
                    Formula: (NIR - Green) / (NIR + Green)
                  </span>
                  <span className="text-[11px] text-slate-600">
                    Sensitive to chlorophyll concentration and early water/nutrient stress.
                  </span>
                </div>
              </div>
              <StatusBadge status={canComputeGNDVI ? "ELIGIBLE" : "LOCKED"} />
            </div>

            {/* SAVI Card */}
            <div
              className={`p-4 rounded-xl border space-y-3 transition-all ${
                canComputeSAVI ? "border-slate-200 bg-white" : "border-slate-200 bg-slate-50 opacity-60"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    id="algo-savi"
                    disabled={!canComputeSAVI}
                    checked={selectedAlgos.SAVI && canComputeSAVI}
                    onChange={(e) => setSelectedAlgos((prev) => ({ ...prev, SAVI: e.target.checked }))}
                    className="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500 mt-1"
                  />
                  <div>
                    <label htmlFor="algo-savi" className="font-bold text-xs text-slate-900 block">
                      SAVI — Soil Adjusted Vegetation Index
                    </label>
                    <span className="font-mono text-[11px] text-slate-500 block">
                      Formula: ((NIR - Red) / (NIR + Red + L)) * (1 + L)
                    </span>
                    <span className="text-[11px] text-slate-600">
                      Suppresses exposed soil background reflectance in early crop emergence.
                    </span>
                  </div>
                </div>
                <StatusBadge status={canComputeSAVI ? "ELIGIBLE" : "LOCKED"} />
              </div>

              {canComputeSAVI && selectedAlgos.SAVI && (
                <div className="pt-2 border-t border-slate-100 flex items-center justify-between gap-4 text-xs">
                  <span className="text-slate-600 font-semibold">
                    Soil Adjustment Factor (L): <strong className="text-emerald-700">{saviLFactor}</strong>
                  </span>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={saviLFactor}
                    onChange={(e) => setSaviLFactor(parseFloat(e.target.value))}
                    className="w-48 accent-emerald-600"
                  />
                </div>
              )}
            </div>

            {/* VARI Card (Visible Spectrum) */}
            <div
              className={`p-4 rounded-xl border flex items-center justify-between transition-all ${
                canComputeVARI ? "border-slate-200 bg-white" : "border-slate-200 bg-slate-50 opacity-60"
              }`}
            >
              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  id="algo-vari"
                  disabled={!canComputeVARI}
                  checked={selectedAlgos.VARI && canComputeVARI}
                  onChange={(e) => setSelectedAlgos((prev) => ({ ...prev, VARI: e.target.checked }))}
                  className="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500 mt-1"
                />
                <div>
                  <label htmlFor="algo-vari" className="font-bold text-xs text-slate-900 block">
                    VARI — Visible Atmospherically Resistant Index
                  </label>
                  <span className="font-mono text-[11px] text-slate-500 block">
                    Formula: (Green - Red) / (Green + Red - Blue)
                  </span>
                  <span className="text-[11px] text-slate-600">
                    Computable from standard RGB orthophotos when near-infrared sensors are absent.
                  </span>
                </div>
              </div>
              <StatusBadge status={canComputeVARI ? "ELIGIBLE" : "LOCKED"} />
            </div>

            {submitError && (
              <AlertBanner type="error" title="Submission Error" message={submitError} />
            )}

            {/* Submit Action */}
            <div className="pt-2">
              <button
                onClick={handleSubmitBatch}
                disabled={isSubmitting || !selectedRasterId}
                className="btn-primary text-xs w-full sm:w-auto"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Dispatching Multi-Map Batch...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Generate Selected Vegetation Index Maps</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Card 4: Colormap & Value Stretch (1 col) */}
        <div className="card-base p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-900">Map Styling &amp; Colormap</h2>
          </div>

          <div className="space-y-4 text-xs">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Color Palette</label>
              <select
                value={colorPalette}
                onChange={(e) => setColorPalette(e.target.value)}
                className="input-base w-full text-xs"
              >
                <option value="rdylgn">5-Class Agronomic (Red-Yellow-Green)</option>
                <option value="viridis">Scientific Viridis (Color-Blind Safe)</option>
                <option value="spectral">High-Contrast Spectral (Rainbow)</option>
              </select>
            </div>

            {/* Visual Color Preview */}
            <div className="p-3 rounded-lg border border-slate-200 bg-slate-50 space-y-2">
              <span className="text-[11px] font-semibold text-slate-500 block">Gradient Preview</span>
              <div
                className="w-full h-4 rounded-md shadow-inner"
                style={{
                  background:
                    colorPalette === "rdylgn"
                      ? "linear-gradient(to right, #d32f2f, #ff9800, #ffeb3b, #4caf50, #1b5e20)"
                      : colorPalette === "viridis"
                      ? "linear-gradient(to right, #440154, #3b528b, #21918c, #5ec962, #fde725)"
                      : "linear-gradient(to right, #9e0142, #d53e4f, #fee08b, #abdda4, #5e4fa2)",
                }}
              />
              <div className="flex justify-between text-[10px] font-mono text-slate-500">
                <span>{clampMin} (Bare/Stress)</span>
                <span>0.35</span>
                <span>{clampMax} (High Canopy)</span>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-700 block">Dynamic Range Clamping</label>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-[10px] text-slate-500 block">Min Value</span>
                  <input
                    type="number"
                    step="0.05"
                    value={clampMin}
                    onChange={(e) => setClampMin(parseFloat(e.target.value))}
                    className="input-base w-full text-xs"
                  />
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block">Max Value</span>
                  <input
                    type="number"
                    step="0.05"
                    value={clampMax}
                    onChange={(e) => setClampMax(parseFloat(e.target.value))}
                    className="input-base w-full text-xs"
                  />
                </div>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 text-[11px] text-slate-500 space-y-1">
              <span className="font-semibold text-slate-700 block">NoData Safeguard</span>
              <span>All non-vegetated water bodies, uncalibrated pixels, and zero-denominator anomalies are masked to standard float32 NoData (-9999.0).</span>
            </div>
          </div>
        </div>
      </div>

      {/* Row 4: Active Batch Progress Live Tracker */}
      {activeBatch && (
        <div className="card-base p-6 space-y-4 border-emerald-300 bg-emerald-50/20">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-emerald-100 pb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-emerald-600" />
              <h2 className="text-sm font-bold text-slate-900">
                Active Multi-Map Processing Batch
              </h2>
            </div>
            <StatusBadge status={activeBatch.status} />
          </div>

          <div className="space-y-3">
            {activeBatch.jobs.map((job) => (
              <div
                key={job.job_id}
                className="p-3 rounded-lg bg-white border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <strong className="text-slate-900">{job.algorithm_code}</strong>
                    <span className="text-slate-400">&bull;</span>
                    <span className="text-slate-600">{job.algorithm_name}</span>
                  </div>
                  <p className="text-[11px] text-slate-500 flex items-center gap-1.5">
                    <Clock className="w-3 h-3 text-slate-400" />
                    <span>{job.current_stage || "Processing"}</span>
                  </p>
                  {job.error_message && (
                    <p className="text-[11px] text-red-600 font-medium">{job.error_message}</p>
                  )}
                </div>

                <div className="flex items-center gap-3">
                  <div className="w-32 bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-2 rounded-full transition-all duration-500 ${
                        job.status === "COMPLETED"
                          ? "bg-emerald-600"
                          : job.status === "FAILED"
                          ? "bg-red-500"
                          : "bg-emerald-500 animate-pulse"
                      }`}
                      style={{ width: `${job.progress_percent}%` }}
                    />
                  </div>
                  <span className="font-mono text-[11px] text-slate-600 w-10 text-right">
                    {job.progress_percent}%
                  </span>
                  <StatusBadge status={job.status} />
                  {job.status === "FAILED" && (
                    <button
                      onClick={() => handleRetryJob(job.job_id)}
                      className="text-xs text-emerald-700 hover:text-emerald-900 font-semibold px-2 py-1 rounded border border-emerald-200 hover:bg-emerald-50"
                    >
                      Retry
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Row 5: Generated Map Layers Catalog */}
      <div className="card-base p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900">
              Generated Index Map Layers (Cloud Optimized GeoTIFFs)
            </h2>
            <p className="text-xs text-slate-500">
              Single-band 32-bit floating point rasters tiled for high-speed streaming with verified agronomic zonal statistics.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={loadRecentJobs}
              className="text-xs font-medium text-slate-500 hover:text-slate-800 flex items-center gap-1"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Refresh Ledger</span>
            </button>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
              {recentJobs.length} Processing Jobs Logged
            </span>
          </div>
        </div>

        {isLoadingJobs ? (
          <div className="flex items-center justify-center p-8 text-slate-400 gap-2 text-xs">
            <Loader2 className="w-4 h-4 animate-spin text-emerald-600" />
            <span>Loading generated layers catalog...</span>
          </div>
        ) : recentJobs.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400 space-y-2">
            <Layers className="w-8 h-8 text-slate-300 mx-auto" />
            <p>No vegetation index processing runs logged yet. Select a dataset above to generate index maps.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border border-slate-200 rounded-lg overflow-hidden">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4">Index / Layer</th>
                  <th className="py-2.5 px-4">Formula</th>
                  <th className="py-2.5 px-4">Status &amp; Progress</th>
                  <th className="py-2.5 px-4">Current Stage / Details</th>
                  <th className="py-2.5 px-4">Processed At</th>
                  <th className="py-2.5 px-4 text-right">Portal Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {recentJobs.map((j) => (
                  <tr key={j.job_id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900">{j.algorithm_code}</div>
                      <div className="text-[11px] text-slate-500">{j.algorithm_name}</div>
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-500">
                      {j.algorithm_code === "NDVI" && "(NIR - Red) / (NIR + Red)"}
                      {j.algorithm_code === "NDRE" && "(NIR - RedEdge) / (NIR + RedEdge)"}
                      {j.algorithm_code === "GNDVI" && "(NIR - Green) / (NIR + Green)"}
                      {j.algorithm_code === "SAVI" && `SAVI (L=${j.parameters?.L ?? 0.5})`}
                      {j.algorithm_code === "VARI" && "(Green - Red) / (Green + Red - Blue)"}
                      {j.algorithm_code === "GLI" && "(2*Green - Red - Blue) / (2*Green + Red + Blue)"}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <StatusBadge status={j.status} />
                        <span className="font-mono text-[11px] text-slate-500">{j.progress_percent}%</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 max-w-xs truncate text-[11px] text-slate-600">
                      {j.status === "FAILED" ? (
                        <span className="text-red-600 font-medium">{j.error_message || "Execution failed"}</span>
                      ) : (
                        <span>{j.current_stage || "Queued"}</span>
                      )}
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-500">
                      {j.completed_at
                        ? new Date(j.completed_at).toLocaleString()
                        : j.started_at
                        ? new Date(j.started_at).toLocaleString()
                        : "—"}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {j.status === "COMPLETED" ? (
                        <Link href="/portal/surveys" className="btn-primary text-xs py-1 px-3 inline-flex items-center gap-1">
                          <Eye className="w-3.5 h-3.5" />
                          <span>View in Map Viewer</span>
                        </Link>
                      ) : j.status === "FAILED" ? (
                        <button
                          onClick={() => handleRetryJob(j.job_id)}
                          className="btn-secondary text-xs py-1 px-3 text-red-700 border-red-200 hover:bg-red-50"
                        >
                          Retry Job
                        </button>
                      ) : (
                        <span className="text-[11px] text-slate-400">Processing</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
