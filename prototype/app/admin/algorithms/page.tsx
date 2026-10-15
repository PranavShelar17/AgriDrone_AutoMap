"use client";

import React, { useState } from "react";
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
} from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import { AlertBanner } from "@/components/AlertBanner";

interface BandMappingItem {
  bandIndex: number;
  detectedName: string;
  wavelength: string;
  role: "blue" | "green" | "red" | "red_edge" | "nir" | "thermal" | "none";
}

export default function AlgorithmsPage() {
  const [selectedOrtho, setSelectedOrtho] = useState("orthophoto_micasense_5band.tif (SURV-101)");
  const [colorPalette, setColorPalette] = useState("rdylgn");
  const [clampMin, setClampMin] = useState(-0.2);
  const [clampMax, setClampMax] = useState(0.85);

  // Band Mappings State
  const [bands, setBands] = useState<BandMappingItem[]>([
    { bandIndex: 1, detectedName: "Band 1 (Blue)", wavelength: "475 nm", role: "blue" },
    { bandIndex: 2, detectedName: "Band 2 (Green)", wavelength: "560 nm", role: "green" },
    { bandIndex: 3, detectedName: "Band 3 (Red)", wavelength: "668 nm", role: "red" },
    { bandIndex: 4, detectedName: "Band 4 (RedEdge)", wavelength: "717 nm", role: "red_edge" },
    { bandIndex: 5, detectedName: "Band 5 (NIR)", wavelength: "840 nm", role: "nir" },
  ]);

  // Selected Algorithms
  const [ndviSelected, setNdviSelected] = useState(true);
  const [ndreSelected, setNdreSelected] = useState(true);
  const [gndviSelected, setGndviSelected] = useState(false);
  const [saviSelected, setSaviSelected] = useState(true);
  const [saviLFactor, setSaviLFactor] = useState(0.5);

  // Simulation State
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationComplete, setGenerationComplete] = useState(true);

  // Derived spectral gating
  const hasNIR = bands.some((b) => b.role === "nir");
  const hasRed = bands.some((b) => b.role === "red");
  const hasGreen = bands.some((b) => b.role === "green");
  const hasRedEdge = bands.some((b) => b.role === "red_edge");

  const canComputeNDVI = hasNIR && hasRed;
  const canComputeNDRE = hasNIR && hasRedEdge;
  const canComputeGNDVI = hasNIR && hasGreen;
  const canComputeSAVI = hasNIR && hasRed;

  const handleRoleChange = (bandIndex: number, newRole: BandMappingItem["role"]) => {
    setBands((prev) =>
      prev.map((b) => (b.bandIndex === bandIndex ? { ...b, role: newRole } : b))
    );
  };

  const handleSimulateCalculation = () => {
    setIsGenerating(true);
    setGenerationComplete(false);
    setTimeout(() => {
      setIsGenerating(false);
      setGenerationComplete(true);
    }, 1500);
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
          <Link
            href="/portal/surveys"
            className="btn-primary text-xs"
          >
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
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
            5 Channels Verified
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <label className="text-xs font-semibold text-slate-700 block mb-1">Select Registered Orthomosaic</label>
            <select
              value={selectedOrtho}
              onChange={(e) => setSelectedOrtho(e.target.value)}
              className="input-base w-full text-xs"
            >
              <option>orthophoto_micasense_5band.tif (SURV-101, WebODM Ingestion - 5 Bands)</option>
              <option>pre_stitched_field12_ortho.tif (SURV-098, Direct Ingestion - 5 Bands)</option>
              <option>rgb_flight_mavic3.tif (SURV-084, Standard 3-Band RGB Only)</option>
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">Raster CRS / Projection</label>
            <div className="input-base w-full text-xs bg-slate-50 text-slate-600 font-mono flex items-center justify-between">
              <span>EPSG:32632 (WGS 84 / UTM 32N)</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Row 2: Band Mapping Grid & Scientific Gating Notice */}
      <div className="card-base p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Spectral Band Mapping &amp; Verification Grid</h2>
            <p className="text-xs text-slate-500">
              Drone sensors do not share universal band ordering. Map internal raster channels to physical spectral roles.
            </p>
          </div>
          <button
            onClick={() => {
              // Quick toggle to simulate RGB-only test
              if (hasNIR) {
                setBands([
                  { bandIndex: 1, detectedName: "Band 1", wavelength: "660 nm", role: "red" },
                  { bandIndex: 2, detectedName: "Band 2", wavelength: "560 nm", role: "green" },
                  { bandIndex: 3, detectedName: "Band 3", wavelength: "480 nm", role: "blue" },
                ]);
              } else {
                setBands([
                  { bandIndex: 1, detectedName: "Band 1 (Blue)", wavelength: "475 nm", role: "blue" },
                  { bandIndex: 2, detectedName: "Band 2 (Green)", wavelength: "560 nm", role: "green" },
                  { bandIndex: 3, detectedName: "Band 3 (Red)", wavelength: "668 nm", role: "red" },
                  { bandIndex: 4, detectedName: "Band 4 (RedEdge)", wavelength: "717 nm", role: "red_edge" },
                  { bandIndex: 5, detectedName: "Band 5 (NIR)", wavelength: "840 nm", role: "nir" },
                ]);
              }
            }}
            className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 flex items-center gap-1 border border-emerald-200 px-2 py-1 rounded-md bg-emerald-50"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>{hasNIR ? "Test RGB-Only Mode" : "Reset to 5-Band Multispectral"}</span>
          </button>
        </div>

        {/* Band Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border border-slate-200 rounded-lg overflow-hidden">
            <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-4">Raster Channel</th>
                <th className="py-2.5 px-4">Sensor Metadata</th>
                <th className="py-2.5 px-4">Nominal Wavelength</th>
                <th className="py-2.5 px-4">Assigned Spectral Role</th>
                <th className="py-2.5 px-4 text-right">Verification</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {bands.map((b) => (
                <tr key={b.bandIndex} className="hover:bg-slate-50/60 transition-colors">
                  <td className="py-2.5 px-4 font-mono font-bold text-slate-900">
                    Channel #{b.bandIndex}
                  </td>
                  <td className="py-2.5 px-4 font-medium">{b.detectedName}</td>
                  <td className="py-2.5 px-4 font-mono text-slate-500">{b.wavelength}</td>
                  <td className="py-2.5 px-4">
                    <select
                      value={b.role}
                      onChange={(e) =>
                        handleRoleChange(b.bandIndex, e.target.value as BandMappingItem["role"])
                      }
                      className="input-base text-xs py-1 px-2 font-semibold"
                    >
                      <option value="blue">Blue Channel</option>
                      <option value="green">Green Channel</option>
                      <option value="red">Red Channel</option>
                      <option value="red_edge">Red-Edge Channel</option>
                      <option value="nir">Near-Infrared (NIR)</option>
                      <option value="thermal">Thermal Infrared</option>
                      <option value="none">Unassigned / Ignored</option>
                    </select>
                  </td>
                  <td className="py-2.5 px-4 text-right">
                    <span className="badge-done">Role Valid</span>
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
            message="Near-Infrared (NIR) band is NOT assigned. Standard 3-band RGB imagery lacks the physical Near-Infrared reflectance required for genuine NDVI, NDRE, GNDVI, or SAVI calculations. All NIR algorithms are locked."
          />
        ) : (
          <AlertBanner
            type="success"
            message="NIR and Red channels successfully verified. All scientific vegetation index algorithms are unlocked."
          />
        )}
      </div>

      {/* Row 3: Algorithm Selection & Color Styling */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Card 3: Algorithm Gating & Selection Matrix (2 cols) */}
        <div className="card-base p-6 lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-900">Algorithm Selection &amp; Parameters</h2>
            <span className="text-xs font-semibold text-slate-500">Rasterio / NumPy</span>
          </div>

          <div className="space-y-3">
            {/* NDVI Card */}
            <div
              className={`p-4 rounded-xl border flex items-center justify-between transition-all ${
                canComputeNDVI
                  ? "border-slate-200 bg-white"
                  : "border-slate-200 bg-slate-50 opacity-60"
              }`}
            >
              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  id="algo-ndvi"
                  disabled={!canComputeNDVI}
                  checked={ndviSelected && canComputeNDVI}
                  onChange={(e) => setNdviSelected(e.target.checked)}
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
                    General photosynthetic activity and canopy greenness measure.
                  </span>
                </div>
              </div>
              <StatusBadge status={canComputeNDVI ? "ELIGIBLE" : "LOCKED"} />
            </div>

            {/* NDRE Card */}
            <div
              className={`p-4 rounded-xl border flex items-center justify-between transition-all ${
                canComputeNDRE
                  ? "border-slate-200 bg-white"
                  : "border-slate-200 bg-slate-50 opacity-60"
              }`}
            >
              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  id="algo-ndre"
                  disabled={!canComputeNDRE}
                  checked={ndreSelected && canComputeNDRE}
                  onChange={(e) => setNdreSelected(e.target.checked)}
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

            {/* SAVI Card */}
            <div
              className={`p-4 rounded-xl border space-y-3 transition-all ${
                canComputeSAVI
                  ? "border-slate-200 bg-white"
                  : "border-slate-200 bg-slate-50 opacity-60"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    id="algo-savi"
                    disabled={!canComputeSAVI}
                    checked={saviSelected && canComputeSAVI}
                    onChange={(e) => setSaviSelected(e.target.checked)}
                    className="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500 mt-1"
                  />
                  <div>
                    <label htmlFor="algo-savi" className="font-bold text-xs text-slate-900 block">
                      SAVI — Soil Adjusted Vegetation Index
                    </label>
                    <span className="font-mono text-[11px] text-slate-500 block">
                      Formula: ((1 + L) * (NIR - Red)) / (NIR + Red + L)
                    </span>
                    <span className="text-[11px] text-slate-600">
                      Suppresses exposed soil background reflectance in early growth stages.
                    </span>
                  </div>
                </div>
                <StatusBadge status={canComputeSAVI ? "ELIGIBLE" : "LOCKED"} />
              </div>

              {canComputeSAVI && saviSelected && (
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

            <div className="pt-2">
              <button
                onClick={handleSimulateCalculation}
                disabled={isGenerating || !hasNIR}
                className="btn-primary text-xs w-full sm:w-auto"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Executing Rasterio Windowed Computation...</span>
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
          </div>
        </div>
      </div>

      {/* Row 4: Generated Map Layers Catalog */}
      <div className="card-base p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Generated Index Map Layers (Cloud Optimized GeoTIFFs)</h2>
            <p className="text-xs text-slate-500">Single-band 32-bit floating point rasters tiled for high-speed streaming.</p>
          </div>
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
            3 Layers Active
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border border-slate-200 rounded-lg overflow-hidden">
            <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-4">Layer Name</th>
                <th className="py-2.5 px-4">Index Formula</th>
                <th className="py-2.5 px-4">COG Status</th>
                <th className="py-2.5 px-4">Dimensions / Size</th>
                <th className="py-2.5 px-4">Storage URI</th>
                <th className="py-2.5 px-4 text-right">Portal Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              <tr className="hover:bg-slate-50/60 transition-colors">
                <td className="py-3 px-4 font-bold text-slate-900">ndvi_pivot4_20261014.tif</td>
                <td className="py-3 px-4 font-mono text-[11px]">(NIR-Red)/(NIR+Red)</td>
                <td className="py-3 px-4">
                  <span className="badge-done">COG Validated</span>
                </td>
                <td className="py-3 px-4">12400 x 9800 px (320 MB)</td>
                <td className="py-3 px-4 font-mono text-slate-500 text-[10px]">azure://surveys/101/indices/ndvi.tif</td>
                <td className="py-3 px-4 text-right">
                  <Link
                    href="/portal/surveys"
                    className="btn-primary text-xs py-1 px-3"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>View in Map Viewer</span>
                  </Link>
                </td>
              </tr>

              <tr className="hover:bg-slate-50/60 transition-colors">
                <td className="py-3 px-4 font-bold text-slate-900">ndre_pivot4_20261014.tif</td>
                <td className="py-3 px-4 font-mono text-[11px]">(NIR-RE)/(NIR+RE)</td>
                <td className="py-3 px-4">
                  <span className="badge-done">COG Validated</span>
                </td>
                <td className="py-3 px-4">12400 x 9800 px (315 MB)</td>
                <td className="py-3 px-4 font-mono text-slate-500 text-[10px]">azure://surveys/101/indices/ndre.tif</td>
                <td className="py-3 px-4 text-right">
                  <Link
                    href="/portal/diagnostics"
                    className="btn-secondary text-xs py-1 px-3"
                  >
                    <span>View Field Diagnostics</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </td>
              </tr>

              <tr className="hover:bg-slate-50/60 transition-colors">
                <td className="py-3 px-4 font-bold text-slate-900">savi_pivot4_20261014.tif</td>
                <td className="py-3 px-4 font-mono text-[11px]">SAVI (L=0.5)</td>
                <td className="py-3 px-4">
                  <span className="badge-done">COG Validated</span>
                </td>
                <td className="py-3 px-4">12400 x 9800 px (325 MB)</td>
                <td className="py-3 px-4 font-mono text-slate-500 text-[10px]">azure://surveys/101/indices/savi.tif</td>
                <td className="py-3 px-4 text-right">
                  <Link
                    href="/portal/surveys"
                    className="btn-secondary text-xs py-1 px-3"
                  >
                    <span>View in Portal</span>
                  </Link>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
