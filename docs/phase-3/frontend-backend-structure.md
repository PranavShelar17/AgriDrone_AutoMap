# AgriDrone AutoMap — Frontend & Backend Structure
## Document Reference: `docs/phase-3/frontend-backend-structure.md`
**Phase**: Phase 3 — System Architecture, Technical Validation & Implementation Blueprint  
**Status**: APPROVED ARCHITECTURE BLUEPRINT  
**Version**: 1.0.0  

---

## 1. Unified Repository Directory Organization

The AgriDrone AutoMap codebase is structured as a clear, modular monorepo containing distinct roots for the presentation tier (`frontend/`), the API and asynchronous worker tier (`backend/`), operational infrastructure (`docker/`), and architectural specifications (`docs/`).

```
agridrone-automap/
├── .github/                      # CI/CD Workflows, PR Templates, Linting Actions
│   └── workflows/
│       ├── frontend-ci.yml       # Next.js build, ESLint, TypeScript check
│       ├── backend-ci.yml        # Pytest, Flake8/Black, Mypy, GDAL test runners
│       └── docker-build.yml      # Container build & security vulnerability scan
├── backend/                      # Python / FastAPI Backend & Celery Worker Root
│   ├── alembic/                  # PostGIS / PostgreSQL Database Migrations
│   │   ├── versions/             # Timestamped migration revisions
│   │   └── env.py                # Alembic environment configuration
│   ├── app/                      # Application Source Code
│   │   ├── api/                  # API Routing Tier
│   │   │   ├── deps.py           # Dependency injection (Auth, DB session, Storage)
│   │   │   └── v1/               # Version 1 REST API Routers
│   │   │       ├── router.py     # Aggregated v1 root router
│   │   │       ├── auth.py       # Authentication & profile endpoints
│   │   │       ├── farms.py      # Farm & Field management endpoints
│   │   │       ├── surveys.py    # Survey lifecycle endpoints
│   │   │       ├── ingestion.py  # Page 1: File upload & validation endpoints
│   │   │       ├── webodm.py     # Page 2: Photogrammetry dispatch & logs
│   │   │       ├── algorithms.py # Page 3: Spectral band mapping & index jobs
│   │   │       ├── portal.py     # Page 4: Farmer GIS layers & survey viewer
│   │   │       └── reports.py    # Page 5: Diagnostics & PDF report generation
│   │   ├── core/                 # Core System Configuration & Utilities
│   │   │   ├── config.py         # Pydantic v2 BaseSettings (Env variables)
│   │   │   ├── logging.py        # Structured JSON logging configuration
│   │   │   ├── security.py       # JWT creation, password hashing, token validation
│   │   │   └── exceptions.py     # Custom application exceptions & HTTP mappings
│   │   ├── db/                   # Persistence Engine
│   │   │   ├── session.py        # SQLAlchemy async/sync session factories
│   │   │   └── base.py           # Declarative base & entity metadata import hub
│   │   ├── models/               # SQLAlchemy 2.0 ORM & GeoAlchemy2 Entities
│   │   │   ├── user.py           # User & Role models
│   │   │   ├── farm.py           # Farm & Field (Polygon geometry) models
│   │   │   ├── survey.py         # Survey & SurveyFile models
│   │   │   ├── task.py           # ProcessingTask & TaskAttempt models
│   │   │   ├── product.py        # MapProduct (Orthophoto, COG, Index) models
│   │   │   └── report.py         # Report & AuditEvent models
│   │   ├── schemas/              # Pydantic v2 Request/Response Data Contracts
│   │   │   ├── common.py         # Pagination, StatusResponse, ErrorResponse
│   │   │   ├── farm.py           # FarmCreate, FarmRead, FieldGeoJSON
│   │   │   ├── survey.py         # SurveyCreate, SurveyDetail, FileUploadIntent
│   │   │   ├── webodm.py         # TaskSubmitRequest, TaskStatusResponse
│   │   │   ├── algorithm.py      # BandInspection, AlgoJobCreate, AlgoJobStatus
│   │   │   ├── portal.py         # FarmerSurveyView, LayerMetadata
│   │   │   └── report.py         # ReportGenerateRequest, ReportSummary
│   │   ├── services/             # Core Business Logic & Domain Services
│   │   │   ├── storage_service.py # Azure Blob client & SAS token generator
│   │   │   ├── webodm_client.py  # WebODM REST API client
│   │   │   ├── raster_service.py # GDAL & Rasterio inspection and COG conversion
│   │   │   ├── index_calculator.py # NumPy spectral math (NDVI, VARI, etc.)
│   │   │   └── report_compiler.py# ReportLab PDF document builder
│   │   └── workers/              # Celery Asynchronous Task Definitions
│   │       ├── celery_app.py     # Celery app initialization & beat schedule
│   │       ├── tasks_ingest.py   # Asynchronous EXIF & raster validation tasks
│   │       ├── tasks_webodm.py   # WebODM task dispatching & status polling
│   │       ├── tasks_raster.py   # COG conversion & index calculation tasks
│   │       └── tasks_report.py   # PDF compilation background tasks
│   ├── tests/                    # Backend Automated Test Suite
│   │   ├── conftest.py           # Pytest fixtures (DB session, mock Azure, test client)
│   │   ├── fixtures/             # Sample GeoTIFF headers, test EXIF JPEGs
│   │   ├── test_api/             # API endpoint integration tests
│   │   ├── test_services/        # Business logic & raster math unit tests
│   │   └── test_workers/         # Celery task execution tests
│   ├── alembic.ini               # Alembic configuration
│   ├── Dockerfile                # Production FastAPI & Celery container definition
│   ├── pyproject.toml            # Poetry / Pip dependency specifications
│   └── requirements.txt          # Pinned Python package dependencies
├── frontend/                     # Next.js 14 App Router Frontend Root
│   ├── app/                      # Next.js 14 App Router Directory
│   │   ├── layout.tsx            # Global root layout (Navbar, Footer, Providers)
│   │   ├── page.tsx              # System launchpad & design review hub
│   │   ├── globals.css           # Tailwind base styles, tokens, utilities
│   │   ├── admin/                # Admin Functionality Route Group
│   │   │   ├── dashboard/page.tsx# Page 1: Admin Ingestion & File Ledger
│   │   │   ├── photogrammetry/page.tsx # Page 2: WebODM Processing & Logs
│   │   │   └── algorithms/page.tsx     # Page 3: Spectral Algorithms & Multi-Map
│   │   └── portal/               # Farmer Functionality Route Group
│   │       ├── surveys/page.tsx  # Page 4: Secure Farmer GIS Map Portal
│   │       └── diagnostics/page.tsx    # Page 5: Diagnostics & Actionable Insights
│   ├── components/               # Reusable Presentation Components
│   │   ├── layout/               # Navbars, Sidebars, Footers, PageHeaders
│   │   │   ├── Navbar.tsx        # Top navigation with status pill
│   │   │   └── PageHeader.tsx    # Standard view header with breadcrumbs
│   │   ├── ui/                   # Atomic UI primitives
│   │   │   ├── Button.tsx        # Primary, secondary, outline, danger buttons
│   │   │   ├── Card.tsx          # Card container with rounded-xl border
│   │   │   ├── StatusBadge.tsx   # Semantic pill badges (Queued, Running, etc.)
│   │   │   ├── AlertBanner.tsx   # Info, warning, error notification boxes
│   │   │   ├── Modal.tsx         # Accessible overlay dialog
│   │   │   └── Table.tsx         # Data table with responsive horizontal scroll
│   │   ├── forms/                # Form inputs & validation controls
│   │   │   ├── Dropzone.tsx      # Chunked drag-and-drop file upload
│   │   │   ├── Select.tsx        # Custom dropdown selector
│   │   │   └── Slider.tsx        # Parameter control slider (SAVI, Opacity)
│   │   └── gis/                  # MapLibre GIS-specific components
│   │       ├── MapViewer.tsx     # MapLibre GL JS canvas wrapper
│   │       ├── LayerControl.tsx  # Layer toggle, opacity, and colormap picker
│   │       ├── SwipeCompare.tsx  # Split-screen swipe comparison divider
│   │       └── ColormapLegend.tsx# Continuous and discrete color ramp legend
│   ├── hooks/                    # Custom React Hooks
│   │   ├── useAuth.ts            # Current user identity & token manager
│   │   ├── useTaskPoller.ts      # Polling hook for asynchronous Celery jobs
│   │   └── useMapInstance.ts     # MapLibre lifecycle & layer registration hook
│   ├── lib/                      # Frontend Core Utilities & API Client
│   │   ├── api.ts                # Axios/Fetch HTTP client configured for /api/v1
│   │   ├── azure-upload.ts       # Direct chunked Azure Blob upload helper
│   │   └── utils.ts              # ClassName merge (clsx/tailwind-merge), formatters
│   ├── types/                    # Shared TypeScript Interface Definitions
│   │   ├── api.ts                # API request/response types
│   │   ├── gis.ts                # GeoJSON, COG metadata, colormap definitions
│   │   └── models.ts             # Domain models (Farm, Survey, Task, Product)
│   ├── package.json              # Frontend package dependencies & scripts
│   ├── tailwind.config.js        # Design system tokens (Emerald/Slate palette)
│   ├── tsconfig.json             # TypeScript compiler settings
│   └── Dockerfile                # Production Next.js standalone container definition
├── docker/                       # Containerized Environment Configuration
│   ├── docker-compose.yml        # Development environment multi-service orchestrator
│   ├── docker-compose.prod.yml   # Production deployment orchestrator
│   └── nginx/                    # Reverse proxy & static caching configuration
│       └── default.conf          # Nginx routing to Next.js and FastAPI
└── docs/                         # Comprehensive Engineering Documentation
    ├── phase-1/                  # Requirements, Scope, Acceptance Criteria (13 files)
    ├── phase-2/                  # UI/UX Specifications, Design System, Review (7 files)
    └── phase-3/                  # System Architecture & Implementation Blueprint (15 files)
```

---

## 2. Frontend Component Boundaries & Responsibilities

1. **State Isolation**:
   - The frontend maintains **zero permanent business state**. All domain records (surveys, tasks, products) are fetched from the FastAPI backend and displayed as confirmed by the server.
   - Transient state is restricted to: active filter selections, upload progress meters, interactive map viewport (center, zoom), and UI drawer visibility.
2. **Client-Side vs Server-Side Responsibilities**:
   - **Server Components (RSC)**: Used for initial page shells, static metadata, and SEO tags.
   - **Client Components (`'use client'`)**: Used for interactive surfaces requiring DOM events:
     - Drag-and-drop file chunking ([Dropzone.tsx](file:///c:/Users/Admin/Desktop/new%20dron%202/frontend/components/forms/Dropzone.tsx))
     - WebGL canvas rendering ([MapViewer.tsx](file:///c:/Users/Admin/Desktop/new%20dron%202/frontend/components/gis/MapViewer.tsx))
     - Polling hooks for background tasks ([useTaskPoller.ts](file:///c:/Users/Admin/Desktop/new%20dron%202/frontend/hooks/useTaskPoller.ts))
     - Form sliders and dropdown state controls.
3. **MapLibre Integration Boundary**:
   - The map canvas is isolated inside `components/gis/MapViewer.tsx`.
   - The map viewer accepts GeoJSON layers for field boundaries and raster COG tile URLs for orthomosaics and vegetation indices.
   - Raw GeoTIFF parsing is strictly prohibited in the browser; the frontend only consumes Cloud-Optimized GeoTIFFs (COGs) served via windowed tile requests or pre-rendered tile streams.

---

## 3. Backend Module Organization & Separation

1. **Router Layer (`app/api/v1/`)**:
   - Strictly responsible for HTTP request handling, deserialization via Pydantic, invoking dependency injection for authentication/database sessions, and returning standardized JSON responses. Contains **zero direct database queries or raw file math**.
2. **Service Layer (`app/services/`)**:
   - Encapsulates pure business logic. Coordinates database transactions, interacts with the Azure Blob SDK, prepares WebODM task parameters, and formats geospatial structures.
3. **Worker Layer (`app/workers/`)**:
   - Defines Celery tasks that run in independent OS processes. Tasks receive simple scalar arguments (e.g., `task_id: str`), instantiate their own database sessions, execute heavy operations (GDAL processing, WebODM polling), update database state, and clean up temporary files.
4. **Data Access Layer (`app/models/` & `app/schemas/`)**:
   - SQLAlchemy 2.0 declarative models manage persistence and relationships. Pydantic v2 schemas define strict inbound validation and outbound response shaping.

---

## 4. Environment Configuration & Secret Handling

Configuration is managed via Pydantic `BaseSettings` reading from `.env` files and environment variables with strict type validation.

```python
# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, RedisDsn

class Settings(BaseSettings):
    PROJECT_NAME: str = "AgriDrone AutoMap"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development", pattern="^(development|staging|production)$")
    
    # Security
    SECRET_KEY: str = Field(..., min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database & Redis
    DATABASE_URL: PostgresDsn = Field(...)
    REDIS_URL: RedisDsn = Field(...)
    
    # Azure Blob Storage
    AZURE_STORAGE_CONNECTION_STRING: str = Field(default="")
    AZURE_STORAGE_ACCOUNT_NAME: str = Field(...)
    AZURE_CONTAINER_RAW: str = "raw-surveys"
    AZURE_CONTAINER_ORTHO: str = "orthomosaics"
    AZURE_CONTAINER_INDICES: str = "vegetation-indices"
    AZURE_CONTAINER_REPORTS: str = "reports"
    
    # WebODM Photogrammetry Service
    WEBODM_API_URL: str = "http://webodm:8000"
    WEBODM_USERNAME: str = Field(default="")
    WEBODM_PASSWORD: str = Field(default="")
    
    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3005"]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
```

---

## 5. Automated Testing Boundaries

| Test Suite | Location | Scope & Strategy | Mocked Dependencies |
| :--- | :--- | :--- | :--- |
| **Backend Unit Tests** | `backend/tests/test_services/` | Raster math formulas (VARI, NDVI), EXIF header parsing, Pydantic schema validation, utility functions. | Azure Storage, WebODM API, Database. |
| **API Integration Tests** | `backend/tests/test_api/` | Endpoint routing, RBAC enforcement, query parameter filtering, response codes, error formats. | Real test PostgreSQL/PostGIS (Docker); Mocked Azure SAS & Celery `.delay()`. |
| **Worker Execution Tests** | `backend/tests/test_workers/` | Celery task lifecycle, retry behavior on network timeouts, database state updates on success/failure. | Real Redis & PostGIS test containers; Simulated WebODM response fixtures. |
| **Frontend Unit Tests** | `frontend/__tests__/components/` | React component rendering, button click handlers, form validation, StatusBadge styling. | Backend API (mocked via MSW - Mock Service Worker). |
| **E2E Integration Tests** | `frontend/__tests__/e2e/` | Full user journey execution (Ingestion $\to$ Photogrammetry $\to$ Algorithm $\to$ Portal $\to$ Diagnostics) using Playwright. | Staging environment with simulated small (10-photo) survey dataset. |
