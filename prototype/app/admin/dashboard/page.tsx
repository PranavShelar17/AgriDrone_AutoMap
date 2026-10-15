"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  UploadCloud,
  FolderUp,
  FileUp,
  Sprout,
  Calendar,
  Camera,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  FileImage,
  ArrowRight,
  Info,
  ShieldCheck,
  Plus,
  Sliders,
  Layers,
} from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import { AlertBanner } from "@/components/AlertBanner";

export default function IngestionPage() {
  const [uploadMode, setUploadMode] = useState<"raw_photos" | "geotiff">("raw_photos");
  const [selectedFarm, setSelectedFarm] = useState("GreenValley Farms");
  const [selectedField, setSelectedField] = useState("North Pivot 4 (Corn, 32.4 ha)");
  const [flightDate, setFlightDate] = useState("2026-10-14");
  const [sensorModel, setSensorModel] = useState("MicaSense RedEdge-P (5-Band Multispectral)");
  const [flightAltitude, setFlightAltitude] = useState(80);

  // Upload simulation state
  const [isSimulatingUpload, setIsSimulatingUpload] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [validationCompleted, setValidationCompleted] = useState(true);

  const handleSimulateUpload = () => {
    setIsSimulatingUpload(true);
    setUploadProgress(0);
    setValidationCompleted(false);

    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsSimulatingUpload(false);
          setValidationCompleted(true);
          return 100;
        }
        return prev + 25;
      });
    }, 400);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 mb-1">
            <span>Page 1 of 5</span>
            <span>&bull;</span>
            <span className="text-emerald-700 font-bold">Admin Dashboard</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Drone Image Ingestion & Survey Management
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Create surveys, upload raw aerial photo batches or pre-stitched GeoTIFFs, and validate spatial eligibility.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/admin/photogrammetry"
            className="btn-primary text-xs"
          >
            <span>Proceed to WebODM</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Row 1: Hierarchy Setup & Pre-Flight Validation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Card 1: Spatial Hierarchy Selector */}
        <div className="card-base p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2 font-semibold text-sm text-slate-800">
              <Sprout className="w-4 h-4 text-emerald-600" />
              <span>Spatial Hierarchy & Flight Setup</span>
            </div>
            <button className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 flex items-center gap-1">
              <Plus className="w-3.5 h-3.5" />
              <span>New Farm</span>
            </button>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Target Farm</label>
              <select
                value={selectedFarm}
                onChange={(e) => setSelectedFarm(e.target.value)}
                className="input-base w-full text-xs"
              >
                <option>GreenValley Farms (Tenant ID: 12)</option>
                <option>Highland Prairie Estates (Tenant ID: 12)</option>
                <option>Baramati Agri Hub (Tenant ID: 12)</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Field Boundary (PostGIS Polygon)</label>
              <select
                value={selectedField}
                onChange={(e) => setSelectedField(e.target.value)}
                className="input-base w-full text-xs"
              >
                <option>North Pivot 4 (Corn, 32.4 ha)</option>
                <option>South Orchard Sector B (Grapes, 14.8 ha)</option>
                <option>East Pasture 1 (Alfalfa, 22.0 ha)</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Flight Date</label>
                <input
                  type="date"
                  value={flightDate}
                  onChange={(e) => setFlightDate(e.target.value)}
                  className="input-base w-full text-xs"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Flight Altitude</label>
                <input
                  type="number"
                  value={flightAltitude}
                  onChange={(e) => setFlightAltitude(Number(e.target.value))}
                  className="input-base w-full text-xs"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Camera Sensor Configuration</label>
              <select
                value={sensorModel}
                onChange={(e) => setSensorModel(e.target.value)}
                className="input-base w-full text-xs"
              >
                <option>MicaSense RedEdge-P (5-Band Multispectral)</option>
                <option>DJI Phantom 4 Multispectral (5-Band + DLS)</option>
                <option>DJI Mavic 3 Enterprise (Standard RGB Only)</option>
                <option>Sentera 6X Multispectral Sensor</option>
              </select>
            </div>
          </div>
        </div>

        {/* Card 2: Pre-Flight Validation Results Card */}
        <div className="card-base p-6 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-3">
              <div className="flex items-center gap-2 font-semibold text-sm text-slate-800">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Pre-Flight Metadata Extraction</span>
              </div>
              <span className="text-[11px] font-semibold text-slate-400">GDAL / ExifTool</span>
            </div>

            {validationCompleted ? (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                    <span className="text-[11px] text-slate-500 font-medium block">Target CRS</span>
                    <strong className="text-xs text-slate-900 font-mono">EPSG:32632 (UTM 32N)</strong>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                    <span className="text-[11px] text-slate-500 font-medium block">Ground Resolution</span>
                    <strong className="text-xs text-slate-900 font-mono">2.4 cm / pixel</strong>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                    <span className="text-[11px] text-slate-500 font-medium block">Bands Detected</span>
                    <strong className="text-xs text-slate-900 font-mono">5 Spectral Channels</strong>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                    <span className="text-[11px] text-slate-500 font-medium block">Geotag Rate</span>
                    <strong className="text-xs text-emerald-700 font-mono">98.4% (342/348 GPS)</strong>
                  </div>
                </div>

                <div className="p-3.5 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-between">
                  <div>
                    <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider block">
                      Ingestion Eligibility Decision
                    </span>
                    <span className="text-xs font-semibold text-emerald-900">
                      ELIGIBLE FOR WEBODM PHOTOGRAMMETRY
                    </span>
                  </div>
                  <StatusBadge status="ELIGIBLE" />
                </div>
              </div>
            ) : (
              <div className="h-44 flex flex-col items-center justify-center text-center p-4">
                <Loader2 className="w-6 h-6 text-emerald-600 animate-spin mb-2" />
                <span className="text-xs font-semibold text-slate-700">Validating Raster Headers...</span>
                <span className="text-[11px] text-slate-400 mt-1">Verifying projection, dimensions & EXIF tags</span>
              </div>
            )}
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>Storage: <strong className="text-slate-700 font-mono">agridrone-storage (Azure Private)</strong></span>
            <span>Auth: Verified</span>
          </div>
        </div>
      </div>

      {/* Row 2: Dual-Mode Upload Dropzone Card */}
      <div className="card-base p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <UploadCloud className="w-5 h-5 text-emerald-600" />
            <h2 className="text-sm font-bold text-slate-900">Upload Aerial Survey Data</h2>
          </div>
          {/* Mode Selector */}
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200">
            <button
              onClick={() => setUploadMode("raw_photos")}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                uploadMode === "raw_photos"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Mode A: Raw Drone Photos (Batch)
            </button>
            <button
              onClick={() => setUploadMode("geotiff")}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                uploadMode === "geotiff"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Mode B: Pre-Stitched GeoTIFF Raster
            </button>
          </div>
        </div>

        {/* Dropzone Container */}
        <div className="border-2 border-dashed border-slate-300 rounded-xl bg-slate-50/50 hover:bg-slate-50 p-8 text-center transition-colors">
          <div className="max-w-md mx-auto space-y-3">
            <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-800">
                {uploadMode === "raw_photos"
                  ? "Drag and drop raw survey photography files here"
                  : "Drag and drop your pre-stitched orthomosaic GeoTIFF here"}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                {uploadMode === "raw_photos"
                  ? "Supported formats: .jpg, .dng, .tif, .tiff with EXIF GPS tags (Max 25 GB / 1,000 photos)"
                  : "Supported formats: .tif, .tiff (GeoTIFF with valid CRS & Affine Transform, Max 10 GB)"}
              </p>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
              <button
                onClick={handleSimulateUpload}
                disabled={isSimulatingUpload}
                className="btn-primary text-xs"
              >
                {isSimulatingUpload ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Uploading Chunks ({uploadProgress}%)...</span>
                  </>
                ) : (
                  <>
                    <FolderUp className="w-3.5 h-3.5" />
                    <span>Browse &amp; Upload Flight Files</span>
                  </>
                )}
              </button>
              <button className="btn-secondary text-xs">
                <span>Direct Azure Blob Streaming</span>
              </button>
            </div>

            {isSimulatingUpload && (
              <div className="space-y-1.5 pt-4">
                <div className="flex justify-between text-xs font-medium text-slate-600">
                  <span>Uploading to Azure Blob Storage container...</span>
                  <span>{uploadProgress}% (18.4 MB/s)</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-emerald-600 h-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        <AlertBanner
          type="info"
          message="Notice: Pre-stitched GeoTIFF rasters with valid CRS and band mappings bypass WebODM photogrammetry (Page 2) and proceed directly to Algorithm Multi-Map Generation (Page 3)."
        />
      </div>

      {/* Row 3: Dataset Ingestion & Eligibility Ledger */}
      <div className="card-base p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Survey Ingestion &amp; Eligibility Ledger</h2>
            <p className="text-xs text-slate-500">Record of uploaded aerial survey datasets and their verified processing routes.</p>
          </div>
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
            3 Records
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border border-slate-200 rounded-lg overflow-hidden">
            <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-4">Survey ID</th>
                <th className="py-2.5 px-4">Field Name</th>
                <th className="py-2.5 px-4">Flight Date</th>
                <th className="py-2.5 px-4">Files / Size</th>
                <th className="py-2.5 px-4">Dataset Type</th>
                <th className="py-2.5 px-4">Eligibility Status</th>
                <th className="py-2.5 px-4 text-right">Recommended Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              <tr className="hover:bg-slate-50/60 transition-colors">
                <td className="py-3 px-4 font-bold text-slate-900">SURV-2026-101</td>
                <td className="py-3 px-4">North Pivot 4</td>
                <td className="py-3 px-4">2026-10-14</td>
                <td className="py-3 px-4">348 files / 4.2 GB</td>
                <td className="py-3 px-4 font-mono">Raw MS (5-Band)</td>
                <td className="py-3 px-4">
                  <span className="badge-done">Eligible WebODM</span>
                </td>
                <td className="py-3 px-4 text-right">
                  <Link
                    href="/admin/photogrammetry"
                    className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 hover:text-emerald-800"
                  >
                    <span>Send to WebODM</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </td>
              </tr>

              <tr className="hover:bg-slate-50/60 transition-colors">
                <td className="py-3 px-4 font-bold text-slate-900">SURV-2026-098</td>
                <td className="py-3 px-4">South Orchard B</td>
                <td className="py-3 px-4">2026-10-12</td>
                <td className="py-3 px-4">1 file / 1.8 GB</td>
                <td className="py-3 px-4 font-mono">Pre-Stitched GeoTIFF</td>
                <td className="py-3 px-4">
                  <span className="badge-done">Direct GIS</span>
                </td>
                <td className="py-3 px-4 text-right">
                  <Link
                    href="/admin/algorithms"
                    className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 hover:text-blue-800"
                  >
                    <span>Direct to Algorithms</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </td>
              </tr>

              <tr className="hover:bg-slate-50/60 transition-colors">
                <td className="py-3 px-4 font-bold text-slate-900">SURV-2026-084</td>
                <td className="py-3 px-4">East Pasture 1</td>
                <td className="py-3 px-4">2026-10-08</td>
                <td className="py-3 px-4">120 files / 1.4 GB</td>
                <td className="py-3 px-4 font-mono">Raw RGB Photos</td>
                <td className="py-3 px-4">
                  <span className="badge-queued">WebODM Completed</span>
                </td>
                <td className="py-3 px-4 text-right">
                  <Link
                    href="/portal/surveys"
                    className="inline-flex items-center gap-1 text-xs font-semibold text-slate-700 hover:text-slate-900"
                  >
                    <span>View Map in Portal</span>
                    <ArrowRight className="w-3.5 h-3.5" />
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
