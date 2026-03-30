# Claude Instructions for agcm_addons

## Module: AGCM (Construction Management)

This is a FastVue addon module for construction project daily activity logging. Migrated from Odoo's AGCM module.

## Critical Rules

### Import Namespace
- All imports MUST use `from addons.agcm.` prefix (NOT bare `from agcm.`)
- Example: `from addons.agcm.models.project import Project`
- The `AddonNamespaceFinder` maps `addons.agcm.*` to `agcm_addons/agcm/`

### API Router
- NEVER add `prefix=` to `APIRouter()` — loader auto-mounts at `/api/v1/agcm`
- Frontend `requestClient` already adds `/api/v1` — use paths like `/agcm/projects`

### Database
- All table names prefixed with `agcm_` (e.g. `agcm_projects`, `agcm_daily_activity_logs`)
- Every model must have `company_id` FK to `companies.id`
- Use `get_effective_company_id()` for company scoping in API endpoints
- Module tables are auto-created by AutoSchemaManager — no alembic migrations needed

### Sequences
- Use `sequence_service.py` for auto-generating codes: `Proj00001`, `DL00001`, `MP00001`, etc.
- Sequence config matches Odoo's `ir_sequence_data.xml` prefixes

### Frontend
- Vue 3 SFCs loaded at runtime by `vue3-sfc-loader`
- Use Ant Design Vue `A`-prefixed components (globally registered, no imports needed)
- Every `.vue` file needs a companion `.css` file (can be empty)
- Import API functions from `#/api/agcm`
- Import `requestClient` from `#/api/request`

### Pagination
- All paginated API endpoints MUST use `page_size: int = Query(20, ge=1, le=200)` (import `Query` from `fastapi`)
- Services should also enforce `page_size = min(page_size, 200)` as a safety net
- Frontend MUST NEVER request `page_size` greater than 200 — the API will reject with 422
- For project/user dropdowns use `page_size: 200` (the max), NOT 500 or unbounded

### Enum Columns
- New modules MUST use `Enum(MyEnum, values_callable=lambda e: [m.value for m in e])` so PostgreSQL stores lowercase values (e.g. `"in_progress"` not `"IN_PROGRESS"`)
- Do NOT add `values_callable` to existing base `agcm` module enums — they already use uppercase member names in the DB
- When passing enum values in seed scripts or API, use the lowercase string value (e.g. `"in_progress"`)

### Child Module Menus
- Child modules (agcm_rfi, agcm_finance, etc.) MUST NOT re-declare the "Construction" parent menu
- Instead, use `"parent": "agcm"` on each menu item to attach to the existing Construction menu
- For Settings sub-items, use `"parent": "agcm.settings"`
- Only the base `agcm` module declares the root `{"name": "Construction", "path": "/agcm"}` menu

### Photo Storage
- Photos stored via core documents module (not binary blobs)
- Upload via multipart `POST /photos/upload`
- Files stored at `uploads/agcm/photos/YYYY/MM/DD/`

### Real-time Events
- Service: `from addons.agcm.services.realtime_events import agcm_realtime`
- All events broadcast to **project team members** via `agcm_project_users` M2M
- Fire-and-forget pattern — `try: await agcm_realtime.xxx(db, entity) except: pass`
- Event types prefixed `agcm:` (e.g., `agcm:rfi:created`, `agcm:task:progress_changed`)
- Frontend listens: `const { on } = useRealtime(); on('agcm:rfi:response_new', handler)`
- No core framework changes needed — plugs into existing WebSocket room infrastructure
- Wired into: RFI (create, close, response), Tasks (create, status, progress), Submittals (create, approve), Change Orders (create, approve), Issues (create, update, resolve)

### Weather
- Two models: `WeatherForecast` (auto from weather.gov) and `Weather` (manual entry)
- Forecast fetched via weather.gov Points API → station observations / hourly forecast

### Reports
- HTML reports served at `/daily-logs/{id}/report/html?token=JWT`
- Token passed as query param for browser new-tab access (no Authorization header)
- `_render_report_html()` in `daily_logs.py` renders the full report
