# Claude Instructions for agcm_addons — BuildForge Construction Platform

## Platform Overview

BuildForge is a comprehensive construction management platform built as 15 addon modules on the FastVue framework. Inspired by Procore (enterprise) and Buildern (SMB), it covers the full construction lifecycle: estimating → scheduling → financial → quality → collaboration → reporting → BIM.

**Total: 15 modules, 104 database tables, 270+ API endpoints, 64+ frontend views, 38,000+ demo records**

## Module Map

| Module | Purpose | Tables | Key Entities |
|--------|---------|--------|-------------|
| `agcm` | Base: projects, daily logs, weather, photos | 17 | Project, DailyActivityLog, ManPower, Weather |
| `agcm_document` | Documents + drawings with revision control | 4 | ProjectFolder, ProjectDocument, Drawing, DrawingRevision |
| `agcm_rfi` | Request for Information workflow | 5 | RFI, RFIResponse, RFILabel |
| `agcm_submittal` | Submittals with multi-step approval | 6 | Submittal, SubmittalApprover, SubmittalPackage |
| `agcm_change_order` | Change orders with line items | 2 | ChangeOrder, ChangeOrderLine |
| `agcm_schedule` | Tasks, WBS, Gantt, dependencies | 4 | Task, WBS, Schedule, TaskDependency |
| `agcm_finance` | Budget, expenses, invoices, bills, prime contracts | 7 | Budget, CostCode, Invoice, Bill, PrimeContract |
| `agcm_progress` | Issues, milestones, estimation, S-curve | 5 | Issue, Milestone, EstimationItem, SCurveData |
| `agcm_estimate` | Cost catalogs, assemblies, estimates, proposals, takeoff | 11 | Estimate, CostItem, Assembly, Proposal, TakeoffSheet |
| `agcm_procurement` | POs, subcontracts, vendor bills, payment apps, T&M | 12 | PurchaseOrder, Subcontract, VendorBill, PaymentApplication, TMTicket |
| `agcm_resource` | Workers, equipment, timesheets | 4 | Worker, Equipment, Timesheet, EquipmentAssignment |
| `agcm_safety` | Checklists, inspections, punch lists, incidents | 8 | SafetyInspection, PunchListItem, IncidentReport, ChecklistTemplate |
| `agcm_portal` | Client selections, bid packages, portal config | 5 | Selection, BidPackage, BidSubmission, PortalConfig |
| `agcm_reporting` | Report definitions, dashboards, widgets | 4 | AGCMReportDefinition, AGCMReportSchedule, AGCMDashboardLayout, AGCMDashboardWidget |
| `agcm_contact` | Centralized vendor/client/subcontractor directory | 1 | Vendor |
| `agcm_bim` | 3D models, xeokit viewer, clash detection, annotations | 6 | BIMModel, BIMViewpoint, BIMElement, BIMAnnotation3D, ClashTest, ClashResult |

## Critical Rules

### Import Namespace
- All imports MUST use `from addons.agcm_<module>.` prefix
- Example: `from addons.agcm_estimate.models.estimate import Estimate`
- The `AddonNamespaceFinder` maps `addons.*` to `agcm_addons/`

### API Router
- NEVER add `prefix=` to `APIRouter()` — loader auto-mounts at `/api/v1/<module_name>`
- Frontend `requestClient` already adds `/api/v1` — use paths like `/agcm/projects`

### HTTP Error Prevention Checklist (404 / 422 / 500)
When writing or modifying code, verify every endpoint against this checklist:

**404 Prevention:**
- Every frontend API call (`requestClient.get/post/put/delete`) MUST have a matching backend route with the same HTTP method and path
- When adding a frontend CRUD view (list/create/edit/delete), ensure ALL four backend endpoints exist — missing PUT/PATCH for edit is a common gap
- Use `page_size` (not `limit`) for pagination on `/users/` and all paginated endpoints — `limit` is silently ignored causing data truncation
- Module must be in `installed_modules` table with `state="installed"` or all its routes return 404
- Verify plural/singular consistency between frontend paths and backend route decorators

**422 Prevention:**
- Schema field names in frontend `requestClient` payloads MUST exactly match Pydantic schema field names (case-sensitive)
- Required fields in `*Create` schemas must always be sent from the frontend form
- `field_validator` constraints (e.g., `item_type` allowed values, `max_length`) must be respected in frontend forms — add client-side validation matching backend constraints
- Query parameters must match FastAPI parameter names exactly (e.g., `page_size` not `limit`, `estimate_id` not `estimateId`)
- Enum values sent from frontend must match backend enum `.value` strings exactly

**500 Prevention:**
- Always check `company_id` scoping — queries without company filter can leak data or hit unique constraints
- Services that call `db.commit()` must handle `IntegrityError` (duplicate key, FK violation)
- Null-check related objects before accessing their attributes (e.g., `estimate.project.name` when project could be None)
- When adding new model fields, ensure existing records won't break — use `nullable=True` or provide defaults
- File/attachment operations must handle missing files gracefully (S3 key deleted, local file moved)

### Database
- All table names prefixed with `agcm_` (104 tables total)
- Every model MUST have `company_id` FK to `companies.id`
- Use `get_effective_company_id()` for company scoping
- Tables auto-created by AutoSchemaManager — no alembic needed

### Module Installation
- Modules must be in `installed_modules` DB table to have routers mounted
- `installed_modules` requires: name, display_name, state="installed", version, category, license
- Auto-discovered from `ADDONS_PATHS` but only installed modules get API routers

### Class Name Conflicts
- AGCM models that share Python class names with core modules MUST be renamed
- `AGCMDashboardLayout`, `AGCMDashboardWidget` — avoid conflict with `modules.base.models.dashboard`
- `AGCMReportDefinition`, `AGCMReportSchedule` — avoid conflict with core report models
- `SafetyInspection`, `SafetyInspectionItem` — avoid conflict with `agcm.models.inspection`
- Use tablename-based relationships: `relationship("agcm_report_schedules", ...)`
- Services use aliases: `from ... import AGCMReportDefinition as ReportDefinition`

### Frontend (SFC-loaded views)
- Vue 3 SFCs loaded at runtime by `vue3-sfc-loader`
- Ant Design Vue components (A-prefixed, globally registered)
- Every `.vue` file needs a companion `.css` file
- Import `requestClient` from `#/api/request`
- Import `echarts` via `import * as echarts from 'echarts'`
- Import xeokit via `import { Viewer, ... } from '@xeokit/xeokit-sdk'`
- NO TypeScript in SFC-loaded views — plain JS only

### Pagination
- All paginated endpoints: `page_size: int = Query(20, ge=1, le=200)`
- Services enforce: `page_size = min(page_size, 200)`
- Frontend: NEVER request `page_size > 200`

### Enum Columns
- New modules: `Enum(MyEnum, values_callable=lambda e: [m.value for m in e])`
- Base `agcm` module: NO `values_callable` (uses uppercase in DB)

### Menus
- Child modules use `"parent": "agcm"` — NEVER re-declare Construction parent
- Settings items use `"parent": "agcm.settings"`

### Real-time Events
- Service: `from addons.agcm.services.realtime_events import agcm_realtime`
- Fire-and-forget: `try: await agcm_realtime.xxx(db, entity) except: pass`
- Wired into: RFI, Tasks, Submittals, Change Orders, Issues

### Generic Systems
- **Comments:** `EntityComment` (agcm_entity_comments) — any entity via entity_type+entity_id
- **Attachments:** `agcm_entity_attachments` M2M — links any entity to documents
- **Approvals:** Wired into core `base_automation` ApprovalChain/ApprovalTask system
  - Integration: `addons.agcm.services.approval_integration` — submit, check, list pending
  - Handlers: `addons.agcm.services.approval_handlers` — entity-specific completion callbacks
  - API: `POST /agcm/approvals/{task_id}/approve|reject`, `GET /agcm/approvals/pending`
  - Entities: purchase_order, change_order, subcontract, estimate, vendor_bill, proposal
  - **Backward compatible**: if no chain configured, entities auto-approve instantly
  - **With chain**: entity status → `pending_approval`, tasks created, chain runs
  - **On completion**: handler in `approval_handlers.py` updates entity status + side effects
  - **Budget Posting**: `addons.agcm.services.budget_posting` — shared cost posting helper
    - `post_to_budget(db, project_id, company_id, column, amount, description=)` — upsert budget line
    - `reverse_budget_posting(...)` — undo a posting (e.g., void after approval)
    - PO approved → `committed_amount` += total_amount (description: "Purchase Orders")
    - Subcontract approved → `committed_amount` += revised_amount (description: "Subcontracts")
    - VendorBill approved → `actual_amount` += total_amount (description: "Vendor Bills")
    - CO approved → `committed_amount` += cost_impact (description: "Approved Change Orders")
    - Timesheet approved → `actual_amount` += total_cost (description: "Labor (Timesheets)")
    - Expense approved → `actual_amount` += line totals (description: "Expenses")
  - Demo chains: `agcm/scripts/seed_approval_chains.py` (PO, CO, Subcontract — 2-step each)
  - Pattern for new approve methods:
    ```python
    tasks = submit_for_approval(db, entity_type, entity_id, user_id, company_id, amount)
    if tasks:
        entity.status = "pending_approval"  # chain will handle completion
    else:
        entity.status = "approved"  # no chain — auto-approve
    ```

### Invoice & Bill Line Items with Tax
- **TaxRate** (`agcm_tax_rates`): company-level tax rates (name, rate %, is_compound, is_default)
- **InvoiceLine** (`agcm_invoice_lines`): qty, unit_price, subtotal, taxable, tax_rate_id, tax_amount, total, retention_pct/amount, cost_code_id
- **BillLine** (`agcm_bill_lines`): qty, unit_cost, subtotal, taxable, tax_rate_id, tax_amount, total, cost_code_id
- Calculation: subtotal = qty × price/cost; tax = subtotal × rate%; total = subtotal + tax
- Document recalculation: amount = sum(subtotals), tax_amount = sum(taxes), total_amount = amount + tax
- API: `/agcm_finance/tax-rates` (CRUD), `/invoice-lines` (CRUD), `/bill-lines` (CRUD)
- Detail endpoints: `GET /invoices/{id}/detail`, `GET /bills/{id}/detail` (include lines)
- Backward compatible: flat amount fields still work when no lines exist

### Reports
- Overview Canvas: SVG charts (donut, bars) in daily log reports
- Project Dashboard: aggregated KPIs in periodic reports
- PDF via WeasyPrint with HTML fallback
- Export formats: CSV, PDF (WeasyPrint via core `pdf_service`), Excel (openpyxl)
- Export endpoint: `GET /reports/{id}/export?format=csv|pdf|excel&token=JWT`
- Token-based auth for browser-initiated downloads (`window.open` with `?token=JWT` pattern, same as BIM)

### BIM Viewer (xeokit SDK)
- 3D viewer: `bim-viewer.vue` (3,044 lines, 10 xeokit plugins)
- 6 tables: `agcm_bim_models`, `agcm_bim_viewpoints`, `agcm_bim_elements`, `agcm_bim_annotations`, `agcm_clash_tests`, `agcm_clash_results`
- Key entities: BIMModel, BIMViewpoint, BIMElement, BIMAnnotation3D, ClashTest, ClashResult
- IFC→XKT conversion via `convert2xkt` CLI through job queue
- XKT streaming: `GET /agcm_bim/models/{id}/xkt`
- Token-based auth for XKT downloads (`?token=JWT` pattern)
- 25 toolbar tools, 12 keyboard shortcuts
- BCF 2.1 viewpoint save/restore with screenshots
- 3D annotations with entity linking (RFI, Issue, Punch List)
- Multi-model federation with transforms
- IFC type color customization, explosion view, storey plans

### Workflow Connections
- Estimate → Budget: `send_to_budget()` creates agcm_finance.Budget records
- Change Order → Budget: auto-updates `committed_amount` on approval
- PO/Subcontract → Budget: auto-updates `committed_amount` on approval
- VendorBill/Timesheet/Expense → Budget: auto-updates `actual_amount` on approval
- **RFI → Change Order**: `POST /agcm_rfi/rfis/{id}/create-change-order` — creates draft CO pre-populated with RFI subject, question, cost_impact, schedule_impact_days, project_id
- Inspection fail → Punch List: auto-creates PunchListItem
- Bid awarded → Subcontract: auto-creates draft Subcontract
- BIM Viewpoints ↔ RFIs/Issues: cross-entity linking

### Project-Level Access Control
- **ProjectMember** (`agcm_project_members`): per-project user→role assignment
- Roles: `owner` > `manager` > `member` > `viewer` (hierarchy)
- Helper: `addons.agcm.services.project_access`
  - `get_user_project_ids(db, user_id, company_id, min_role=)` — list accessible project IDs
  - `has_project_access(db, user_id, project_id, min_role=)` — check single project
  - `check_project_role(db, user_id, project_id, min_role=)` — role hierarchy check
  - `get_project_role(db, user_id, project_id)` — get user's role string
- API: `GET/POST /agcm/projects/{id}/members`, `PUT /agcm/project-members/{id}/role`, `DELETE /agcm/project-members/{id}`
- Opt-in pattern for services:
  ```python
  from addons.agcm.services.project_access import get_user_project_ids
  project_ids = get_user_project_ids(db, user_id, company_id)
  query = query.filter(Model.project_id.in_(project_ids))
  ```

### Audit Trail & Activity
- **ActivityMixin**: 30+ models include `ActivityMixin` for automatic audit logging
- All mutations (create/update/delete) automatically logged with user, timestamp, field changes
- Frontend: `ActivityThread` Vue component for activity display in detail views
- Component location: `frontend/packages/effects/common-ui/src/components/activity-thread/activity-thread.vue`
- Props: `modelName`, `recordId`, `accessToken`, `apiBase`, `showMessages`, `showActivities`

### Caching
- Two-tier caching: L1 (in-process LRU 512) + L2 (Redis)
- Pattern: `cache.get_or_set(key, factory, ttl)` with stampede protection
- Compressed storage for values > 1KB: `cache.set_compressed/get_compressed`
- Cache invalidation: `_invalidate_<module>_cache(project_id=None)` pattern
- All 13 services use TTL=300s caching with distributed invalidation
- See `docs/SERVICE_STANDARDIZATION.md` for complete pattern documentation

### Soft Delete
- Models with soft delete: RFI, Task, ChangeOrder
- Mixin: `SoftDeleteMixin` adds `deleted_at` timestamp column
- Service methods: `delete_item()` (soft), `hard_delete_item()`, `restore_item()`
- API endpoints: `DELETE /{id}` (soft), `POST /{id}/restore`
- Deleted records excluded from queries unless `include_deleted=True`

### Field Indexes
- Frequently queried columns have indexes for performance
- Indexed: status, dates, foreign keys, company_id, project_id
- See individual model files for index definitions

### Service Standardization
All services follow `docs/SERVICE_STANDARDIZATION.md` pattern:
- List methods return `dict` with `items`, `total`, `page`, `page_size`
- Get methods return `Optional[Model]`
- Create/Update methods return `Model` or `Optional[Model]`
- Delete methods return `bool`
- Restore methods return `Optional[Model]`
- Services commit internally (no external transaction management)
