"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  MapPin,
  Calendar,
  Layers,
  Download,
  Info,
  CheckCircle2,
  Sliders,
  AlertTriangle,
  ArrowRight,
  Shield,
  FileText,
  Lock,
} from "lucide-react";
import { InteractiveMapPreview } from "@/components/InteractiveMapPreview";
import { StatusBadge } from "@/components/StatusBadge";
import { AlertBanner } from "@/components/AlertBanner";

export default function FarmerPortalPage() {
  const [selectedFarm, setSelectedFarm] = useState("GreenValley Farms");
  const [selectedField, setSelectedField] = useState("North Pivot 4 (Corn, 32.4 ha)");
  const [selectedSurveyDate, setSelectedSurveyDate] = useState("2026-10-14");

  // Map Controls State
  const [activeLayer, setActiveLayer] = useState<"ortho" | "ndvi" | "ndre" | "savi">("ndvi");
  const [opacity, setOpacity] = useState(85);
  const [splitMode, setSplitMode] = useState(false);

  // Download simulation
  const [downloadingReport, setDownloadingReport] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  // Prototype state switchers for design review
  const [simulateDenied, setSimulateDenied] = useState(false);

  const handleSimulateDownload = () => {
    setDownloadingReport(true);
    setDownloadSuccess(false);
    setTimeout(() => {
      setDownloadingReport(false);
      setDownloadSuccess(true);
    }, 1200);
  };

  if (simulateDenied) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center space-y-4">
        <div className="w-16 h-16 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto">
          <Lock className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-slate-900">Access Denied: Cross-Tenant Guard Triggered</h2>
        <p className="text-sm text-slate-600 max-w-md mx-auto">
          You do not have authorized permission to view survey rasters for this farm entity. Survey data is strictly
          partitioned by tenant ownership.
        </p>
        <button
          onClick={() => setSimulateDenied(false)}
          className="btn-primary text-xs"
        >
          Return to Authorized Field
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 mb-1">
            <span>Page 4 of 5</span>
            <span>&bull;</span>
            <span className="text-emerald-700 font-bold">Secure Farmer Portal</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Field Map Viewer &amp; Survey Discovery
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Authorized spatial view of your fields, orthomosaic layers, vegetation vigor maps, and verified reports.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setSimulateDenied(true)}
            className="btn-secondary text-xs text-slate-600"
            title="Preview how unauthorized tenant requests are safely rejected"
          >
            <Shield className="w-3.5 h-3.5 text-slate-400" />
            <span>Test Tenant Guard (Denial State)</span>
          </button>
          <Link
            href="/portal/diagnostics"
            className="btn-primary text-xs"
          >
            <span>View Diagnostics (Page 5)</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Row 1: Field Selector & Survey Timeline */}
      <div className="card-base p-4 bg-white flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div>
            <span className="font-semibold text-slate-500 block mb-1">Assigned Farm</span>
            <select
              value={selectedFarm}
              onChange={(e) => setSelectedFarm(e.target.value)}
              className="input-base text-xs font-bold text-slate-900"
            >
              <option>GreenValley Farms</option>
            </select>
          </div>

          <div>
            <span className="font-semibold text-slate-500 block mb-1">Select Field</span>
            <select
              value={selectedField}
              onChange={(e) => setSelectedField(e.target.value)}
              className="input-base text-xs font-bold text-slate-900"
            >
              <option>North Pivot 4 (Corn, 32.4 ha)</option>
              <option>South Orchard Sector B (14.8 ha)</option>
            </select>
          </div>

          <div>
            <span className="font-semibold text-slate-500 block mb-1">Survey Flight Date</span>
            <select
              value={selectedSurveyDate}
              onChange={(e) => setSelectedSurveyDate(e.target.value)}
              className="input-base text-xs font-bold text-emerald-800 bg-emerald-50/50 border-emerald-200"
            >
              <option value="2026-10-14">2026-10-14 (Latest - Corn V6 Stage)</option>
              <option value="2026-09-28">2026-09-28 (Emergence Stage)</option>
            </select>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
            Tenant Isolated: Farmer Account #48
          </span>
        </div>
      </div>

      {/* Row 2: Interactive Map Canvas + Controls Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Main Map Viewer Canvas (3 cols) */}
        <div className="lg:col-span-3">
          <InteractiveMapPreview
            fieldName="North Pivot 4"
            surveyDate={selectedSurveyDate}
            activeLayer={activeLayer}
            onLayerChange={setActiveLayer}
            opacity={opacity}
            onOpacityChange={setOpacity}
            splitMode={splitMode}
            onToggleSplit={() => setSplitMode(!splitMode)}
          />
        </div>

        {/* Sidebar Controls & Legend Panel (1 col) */}
        <div className="card-base p-5 space-y-5 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="border-b border-slate-100 pb-3">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
                Active Layer Selection
              </h2>
              <div className="space-y-1.5 pt-1">
                <label className="flex items-center gap-2.5 text-xs text-slate-800 p-2 rounded-lg hover:bg-slate-50 cursor-pointer">
                  <input
                    type="radio"
                    name="layer-radio"
                    checked={activeLayer === "ortho"}
                    onChange={() => setActiveLayer("ortho")}
                    className="text-emerald-600 focus:ring-emerald-500"
                  />
                  <div>
                    <span className="font-bold block">True Color RGB</span>
                    <span className="text-[10px] text-slate-500">Visual aerial orthomosaic</span>
                  </div>
                </label>

                <label className="flex items-center gap-2.5 text-xs text-slate-800 p-2 rounded-lg hover:bg-slate-50 cursor-pointer">
                  <input
                    type="radio"
                    name="layer-radio"
                    checked={activeLayer === "ndvi"}
                    onChange={() => setActiveLayer("ndvi")}
                    className="text-emerald-600 focus:ring-emerald-500"
                  />
                  <div>
                    <span className="font-bold block text-emerald-800">NDVI Canopy Vigor</span>
                    <span className="text-[10px] text-slate-500">Calibrated greenness &amp; biomass</span>
                  </div>
                </label>

                <label className="flex items-center gap-2.5 text-xs text-slate-800 p-2 rounded-lg hover:bg-slate-50 cursor-pointer">
                  <input
                    type="radio"
                    name="layer-radio"
                    checked={activeLayer === "ndre"}
                    onChange={() => setActiveLayer("ndre")}
                    className="text-emerald-600 focus:ring-emerald-500"
                  />
                  <div>
                    <span className="font-bold block text-blue-800">NDRE Red-Edge Chlorophyll</span>
                    <span className="text-[10px] text-slate-500">Dense canopy nitrogen status</span>
                  </div>
                </label>

                <label className="flex items-center gap-2.5 text-xs text-slate-800 p-2 rounded-lg hover:bg-slate-50 cursor-pointer">
                  <input
                    type="radio"
                    name="layer-radio"
                    checked={activeLayer === "savi"}
                    onChange={() => setActiveLayer("savi")}
                    className="text-emerald-600 focus:ring-emerald-500"
                  />
                  <div>
                    <span className="font-bold block text-amber-800">SAVI Soil Adjusted</span>
                    <span className="text-[10px] text-slate-500">Early crop growth stage (L=0.5)</span>
                  </div>
                </label>
              </div>
            </div>

            {/* Opacity Slider */}
            <div className="space-y-1.5 border-b border-slate-100 pb-4">
              <div className="flex justify-between text-xs font-semibold text-slate-700">
                <span>Layer Opacity</span>
                <span className="font-mono text-emerald-700">{opacity}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="100"
                value={opacity}
                onChange={(e) => setOpacity(Number(e.target.value))}
                className="w-full accent-emerald-600 cursor-pointer"
              />
            </div>

            {/* Scientific Legend */}
            <div className="space-y-2">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Agronomic Color Scale
              </h2>
              <div className="space-y-1.5 text-xs">
                <div className="flex items-center justify-between p-1.5 rounded-md hover:bg-slate-50">
                  <div className="flex items-center gap-2">
                    <span className="w-3.5 h-3.5 rounded-sm bg-[#1b5e20] shrink-0" />
                    <span className="text-slate-800 font-medium">Dense Canopy (&gt; 0.65)</span>
                  </div>
                  <span className="font-mono font-bold text-slate-600">18.2 ha (56%)</span>
                </div>

                <div className="flex items-center justify-between p-1.5 rounded-md hover:bg-slate-50">
                  <div className="flex items-center gap-2">
                    <span className="w-3.5 h-3.5 rounded-sm bg-[#4caf50] shrink-0" />
                    <span className="text-slate-800 font-medium">Moderate Vigor (0.45-65)</span>
                  </div>
                  <span className="font-mono font-bold text-slate-600">9.1 ha (28%)</span>
                </div>

                <div className="flex items-center justify-between p-1.5 rounded-md hover:bg-slate-50">
                  <div className="flex items-center gap-2">
                    <span className="w-3.5 h-3.5 rounded-sm bg-[#ffeb3b] shrink-0" />
                    <span className="text-slate-800 font-medium">Transitional (0.30-45)</span>
                  </div>
                  <span className="font-mono font-bold text-slate-600">3.2 ha (10%)</span>
                </div>

                <div className="flex items-center justify-between p-1.5 rounded-md hover:bg-slate-50">
                  <div className="flex items-center gap-2">
                    <span className="w-3.5 h-3.5 rounded-sm bg-[#ff9800] shrink-0" />
                    <span className="text-slate-800 font-medium">Low Vigor (0.15-30)</span>
                  </div>
                  <span className="font-mono font-bold text-slate-600">1.1 ha (3%)</span>
                </div>

                <div className="flex items-center justify-between p-1.5 rounded-md hover:bg-slate-50">
                  <div className="flex items-center gap-2">
                    <span className="w-3.5 h-3.5 rounded-sm bg-[#d32f2f] shrink-0" />
                    <span className="text-slate-800 font-medium">Bare Ground (&lt; 0.15)</span>
                  </div>
                  <span className="font-mono font-bold text-slate-600">0.8 ha (2%)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Secure Download Drawer */}
          <div className="pt-4 border-t border-slate-100 space-y-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
              Official Deliverables
            </span>
            <button
              onClick={handleSimulateDownload}
              disabled={downloadingReport}
              className="btn-primary w-full text-xs py-2.5"
            >
              <Download className="w-3.5 h-3.5" />
              <span>
                {downloadingReport ? "Generating 15-Min SAS Link..." : "Download Official PDF Report"}
              </span>
            </button>

            {downloadSuccess && (
              <p className="text-[11px] text-emerald-700 bg-emerald-50 border border-emerald-200 p-2 rounded-lg font-medium flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                <span>Signed Azure SAS URL ready (valid 15m)</span>
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
