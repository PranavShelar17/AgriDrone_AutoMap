# AgriDrone AutoMap — Reference Template Analysis

## 1. Executive Summary & Inspected Reference Artifacts

In strict compliance with the Phase 2 requirements, a thorough inspection of the project workspace and local reference assets was conducted. The following actual reference assets were located, inspected, and analyzed on the local system:

1. **Source Reference Archives**:
   - `C:\Users\Admin\Downloads\drone-main.zip` (323 KB)
   - `C:\Users\Admin\Downloads\drone-main (1).zip` (323 KB)
2. **Extracted Reference Implementation**:
   - `C:\Users\Admin\Desktop\agridron\drone-main (1)\drone-main\frontend\`
     - Next.js 16.3.8 (App Router), React 19.2.8, Tailwind CSS v4 (`@tailwindcss/postcss: ^4`), TypeScript 5.
     - Lucide React icons (`lucide-react: ^1.49.0`), Leaflet GIS viewer (`leaflet: ^1.9.4`).
3. **Advanced Operational Codebase**:
   - `C:\Users\Admin\Desktop\dron\frontend\`
     - Next.js App Router, Tailwind CSS, customized agricultural color palettes, modular UI components (`components/ui`, `components/layout`, `components/map`).

Both reference codebases were analyzed to extract the design language, layout patterns, component structure, color tokens, and typography to serve as the **authoritative design baseline** for AgriDrone AutoMap.

---

## 2. Overall Page Layout & Structure

### A. Layout Archetype
The reference template utilizes a **Clean Agricultural Utility Dashboard** archetype characterized by:
- A **Sticky Top Navigation Header** (`h-16`, `sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-slate-200`) providing universal access to primary sections.
- An organic off-white/slate canvas background (`--bg-main: #f8fafc;`) that provides gentle contrast against pure white card surfaces (`#ffffff`).
- Centered container layouts constrained to a maximum width of `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8`, ensuring balanced information density on ultra-wide monitors without edge stretching.
- Clean 12px rounded cards with 1px subtle borders (`border-slate-200` / `#e2e8f0`) and soft, natural drop shadows (`box-shadow: 0 1px 3px 0 rgba(0,0,0,0.04)`).

### B. Header & Navigation Structure
- **Left**: Brand lockup featuring a rounded square icon box (`w-9 h-9 rounded-lg`) housing an agricultural glyph (`Sprout` icon) with an emerald/forest background, flanked by primary platform title ("Dronepipe" / "AgriDrone AutoMap") and an uppercase tracking subtitle ("PRECISION MAPPING").
- **Center**: Horizontal navigation link cluster (`hidden md:flex items-center gap-1 ml-8`). Active link state features a soft slate fill (`bg-slate-100 text-slate-900`) and emerald accent icon; inactive links use muted text (`text-slate-600 hover:text-slate-900 hover:bg-slate-50`).
- **Right Utility Area**:
  - **Live Service Status Pill**: e.g., "NodeODM Online" (`bg-emerald-50 text-emerald-800 border-emerald-200` with an animated pulsing dot `pulse-active`) or "NodeODM Offline" (`bg-rose-50 text-rose-800 border-rose-200`).
  - **User Profile & Role Pill**: User display name with an uppercase role badge (`text-[10px] tracking-wider uppercase text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200`).
  - **Logout / Session Control**: Subtle icon button with hover transitions.

---

## 3. Visual Identity, Color System & Typography

### A. Color Palette Tokens
Extracted directly from `globals.css` and `tailwind.config.ts` across the reference codebases:

| Token Name | Hex Code | Reference Role & Usage |
| :--- | :--- | :--- |
| `--primary` | `#059669` | Emerald 600: Primary actions, brand icons, active tabs, focus rings. |
| `--primary-hover` | `#047857` | Emerald 700: Button hover states, active menu borders. |
| `--primary-light` | `#ecfdf5` | Emerald 50: Pill badge backgrounds, success banners, selected card fills. |
| `--brand-dark` | `#1B4D3E` | Deep Forest Green: High-contrast headings, dark mode borders, key brand marks. |
| `--bg-main` | `#f8fafc` | Slate 50: Page canvas background. |
| `--bg-card` | `#ffffff` | Pure White: Card, panel, and modal background surfaces. |
| `--border-subtle` | `#e2e8f0` | Slate 200: Default card, table row, and divider borders. |
| `--border-strong` | `#cbd5e1` | Slate 300: Form input borders, hover states, card dividers. |
| `--text-primary` | `#0f172a` | Slate 900: Primary headings, metric labels, high-emphasis text. |
| `--text-secondary` | `#475569` | Slate 600: Body copy, form labels, secondary descriptions. |
| `--text-muted` | `#94a3b8` | Slate 400: Placeholders, timestamps, disabled labels. |
| `--accent-blue` | `#0284c7` | Sky 600: Informational alerts, processing badges, active download progress. |
| `--accent-amber` | `#d97706` | Amber 600: Warnings, missing EXIF tags, uploading status. |
| `--accent-rose` | `#e11d48` | Rose 600: Errors, failed processing, missing bands, destructive actions. |

### B. Typography Scale & Standards
- **Font Stack**: Modern system sans-serif (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`) with optional `Inter` pairing.
- **Hierarchy**:
  - Page Titles: `text-2xl font-bold tracking-tight text-slate-900`
  - Section Headers: `text-lg font-semibold text-slate-900`
  - Card Titles & Sub-headings: `text-sm font-semibold text-slate-800`
  - Body Copy: `text-sm text-slate-600 leading-relaxed`
  - Micro-copy & Badges: `text-xs font-medium` or `text-[11px] uppercase tracking-wider font-semibold`
  - Technical / Logs: Monospace stack (`ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace`) at `text-xs font-mono`.

---

## 4. Component Styles & Interaction Patterns

### A. Buttons & Actions
- **Primary Action (`.btn-primary`)**: Solid emerald fill (`bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm`), 8px corner radius (`rounded-lg`), medium text weight (`font-medium text-sm`), flex container with 0.5rem icon gap (`gap-2`).
- **Secondary Action (`.btn-secondary`)**: Clean white surface (`bg-white hover:bg-slate-50 text-slate-700 border border-slate-200`), 8px radius, subtle hover feedback.
- **Destructive Action**: Muted rose (`bg-white hover:bg-rose-50 text-rose-600 border border-rose-200`).
- **Icon Actions**: Compact padding (`p-1.5 text-slate-400 hover:text-slate-600 rounded-md transition-colors`).

### B. Cards & Panels
- **Standard Card (`.card-base`)**: Border 1px solid `#e2e8f0`, border radius 12px (`rounded-xl`), background `#ffffff`, padding `p-5` or `p-6`.
- **Interactive Card (`.card-hover`)**: Subtle lift and border darken on hover (`hover:border-slate-300 hover:shadow-md transition-all`).

### C. Status Badges
Pill-shaped containers (`rounded-full px-2.5 py-0.5 text-xs font-semibold inline-flex items-center gap-1.5`) with dedicated semantic palettes:
- **Done / Success (`.badge-done`)**: `bg-emerald-50 text-emerald-700 border border-emerald-200` with `CheckCircle2` icon.
- **Processing (`.badge-processing`)**: `bg-blue-50 text-blue-700 border border-blue-200` with spinning `Loader2` icon.
- **Queued / Ready (`.badge-queued`)**: `bg-slate-50 text-slate-600 border border-slate-200` with `Clock` icon.
- **Failed (`.badge-failed`)**: `bg-rose-50 text-rose-700 border border-rose-200` with `AlertCircle` icon.
- **Uploading (`.badge-uploading`)**: `bg-amber-50 text-amber-700 border border-amber-200` with `UploadCloud` icon.

### D. Form Controls & Upload Dropzone
- **Input Fields (`.input-base`)**: 1px border `#cbd5e1`, 8px radius, focus state with emerald ring (`focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600`).
- **Upload Dropzone**: Dashed border container (`border-2 border-dashed border-slate-300 rounded-xl bg-slate-50/50 hover:bg-slate-50 p-8 text-center transition-colors`), animated drag-over state (`border-emerald-500 bg-emerald-50/30`), with clear dual-action buttons ("Select Photo Batch" vs "Select GeoTIFF Raster").

### E. Map Viewer Layout Proportions
- In `MapViewer.tsx`, the map layout features:
  - Top breadcrumb/flight header (`h-14 border-b border-slate-200 px-6 flex items-center justify-between`).
  - Floating control toolbar on top of map or dedicated side panel (`w-80 border-r border-slate-200 bg-white p-4`).
  - Layer selector radio toggles (Ortho RGB vs Index layers).
  - Continuous opacity slider and colormap selector.
  - Interactive coordinate click probe displaying lat/lon and probed pixel value in a compact popup.

---

## 5. Scope Adaptation: Aligning Reference to the Strict Five-Page Model

The reference archives (`drone-main` and `dron`) contained general routes such as `/farms`, `/flights`, `/scout`, `/upload`, `/settings`, and `/users`. In accordance with Phase 1 directives, **all functionality is strictly consolidated into exactly five main functional pages**:

1. **Page 1 — Admin Dashboard & Drone Image Ingestion** (`/admin/dashboard`):
   - Adapts the `/farms` hierarchy selection and the `/upload` dropzone into a single unified administrative ingestion cockpit with pre-flight CRS/EXIF validation.
2. **Page 2 — WebODM Photogrammetry Processing** (`/admin/photogrammetry`):
   - Adapts the WebODM task monitoring, preset selection, and log streaming from `/flights/[id]` into a dedicated photogrammetry execution console.
3. **Page 3 — Algorithm & Multi-Map Generation** (`/admin/algorithms`):
   - Adapts the spectral band assignment, vegetation index generation (NDVI, NDRE, GNDVI, SAVI), and layer catalog into a dedicated precision calculation workbench.
4. **Page 4 — Secure Farmer Portal** (`/portal/surveys`):
   - Adapts the interactive Leaflet/MapLibre viewer from `MapViewer.tsx` and `/scout` into an isolated, tenant-safe map viewing portal with swipe comparison and dynamic legends.
5. **Page 5 — Diagnostics & Actionable Insights** (`/portal/diagnostics`):
   - Adapts zonal time-series, statistical histograms, area summaries, and report generation into a dedicated agronomic evaluation and PDF compilation center.

---

## 6. Preserved Assets & Design Authority Confirmation

- **Preserved Design Identity**: The clean, emerald-and-slate agricultural aesthetic, font stacks, card radii, and badge patterns from `drone-main` are 100% preserved as the design authority.
- **Zero Arbitrary Redesign**: No alternative themes, dark modes, or flashy ungrounded widgets were invented.
- **Component Preservation**: Icons (`lucide-react`), card styles, badge styles, and layout spacing are systematically mapped directly into the AgriDrone AutoMap Design System.
