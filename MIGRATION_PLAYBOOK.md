# Odoo to FastVue Migration Playbook

Step-by-step guide for migrating Odoo modules into FastVue addons.
Based on the AGCM (Construction Management) module migration as the reference implementation.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Phase 1: Read & Map the Odoo Module](#3-phase-1-read--map-the-odoo-module)
4. [Phase 2: Create Addon Directory](#4-phase-2-create-addon-directory)
5. [Phase 3: Models](#5-phase-3-models)
6. [Phase 4: Schemas](#6-phase-4-schemas)
6a. [Phase 6a: Reports (PDF)](#6a-phase-6a-reports-pdf)
7. [Phase 5: Services](#7-phase-5-services)
8. [Phase 6: API Routes](#8-phase-6-api-routes)
9. [Phase 7: Frontend API Client](#9-phase-7-frontend-api-client)
10. [Phase 8: Frontend Views](#10-phase-8-frontend-views)
11. [Phase 9: Manifest & Menus](#11-phase-9-manifest--menus)
12. [Phase 10: Environment & Startup](#12-phase-10-environment--startup)
13. [Odoo-to-FastVue Mapping Reference](#13-odoo-to-fastvue-mapping-reference)
14. [Common Pitfalls](#14-common-pitfalls)

---

## 1. Overview

### Migration Order (always follow this sequence)

```
1. Models        (SQLAlchemy tables + relationships)
2. Schemas       (Pydantic Create/Update/Response)
3. Services      (Business logic layer)
4. API Routes    (FastAPI endpoints)
5. Frontend API  (JavaScript client functions)
6. Frontend Views (Vue 3 SFCs)
7. Manifest      (Module registration + menus)
```

### Key Principles

- Module code MUST stay in its addon directory — never in `/app/` or frontend `src/`
- NEVER add `prefix=` to APIRouter — the module loader mounts at `/api/v1/{module}`
- `requestClient` already adds `/api/v1` — use relative paths like `/agcm/projects`
- Tables are auto-created on startup by AutoSchemaManager — no manual alembic needed for addon tables
- All models must be company-scoped (`company_id` FK to `companies.id`)

---

## 2. Prerequisites

Before starting, identify from the Odoo module:

- [ ] All model classes (in `models/` Python files)
- [ ] Field types and relationships (Many2one, One2many, Many2many)
- [ ] Business logic in `create()`, `write()`, `copy()` overrides
- [ ] Access control groups and rules (in `security/`)
- [ ] Controllers/endpoints (in `controllers/`)
- [ ] Wizard models (in `wizard/`)
- [ ] Menu structure (in `views/*.xml`)

---

## 3. Phase 1: Read & Map the Odoo Module

### Step 1: Catalog all Odoo models

For each model, document:

| Odoo Model | Odoo Table | FastVue Table | Type |
|---|---|---|---|
| `project` | `project` | `{module}_projects` | Core |
| `daily.activity.log` | `daily_activity_log` | `{module}_daily_activity_logs` | Core |
| `tradelist` | `tradelist` | `{module}_trades` | Lookup |
| `man.power` | `man_power` | `{module}_manpower` | Child |

### Step 2: Map relationships

| Odoo Relationship | FastVue Equivalent |
|---|---|
| `fields.Many2one('res.company')` | `Column(Integer, ForeignKey("companies.id"))` |
| `fields.Many2one('res.users')` | `Column(Integer, ForeignKey("users.id"))` |
| `fields.Many2one('other.model')` | `Column(Integer, ForeignKey("{module}_other_models.id"))` |
| `fields.One2many('child', 'parent_id')` | `relationship("child_table", back_populates="parent")` |
| `fields.Many2many('other', 'rel_table')` | `Table("rel_table", ...) + relationship(secondary=...)` |

### Step 3: Identify business logic to migrate

Look for these Odoo patterns:

- `@api.model_create_multi def create()` → Service `.create()` method
- `def write(vals)` → Service `.update()` method
- `def copy(default)` → Service `.copy()` / `.makelog()` method
- `ir.sequence` usage → Service `._next_sequence()` method
- `search_read` overrides → Service `.list()` with filters
- `@api.depends` computed fields → Service or model method
- Cron jobs → Background task / scheduled endpoint

---

## 4. Phase 2: Create Addon Directory

```bash
# From the project root
mkdir -p {your_addons_dir}/{module}/{models,schemas,services,api,static/api,static/views}
```

### Required files

```
{module}/
├── __init__.py               # Just a comment line
├── __manifest__.py            # Module metadata (Phase 9)
├── models/__init__.py         # Export all model classes
├── schemas/__init__.py        # Export all schemas
├── services/__init__.py       # Export service classes
├── api/__init__.py            # Export router (CRITICAL)
├── static/api/index.js        # Frontend API client
└── static/views/              # Vue SFC files
```

### api/__init__.py (CRITICAL — must export `router`)

```python
"""Module API Routes"""

from fastapi import APIRouter

from {module}.api.{entity1} import router as entity1_router
from {module}.api.{entity2} import router as entity2_router

router = APIRouter()
router.include_router(entity1_router)
router.include_router(entity2_router)
```

### __init__.py (root — minimal)

```python
# {Module Name}
```

---

## 5. Phase 3: Models

### Naming Convention

| Convention | Example |
|---|---|
| Table name | `{module}_{plural_entity}` e.g. `agcm_projects` |
| Class name | PascalCase e.g. `Project` |
| M2M table | `{module}_{entity1}_{entity2}` e.g. `agcm_project_users` |
| ForeignKey target | Always use `__tablename__` e.g. `"agcm_projects.id"` |
| Relationship target | Always use `__tablename__` e.g. `"agcm_projects"` |

### Available Base Classes & Mixins

```python
from app.db.base import Base
from app.models.base import (
    TimestampMixin,      # created_at, updated_at
    AuditMixin,          # created_by, updated_by (FK to users)
    SoftDeleteMixin,     # is_deleted, deleted_at, deleted_by + .soft_delete()
    ActiveMixin,         # is_active + .activate()/.deactivate()
    MetadataMixin,       # metadata_json, tags
    VersionMixin,        # version (optimistic locking)
    CompanyScopedMixin,  # company_id (alternative to manual FK)
)
```

### Pattern A: Simple Lookup Table

```python
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.base import TimestampMixin

class Trade(Base, TimestampMixin):
    __tablename__ = "agcm_trades"
    _description = "Construction trade classifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
```

### Pattern B: Core Model with Relationships

```python
import enum
from sqlalchemy import (
    Column, Date, Enum, Float, ForeignKey, Integer, String, Table, Index,
)
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin, SoftDeleteMixin

class ProjectStatus(str, enum.Enum):
    NEW = "new"
    IN_PROGRESS = "inprogress"
    COMPLETED = "completed"

# Many-to-many association table
agcm_project_users = Table(
    "agcm_project_users",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("agcm_projects.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)

class Project(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    __tablename__ = "agcm_projects"
    _description = "Construction projects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.NEW, nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    owner = relationship("User", foreign_keys=[owner_id], lazy="select")
    user_ids = relationship("User", secondary=agcm_project_users, lazy="dynamic")

    # One2Many children
    daily_logs = relationship(
        "agcm_daily_activity_logs",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_agcm_project_company_status", "company_id", "status"),
    )
```

### Pattern C: Child Entity (belongs to parent via FK)

```python
class ManPower(Base, TimestampMixin, AuditMixin):
    __tablename__ = "agcm_manpower"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence_name = Column(String(50), nullable=True)
    name = Column(String(255), nullable=True)

    # Parent FK
    dailylog_id = Column(Integer, ForeignKey("agcm_daily_activity_logs.id", ondelete="CASCADE"), nullable=False, index=True)

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    dailylog = relationship("agcm_daily_activity_logs", back_populates="manpower_lines", lazy="select")
```

### models/__init__.py

```python
"""Module Models"""

from {module}.models.lookups import Trade, InspectionType
from {module}.models.project import Project, ProjectStatus, agcm_project_users
from {module}.models.daily_log import DailyActivityLog
from {module}.models.manpower import ManPower

__all__ = [
    "Trade", "InspectionType",
    "Project", "ProjectStatus", "agcm_project_users",
    "DailyActivityLog",
    "ManPower",
]
```

---

## 6. Phase 4: Schemas

### Pattern: Create / Update / Response hierarchy

```python
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class ProjectBase(BaseModel):
    name: str
    ref_number: str
    start_date: date
    end_date: date
    owner_id: int
    status: Optional[str] = "new"

class ProjectCreate(ProjectBase):
    user_ids: Optional[List[int]] = []     # M2M handled separately

class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore unknown fields
    name: Optional[str] = None
    status: Optional[str] = None
    # ... all fields optional for PATCH semantics

class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # ORM mode
    id: int
    company_id: int
    name: str
    status: Optional[str] = None
    created_at: Optional[datetime] = None

class ProjectDetail(ProjectResponse):
    """Extended with computed/related fields"""
    user_ids: List[int] = []
    daily_log_count: int = 0
```

---

## 7. Phase 5: Services

### Service Class Pattern

```python
from sqlalchemy.orm import Session

class ProjectService:
    """Handles Project CRUD and business logic."""

    def __init__(self, db: Session, company_id: int, user_id: int):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id

    def _next_sequence(self) -> str:
        """Replaces Odoo ir.sequence — generate PROJ-0001, PROJ-0002, etc."""
        last = (
            self.db.query(Project.sequence_name)
            .filter(Project.company_id == self.company_id)
            .order_by(Project.id.desc())
            .first()
        )
        if last and last[0] and last[0].startswith("PROJ-"):
            try:
                num = int(last[0].split("-")[1]) + 1
            except (IndexError, ValueError):
                num = 1
        else:
            num = 1
        return f"PROJ-{num:04d}"

    def list_projects(self, page=1, page_size=20, search=None, status=None) -> dict:
        query = self.db.query(Project).filter(
            Project.company_id == self.company_id,
            Project.is_deleted == False,
        )
        if status:
            query = query.filter(Project.status == status)
        if search:
            query = query.filter(Project.name.ilike(f"%{search}%"))

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(Project.id.desc()).offset(skip).limit(page_size).all()

        return {
            "items": items, "results": items,
            "total": total, "count": total,
            "page": page, "page_size": page_size,
        }

    def create_project(self, data: ProjectCreate) -> Project:
        project = Project(
            company_id=self.company_id,
            sequence_name=self._next_sequence(),
            name=data.name,
            # ... map all fields ...
            created_by=self.user_id,
        )
        self.db.add(project)
        self.db.flush()
        # Handle M2M separately after flush (need project.id)
        self._sync_m2m_users(project.id, set(data.user_ids or []))
        self.db.commit()
        self.db.refresh(project)
        return project

    def _sync_m2m_users(self, project_id: int, user_ids: set):
        """Sync M2M relationship — delete all, re-insert."""
        self.db.execute(agcm_project_users.delete().where(
            agcm_project_users.c.project_id == project_id
        ))
        for uid in user_ids:
            self.db.execute(agcm_project_users.insert().values(
                project_id=project_id, user_id=uid
            ))
```

### Generic Child CRUD Pattern

For models that share the same CRUD shape (all daily log children), use a generic method:

```python
def create_child(self, model_class, data: dict):
    data["company_id"] = self.company_id
    data["created_by"] = self.user_id
    record = model_class(**data)
    self.db.add(record)
    self.db.commit()
    self.db.refresh(record)
    return record

def update_child(self, model_class, record_id: int, data: dict):
    record = self.db.query(model_class).filter(model_class.id == record_id).first()
    if not record:
        return None
    for key, value in data.items():
        setattr(record, key, value)
    record.updated_by = self.user_id
    self.db.commit()
    self.db.refresh(record)
    return record
```

---

## 8. Phase 6: API Routes

### Dependencies Available

```python
from app.api.deps import (
    get_db,                  # Session dependency
    get_current_user,        # Authenticated user
    get_effective_company_id,# Company ID with fallback
    PaginationParams,        # page, page_size, skip
    get_pagination,          # Pagination dependency
    company_scope,           # Filter clause for company isolation
)
```

### Pattern A: Standard CRUD Endpoints

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, get_effective_company_id, PaginationParams, get_pagination

router = APIRouter()  # NO prefix=

def _get_service(db, current_user):
    company_id = get_effective_company_id(current_user, db)
    return ProjectService(db=db, company_id=company_id, user_id=current_user.id)

@router.get("/projects", response_model=None)
async def list_projects(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    svc = _get_service(db, current_user)
    return svc.list_projects(page=pagination.page, page_size=pagination.page_size, ...)

@router.post("/projects", response_model=None, status_code=201)
async def create_project(data: ProjectCreate, db=Depends(get_db), current_user=Depends(get_current_user)):
    svc = _get_service(db, current_user)
    project = svc.create_project(data)
    return ProjectResponse.model_validate(project).model_dump()

@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(project_id: int, db=Depends(get_db), current_user=Depends(get_current_user)):
    svc = _get_service(db, current_user)
    if not svc.delete_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
```

### Pattern B: CRUD Route Factory (for many similar entities)

```python
def _child_crud_routes(prefix, model_class, create_schema, update_schema, response_schema):
    @router.get(f"/{prefix}", response_model=None)
    async def list_items(dailylog_id: int = Query(...), db=Depends(get_db), current_user=Depends(get_current_user), pagination=Depends(get_pagination)):
        svc = _get_service(db, current_user)
        return svc.list_children(model_class, dailylog_id, pagination.page, pagination.page_size)

    @router.post(f"/{prefix}", response_model=None, status_code=201)
    async def create_item(data: create_schema, db=Depends(get_db), current_user=Depends(get_current_user)):
        svc = _get_service(db, current_user)
        return response_schema.model_validate(svc.create_child(model_class, data.model_dump())).model_dump()

    # ... PUT, DELETE, GET by ID ...

    # CRITICAL: rename functions to avoid FastAPI route conflicts
    list_items.__name__ = f"list_{prefix}"
    create_item.__name__ = f"create_{prefix}"

# Register all at once
_child_crud_routes("manpower", ManPower, ManPowerCreate, ManPowerUpdate, ManPowerResponse)
_child_crud_routes("notes", Notes, NotesCreate, NotesUpdate, NotesResponse)
# ... etc
```

### Pattern C: Simple Lookup CRUD (no service layer needed)

```python
@router.get("/trades", response_model=list[LookupResponse])
async def list_trades(db=Depends(get_db), current_user=Depends(get_current_user)):
    company_id = get_effective_company_id(current_user, db)
    return db.query(Trade).filter(Trade.company_id == company_id).order_by(Trade.name).all()

@router.post("/trades", response_model=LookupResponse, status_code=201)
async def create_trade(data: LookupCreate, db=Depends(get_db), current_user=Depends(get_current_user)):
    company_id = get_effective_company_id(current_user, db)
    record = Trade(name=data.name, company_id=company_id)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
```

---

## 9. Phase 7: Frontend API Client

File: `static/api/index.js`

```javascript
import { requestClient } from '#/api/request';

const BASE_URL = '/{module}';  // e.g. '/agcm'

// CRUD pattern for each entity
export async function getProjectsApi(params = {}) {
  return requestClient.get(`${BASE_URL}/projects`, { params });
}
export async function getProjectApi(id) {
  return requestClient.get(`${BASE_URL}/projects/${id}`);
}
export async function createProjectApi(data) {
  return requestClient.post(`${BASE_URL}/projects`, data);
}
export async function updateProjectApi(id, data) {
  return requestClient.put(`${BASE_URL}/projects/${id}`, data);
}
export async function deleteProjectApi(id) {
  return requestClient.delete(`${BASE_URL}/projects/${id}`);
}
```

**Key rule**: `requestClient` already prepends `/api/v1`, so use paths like `/agcm/projects` not `/api/v1/agcm/projects`.

---

## 10. Phase 8: Frontend Views

### Framework: Vue 3 + Ant Design Vue + Vben Page

### Pattern A: List View (Table with Search/Filter/Pagination)

```vue
<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import {
  Button, Card, Input, message, Popconfirm, Select, Space, Table, Tag,
} from 'ant-design-vue';
import {
  DeleteOutlined, EditOutlined, EyeOutlined, PlusOutlined, ReloadOutlined, SearchOutlined,
} from '@ant-design/icons-vue';
import { getProjectsApi, deleteProjectApi } from '#/api/{module}';

defineOptions({ name: '{Module}List' });
const router = useRouter();

const pagination = ref({
  current: 1, pageSize: 20, total: 0,
  showSizeChanger: true, showTotal: (t) => `Total ${t} items`,
});
const loading = ref(false);
const items = ref([]);
const searchText = ref('');

const columns = computed(() => [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Status', key: 'status', width: 120 },
  { title: 'Actions', key: 'actions', width: 150, fixed: 'right' },
]);

async function fetchData() {
  loading.value = true;
  try {
    const params = {
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
      search: searchText.value || undefined,
    };
    const response = await getProjectsApi(params);
    items.value = response.items || [];
    pagination.value.total = response.total || 0;
  } catch { message.error('Failed to load'); }
  finally { loading.value = false; }
}

function onTableChange(pag) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

onMounted(fetchData);
</script>

<template>
  <Page title="Projects" description="Manage projects">
    <Card>
      <div class="mb-4 flex items-center justify-between">
        <Space>
          <Input v-model:value="searchText" placeholder="Search..." @press-enter="fetchData">
            <template #prefix><SearchOutlined /></template>
          </Input>
        </Space>
        <Button type="primary" @click="router.push('/{module}/form')">
          <template #icon><PlusOutlined /></template> New
        </Button>
      </div>
      <Table :columns="columns" :data-source="items" :loading="loading"
             :pagination="pagination" row-key="id" @change="onTableChange">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <Tag :color="record.status === 'active' ? 'green' : 'default'">{{ record.status }}</Tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="router.push(`/{module}/detail/${record.id}`)">
                <template #icon><EyeOutlined /></template>
              </Button>
              <Button type="link" size="small" @click="router.push(`/{module}/form/${record.id}`)">
                <template #icon><EditOutlined /></template>
              </Button>
              <Popconfirm title="Delete?" @confirm="handleDelete(record)">
                <Button type="link" size="small" danger>
                  <template #icon><DeleteOutlined /></template>
                </Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>
  </Page>
</template>
```

### Pattern B: Form View (Create/Edit)

```vue
<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import { Button, Card, Col, Divider, Form, FormItem, Input, message, Row, Select, Space } from 'ant-design-vue';
import { ArrowLeftOutlined, SaveOutlined } from '@ant-design/icons-vue';
import { createApi, getApi, updateApi } from '#/api/{module}';

const route = useRoute();
const router = useRouter();
const entityId = computed(() => route.params.id);
const isEdit = computed(() => !!entityId.value);
const saving = ref(false);
const formData = ref({ name: '', status: 'new' });

async function loadData() {
  if (!entityId.value) return;
  const data = await getApi(entityId.value);
  formData.value = { name: data.name, status: data.status };
}

async function handleSave() {
  saving.value = true;
  try {
    if (isEdit.value) {
      await updateApi(entityId.value, formData.value);
      message.success('Updated');
    } else {
      const result = await createApi(formData.value);
      message.success('Created');
      router.replace(`/{module}/form/${result.id}`);
    }
  } catch { message.error('Failed to save'); }
  finally { saving.value = false; }
}

onMounted(loadData);
</script>

<template>
  <Page auto-content-height>
    <Card :bordered="false">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
        <Space>
          <Button @click="router.push('/{module}/list')">
            <template #icon><ArrowLeftOutlined /></template> Back
          </Button>
          <h3 style="margin:0">{{ isEdit ? 'Edit' : 'New' }}</h3>
        </Space>
        <Button type="primary" :loading="saving" @click="handleSave">
          <template #icon><SaveOutlined /></template> Save
        </Button>
      </div>
      <Divider />
      <Form layout="vertical">
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Name" required>
              <Input v-model:value="formData.name" placeholder="Enter name" />
            </FormItem>
          </Col>
        </Row>
      </Form>
    </Card>
  </Page>
</template>
```

### Pattern C: Detail View (Read-only with Stats)

```vue
<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowLeftOutlined, EditOutlined } from '@ant-design/icons-vue';
import { getApi } from '#/api/{module}';

const route = useRoute();
const router = useRouter();
const entityId = computed(() => route.params.id);
const loading = ref(false);
const entity = ref(null);

async function fetchData() {
  loading.value = true;
  try { entity.value = await getApi(entityId.value); }
  catch { console.error('Failed to load'); }
  finally { loading.value = false; }
}

onMounted(fetchData);
</script>

<template>
  <div class="p-6">
    <ASpin :spinning="loading">
      <div class="mb-4 flex items-center gap-3">
        <AButton @click="router.push('/{module}/list')">
          <template #icon><ArrowLeftOutlined /></template> Back
        </AButton>
        <AButton v-if="entity" @click="router.push(`/{module}/form/${entityId}`)">
          <template #icon><EditOutlined /></template> Edit
        </AButton>
      </div>
      <template v-if="entity">
        <ACard class="mb-4">
          <h1 class="text-2xl font-bold">{{ entity.name }}</h1>
          <ATag>{{ entity.status }}</ATag>
        </ACard>
        <ACard title="Details">
          <ADescriptions :column="3" bordered size="small">
            <ADescriptionsItem label="Field">{{ entity.field || '-' }}</ADescriptionsItem>
          </ADescriptions>
        </ACard>
      </template>
      <AEmpty v-else-if="!loading" description="Not found" />
    </ASpin>
  </div>
</template>
```

### Pattern D: Settings / Lookup CRUD (Table + Modal)

```vue
<!-- Single-page CRUD with modal for create/edit -->
<script setup>
const API_URL = '/{module}/trades';
const ENTITY_NAME = 'Trade';
const modalVisible = ref(false);
const editingId = ref(null);
const formName = ref('');

function openCreate() { editingId.value = null; formName.value = ''; modalVisible.value = true; }
function openEdit(r) { editingId.value = r.id; formName.value = r.name; modalVisible.value = true; }

async function handleSave() {
  if (editingId.value) await requestClient.put(`${API_URL}/${editingId.value}`, { name: formName.value });
  else await requestClient.post(API_URL, { name: formName.value });
  modalVisible.value = false;
  fetchData();
}
</script>
```

---

## 11. Phase 9: Manifest & Menus

```python
{
    "name": "Module Name",
    "technical_name": "module_name",
    "version": "1.0.0",
    "summary": "Short description",
    "description": "...",
    "author": "FastVue",
    "license": "MIT",
    "category": "Category",

    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": ["base"],

    "models": ["models"],
    "api": ["api"],
    "services": ["services"],

    "views": [
        "views/list.vue",
        "views/form.vue",
        "views/detail.vue",
    ],

    "menus": [
        {
            "name": "Module",
            "path": "/module",
            "icon": "lucide:icon-name",
            "sequence": 40,
            "children": [
                {
                    "name": "Entity List",
                    "path": "/module/entities",
                    "icon": "lucide:list",
                    "sequence": 1,
                    "viewName": "list",       # maps to views/list.vue
                },
                # Hidden routes for form/detail (not in sidebar)
                {
                    "name": "Entity Form",
                    "path": "/module/entities/form",
                    "hideInMenu": True,
                    "viewName": "form",
                    "sequence": 100,
                },
                {
                    "name": "Entity Detail",
                    "path": "/module/entities/detail",
                    "hideInMenu": True,
                    "viewName": "detail",
                    "sequence": 101,
                },
            ],
        },
    ],

    "permissions": [...],
    "access_rights": [...],
}
```

---

## 12. Phase 10: Environment & Startup

### Create .env file

```bash
# Copy existing .env and change:
cp backend/.env backend/.env.{module}
# Edit: POSTGRES_DB=fastvue_{module}
# Edit: ADDONS_PATHS=addons,{your_addons_dir}
```

### Create database

```bash
PGPASSWORD="password" psql -h localhost -p 5433 -U user -d postgres \
  -c "CREATE DATABASE fastvue_{module};"
```

### Run

```bash
cd /opt/FastVue
ENV_FILE=backend/.env.{module} bash run.sh run
```

AutoSchemaManager auto-creates all addon tables on first startup. No alembic migration needed for addon tables.

### Verify

```bash
# Check routes loaded
curl http://localhost:8000/api/v1/{module}/projects
```

---

## 12a. Phase 11: Reports (PDF Generation)

Odoo uses QWeb XML templates rendered server-side to PDF via wkhtmltopdf.
FastVue replaces this with a **backend HTML-to-PDF endpoint** using WeasyPrint or
an equivalent Python library, serving the same report structure.

### Understanding the Odoo Report Structure

An Odoo report consists of these XML files:

| File | Purpose |
|---|---|
| `ir_actions_report.xml` | Report registration (name, model, filename) |
| `report_templates.xml` or `ir_actions_report_template.xml` | Header/footer layout + report body template |
| `report/dailylogreport.py` | Optional Python class for computed data |

#### Odoo Report Anatomy (from AGCM daily log report)

```
┌──────────────────────────────────────────────────────────────────┐
│ HEADER (repeats every page)                                      │
│  ┌──────────────┐                    Project: HCESD2 Admin Bldg  │
│  │  Company Logo │                   14418 Beaumont Hwy           │
│  │  + Address    │                   Houston Texas                │
│  └──────────────┘                                                │
├──────────────────────────────────────────────────────────────────┤
│ BODY                                                             │
│  Site Observation Report: Tuesday, 17 March 2026                 │
│                                                                  │
│  [Daily Snapshot] — weather at 6AM/9AM/12PM/3PM/6PM/9PM          │
│  [Manpower Report] — table: Comments|Location|Workers|Hours|Vendor│
│  [Notes Report] — table: Comments|Description                    │
│  [Inspection Report] — table: Type|Result                        │
│  [Visitors Report] — table: Name|Reason|Entry|Exit|Person|Comment│
│  [Delay Report] — table: Name|Reason|Delay|Contractor            │
│  [Deficiency Report] — table: Name|Description                   │
│  [Photos] — 2-column grid of resized images with captions        │
├──────────────────────────────────────────────────────────────────┤
│ FOOTER (repeats every page)                                      │
│  Project Name: HCESD2     Page: 1 of 5     By: Administrator    │
│  Report Date: 2026-03-17                   Printed On: 2026-03-29│
└──────────────────────────────────────────────────────────────────┘
```

### Key Odoo QWeb Patterns and Their FastVue Equivalents

#### 1. Report Registration

**Odoo** (`ir_actions_report.xml`):
```xml
<record id="action_report_dailylog" model="ir.actions.report">
    <field name="name">DailyLog</field>
    <field name="model">daily.activity.log</field>
    <field name="report_type">qweb-pdf</field>
    <field name="report_name">agcm.report_dailylog</field>
    <field name="print_report_name">
        'Daily Log - %s - %s' % (object.date, object.sequence_name)
    </field>
</record>
```

**FastVue equivalent**: A backend API endpoint that generates and returns PDF:
```python
@router.get("/daily-logs/{log_id}/report/pdf", response_class=Response)
async def export_daily_log_pdf(log_id: int, ...):
    # 1. Fetch data (log + all children)
    # 2. Render HTML template
    # 3. Convert to PDF (weasyprint/puppeteer)
    # 4. Return Response(content=pdf_bytes, media_type="application/pdf",
    #        headers={"Content-Disposition": f"attachment; filename=\"Daily Log - {log.date} - {log.sequence_name}.pdf\""})
```

#### 2. Header with Company Logo + Project Info

**Odoo QWeb** — uses `t-if` for office-specific addresses:
```xml
<div style="width:45%;float:left;">
    <img t-att-src="image_data_uri(o.company_id.logo)" alt="Logo"/>
    <t t-if="o.project_id.agcm_office=='east'">
        <li>3200 Wilcrest Drive, Suite #100</li>
        <li>Houston, TX 77042</li>
    </t>
    <t t-if="o.project_id.agcm_office=='south'">
        <li>1101 Ocean Drive</li>
        <li>Corpus Christi, TX 78404</li>
    </t>
</div>
<div style="width:55%;float:right;">
    <li>Project : <span t-esc="o.project_id.name"/></li>
    <li><span t-esc="o.project_id.street"/></li>
    <li><span t-esc="o.project_id.city"/> <span t-esc="o.project_id.state_id.name"/></li>
</div>
```

**FastVue equivalent** — Jinja2 template or HTML string:
```python
# In report service or template
OFFICE_ADDRESSES = {
    "east": ("3200 Wilcrest Drive, Suite #100", "Houston, TX 77042"),
    "south": ("1101 Ocean Drive", "Corpus Christi, TX 78404"),
    "central": ("85 N.E. Loop 410, Suite 600", "San Antonio, TX 78216"),
    "north": ("5606 SMU Boulevard, Suite #600752", "Dallas, TX 73560"),
}
address = OFFICE_ADDRESSES.get(project.agcm_office, OFFICE_ADDRESSES["east"])
```

#### 3. Report Body — Child Entity Tables

**Odoo QWeb** — conditional section with `t-if` + `t-foreach`:
```xml
<t t-if="o.manpower_lines">
    <h4>Manpower Report</h4>
    <table class="table table-sm">
        <thead>
            <tr>
                <th style="background-color:#D3D3D3;">Comments</th>
                <th style="background-color:#D3D3D3;">Location</th>
                <th style="background-color:#D3D3D3;">Number Of Workers</th>
                <th style="background-color:#D3D3D3;">Total Hours</th>
                <th style="background-color:#D3D3D3;">Vendor</th>
            </tr>
        </thead>
        <tbody>
            <t t-foreach="o.manpower_lines" t-as="manpower_line">
                <tr>
                    <td><span t-field="manpower_line.name"/></td>
                    <td><span t-field="manpower_line.location"/></td>
                    <td><span t-field="manpower_line.number_of_workers"/></td>
                    <td><span t-field="manpower_line.total_hours"/></td>
                    <td><span t-field="manpower_line.partner_id"/></td>
                </tr>
            </t>
        </tbody>
    </table>
</t>
```

**FastVue equivalent** — Jinja2 template:
```html
{% if manpower_lines %}
<h4>Manpower Report</h4>
<table class="report-table">
    <thead>
        <tr>
            <th>Comments</th>
            <th>Location</th>
            <th>Number Of Workers</th>
            <th>Total Hours</th>
            <th>Vendor</th>
        </tr>
    </thead>
    <tbody>
        {% for line in manpower_lines %}
        <tr>
            <td>{{ line.name or '' }}</td>
            <td>{{ line.location or '' }}</td>
            <td>{{ line.number_of_workers }}</td>
            <td>{{ line.total_hours }}</td>
            <td>{{ line.partner_name or '' }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% endif %}
```

#### 4. Photo Grid — 2-column layout with resized images

**Odoo QWeb** — calls `_get_two_rows()` to split photos into pairs, `base64_img_resize_report()` to resize:
```xml
<t t-set="photos_to_report" t-value="o._get_two_rows()"/>
<t t-if="photos_to_report">
    <h4>Photos</h4>
    <table>
        <t t-foreach="photos_to_report" t-as="pline">
            <tr>
                <t t-foreach="pline" t-as="plinel">
                    <td style="width: 420px;">
                        <span t-esc="o.base64_img_resize_report(plinel.image)"
                              t-options='{"widget": "image", "style":"width:420px;height:420px"}'/>
                        <span t-field="plinel.name"/>
                    </td>
                </t>
            </tr>
        </t>
    </table>
</t>
```

**FastVue equivalent** — pair photos in Python, embed as base64 `<img>` tags:
```python
import base64
from PIL import Image
import io

def resize_image_for_report(image_bytes, target_size=(420, 420)):
    """Resize image to fit target, center on white background."""
    img = Image.open(io.BytesIO(image_bytes))
    img.thumbnail(target_size, Image.LANCZOS)
    new_img = Image.new("RGB", target_size, (255, 255, 255))
    left = (target_size[0] - img.width) // 2
    top = (target_size[1] - img.height) // 2
    new_img.paste(img, (left, top))
    buf = io.BytesIO()
    new_img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def pair_items(items):
    """Split list into pairs for 2-column grid."""
    return [items[i:i+2] for i in range(0, len(items), 2)]
```

```html
<!-- Jinja2 template -->
{% if photos %}
<h4>Photos</h4>
<table>
    {% for pair in photo_pairs %}
    <tr>
        {% for photo in pair %}
        <td style="width:420px; vertical-align:top;">
            <img src="data:image/png;base64,{{ photo.image_b64 }}"
                 style="width:420px; height:420px;"/>
            <div>{{ photo.name }}</div>
        </td>
        {% endfor %}
    </tr>
    {% endfor %}
</table>
{% endif %}
```

#### 5. Footer — Page numbers + metadata

**Odoo QWeb** — uses wkhtmltopdf's `<span class="page"/>` magic:
```xml
<div class="footer">
    <span>Project Name: <span t-esc="o.project_id.name"/></span>
    <span style="float:right;">By: <span t-esc="user.name"/></span>
    <div>
        Report Date: <span t-esc="o.date"/>
        Page: <span class="page"/> of <span class="topage"/>
        Printed On: <span t-esc="datetime.datetime.now().strftime('%Y-%m-%d %H:%M')"/>
    </div>
</div>
```

**FastVue equivalent** — WeasyPrint uses CSS `@page` for repeating headers/footers:
```css
@page {
    size: letter;
    margin: 1in 0.75in;
    @top-left { content: element(header-left); }
    @top-right { content: element(header-right); }
    @bottom-left { content: "Project: " attr(data-project) "  |  Report Date: " attr(data-date); }
    @bottom-center { content: "Page " counter(page) " of " counter(pages); }
    @bottom-right { content: "By: " attr(data-user) "  |  Printed: " attr(data-printed); }
}
```

### QWeb-to-Jinja2 Migration Cheat Sheet

| Odoo QWeb | Jinja2 | Notes |
|---|---|---|
| `<t t-if="condition">` | `{% if condition %}` | |
| `<t t-foreach="list" t-as="item">` | `{% for item in list %}` | |
| `<span t-field="obj.field"/>` | `{{ obj.field }}` | |
| `<span t-esc="expr"/>` | `{{ expr }}` | |
| `t-att-src="image_data_uri(img)"` | `src="data:image/png;base64,{{ img_b64 }}"` | |
| `t-att-style="..."` | `style="{{ ... }}"` | |
| `<t t-set="var" t-value="expr"/>` | `{% set var = expr %}` | |
| `<t t-call="template_name"/>` | `{% include "template.html" %}` | |
| `<span class="page"/>` (wkhtmltopdf) | `counter(page)` (WeasyPrint CSS) | Page numbers |
| `t-options='{"widget": "image"}'` | `<img src="data:image/...;base64,..."/>` | |

### FastVue Report Implementation Pattern

```
{module}/
├── services/
│   └── report_service.py        # Data aggregation + PDF generation
├── templates/
│   └── daily_log_report.html    # Jinja2 HTML template
└── api/
    └── reports.py               # GET /{entity}/{id}/report/pdf
```

**Backend API endpoint**:
```python
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from weasyprint import HTML

@router.get("/daily-logs/{log_id}/report/pdf")
async def export_pdf(log_id: int, db=Depends(get_db), current_user=Depends(get_current_user)):
    svc = ReportService(db, company_id, user_id)
    html_content = svc.render_daily_log_report(log_id)
    pdf_bytes = HTML(string=html_content).write_pdf()
    filename = f"Daily Log - {log.date} - {log.sequence_name}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
```

**Frontend "Export PDF" button**:
```javascript
async function exportPdf(logId) {
  const response = await requestClient.get(
    `${BASE_URL}/daily-logs/${logId}/report/pdf`,
    { responseType: 'blob' }
  );
  const url = URL.createObjectURL(new Blob([response]));
  const a = document.createElement('a');
  a.href = url;
  a.download = `daily-log-${logId}.pdf`;
  a.click();
  URL.revokeObjectURL(url);
}
```

---

## 13. Odoo-to-FastVue Mapping Reference

### Field Types

| Odoo Field | SQLAlchemy Column |
|---|---|
| `fields.Char(size=128)` | `Column(String(128))` |
| `fields.Text()` | `Column(Text)` |
| `fields.Integer()` | `Column(Integer)` |
| `fields.Float()` | `Column(Float)` |
| `fields.Boolean()` | `Column(Boolean)` |
| `fields.Date()` | `Column(Date)` |
| `fields.Datetime()` | `Column(DateTime(timezone=True))` |
| `fields.Selection([...])` | `Column(Enum(MyEnum))` or `Column(String)` |
| `fields.Binary()` | `Column(LargeBinary)` |
| `fields.Json()` | `Column(JSON)` |
| `fields.Many2one('model')` | `Column(Integer, ForeignKey("table.id"))` |
| `fields.One2many('model','fk')` | `relationship("table", back_populates="parent")` |
| `fields.Many2many('model')` | `Table() + relationship(secondary=)` |

### Business Logic

| Odoo Pattern | FastVue Equivalent |
|---|---|
| `ir.sequence.next_by_code('x')` | `service._next_sequence()` |
| `@api.model_create_multi def create` | `service.create_entity()` |
| `def write(vals)` | `service.update_entity()` |
| `def copy(default)` | `service.copy_entity()` / `makelog()` |
| `@api.depends(...) def _compute` | Compute in service or model method |
| `@api.onchange(...)` | Frontend validation / watch |
| `search_read` domain filter | Service query `.filter(...)` |
| `self.env.user` | `current_user` from `Depends(get_current_user)` |
| `self.env.company` | `get_effective_company_id(current_user, db)` |
| `self.env['model'].browse(id)` | `db.query(Model).filter(Model.id == id).first()` |
| `self.env['model'].search([...])` | `db.query(Model).filter(...).all()` |
| `record.write({...})` | `setattr(record, key, val); db.commit()` |
| `record.unlink()` | `db.delete(record); db.commit()` |

### Access Control

| Odoo | FastVue |
|---|---|
| `res.groups` | `__manifest__.py` permissions list |
| `ir.model.access.csv` | `__manifest__.py` access_rights |
| `ir.rule` domain filters | Service-level query filters |
| `self.env.user.has_group('x')` | `PermissionChecker("permission.codename")` |

### Views

| Odoo View | FastVue Equivalent |
|---|---|
| `tree` view (XML) | Table in `list.vue` with columns array |
| `form` view (XML) | `form.vue` with Row/Col/FormItem |
| `search` view | Search + Select filters in list toolbar |
| `kanban` view | Card grid layout in list view |
| `action_window` | `router.push()` navigation |
| `wizard` (TransientModel) | Modal or separate form view |

---

## 14. Common Pitfalls

1. **DO NOT** add `prefix=` to `APIRouter()` — the loader auto-mounts at `/api/v1/{module}`
2. **DO NOT** include `/api/v1` in frontend API calls — `requestClient` adds it
3. **DO NOT** use class names in `relationship()` — use `__tablename__` for unambiguous lookup
4. **DO NOT** use `company_id` on User — it's `current_company_id`
5. **DO NOT** create alembic migrations for addon tables — AutoSchemaManager handles it
6. **DO NOT** put module code in `/app/` or `/frontend/src/` — keep in addon directory
7. **DO NOT** use bare `from {module}.` imports — MUST use `from addons.{module}.` (see #13 below)
8. **DO** prefix all table names with `{module}_` to avoid collisions
9. **DO** include `company_id` FK on every model for multi-tenancy
10. **DO** use `get_effective_company_id()` not `current_user.current_company_id` directly
11. **DO** return both `items`/`results` and `total`/`count` in list responses for client compatibility
12. **DO** rename factory-generated endpoint functions to avoid FastAPI duplicate name errors
13. **DO** use `cascade="all, delete-orphan"` on parent One2Many relationships
14. **DO** install the module via API (`POST /api/v1/modules/install/{name}`) — uninstalled modules have tables created but routes are NOT mounted
15. **DO** symlink your addons dir into `backend/` if it lives outside — ADDONS_PATHS are resolved relative to `backend/`

### CRITICAL: Import Path Convention

All addon modules (regardless of which physical directory they live in) use the unified
`addons.{module_name}` import namespace. **Never use bare module imports.**

```python
# CORRECT — unified addons namespace
from addons.agcm.models.project import Project
from addons.agcm.schemas.project import ProjectCreate
from addons.agcm.services.project_service import ProjectService

# WRONG — bare module name fails at runtime
from agcm.models.project import Project  # ModuleNotFoundError!
```

This applies to ALL internal cross-references: models/__init__.py, schemas/__init__.py,
services/__init__.py, api/__init__.py, and all service/api files that import models or schemas.

### Module Installation Requirement

After first startup, the module's tables are auto-created by AutoSchemaManager, but
**routes are only mounted for installed modules**. You must install via the API:

```bash
# Login first
TOKEN=$(curl -s -X POST http://localhost:8200/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@fastvue.com","password":"admin123"}' \
  | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

# Install the module
curl -X POST http://localhost:8200/api/v1/modules/install/{module_name} \
  -H "Authorization: Bearer $TOKEN"

# Restart backend to mount routes
```

---

## 15. Sequence Generation (ir.sequence Migration)

Odoo uses `ir.sequence` records defined in XML to auto-generate codes like `DL00001`, `Proj00002`.

### Odoo `ir_sequence_data.xml` Pattern

```xml
<record id="seq_daily_activity_log" model="ir.sequence">
    <field name="name">Daily Activity Log</field>
    <field name="code">daily.activity.log</field>
    <field name="prefix">DL</field>
    <field name="padding">5</field>
    <field name="company_id" eval="False"/>
</record>
```

### FastVue Equivalent: `sequence_service.py`

Create a centralized sequence generator:

```python
# services/sequence_service.py
import re
from sqlalchemy.orm import Session

SEQUENCE_CONFIG = {
    "agcm_projects":            ("Proj", 5),
    "agcm_daily_activity_logs": ("DL", 5),
    "agcm_manpower":            ("MP", 5),
    "agcm_accidents":           ("ACC", 5),
    "agcm_weather":             ("Weather", 5),
    "agcm_notes":               ("Observations", 5),
    "agcm_inspections":         ("Inspection", 5),
    "agcm_visitors":            ("Visitor", 5),
    "agcm_safety_violations":   ("SV", 5),
    "agcm_delays":              ("Delay", 5),
    "agcm_photos":              ("PH", 5),
}

def next_sequence(db: Session, model_class, company_id: int) -> str:
    tablename = model_class.__tablename__
    prefix, padding = SEQUENCE_CONFIG.get(tablename, ("SEQ", 5))

    last = (
        db.query(model_class.sequence_name)
        .filter(model_class.company_id == company_id)
        .filter(model_class.sequence_name.isnot(None))
        .order_by(model_class.id.desc())
        .first()
    )
    num = 1
    if last and last[0]:
        match = re.search(r'(\d+)$', last[0])
        if match:
            num = int(match.group(1)) + 1
    return f"{prefix}{num:0{padding}d}"
```

Then call from services:
```python
from .sequence_service import next_sequence

# In create methods:
data["sequence_name"] = next_sequence(self.db, ModelClass, self.company_id)
```

### Mapping Odoo Prefixes to FastVue

| Odoo Code | Prefix | Padding | Example |
|---|---|---|---|
| `project` | Proj | 5 | Proj00001 |
| `daily.activity.log` | DL | 5 | DL00001 |
| `man.power` | MP | 5 | MP00001 |
| `accident` | ACC | 5 | ACC00001 |
| `weather` | Weather | 5 | Weather00001 |
| `notes` | Observations | 5 | Observations00001 |
| `inspection` | Inspection | 5 | Inspection00001 |
| `visitor` | Visitor | 5 | Visitor00001 |
| `safety.violation` | SV | 5 | SV00001 |
| `delay` | Delay | 5 | Delay00001 |
| `photo` | PH | 5 | PH00001 |

---

## 16. Odoo Cron Jobs → FastVue Background Tasks

Odoo uses `ir.cron` XML records for scheduled tasks. In AGCM, weather cron jobs fetch weather data at 6AM/9AM/12PM/3PM/6PM intervals.

### Odoo Pattern (weather_cron.xml)

```xml
<record forcecreate="True" id="ir_cron_auto_post_weather_6am" model="ir.cron">
    <field name="name">Weather : Auto Post Weather Entries at 6:00</field>
    <field name="model_id" ref="model_weather"/>
    <field name="state">code</field>
    <field name="code">model._autopost_weather_entries([6])</field>
    <field name="interval_number">3</field>
    <field name="interval_type">hours</field>
    <field name="numbercall">-1</field>
</record>
```

### FastVue Equivalent Options

1. **APScheduler** (already in FastVue):
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(fetch_weather, 'cron', hour=6, minute=0)
scheduler.add_job(fetch_weather, 'cron', hour=9, minute=0)
```

2. **FastAPI background tasks** for on-demand fetching
3. **Celery** for production-grade distributed scheduling

---

## Reference Implementation

See the complete AGCM module at: `/opt/FastVue/agcm_addons/agcm/`

```
40+ files, ~6,000+ lines
19 database tables (17 entity + 2 M2M)
72+ API endpoints
11 Vue frontend views
```
