"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Sprout,
  UploadCloud,
  Layers,
  Sliders,
  MapPin,
  BarChart3,
  Menu,
  X,
  ShieldCheck,
} from "lucide-react";

export function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { label: "1. Ingestion", href: "/admin/dashboard", icon: UploadCloud },
    { label: "2. WebODM", href: "/admin/photogrammetry", icon: Layers },
    { label: "3. Algorithms", href: "/admin/algorithms", icon: Sliders },
    { label: "4. Farmer Portal", href: "/portal/surveys", icon: MapPin },
    { label: "5. Diagnostics", href: "/portal/diagnostics", icon: BarChart3 },
  ];

  return (
    <>
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Brand Logo & Title */}
            <div className="flex items-center gap-3">
              <Link href="/admin/dashboard" className="flex items-center gap-2.5 text-slate-900 group">
                <div className="w-9 h-9 rounded-lg text-white flex items-center justify-center shadow-sm shrink-0 bg-emerald-600">
                  <Sprout className="w-5 h-5" />
                </div>
                <div>
                  <span className="font-bold tracking-tight text-base text-slate-900 block leading-tight">
                    AgriDrone AutoMap
                  </span>
                  <span className="text-[10px] font-semibold text-emerald-700 uppercase tracking-wider block">
                    Precision Mapping Platform
                  </span>
                </div>
              </Link>

              {/* Desktop Nav Items */}
              <nav className="hidden lg:flex items-center gap-1 ml-6">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                        isActive
                          ? "bg-emerald-50 text-emerald-800 border border-emerald-200 shadow-xs"
                          : "text-slate-600 hover:text-slate-900 hover:bg-slate-50 border border-transparent"
                      }`}
                    >
                      <Icon className={`w-3.5 h-3.5 ${isActive ? "text-emerald-600" : "text-slate-400"}`} />
                      {item.label}
                    </Link>
                  );
                })}
              </nav>
            </div>

            {/* Right Status Pill & User */}
            <div className="flex items-center gap-3">
              {/* NodeODM Status Pill */}
              <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-xs font-medium text-emerald-800">
                <span className="w-2 h-2 rounded-full bg-emerald-500 pulse-active" />
                <span className="font-semibold text-[11px]">NodeODM Online</span>
              </div>

              {/* User Role Indicator */}
              <div className="hidden sm:flex items-center gap-2 border-l border-slate-200 pl-3">
                <div className="text-right">
                  <span className="text-xs font-semibold text-slate-800 block leading-none">
                    Admin Operator
                  </span>
                  <span className="text-[10px] font-medium tracking-wider uppercase text-emerald-700 bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-200 inline-block mt-0.5">
                    Tenant ID: 12
                  </span>
                </div>
              </div>

              {/* Mobile Hamburger Toggle */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="lg:hidden p-2 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-100"
                aria-label="Toggle Navigation"
              >
                {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>

        {/* Prototype Banner Notification */}
        <div className="bg-emerald-700 text-white text-[11px] font-medium py-1 px-4 text-center tracking-wide flex items-center justify-center gap-2">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>PHASE 2 VISUAL PROTOTYPE — 5-Page Reference Design Review (Mock Data Only)</span>
        </div>
      </header>

      {/* Mobile Navigation Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex justify-end">
          <div className="w-72 bg-white h-full shadow-2xl p-6 flex flex-col justify-between">
            <div className="space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-slate-200">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center">
                    <Sprout className="w-4 h-4" />
                  </div>
                  <span className="font-bold text-sm text-slate-900">AgriDrone AutoMap</span>
                </div>
                <button
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-1.5 text-slate-400 hover:text-slate-600 rounded-md"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <nav className="space-y-1.5">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block px-2 mb-2">
                  Five Core Functional Pages
                </span>
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                        isActive
                          ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                          : "text-slate-600 hover:bg-slate-50"
                      }`}
                    >
                      <Icon className={`w-4 h-4 ${isActive ? "text-emerald-600" : "text-slate-400"}`} />
                      {item.label}
                    </Link>
                  );
                })}
              </nav>
            </div>

            <div className="pt-4 border-t border-slate-200 text-xs text-slate-500">
              <div className="flex items-center gap-2 mb-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500 pulse-active" />
                <span className="font-semibold text-slate-700">NodeODM: Online</span>
              </div>
              <p className="text-[11px] text-slate-400">AgriDrone AutoMap v0.2.0 (Phase 2)</p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
