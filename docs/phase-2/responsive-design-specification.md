# AgriDrone AutoMap — Responsive Design Specification

## 1. Responsive Philosophy & Breakpoint Standards

Agricultural field operators, agronomists, and drone pilots frequently transition between dual-monitor office workstations, rugged field laptops, in-cab tractor tablets, and mobile smartphones on site.

The AgriDrone AutoMap responsive architecture adheres to four explicit breakpoints using standard Tailwind CSS classes:

| Breakpoint Tier | Viewport Width Range | Target Hardware Profile |
| :--- | :--- | :--- |
| **Desktop** (`2xl` / `xl`) | $\ge 1440\text{ px}$ | High-resolution workstations, multi-panel office monitors. |
| **Laptop** (`lg`) | $1024\text{ px} - 1439\text{ px}$ | Standard laptops, MacBook 13"-16", portable field laptops. |
| **Tablet** (`md`) | $768\text{ px} - 1023\text{ px}$ | Apple iPad (Air/Pro), Android field tablets, in-cab tractor mounts. |
| **Mobile** (`sm` / base) | $< 768\text{ px}$ ($375\text{ px} - 767\text{ px}$) | Modern smartphones (iPhone, Samsung Galaxy, Pixel). |

*Critical Accessibility & Usability Rule*: **No core functionality is removed on smaller viewports**. Controls adapt in layout, touch targets, and visual hierarchy, but users retain full capability to inspect maps, trigger jobs, and download reports across all devices.

---

## 2. Navigation & Header Responsive Adaptation

```mermaid
flowchart TD
    subgraph Desktop and Laptop: Width >= 1024px
        D_Nav[Inline Horizontal Links<br/>Logo | Ingestion | WebODM | Algorithms | Portal | Diagnostics | User Pill]
    end
    subgraph Tablet: 768px to 1023px
        T_Nav[Condensed Horizontal Links<br/>Logo | Icons with Tooltips | User Pill]
    end
    subgraph Mobile: Width < 768px
        M_Nav[Mobile Bar + Hamburger Drawer<br/>Logo | Node Status Dot | Hamburger Toggle]
        M_Nav --> M_Drawer[Slide-over Sheet Drawer<br/>Vertical Navigation Stack<br/>Touch Targets >= 48px]
    end
```

### Details:
- **Desktop & Laptop ($\ge 1024\text{ px}$)**:
  - Full horizontal menu bar with icons, text labels, NodeODM status badge, and user role pill.
- **Tablet ($768\text{ px} - 1023\text{ px}$)**:
  - Status text labels collapse to icon pills with native hover tooltips. Text labels remain visible for active route.
- **Mobile ($< 768\text{ px}$)**:
  - Top bar renders: Brand logo lockup, mini pulsing NodeODM dot, and an accessible hamburger button (`aria-label="Toggle Navigation"`).
  - Tapping hamburger triggers a slide-over mobile drawer (`fixed inset-0 z-50 bg-white shadow-2xl p-6`).
  - Drawer presents large, touch-friendly navigation tiles with minimum touch targets of $48 \times 48\text{ px}$.

---

## 3. Page-by-Page Responsive Layout Behaviors

### Page 1 — Admin Dashboard & Drone Image Ingestion
- **Desktop / Laptop**:
  - Top row: 2-column grid (`grid-cols-1 lg:grid-cols-2 gap-6`). Hierarchy selector on left; Pre-flight validation on right.
  - Dropzone spans full container width (`col-span-full`).
  - Dataset ledger: Standard 7-column table with pagination.
- **Tablet**:
  - Top cards stack vertically (`space-y-6`).
  - Dropzone buttons stack side-by-side (`flex-row gap-4`).
  - Dataset ledger enables horizontal scroll with sticky primary column (Survey ID).
- **Mobile**:
  - Full single-column vertical stack.
  - Dropzone action buttons stack vertically as full-width tap targets (`w-full py-3.5`).
  - Dataset ledger converts into a **Mobile Card List View** (`block lg:hidden`), rendering each survey as a self-contained card showing Date, Files, Size, Badge, and Action button to eliminate awkward horizontal scrolling.

---

### Page 2 — WebODM Photogrammetry Processing
- **Desktop / Laptop**:
  - Top row: 2-column grid (`grid-cols-3` with `col-span-2` for task options and `col-span-1` for node health).
  - Middle: Full-width progress card and log terminal (`h-64`).
  - Bottom: Generated artifacts table.
- **Tablet**:
  - Task options and node health stack into a single column.
  - Terminal height reduces to `h-56` with touch scroll enabled.
- **Mobile**:
  - Preset radio buttons convert to large selectable tap cards.
  - Log terminal displays a collapsible disclosure accordion (`defaultCollapsed={true}`) with a "View Raw Logs" toggle to prevent log feeds from monopolizing the mobile screen.
  - Progress bar, percentage, and Cancel button remain persistently visible at top.

---

### Page 3 — Algorithm & Multi-Map Generation
- **Desktop / Laptop**:
  - Spectral band mapping table renders as a structured 4-column grid.
  - Algorithm selection matrix renders as a 2x2 grid with inline parameter sliders.
- **Tablet**:
  - Band mapping table maintains 4 columns with touch-friendly select dropdowns.
  - Algorithm cards stack vertically (`space-y-4`).
- **Mobile**:
  - Band mapping table adapts into an interactive stacked list: each band displays as a card with detected wavelength and a full-width selector dropdown for assigned role.
  - SAVI soil factor slider expands to full width with large thumb control ($24\text{ px}$ touch target).

---

### Page 4 — Secure Farmer Portal (Interactive Map Viewer)
- **Desktop / Laptop**:
  - Side-by-side layout: MapLibre container occupies `flex-1` (min height $680\text{ px}$); side control panel occupies `w-80` or `w-96` on the right.
- **Tablet**:
  - MapLibre container occupies top area ($500\text{ px}$ height); control panel wraps beneath map or slides in as an overlay drawer.
- **Mobile**:
  - **Full-Screen Mobile Map Experience**: Map container expands to full viewport height (`h-[calc(100vh-4rem)]`).
  - Layer selection and legend collapse into a floating **Bottom Sheet Drawer** (`rounded-t-2xl shadow-2xl bg-white/95 backdrop-blur-md p-4`).
  - Tapping "Layers & Legend" expands the drawer to inspect index color swatches and toggle NDVI / RGB.
  - Two-finger pinch-to-zoom and pan enabled with clear touch instructions.

---

### Page 5 — Diagnostics & Actionable Insights
- **Desktop / Laptop**:
  - Statistical summary metric cards render in a 4-column grid (`grid-cols-4 gap-4`).
  - Zonal breakdown chart and limitation disclosures render side-by-side (`grid-cols-2 gap-6`).
  - ReportLab PDF generator card spans full width.
- **Tablet**:
  - Metric cards adapt to 2x2 grid (`grid-cols-2 gap-4`).
  - Zonal breakdown and limitations stack vertically.
- **Mobile**:
  - Metric cards stack in a 2-column or 1-column layout.
  - Zonal vegetation breakdown bar chart renders stacked horizontal bars with text percentages clearly visible above bars.
  - PDF report download cards render large, full-width touch buttons.

---

## 4. Touch Targets & Form Ergonomics

- **Minimum Touch Target**: In accordance with WCAG 2.5.5, all interactive elements (buttons, selectors, toggles, map markers) on mobile and tablet provide a minimum touch target area of **$44 \times 44\text{ px}$**.
- **Form Input Heights**: Input fields on mobile use `py-3 px-3 text-base` (preventing unwanted iOS browser auto-zooming on focus) with $8\text{ px}$ radius.
- **Tap Feedback**: Interactive cards and buttons implement active scale suppression (`active:scale-[0.98] transition-transform`) for tactile physical feedback on touchscreens.
