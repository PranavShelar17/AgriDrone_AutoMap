import "./globals.css";
import React from "react";
import type { Metadata } from "next";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "AgriDrone AutoMap — Precision Mapping Platform",
  description: "Production-grade agricultural drone mapping, photogrammetry, and geospatial analytics.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col bg-slate-50 text-slate-900 antialiased">
        <Navbar />
        <main className="flex-1 w-full">{children}</main>
        <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
          <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
            <span>AgriDrone AutoMap &copy; 2026. All rights reserved.</span>
            <span className="font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              Phase 2: Visual Prototype Review
            </span>
          </div>
        </footer>
      </body>
    </html>
  );
}
