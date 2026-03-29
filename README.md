# FastVue AGCM Addons

Construction Management addons for the [FastVue](https://github.com/senthilnathang/FastVue) framework. A daily activity logging system for construction projects — migrated from Odoo's AGCM module.

## Repository

| Item | Details |
|------|---------|
| **Standalone repo** | https://github.com/senthilnathang/agcm_addons |
| **Parent framework** | https://github.com/senthilnathang/FastVue |
| **Install path** | `backend/agcm_addons/` inside a FastVue deployment (symlink or copy) |
| **Module count** | 1 module (`agcm`) |

---

## Features

### Core Entities
- **Projects** — construction projects with location, contractors, trades, geolocation
- **Daily Activity Logs** — per-project daily records with date validation
- **Manpower** — worker tracking (workers, hours, total hours, contractor)
- **Notes/Observations** — daily site observations
- **Inspections** — third-party inspection records with type and result
- **Accidents** — incident reporting with resolution tracking
- **Visitors** — visitor log with entry/exit times
- **Safety Observations** — safety violation/observation notices
- **Delays** — delay tracking with reason and contractor
- **Deficiencies** — deficiency reports
- **Photos** — site photo documentation via core documents module (multipart upload)
- **Weather** — auto-fetched forecast from weather.gov + manual observations

### Dashboards
- **Overview Dashboard** — executive KPIs across all projects (status, manpower, safety, weather)
- **Project Analytics** — single project deep-dive with trends, funnel, and inspection results
- **Daily Log Analytics** — single day breakdown with weather strip and activity distribution

### Reports
- **Daily Log PDF** — individual daily log report matching the Odoo PDF layout
- **Periodic Project Report** — combined multi-day report with cover page and page breaks

### Settings
- Trades, Inspection Types, Accident Types, Violation Types — CRUD configuration tables

---

## Module Structure

```
agcm_addons/
├── agcm/
│   ├── __manifest__.py              # Module metadata, menus, permissions
│   ├── __init__.py
│   ├── models/                       # 13 SQLAlchemy models (17 tables + 2 M2M)
│   │   ├── project.py               # Project + M2M association tables
│   │   ├── daily_activity_log.py    # Central daily log hub
│   │   ├── manpower.py, notes.py, inspection.py, accident.py
│   │   ├── visitor.py, safety_violation.py, delay.py, deficiency.py
│   │   ├── photo.py                 # Documents module integration
│   │   ├── weather.py               # Weather + WeatherForecast
│   │   └── lookups.py               # Trade, InspectionType, AccidentType, ViolationType
│   ├── schemas/                      # Pydantic Create/Update/Response schemas
│   ├── services/                     # Business logic layer
│   │   ├── project_service.py       # CRUD + M2M sync + sequence gen
│   │   ├── daily_activity_log_service.py  # CRUD + makelog copy + child CRUD
│   │   ├── weather_service.py       # weather.gov API + manual weather
│   │   └── sequence_service.py      # Odoo ir.sequence equivalent
│   ├── api/                          # FastAPI route handlers
│   │   ├── projects.py, daily_logs.py, settings.py
│   │   ├── weather.py, photos.py, dashboard.py
│   │   └── __init__.py              # Router wiring
│   ├── static/
│   │   ├── api/index.js             # Frontend API client
│   │   └── views/                    # Vue 3 SFC views
│   │       ├── dashboard-overview.vue, dashboard-project.vue, dashboard-dailylog.vue
│   │       ├── projects.vue, project-form.vue, project-detail.vue
│   │       ├── daily-logs.vue, daily-log-form.vue, daily-log-detail.vue, daily-log-copy.vue
│   │       ├── periodic-report.vue
│   │       └── settings-*.vue
│   └── scripts/
│       └── seed_demo_data.py        # Demo data generator (500+ records per table)
├── MIGRATION_PLAYBOOK.md            # Complete Odoo-to-FastVue migration guide
└── README.md
```

---

## Installation

### 1. Clone into FastVue

```bash
cd /opt/FastVue
git clone https://github.com/senthilnathang/agcm_addons.git
ln -s /opt/FastVue/agcm_addons /opt/FastVue/backend/agcm_addons
```

### 2. Configure Environment

```bash
cp backend/.env backend/.env.agcm
# Edit .env.agcm:
#   POSTGRES_DB=fastvue_agcm
#   ADDONS_PATHS=addons,agcm_addons
```

### 3. Create Database

```bash
PGPASSWORD="password" psql -h localhost -p 5433 -U user -d postgres \
  -c "CREATE DATABASE fastvue_agcm;"
```

### 4. Initialize & Install Module

```bash
# Initialize core tables + seed admin user
bash run.sh init --env-file backend/.env.agcm

# Start backend
bash run.sh run backend --env-file backend/.env.agcm --backend-port 8200

# Install the AGCM module
TOKEN=$(curl -s -X POST http://localhost:8200/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@fastvue.com","password":"admin123"}' \
  | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

curl -X POST http://localhost:8200/api/v1/modules/install/agcm \
  -H "Authorization: Bearer $TOKEN"

# Restart backend to mount routes
# Start frontend
```

### 5. Load Demo Data (Optional)

```bash
cd /opt/FastVue/backend
source .venv/bin/activate
PYTHONPATH="/opt/FastVue/agcm_addons:." ENV_FILE=.env.agcm \
  python /opt/FastVue/agcm_addons/agcm/scripts/seed_demo_data.py
```

---

## API Endpoints

All endpoints mount at `/api/v1/agcm/...`

| Group | Endpoints |
|-------|-----------|
| Projects | `GET/POST /projects`, `GET/PUT/DELETE /projects/{id}` |
| Daily Logs | `GET/POST /daily-logs`, `GET/PUT/DELETE /daily-logs/{id}`, `POST /daily-logs/makelog` |
| Child Entities | CRUD for `/manpower`, `/notes`, `/inspections`, `/accidents`, `/visitors`, `/safety-violations`, `/delays`, `/deficiencies` |
| Photos | `GET /photos`, `POST /photos/upload` (multipart), `DELETE /photos/{id}` |
| Weather | `POST /weather/fetch-forecast`, `GET /weather/forecast`, `GET/POST /weather/manual` |
| Settings | CRUD for `/trades`, `/inspection-types`, `/accident-types`, `/violation-types` |
| Dashboards | `GET /dashboard/overview`, `/dashboard/project/{id}`, `/dashboard/dailylog/{id}` |
| Reports | `GET /daily-logs/{id}/report/html`, `/daily-logs/{id}/report/pdf`, `/reports/periodic` |

---

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: Vue 3, Ant Design Vue, Vben Admin, ECharts
- **File Storage**: Core documents module (local/S3)
- **Weather API**: weather.gov (NWS)

---

## Migration Reference

See [MIGRATION_PLAYBOOK.md](MIGRATION_PLAYBOOK.md) for the complete Odoo-to-FastVue migration guide covering models, schemas, services, APIs, views, reports, sequences, and cron jobs.
