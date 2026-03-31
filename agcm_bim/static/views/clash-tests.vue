<script setup>
import { onMounted, ref, watch } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Badge,
  Button,
  Card,
  Col,
  Input,
  InputNumber,
  message,
  Modal,
  Popconfirm,
  Row,
  Select,
  SelectOption,
  Space,
  Spin,
  Table,
  Tag,
  Tooltip,
} from 'ant-design-vue';
import {
  DeleteOutlined,
  EyeOutlined,
  PlusOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
  SearchOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';
import { useRouter } from 'vue-router';

defineOptions({ name: 'AGCMClashTests' });

const router = useRouter();
const BASE = '/agcm_bim';

const loading = ref(false);
const projectId = ref(null);
const projects = ref([]);
const tests = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const filterStatus = ref(null);

// Models for selection
const bimModels = ref([]);

// Create modal
const showCreate = ref(false);
const createForm = ref({ name: '', description: '', project_id: null, model_a_id: null, model_b_id: null, test_type: 'hard', tolerance: 0.01 });
const creating = ref(false);

// Running state
const runningId = ref(null);

const statusOptions = [
  { value: 'pending', label: 'Pending' },
  { value: 'running', label: 'Running' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
];

const testTypeOptions = [
  { value: 'hard', label: 'Hard Clash (physical overlap)' },
  { value: 'soft', label: 'Soft Clash (clearance zone)' },
  { value: 'clearance', label: 'Clearance (min distance)' },
  { value: 'duplicate', label: 'Duplicate Detection' },
];

const statusColors = { pending: 'default', running: 'processing', completed: 'success', failed: 'error' };
const severityColors = { critical: '#f5222d', major: '#fa8c16', minor: '#faad14', info: '#1890ff' };

const columns = [
  { title: 'Seq', dataIndex: 'sequence_name', key: 'sequence_name', width: 110 },
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Type', dataIndex: 'test_type', key: 'test_type', width: 100 },
  { title: 'Status', dataIndex: 'status', key: 'status', width: 120 },
  { title: 'Total', dataIndex: 'total_clashes', key: 'total_clashes', width: 80 },
  { title: 'Severity', key: 'severity', width: 200 },
  { title: 'Duration', dataIndex: 'duration_seconds', key: 'duration', width: 100 },
  { title: 'Actions', key: 'actions', width: 160 },
];

async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = data.items || data.results || [];
  } catch { message.error('Failed to load projects'); }
}

async function fetchModels() {
  if (!projectId.value) { bimModels.value = []; return; }
  try {
    const data = await requestClient.get(`${BASE}/models`, { params: { project_id: projectId.value, page_size: 200, status: 'ready' } });
    bimModels.value = data.items || [];
  } catch { bimModels.value = []; }
}

async function fetchTests() {
  loading.value = true;
  try {
    const params = { page: page.value, page_size: pageSize.value };
    if (projectId.value) params.project_id = projectId.value;
    if (filterStatus.value) params.status = filterStatus.value;

    const data = await requestClient.get(`${BASE}/clash-tests`, { params });
    tests.value = data.items || [];
    total.value = data.total || 0;
  } catch { message.error('Failed to load clash tests'); }
  finally { loading.value = false; }
}

function goToResults(record) {
  router.push({ path: '/agcm/bim/clash-results', query: { test_id: record.id } });
}

function openCreate() {
  createForm.value = { name: '', description: '', project_id: projectId.value, model_a_id: null, model_b_id: null, test_type: 'hard', tolerance: 0.01 };
  showCreate.value = true;
}

async function handleCreate() {
  if (!createForm.value.name || !createForm.value.project_id) {
    message.warning('Name and project are required');
    return;
  }
  creating.value = true;
  try {
    await requestClient.post(`${BASE}/clash-tests`, createForm.value);
    message.success('Clash test created');
    showCreate.value = false;
    fetchTests();
  } catch { message.error('Failed to create clash test'); }
  finally { creating.value = false; }
}

async function handleRun(record) {
  runningId.value = record.id;
  try {
    await requestClient.post(`${BASE}/clash-tests/${record.id}/run`);
    message.success('Clash test completed');
    fetchTests();
  } catch { message.error('Clash test failed'); }
  finally { runningId.value = null; }
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/clash-tests/${record.id}`);
    message.success('Clash test deleted');
    fetchTests();
  } catch { message.error('Failed to delete'); }
}

watch(projectId, () => { page.value = 1; fetchTests(); fetchModels(); });

onMounted(async () => {
  await fetchProjects();
  fetchTests();
});
</script>

<template>
  <Page title="Clash Detection" description="Run AABB-based clash tests between BIM models and track resolution">
    <Card>
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <Select v-model:value="projectId" placeholder="All Projects" style="width: 260px" allow-clear show-search option-filter-prop="label">
          <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.sequence_name }} - {{ p.name }}</SelectOption>
        </Select>
        <Select v-model:value="filterStatus" placeholder="Status" style="width: 130px" allow-clear @change="fetchTests">
          <SelectOption v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</SelectOption>
        </Select>
        <div class="flex-1" />
        <Button @click="fetchTests"><template #icon><ReloadOutlined /></template>Refresh</Button>
        <Button type="primary" @click="openCreate"><template #icon><PlusOutlined /></template>New Clash Test</Button>
      </div>

      <Table
        :columns="columns"
        :data-source="tests"
        :loading="loading"
        row-key="id"
        size="middle"
        :pagination="{ current: page, pageSize, total, showSizeChanger: true, showTotal: (t) => `${t} tests` }"
        @change="(p) => { page = p.current; pageSize = p.pageSize; fetchTests(); }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'test_type'">
            <Tag>{{ record.test_type }}</Tag>
          </template>
          <template v-else-if="column.key === 'status'">
            <Badge :status="statusColors[record.status] || 'default'" :text="record.status" />
          </template>
          <template v-else-if="column.key === 'severity'">
            <Space v-if="record.total_clashes > 0">
              <Tag v-if="record.critical_count" color="red">{{ record.critical_count }} critical</Tag>
              <Tag v-if="record.major_count" color="orange">{{ record.major_count }} major</Tag>
              <Tag v-if="record.minor_count" color="gold">{{ record.minor_count }} minor</Tag>
            </Space>
            <span v-else>-</span>
          </template>
          <template v-else-if="column.key === 'duration'">
            {{ record.duration_seconds ? record.duration_seconds.toFixed(1) + 's' : '-' }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Tooltip title="View results">
                <Button type="link" size="small" @click="goToResults(record)" :disabled="record.status !== 'completed'"><EyeOutlined /></Button>
              </Tooltip>
              <Tooltip title="Run test">
                <Button type="link" size="small" @click="handleRun(record)" :loading="runningId === record.id"><PlayCircleOutlined /></Button>
              </Tooltip>
              <Popconfirm title="Delete this test?" @confirm="handleDelete(record)">
                <Button type="link" size="small" danger><DeleteOutlined /></Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <!-- Create Modal -->
    <Modal v-model:open="showCreate" title="New Clash Test" @ok="handleCreate" :confirm-loading="creating" ok-text="Create" width="600">
      <div class="flex flex-col gap-3 py-2">
        <div>
          <label class="mb-1 block text-sm font-medium">Project *</label>
          <Select v-model:value="createForm.project_id" placeholder="Select project" style="width: 100%" show-search option-filter-prop="label" @change="fetchModels">
            <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.name }}</SelectOption>
          </Select>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">Test Name *</label>
          <Input v-model:value="createForm.name" placeholder="e.g. Structural vs MEP - Level 2" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">Description</label>
          <Input v-model:value="createForm.description" placeholder="Optional description" />
        </div>
        <Row :gutter="12">
          <Col :span="12">
            <label class="mb-1 block text-sm font-medium">Model A</label>
            <Select v-model:value="createForm.model_a_id" placeholder="Select model" style="width: 100%" allow-clear show-search option-filter-prop="label">
              <SelectOption v-for="m in bimModels" :key="m.id" :value="m.id" :label="m.name">{{ m.sequence_name }} - {{ m.name }}</SelectOption>
            </Select>
          </Col>
          <Col :span="12">
            <label class="mb-1 block text-sm font-medium">Model B (same for self-clash)</label>
            <Select v-model:value="createForm.model_b_id" placeholder="Select model" style="width: 100%" allow-clear show-search option-filter-prop="label">
              <SelectOption v-for="m in bimModels" :key="m.id" :value="m.id" :label="m.name">{{ m.sequence_name }} - {{ m.name }}</SelectOption>
            </Select>
          </Col>
        </Row>
        <Row :gutter="12">
          <Col :span="12">
            <label class="mb-1 block text-sm font-medium">Test Type</label>
            <Select v-model:value="createForm.test_type" style="width: 100%">
              <SelectOption v-for="t in testTypeOptions" :key="t.value" :value="t.value">{{ t.label }}</SelectOption>
            </Select>
          </Col>
          <Col :span="12">
            <label class="mb-1 block text-sm font-medium">Tolerance (meters)</label>
            <InputNumber v-model:value="createForm.tolerance" :min="0.001" :max="1" :step="0.01" style="width: 100%" />
          </Col>
        </Row>
      </div>
    </Modal>
  </Page>
</template>
