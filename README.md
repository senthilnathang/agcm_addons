# BuildForge Construction Platform

Comprehensive construction management platform built as 15 addon modules on the [FastVue](https://github.com/senthilnathang/FastVue) framework. Covers the full construction lifecycle: estimating, scheduling, financial, quality, collaboration, reporting, and BIM.

## Repository

| Item | Details |
|------|---------|
| **Standalone repo** | https://github.com/senthilnathang/agcm_addons |
| **Parent framework** | https://github.com/senthilnathang/FastVue |
| **Install path** | `agcm_addons/` inside a FastVue deployment |
| **Module count** | 15 modules, 104 database tables, 270+ API endpoints |
| **Demo data** | 38,000+ records across all modules |

---

## Module Map

| Module | Purpose | Tables | Key Entities |
|--------|---------|--------|-------------|
| `agcm` | Base: projects, daily logs, weather, photos | 17 | Project, DailyActivityLog, ManPower, Weather |
| `agcm_document` | Documents + drawings with revision control | 4 | ProjectFolder, ProjectDocument, Drawing |
| `agcm_rfi` | Request for Information workflow | 5 | RFI, RFIResponse, RFILabel |
| `agcm_submittal` | Submittals with multi-step approval | 6 | Submittal, SubmittalApprover, SubmittalPackage |
| `agcm_change_order` | Change orders with line items | 2 | ChangeOrder, ChangeOrderLine |
| `agcm_schedule` | Tasks, WBS, Gantt, dependencies | 4 | Task, WBS, Schedule, TaskDependency |
| `agcm_estimate` | Cost catalogs, assemblies, estimates, proposals, takeoff | 11 | Estimate, CostItem, Assembly, Proposal |
| `agcm_finance` | Budget, expenses, invoices, bills, prime contracts | 7 | Budget, CostCode, Invoice, Bill |
| `agcm_procurement` | POs, subcontracts, vendor bills, payment apps, T&M | 12 | PurchaseOrder, Subcontract, VendorBill |
| `agcm_progress` | Issues, milestones, estimation, S-curve | 5 | Issue, Milestone, EstimationItem, SCurveData |
| `agcm_resource` | Workers, equipment, timesheets | 4 | Worker, Equipment, Timesheet |
| `agcm_safety` | Checklists, inspections, punch lists, incidents | 8 | SafetyInspection, PunchListItem, IncidentReport |
| `agcm_portal` | Client selections, bid packages, portal config | 5 | Selection, BidPackage, BidSubmission |
| `agcm_reporting` | Report definitions, dashboards, KPI widgets | 4 | AGCMReportDefinition, AGCMDashboardLayout |
| `agcm_bim` | 3D models (xeokit), clash detection, annotations | 6 | BIMModel, ClashTest, BIMAnnotation3D |

---

## Key Features

### Core (`agcm`)
- Projects with location, contractors, trades, geolocation
- Daily activity logs with manpower, weather, inspections, safety, photos
- Executive dashboards with KPIs across all projects
- PDF reports via WeasyPrint with HTML fallback
- Activity audit trail on all major entities
- Two-tier caching (L1 + Redis) with distributed invalidation

### Coordination (`agcm_rfi`, `agcm_submittal`, `agcm_change_order`)
- RFI workflow with threaded responses and labels (soft delete enabled)
- Submittal tracking with multi-step approval chain
- Change orders with line items and cost/schedule impact (soft delete enabled)
- Task scheduling with soft delete and restore capability

### Scheduling (`agcm_schedule`)
- WBS hierarchy, task dependencies (FS/SS/FF/SF)
- Gantt chart via ECharts with critical path
- Task status workflow (todo/in_progress/in_review/completed)

### Financial (`agcm_finance`, `agcm_estimate`, `agcm_procurement`)
- Hierarchical cost codes and budget management
- Cost catalogs, assemblies, estimates, proposals, takeoffs
- Purchase orders, subcontracts, vendor bills, payment applications
- T&M tickets with labor/equipment/material tracking

### Quality & Safety (`agcm_safety`, `agcm_progress`)
- Checklist templates with inspection items
- Punch list management with priority/status workflow
- Incident reporting with severity classification
- S-curve tracking, milestones, project images

### Reporting (`agcm_reporting`)
- Custom report builder with column/filter configuration
- Export: CSV, PDF (WeasyPrint via core pdf_service), Excel (openpyxl)
- Dashboard layouts with configurable widgets (KPI cards, charts, tables)
- Scheduled report delivery via email

### BIM (`agcm_bim`)
- 3D model management (IFC, RVT, NWD, FBX, GLB, OBJ)
- xeokit SDK viewer with 25 tools and 12 keyboard shortcuts
- BCF 2.1 viewpoint save/restore with screenshots
- AABB clash detection between model pairs
- 3D annotations with entity linking (RFI, Issue, Punch List)

---

## Module Structure

```
agcm_addons/
├── agcm/                    # Base construction module
├── agcm_document/           # Document management
├── agcm_rfi/                # RFI workflow
├── agcm_submittal/          # Submittal tracking
├── agcm_change_order/       # Change orders
├── agcm_schedule/           # Task scheduling & Gantt
├── agcm_estimate/           # Estimating & takeoff
├── agcm_finance/            # Budget & financial
├── agcm_procurement/        # Procurement management
├── agcm_progress/           # Progress tracking
├── agcm_resource/           # Resource management
├── agcm_safety/             # Quality & safety
├── agcm_portal/             # Client/sub portals
├── agcm_reporting/          # Reports & dashboards
├── agcm_bim/                # BIM 3D viewer
├── scripts/                 # Seed data scripts
├── tests/                   # pytest test suite (184+ tests)
├── docs/                    # Service standardization patterns
├── CLAUDE.md                # Architecture reference
├── MIGRATION_PLAYBOOK.md    # Odoo migration guide
└── README.md
```

Each module follows the standard addon structure:
```
agcm_<module>/
├── __manifest__.py          # Metadata, menus, permissions
├── __init__.py
├── models/                  # SQLAlchemy ORM models
├── schemas/                 # Pydantic request/response schemas
├── services/                # Business logic layer
├── api/                     # FastAPI route handlers
└── static/
    ├── api/index.js         # Frontend API client
    └── views/               # Vue 3 SFC views + CSS
```

---

## Installation

### 1. Clone into FastVue

```bash
cd /opt/FastVue
git clone https://github.com/senthilnathang/agcm_addons.git
```

### 2. Configure Environment

```bash
cp backend/.env backend/.env.agcm
# Edit .env.agcm:
#   POSTGRES_DB=fastvue_agcm
#   ADDONS_PATHS=addons,agcm_addons
```

### 3. Start & Install Modules

```bash
bash run.sh init --env-file backend/.env.agcm
bash run.sh run backend --env-file backend/.env.agcm

# Install all modules via API
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@fastvue.com","password":"admin123"}' \
  | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

for mod in agcm agcm_document agcm_rfi agcm_submittal agcm_change_order \
  agcm_schedule agcm_estimate agcm_finance agcm_procurement agcm_progress \
  agcm_resource agcm_safety agcm_portal agcm_reporting agcm_bim; do
  curl -X POST "http://localhost:8000/api/v1/modules/install/$mod" \
    -H "Authorization: Bearer $TOKEN"
done
```

### 4. Load Demo Data

```bash
cd /opt/FastVue/backend && source .venv/bin/activate

# Base projects + daily logs
PYTHONPATH="/opt/FastVue/agcm_addons:." ENV_FILE=.env.agcm \
  python /opt/FastVue/agcm_addons/agcm/scripts/seed_demo_data.py

# All addon modules
PYTHONPATH="/opt/FastVue/agcm_addons:." ENV_FILE=.env.agcm \
  python /opt/FastVue/agcm_addons/scripts/seed_all_modules.py

# Estimate, Procurement, Resource/Safety/Portal/Reporting, BIM
PYTHONPATH="/opt/FastVue/agcm_addons:." ENV_FILE=.env.agcm \
  python /opt/FastVue/agcm_addons/scripts/seed_estimate_data.py
PYTHONPATH="/opt/FastVue/agcm_addons:." ENV_FILE=.env.agcm \
  python /opt/FastVue/agcm_addons/scripts/seed_procurement_data.py
PYTHONPATH="/opt/FastVue/agcm_addons:." ENV_FILE=.env.agcm \
  python /opt/FastVue/agcm_addons/scripts/seed_phases_3to6.py
PYTHONPATH="/opt/FastVue/agcm_addons:." ENV_FILE=.env.agcm \
  python /opt/FastVue/agcm_addons/scripts/seed_bim_data.py
```

---

## Running Tests

```bash
cd /opt/FastVue/agcm_addons
/opt/FastVue/backend/.venv/bin/python -m pytest tests/ -v
```

Requires PostgreSQL at `localhost:5433` with database `fastvue_test`.

---

## Workflow Connections

- **Estimate -> Budget**: `send_to_budget()` creates agcm_finance budget records
- **Change Order -> Budget**: auto-updates committed amounts on approval
- **Inspection fail -> Punch List**: auto-creates PunchListItem
- **Bid awarded -> Subcontract**: auto-creates draft Subcontract
- **BIM Viewpoints <-> RFIs/Issues**: cross-entity linking via polymorphic FK

---

## Architecture

### Service Layer
All 13 module services are standardized following `docs/SERVICE_STANDARDIZATION.md`:
- Consistent return types across all list/get/create/update/delete/restore methods
- Two-tier caching (L1 in-process + L2 Redis) with TTL=300s
- Cache invalidation on all mutations
- Activity logging via ActivityMixin

### Activity Audit Trail
30+ models include ActivityMixin for automatic audit logging:
- All entity mutations logged with user, timestamp, and field changes
- ActivityThread Vue component integrated in 8+ detail views
- Activity tab on: Project, RFI, ChangeOrder, Estimate, PO, Subcontract, Submittal, BIM Model

### Soft Delete
RFI, Task, and ChangeOrder support soft delete with restore:
- `deleted_at` timestamp marks deleted records
- Deleted records excluded from queries by default
- `restore_item()` API endpoint to recover

---

## Tech Stack

- **Backend**: Python 3.12, FastAPI 0.128, SQLAlchemy 2.0, PostgreSQL 16
- **Frontend**: Vue 3.5, Ant Design Vue 4, ECharts 6, Tailwind CSS
- **BIM Viewer**: xeokit SDK (IFC/XKT), BCF 2.1
- **PDF**: WeasyPrint with Jinja2 templates
- **File Storage**: Core documents module (local/S3)
- **Weather API**: weather.gov (NWS)

---

## References

- [CLAUDE.md](CLAUDE.md) — Architecture reference for AI assistants
- [MIGRATION_PLAYBOOK.md](MIGRATION_PLAYBOOK.md) — Odoo-to-FastVue migration guide
