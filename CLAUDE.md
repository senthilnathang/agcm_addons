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

### Photo Storage
- Photos stored via core documents module (not binary blobs)
- Upload via multipart `POST /photos/upload`
- Files stored at `uploads/agcm/photos/YYYY/MM/DD/`

### Weather
- Two models: `WeatherForecast` (auto from weather.gov) and `Weather` (manual entry)
- Forecast fetched via weather.gov Points API → station observations / hourly forecast

### Reports
- HTML reports served at `/daily-logs/{id}/report/html?token=JWT`
- Token passed as query param for browser new-tab access (no Authorization header)
- `_render_report_html()` in `daily_logs.py` renders the full report
