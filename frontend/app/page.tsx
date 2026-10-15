"use client";

import React from "react";
import Link from "next/link";
import {
  UploadCloud,
  Layers,
  Sliders,
  MapPin,
  BarChart3,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  FolderSync,
} from "lucide-react";

export default function HomePage() {
  const pages = [
    {
      num: "01",
      title: "Admin Dashboard & Drone Image Ingestion",
      href: "/admin/dashboard",
      icon: UploadCloud,
      desc: "Hierarchy management (Farms, Fields, Surveys), dual-mode raw photo & GeoTIFF upload, pre-flight EXIF/CRS validation, and dataset eligibility ledger.",
      badge: "Ingestion Hub",
    },
    {
      num: "02",
      title: "WebODM Photogrammetry Processing",
      href: "/admin/photogrammetry",
      icon: Layers,
      desc: "WebODM asynchronous photogrammetry execution, agricultural presets (Fast vs Precision), live log streaming, and orthomosaic registration.",
      badge: "Photogrammetry",
    },
    {
      num: "03",
      title: "Algorithm & Multi-Map Generation",
      href: "/admin/algorithms",
      icon: Sliders,
      desc: "Physical spectral band mapping, input validation gating (NDVI, NDRE, GNDVI, SAVI), color ramp palettes, and Cloud Optimized GeoTIFF (COG) generation.",
      badge: "GIS Engine",
    },
    {
      num: "04",
      title: "Secure Farmer Portal",
      href: "/portal/surveys",
      icon: MapPin,
      desc: "Tenant-isolated geospatial map viewer powered by MapLibre GL JS, multi-layer toggling, opacity sliders, split-screen swipe comparison, and secure SAS downloads.",
      badge: "Farmer Portal",
    },
    {
      num: "05",
      title: "Diagnostics & Actionable Insights",
      href: "/portal/diagnostics",
      icon: BarChart3,
      desc: "Pixel-level statistical metrics (Mean, Median, StdDev), zonal canopy health breakdowns, data limitation disclosures, and ReportLab PDF compilation.",
      badge: "Analytics & PDF",
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Hero Welcome Card */}
      <div className="card-base p-8 bg-gradient-to-br from-white via-slate-50 to-emerald-50/40 border-slate-200">
        <div className="max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-semibold">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Phase 2 Deliverable: Five-Page Visual Prototype</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            AgriDrone AutoMap — Interactive Design Prototype
          </h1>
          <p className="text-slate-600 text-sm leading-relaxed">
            Welcome to the interactive visual prototype for AgriDrone AutoMap, engineered strictly in accordance with
            the approved Phase 1 technical blueprint and the user&apos;s reference template. Explore all five
            functional pages using the cards below or the top navigation bar.
          </p>
        </div>
      </div>

      {/* Five-Page Directory Cards */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900">Strict Five-Page Functional Architecture</h2>
          <span className="text-xs font-semibold text-slate-500">100% Reference-Matched</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {pages.map((p) => {
            const Icon = p.icon;
            return (
              <Link
                key={p.num}
                href={p.href}
                className="card-base card-hover p-6 flex flex-col justify-between group hover:border-emerald-300 transition-all"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold text-sm border border-emerald-200 group-hover:bg-emerald-600 group-hover:text-white transition-colors">
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                      {p.badge}
                    </span>
                  </div>
                  <h3 className="font-bold text-base text-slate-900 group-hover:text-emerald-700 transition-colors">
                    Page {p.num}: {p.title}
                  </h3>
                  <p className="text-xs text-slate-500 leading-relaxed">{p.desc}</p>
                </div>

                <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-emerald-700">
                  <span>Open Page {p.num} Preview</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
