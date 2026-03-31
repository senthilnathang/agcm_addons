<script setup>
import { computed, onMounted, ref, watch } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Badge,
  Button,
  Card,
  Col,
  Descriptions,
  DescriptionsItem,
  Drawer,
  Input,
  message,
  Modal,
  Popconfirm,
  Progress,
  Row,
  Select,
  SelectOption,
  Space,
  Statistic,
  Table,
  Tag,
  Tooltip,
  Upload,
} from 'ant-design-vue';
import {
  CloudUploadOutlined,
  DeleteOutlined,
  EyeOutlined,
  HistoryOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';
import { useRouter } from 'vue-router';

defineOptions({ name: 'AGCMBIMModels' });

const router = useRouter();
const BASE = '/agcm_bim';

const loading = ref(false);
const projectId = ref(null);
const projects = ref([]);
const models = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const filterDiscipline = ref(null);
const filterStatus = ref(null);
const searchText = ref('');

// Create modal
const showCreate = ref(false);
const createForm = ref({ name: '', description: '', discipline: null, file_format: null, project_id: null });
const creating = ref(false);

// Version drawer
const showVersions = ref(false);
const versions = ref([]);
const versionsLoading = ref(false);

const disciplineOptions = [
  { value: 'architectural', label: 'Architectural' },
  { value: 'structural', label: 'Structural' },
  { value: 'mep', label: 'MEP' },
  { value: 'civil', label: 'Civil' },
  { value: 'composite', label: 'Composite' },
];

const formatOptions = [
  { value: 'ifc', label: 'IFC' },
  { value: 'rvt', label: 'Revit (RVT)' },
  { value: 'nwd', label: 'Navisworks (NWD)' },
  { value: 'fbx', label: 'FBX' },
  { value: 'glb', label: 'glTF/GLB' },
  { value: 'obj', label: 'OBJ' },
];

const statusOptions = [
  { value: 'uploading', label: 'Uploading' },
  { value: 'processing', label: 'Processing' },
  { value: 'ready', label: 'Ready' },
  { value: 'failed', label: 'Failed' },
  { value: 'archived', label: 'Archived' },
];

const statusColors = {
  uploading: 'processing',
  processing: 'warning',
  ready: 'success',
  failed: 'error',
  archived: 'default',
};

const disciplineColors = {
  architectural: 'blue',
  structural: 'red',
  mep: 'green',
  civil: 'orange',
  composite: 'purple',
};

const columns = [
  { title: 'Seq', dataIndex: 'sequence_name', key: 'sequence_name', width: 120 },
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Discipline', dataIndex: 'discipline', key: 'discipline', width: 130 },
  { title: 'Format', dataIndex: 'file_format', key: 'file_format', width: 80 },
  { title: 'Status', dataIndex: 'status', key: 'status', width: 120 },
  { title: 'Version', dataIndex: 'version', key: 'version', width: 80 },
  { title: 'Elements', dataIndex: 'element_count', key: 'element_count', width: 100 },
  { title: 'Size', dataIndex: 'file_size', key: 'file_size', width: 100 },
  { title: 'Actions', key: 'actions', width: 180 },
];

function formatSize(bytes) {
  if (!bytes) return '-';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
}

async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = data.items || data.results || [];
  } catch { message.error('Failed to load projects'); }
}

async function fetchModels() {
  loading.value = true;
  try {
    const params = { page: page.value, page_size: pageSize.value };
    if (projectId.value) params.project_id = projectId.value;
    if (filterDiscipline.value) params.discipline = filterDiscipline.value;
    if (filterStatus.value) params.status = filterStatus.value;
    if (searchText.value) params.search = searchText.value;

    const data = await requestClient.get(`${BASE}/models`, { params });
    models.value = data.items || [];
    total.value = data.total || 0;
  } catch { message.error('Failed to load BIM models'); }
  finally { loading.value = false; }
}

function goToViewer(record) {
  router.push({ path: '/agcm/bim/viewer', query: { id: record.id } });
}

function openCreate() {
  createForm.value = { name: '', description: '', discipline: null, file_format: null, project_id: projectId.value };
  showCreate.value = true;
}

async function handleCreate() {
  if (!createForm.value.name || !createForm.value.project_id) {
    message.warning('Name and project are required');
    return;
  }
  creating.value = true;
  try {
    await requestClient.post(`${BASE}/models`, createForm.value);
    message.success('Model created');
    showCreate.value = false;
    fetchModels();
  } catch { message.error('Failed to create model'); }
  finally { creating.value = false; }
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/models/${record.id}`);
    message.success('Model deleted');
    fetchModels();
  } catch { message.error('Failed to delete model'); }
}

async function handleNewVersion(record) {
  try {
    await requestClient.post(`${BASE}/models/${record.id}/new-version`);
    message.success('New version created');
    fetchModels();
  } catch { message.error('Failed to create version'); }
}

async function handleProcess(record) {
  try {
    await requestClient.post(`${BASE}/models/${record.id}/process`);
    message.success('Model processing started');
    fetchModels();
  } catch { message.error('Failed to process model'); }
}

async function openVersions(record) {
  versionsLoading.value = true;
  showVersions.value = true;
  try {
    versions.value = await requestClient.get(`${BASE}/models/${record.id}/versions`);
  } catch { message.error('Failed to load versions'); }
  finally { versionsLoading.value = false; }
}

watch(projectId, () => { page.value = 1; fetchModels(); });

onMounted(async () => {
  await fetchProjects();
  fetchModels();
});
</script>

<template>
  <Page title="BIM 3D Models" description="Upload and manage Building Information Models across projects">
    <Card>
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <Select v-model:value="projectId" placeholder="All Projects" style="width: 260px" allow-clear show-search option-filter-prop="label">
          <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.sequence_name }} - {{ p.name }}</SelectOption>
        </Select>
        <Input v-model:value="searchText" placeholder="Search models..." style="width: 180px" allow-clear @press-enter="fetchModels">
          <template #prefix><SearchOutlined /></template>
        </Input>
        <Select v-model:value="filterDiscipline" placeholder="Discipline" style="width: 140px" allow-clear @change="fetchModels">
          <SelectOption v-for="d in disciplineOptions" :key="d.value" :value="d.value">{{ d.label }}</SelectOption>
        </Select>
        <Select v-model:value="filterStatus" placeholder="Status" style="width: 130px" allow-clear @change="fetchModels">
          <SelectOption v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</SelectOption>
        </Select>
        <div class="flex-1" />
        <Button @click="fetchModels"><template #icon><ReloadOutlined /></template>Refresh</Button>
        <Button type="primary" @click="openCreate"><template #icon><PlusOutlined /></template>Upload Model</Button>
      </div>

      <Table
        :columns="columns"
        :data-source="models"
        :loading="loading"
        row-key="id"
        size="middle"
        :pagination="{ current: page, pageSize, total, showSizeChanger: true, showTotal: (t) => `${t} models` }"
        @change="(p) => { page = p.current; pageSize = p.pageSize; fetchModels(); }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'discipline'">
            <Tag v-if="record.discipline" :color="disciplineColors[record.discipline]">{{ record.discipline }}</Tag>
            <span v-else>-</span>
          </template>
          <template v-else-if="column.key === 'file_format'">
            <Tag v-if="record.file_format">{{ (record.file_format || '').toUpperCase() }}</Tag>
            <span v-else>-</span>
          </template>
          <template v-else-if="column.key === 'status'">
            <Badge :status="statusColors[record.status] || 'default'" :text="record.status" />
          </template>
          <template v-else-if="column.key === 'version'">
            v{{ record.version }}
            <Tag v-if="record.is_current" color="green" size="small">current</Tag>
          </template>
          <template v-else-if="column.key === 'file_size'">
            {{ formatSize(record.file_size) }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Tooltip title="View model">
                <Button type="link" size="small" @click="goToViewer(record)"><EyeOutlined /></Button>
              </Tooltip>
              <Tooltip title="Version history">
                <Button type="link" size="small" @click="openVersions(record)"><HistoryOutlined /></Button>
              </Tooltip>
              <Tooltip title="Process">
                <Button type="link" size="small" @click="handleProcess(record)" :disabled="record.status === 'ready'"><ThunderboltOutlined /></Button>
              </Tooltip>
              <Popconfirm title="Delete this model?" @confirm="handleDelete(record)">
                <Button type="link" size="small" danger><DeleteOutlined /></Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <!-- Create Modal -->
    <Modal v-model:open="showCreate" title="Upload BIM Model" @ok="handleCreate" :confirm-loading="creating" ok-text="Create">
      <div class="flex flex-col gap-3 py-2">
        <div>
          <label class="mb-1 block text-sm font-medium">Project *</label>
          <Select v-model:value="createForm.project_id" placeholder="Select project" style="width: 100%" show-search option-filter-prop="label">
            <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.name }}</SelectOption>
          </Select>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">Model Name *</label>
          <Input v-model:value="createForm.name" placeholder="e.g. Structural Model - Building A" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">Description</label>
          <Input v-model:value="createForm.description" placeholder="Optional description" />
        </div>
        <Row :gutter="12">
          <Col :span="12">
            <label class="mb-1 block text-sm font-medium">Discipline</label>
            <Select v-model:value="createForm.discipline" placeholder="Select" style="width: 100%" allow-clear>
              <SelectOption v-for="d in disciplineOptions" :key="d.value" :value="d.value">{{ d.label }}</SelectOption>
            </Select>
          </Col>
          <Col :span="12">
            <label class="mb-1 block text-sm font-medium">Format</label>
            <Select v-model:value="createForm.file_format" placeholder="Select" style="width: 100%" allow-clear>
              <SelectOption v-for="f in formatOptions" :key="f.value" :value="f.value">{{ f.label }}</SelectOption>
            </Select>
          </Col>
        </Row>
      </div>
    </Modal>

    <!-- Version History Drawer -->
    <Drawer v-model:open="showVersions" title="Version History" width="500">
      <Table :data-source="versions" :loading="versionsLoading" row-key="id" size="small" :pagination="false">
        <template #default>
          <Table.Column title="Version" dataIndex="version" key="version" width="80">
            <template #default="{ record }">
              v{{ record.version }}
              <Tag v-if="record.is_current" color="green" size="small">current</Tag>
            </template>
          </Table.Column>
          <Table.Column title="Name" dataIndex="name" key="name" />
          <Table.Column title="Status" dataIndex="status" key="status" width="100">
            <template #default="{ record }">
              <Badge :status="statusColors[record.status] || 'default'" :text="record.status" />
            </template>
          </Table.Column>
          <Table.Column title="Created" dataIndex="created_at" key="created_at" width="160">
            <template #default="{ record }">
              {{ record.created_at ? new Date(record.created_at).toLocaleDateString() : '-' }}
            </template>
          </Table.Column>
        </template>
      </Table>
    </Drawer>
  </Page>
</template>
