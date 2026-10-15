"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  BarChart3,
  Download,
  AlertTriangle,
  Info,
  CheckCircle2,
  FileText,
  Loader2,
  Layers,
  ArrowRight,
  ShieldAlert,
  Printer,
  Sparkles,
} from "lucide-react";
import { AlertBanner } from "@/components/AlertBanner";
import { StatusBadge } from "@/components/StatusBadge";

export default function DiagnosticsPage() {
  const [selectedSurvey, setSelectedSurvey] = useState("SURV-2026-101 (North Pivot 4 - 2026-10-14)");
  const [selectedIndex, setSelectedIndex] = useState("NDVI");

  // PDF report options
  const [includeHistogram, setIncludeHistogram] = useState(true);
  const [includeThumbnail, setIncludeThumbnail] = useState(true);
  const [includeNotes, setIncludeNotes] = useState(true);
  const [agronomistNotes, setAgronomistNotes] = useState(
    "Field demonstrated healthy, uniform canopy development across North Pivot. A localized zone of reduced vigor (1.1 ha) in the south-west quadrant warrants ground inspection for potential irrigation nozzle clogging or soil compaction."
  );

  // PDF generation simulation
  const [isCompilingPdf, setIsCompilingPdf] = useState(false);
  const [pdfReady, setPdfReady] = useState(true);

  const handleCompilePdf = () => {
    setIsCompilingPdf(true);
    setPdfReady(false);
    setTimeout(() => {
      setIsCompilingPdf(false);
      setPdfReady(true);
    }, 1500);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 mb-1">
            <span>Page 5 of 5</span>
            <span>&bull;</span>
            <span className="text-emerald-700 font-bold">Agronomic Diagnostics</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Diagnostics &amp; Actionable Insights
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Transparent, pixel-level statistical metrics, canopy zoning distributions, data limitations, and ReportLab PDF compilation.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/portal/surveys"
            className="btn-secondary text-xs"
          >
            <span>Back to Map Viewer</span>
          </Link>
          <button
            onClick={handleCompilePdf}
            disabled={isCompilingPdf}
            className="btn-primary text-xs"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>{isCompilingPdf ? "Compiling PDF..." : "Compile Verified PDF"}</span>
          </button>
        </div>
      </div>

      {/* Row 1: KPI Statistical Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <div className="card-base p-5 space-y-1">
          <span className="text-xs font-semibold text-slate-500 block">Mean Index Value</span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900 font-mono">0.64</span>
            <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded">
              High Vigor
            </span>
          </div>
          <p className="text-[11px] text-slate-400">Normal distribution across canopy</p>
        </div>

        {/* Metric 2 */}
        <div className="card-base p-5 space-y-1">
          <span className="text-xs font-semibold text-slate-500 block">Median Value</span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900 font-mono">0.68</span>
            <span className="text-xs font-semibold text-slate-400">50th Percentile</span>
          </div>
          <p className="text-[11px] text-slate-400">Robust against edge outliers</p>
        </div>

        {/* Metric 3 */}
        <div className="card-base p-5 space-y-1">
          <span className="text-xs font-semibold text-slate-500 block">Standard Deviation</span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900 font-mono">&plusmn; 0.14</span>
            <span className="text-xs font-medium text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded">
              Moderate
            </span>
          </div>
          <p className="text-[11px] text-slate-400">Spatial canopy variability index</p>
        </div>

        {/* Metric 4 */}
        <div className="card-base p-5 space-y-1">
          <span className="text-xs font-semibold text-slate-500 block">Total Mapped Field Area</span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900 font-mono">32.4</span>
            <span className="text-xs font-semibold text-slate-600">Hectares</span>
          </div>
          <p className="text-[11px] text-emerald-600 font-medium">100% Valid (0% Cloud Mask)</p>
        </div>
      </div>

      {/* Row 2: Zonal Canopy Health Breakdown + Field Limitations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Card 1: Zonal Canopy Distribution Breakdown */}
        <div className="card-base p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-emerald-600" />
              <h2 className="text-sm font-bold text-slate-900">Zonal Vegetation Health Distribution</h2>
            </div>
            <span className="text-xs font-semibold text-slate-500">Clipped to PostGIS Polygon</span>
          </div>

          {/* Stacked Visual Bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs font-semibold text-slate-700">
              <span>Canopy Vigor Composition</span>
              <span>32.4 ha Total</span>
            </div>
            <div className="w-full h-6 rounded-lg overflow-hidden flex shadow-inner border border-slate-200">
              <div style={{ width: "56.2%" }} className="bg-[#1b5e20]" title="Dense Canopy: 56.2%" />
              <div style={{ width: "28.1%" }} className="bg-[#4caf50]" title="Moderate Vigor: 28.1%" />
              <div style={{ width: "9.9%" }} className="bg-[#ffeb3b]" title="Transitional: 9.9%" />
              <div style={{ width: "3.4%" }} className="bg-[#ff9800]" title="Low Vigor: 3.4%" />
              <div style={{ width: "2.4%" }} className="bg-[#d32f2f]" title="Bare Soil: 2.4%" />
            </div>
          </div>

          {/* Table Breakdown */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border border-slate-200 rounded-lg overflow-hidden">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-2 px-3">Canopy Class</th>
                  <th className="py-2 px-3">Index Interval</th>
                  <th className="py-2 px-3">Area (Hectares)</th>
                  <th className="py-2 px-3 text-right">% of Field</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                <tr>
                  <td className="py-2 px-3 font-semibold flex items-center gap-2">
                    <span className="w-3 h-3 rounded-xs bg-[#1b5e20]" />
                    <span>Dense Canopy Vigour</span>
                  </td>
                  <td className="py-2 px-3 font-mono">&gt; 0.65</td>
                  <td className="py-2 px-3 font-mono font-bold text-slate-900">18.2 ha</td>
                  <td className="py-2 px-3 font-mono text-right text-emerald-700 font-bold">56.2%</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold flex items-center gap-2">
                    <span className="w-3 h-3 rounded-xs bg-[#4caf50]" />
                    <span>Moderate Canopy</span>
                  </td>
                  <td className="py-2 px-3 font-mono">0.45 &ndash; 0.65</td>
                  <td className="py-2 px-3 font-mono font-bold text-slate-900">9.1 ha</td>
                  <td className="py-2 px-3 font-mono text-right font-bold">28.1%</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold flex items-center gap-2">
                    <span className="w-3 h-3 rounded-xs bg-[#ffeb3b]" />
                    <span>Transitional / Sparse</span>
                  </td>
                  <td className="py-2 px-3 font-mono">0.30 &ndash; 0.45</td>
                  <td className="py-2 px-3 font-mono font-bold text-slate-900">3.2 ha</td>
                  <td className="py-2 px-3 font-mono text-right font-bold">9.9%</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold flex items-center gap-2">
                    <span className="w-3 h-3 rounded-xs bg-[#ff9800]" />
                    <span>Stressed / Low Biomass</span>
                  </td>
                  <td className="py-2 px-3 font-mono">0.15 &ndash; 0.30</td>
                  <td className="py-2 px-3 font-mono font-bold text-slate-900">1.1 ha</td>
                  <td className="py-2 px-3 font-mono text-right text-amber-700 font-bold">3.4%</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold flex items-center gap-2">
                    <span className="w-3 h-3 rounded-xs bg-[#d32f2f]" />
                    <span>Bare Ground / Water</span>
                  </td>
                  <td className="py-2 px-3 font-mono">&lt; 0.15</td>
                  <td className="py-2 px-3 font-mono font-bold text-slate-900">0.8 ha</td>
                  <td className="py-2 px-3 font-mono text-right text-rose-700 font-bold">2.4%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Card 2: Field Limitation Disclosures & Agronomic Safeguards */}
        <div className="card-base p-6 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-3">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-amber-600" />
                <h2 className="text-sm font-bold text-slate-900">Data Limitations &amp; Quality Notes</h2>
              </div>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
                Ground Scouting Required
              </span>
            </div>

            <div className="space-y-3 text-xs text-slate-600 leading-relaxed">
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                <span className="font-bold text-slate-800 block">Radiometric Calibration Status:</span>
                <p>
                  Calculated from <strong>Calibrated Surface Reflectance</strong> (calibrated via downwelling light
                  sensor and reflectance panel in WebODM). Results can be reliably compared against historical flights.
                </p>
              </div>

              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                <span className="font-bold text-slate-800 block">Solar Zenith &amp; Atmospheric Conditions:</span>
                <p>Flight executed at 12:45 PM solar noon. Solar elevation: 54.2&deg;. Zero cloud shadow artifacts detected.</p>
              </div>
            </div>
          </div>

          {/* Mandatory Agronomic Disclaimer Callout */}
          <AlertBanner
            type="warning"
            title="Agronomic Disclaimer (Scientific & Legal Boundary)"
            message="Vegetation index maps measure relative optical reflectance across canopy surfaces. An index reduction does NOT constitute a diagnosis of specific plant pathogens, fungal diseases, nematode infestations, or yield forecasts. Physical ground inspection is mandatory prior to taking corrective chemical or irrigation action."
          />
        </div>
      </div>

      {/* Row 3: ReportLab PDF Compilation Card */}
      <div className="card-base p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900">ReportLab PDF Report Generation</h2>
            <p className="text-xs text-slate-500">
              Compile an official, publication-ready PDF summary document with field statistics, histograms, and notes.
            </p>
          </div>
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
            ReportLab 4.x Engine
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Agronomist Field Observations (Included in Official PDF)
              </label>
              <textarea
                rows={3}
                value={agronomistNotes}
                onChange={(e) => setAgronomistNotes(e.target.value)}
                className="input-base w-full text-xs"
              />
            </div>

            <div className="flex flex-wrap items-center gap-6 text-xs">
              <label className="flex items-center gap-2 cursor-pointer font-medium text-slate-700">
                <input
                  type="checkbox"
                  checked={includeHistogram}
                  onChange={(e) => setIncludeHistogram(e.target.checked)}
                  className="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500"
                />
                <span>Include Value Histogram Chart</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer font-medium text-slate-700">
                <input
                  type="checkbox"
                  checked={includeThumbnail}
                  onChange={(e) => setIncludeThumbnail(e.target.checked)}
                  className="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500"
                />
                <span>Include True Color RGB Overview Thumbnail</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer font-medium text-slate-700">
                <input
                  type="checkbox"
                  checked={includeNotes}
                  onChange={(e) => setIncludeNotes(e.target.checked)}
                  className="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500"
                />
                <span>Include Agronomist Field Notes</span>
              </label>
            </div>

            <div>
              <button
                onClick={handleCompilePdf}
                disabled={isCompilingPdf}
                className="btn-primary text-xs"
              >
                {isCompilingPdf ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Assembling Vector Charts &amp; Formatting PDF...</span>
                  </>
                ) : (
                  <>
                    <FileText className="w-3.5 h-3.5" />
                    <span>Compile Official PDF Report</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Download Box */}
          <div className="card-base p-4 bg-slate-50 border-slate-200 flex flex-col justify-between">
            <div className="space-y-2">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                Latest Compiled Document
              </span>
              <div className="flex items-center gap-2 text-xs font-bold text-slate-900">
                <FileText className="w-4 h-4 text-emerald-600" />
                <span>SurveyReport_SURV-101_20261014.pdf</span>
              </div>
              <p className="text-[11px] text-slate-500 font-mono">
                Size: 2.4 MB | Timestamp: 2026-10-14 13:05 UTC
              </p>
            </div>

            <div className="pt-4">
              <button className="btn-secondary w-full text-xs justify-center py-2">
                <Download className="w-3.5 h-3.5 text-slate-600" />
                <span>Download via Signed Azure SAS</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
