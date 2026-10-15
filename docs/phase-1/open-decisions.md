# AgriDrone AutoMap — Open Architectural & Operational Decisions

## 1. Overview & Decision Governance

To maintain engineering discipline and prevent arbitrary technical assumptions, this document captures all **unresolved architectural, operational, and business decisions**.

Each decision is documented with its technical context, why it matters, options under consideration, and the specific phase by which resolution is required.

---

## 2. Decision Registry

### Decision 01: Authentication Provider & Session Architecture
- **Current Status**: **UNRESOLVED / OPEN**
- **Why It Matters**: Dictates user table schema design, JWT/cookie session handling, password hashing libraries, and API route protection middleware.
- **Candidate Options**:
  1. *Custom OAuth2 with JWT Tokens*: Implemented in FastAPI using bcrypt and PyJWT; full local control; minimal external dependencies.
  2. *Microsoft Entra ID (Azure AD)*: Native enterprise single sign-on; direct alignment with Azure cloud resources; higher setup complexity for external farmers.
  3. *NextAuth / Auth.js with Database Session Store*: Handled predominantly on the Next.js frontend with session tokens passed to FastAPI.
- **Deadline for Resolution**: **Phase 4** (Database Schema) and **Phase 9** (Authentication Enforcement).

---

### Decision 02: Administrator and Farmer Account Provisioning Flow
- **Current Status**: **UNRESOLVED / OPEN**
- **Why It Matters**: Determines whether farmers can self-register, require email invitation links from administrators, or are manually provisioned via database seeds/admin consoles.
- **Candidate Options**:
  1. *Admin-Invited Provisioning*: Administrator creates Farm and triggers an email invite containing a secure sign-up link for the farmer.
  2. *Direct Manual Provisioning*: Administrator manually inputs farmer credentials and assigns farm IDs directly.
  3. *Self-Service Registration with Admin Approval*: Farmers sign up on a public form and await manual administrator verification before viewing data.
- **Deadline for Resolution**: **Phase 4** (User Model Design) and **Phase 9** (Portal Access).

---

### Decision 03: Delivery of Reference UI/UX Template Assets
- **Current Status**: **PENDING USER DELIVERY**
- **Why It Matters**: The user has established that an external reference UI/UX template and screenshots represent the strict design authority. As verified during workspace inspection, the directory is currently empty.
- **Action Required**: The user must supply template HTML/React/Tailwind files, stylesheets, and screenshots into the project directory before UI/UX design begins.
- **Deadline for Resolution**: **Prior to Commencing Phase 2**.

---

### Decision 04: Supported Drone Cameras & Spectral Sensor Models
- **Current Status**: **UNRESOLVED / OPEN**
- **Why It Matters**: Affects EXIF/XMP parsing algorithms, band wavelength identification, and radiometric calibration parameters in WebODM.
- **Candidate Options**:
  - *Standard RGB*: DJI Phantom 4 Pro, Mavic 3 Enterprise, Sony RX100 (RGB only; orthomosaic eligible, vegetation index ineligible).
  - *Multispectral*: MicaSense RedEdge (3/M/MX/P), DJI Phantom 4 Multispectral, DJI Mavic 3 Multispectral, Sentera 6X.
- **Impact**: Determines default band mapping configurations and radiometric sensor presets.
- **Deadline for Resolution**: **Phase 5** (Ingestion Pipeline) and **Phase 6** (WebODM).

---

### Decision 05: Initial Validation Test Datasets
- **Current Status**: **UNRESOLVED / OPEN**
- **Why It Matters**: Real-world agricultural drone flights produce 1GB to 20GB+ of imagery. Developers require agreed sample datasets to validate EXIF parsing, WebODM reconstruction, and multi-band Rasterio index calculations.
- **Action Required**: Stakeholder to provide or approve standardized sample flights:
  1. Sample A: ~50-100 geotagged RGB photos for rapid WebODM pipeline verification.
  2. Sample B: 5-band multispectral photo set (or pre-stitched 5-band GeoTIFF) with validated NIR, Red, RedEdge, and Green bands for index validation.
- **Deadline for Resolution**: **Phase 3** (Technical Validation) and **Phase 5** (Ingestion).

---

### Decision 06: Maximum File Size Limits & Azure Storage Retention Policies
- **Current Status**: **PROPOSED / AWAITING APPROVAL**
- **Why It Matters**: Ingesting high-resolution aerial datasets directly impacts Azure Blob Storage costs and network bandwidth.
- **Proposed Baseline**:
  - Max batch upload: 25 GB / 1,000 photos per survey.
  - Max single GeoTIFF: 10 GB.
  - Retention tiering: Move raw photos to Azure Cool/Archive tier after 30 days; retain orthomosaics and index COGs in Hot storage.
- **Deadline for Resolution**: **Phase 5** (Ingestion Pipeline).

---

### Decision 07: Azure Cloud Region, Account Setup & Budgetary Constraints
- **Current Status**: **UNRESOLVED / OPEN**
- **Why It Matters**: Cloud data sovereignty, network latency, and monthly cloud spend.
- **Key Parameters to Confirm**:
  - Azure Subscription & Resource Group.
  - Azure Region (e.g., East US, West Europe, Southeast Asia) to minimize latency to farm locations.
  - Expected monthly cloud budget limit for storage and egress.
- **Deadline for Resolution**: **Phase 3** (Technical Validation) and **Phase 5** (Ingestion).

---

### Decision 08: WebODM Deployment Architecture & Hardware Sizing
- **Current Status**: **UNRESOLVED / OPEN**
- **Why It Matters**: WebODM photogrammetry is heavily CPU- and RAM-intensive.
- **Candidate Options**:
  1. *Local / Dedicated Docker Node*: WebODM running on a dedicated on-premise workstation or cloud VM (minimum 8 vCPU, 32GB RAM).
  2. *Cloud VM on Azure*: Azure Virtual Machine (e.g., Standard_D8s_v5 or Standard_D16s_v5) running WebODM Docker node with auto-shutdown to control costs.
  3. *External Managed Cluster*: Integration with an existing institutional WebODM cluster via external REST API.
- **Deadline for Resolution**: **Phase 3** (PoC) and **Phase 6** (WebODM Integration).

---

### Decision 09: Expected Concurrent User Count & Target Performance Benchmarks
- **Current Status**: **PROPOSED / AWAITING STAKEHOLDER BENCHMARKS**
- **Why It Matters**: Sizing Celery worker concurrency, Redis memory, and database connection pooling.
- **Proposed Target**:
  - Initial deployment: 5-20 concurrent administrative operators; 50-200 registered farmers.
  - API response time target: $< 200\text{ ms}$ for non-GIS CRUD requests.
  - Map tile response target: $< 1.5\text{ seconds}$ per viewport view.
- **Deadline for Resolution**: **Phase 3** (Architecture) and **Phase 10** (Load Testing).

---

### Decision 10: Approved Index Visualization Color Scales & Classification Standards
- **Current Status**: **UNRESOLVED / OPEN**
- **Why It Matters**: Farmers and agronomists rely on visual conventions to spot stressed canopy areas.
- **Candidate Palettes**:
  1. *5-Class Agronomic RdYlGn*: Red ($<0.2$, Bare/Stressed), Orange ($0.2-0.4$), Yellow ($0.4-0.6$), Light Green ($0.6-0.75$), Dark Green ($>0.75$, High Biomass).
  2. *Scientific Continuous Viridis*: Perceptually uniform, accessible for color-blind users, standard in remote sensing publications.
  3. *Dual Palette Support*: Default to 5-Class Agronomic with an in-portal toggle for Viridis.
- **Deadline for Resolution**: **Phase 7** (Algorithms) and **Phase 8** (Map Legends).
