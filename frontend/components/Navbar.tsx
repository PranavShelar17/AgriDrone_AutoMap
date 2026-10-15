"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
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
  LogOut,
  LogIn,
  User,
} from "lucide-react";

export function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, isAuthenticated, logout, isFarmer } = useAuth();

  const allNavItems = [
    { label: "1. Ingestion", href: "/admin/dashboard", icon: UploadCloud, adminOnly: true },
    { label: "2. WebODM", href: "/admin/photogrammetry", icon: Layers, adminOnly: true },
    { label: "3. Algorithms", href: "/admin/algorithms", icon: Sliders, adminOnly: true },
    { label: "4. Farmer Portal", href: "/portal/surveys", icon: MapPin, adminOnly: false },
    { label: "5. Diagnostics", href: "/portal/diagnostics", icon: BarChart3, adminOnly: false },
  ];

  // If logged in as Farmer, only display Farmer-accessible pages
  const visibleNavItems = isFarmer
    ? allNavItems.filter((item) => !item.adminOnly)
    : allNavItems;

  return (
    <>
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Brand Logo & Title */}
            <div className="flex items-center gap-3">
              <Link
                href={isFarmer ? "/portal/surveys" : "/admin/dashboard"}
                className="flex items-center gap-2.5 text-slate-900 group"
              >
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
                {visibleNavItems.map((item) => {
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

            {/* Right Status Pill & User Controls */}
            <div className="flex items-center gap-3">
              {/* NodeODM Status Pill */}
              <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-xs font-medium text-emerald-800">
                <span className="w-2 h-2 rounded-full bg-emerald-500 pulse-active" />
                <span className="font-semibold text-[11px]">NodeODM Online</span>
              </div>

              {/* User Authentication Profile & Actions */}
              {isAuthenticated && user ? (
                <div className="flex items-center gap-3 border-l border-slate-200 pl-3">
                  <div className="hidden sm:block text-right">
                    <span className="text-xs font-semibold text-slate-800 block leading-none truncate max-w-[140px]">
                      {user.full_name}
                    </span>
                    <span
                      className={`text-[10px] font-semibold tracking-wider uppercase px-1.5 py-0.2 rounded border inline-block mt-0.5 ${
                        user.role === "ADMIN"
                          ? "text-emerald-700 bg-emerald-50 border-emerald-200"
                          : "text-blue-700 bg-blue-50 border-blue-200"
                      }`}
                    >
                      {user.role === "ADMIN" ? "Admin Operator" : "Farmer Account"}
                    </span>
                  </div>

                  <button
                    onClick={() => logout()}
                    title="Sign Out"
                    className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-600 hover:text-rose-700 hover:bg-rose-50 border border-slate-200 hover:border-rose-200 transition-colors"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">Logout</span>
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2 border-l border-slate-200 pl-3">
                  <Link
                    href="/login"
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 shadow-xs transition-colors"
                  >
                    <LogIn className="w-3.5 h-3.5" />
                    <span>Sign In</span>
                  </Link>
                </div>
              )}

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

        {/* Phase 9 Status Banner */}
        <div className="bg-emerald-800 text-white text-[11px] font-medium py-1 px-4 text-center tracking-wide flex items-center justify-center gap-2">
          <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
          <span className="truncate">
            {isAuthenticated
              ? user?.role === "ADMIN"
                ? "PHASE 9 — Authenticated as System Administrator (Full Administrative Access)"
                : `PHASE 9 — Secure Farmer Portal Session (${user?.full_name} • Isolated Access)`
              : "AgriDrone AutoMap — Precision Agricultural Drone Mapping & Geospatial Platform"}
          </span>
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

              {/* Authenticated user indicator for mobile */}
              {isAuthenticated && user && (
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 text-slate-500" />
                    <span className="text-xs font-semibold text-slate-800 truncate">
                      {user.full_name}
                    </span>
                  </div>
                  <span
                    className={`text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded border inline-block mt-1 ${
                      user.role === "ADMIN"
                        ? "text-emerald-700 bg-emerald-50 border-emerald-200"
                        : "text-blue-700 bg-blue-50 border-blue-200"
                    }`}
                  >
                    {user.role}
                  </span>
                </div>
              )}

              <nav className="space-y-1.5">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block px-2 mb-2">
                  {isFarmer ? "Farmer Navigation" : "Platform Modules"}
                </span>
                {visibleNavItems.map((item) => {
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

            <div className="pt-4 border-t border-slate-200 text-xs text-slate-500 space-y-3">
              {isAuthenticated ? (
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    logout();
                  }}
                  className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-medium text-rose-700 bg-rose-50 border border-rose-200 hover:bg-rose-100 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Sign Out</span>
                </button>
              ) : (
                <Link
                  href="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 transition-colors"
                >
                  <LogIn className="w-4 h-4" />
                  <span>Sign In</span>
                </Link>
              )}
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500 pulse-active" />
                <span className="font-semibold text-slate-700">NodeODM: Online</span>
              </div>
              <p className="text-[11px] text-slate-400">AgriDrone AutoMap v0.9.0 (Phase 9)</p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
