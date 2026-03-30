<script setup>
import { computed, onMounted, ref, watch } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Badge,
  Button,
  Card,
  Col,
  Input,
  message,
  Popconfirm,
  Row,
  Select,
  SelectOption,
  Space,
  Table,
  Tag,
} from 'ant-design-vue';
import {
  DeleteOutlined,
  EyeOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';
import { useRouter } from 'vue-router';

defineOptions({ name: 'AGCMRFIs' });

const router = useRouter();
const BASE = '/agcm_rfi';

const loading = ref(false);
const projectId = ref(null);
const projects = ref([]);
const rfis = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const filterStatus = ref(null);
const filterPriority = ref(null);
const searchText = ref('');

const statusOptions = [
  { value: 'draft', label: 'Draft' },
  { value: 'open', label: 'Open' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'answered', label: 'Answered' },
  { value: 'closed', label: 'Closed' },
];

const priorityOptions = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
];

const statusColors = { draft: 'default', open: 'processing', in_progress: 'warning', answered: 'success', closed: 'default' };
const priorityColors = { low: 'green', medium: 'orange', high: 'red' };

const columns = [
  { title: 'Seq', dataIndex: 'sequence_name', key: 'sequence_name', width: 120 },
  { title: 'Subject', dataIndex: 'subject', key: 'subject' },
  { title: 'Priority', dataIndex: 'priority', key: 'priority', width: 100 },
  { title: 'Status', dataIndex: 'status', key: 'status', width: 130 },
  { title: 'Due Date', dataIndex: 'due_date', key: 'due_date', width: 120 },
  { title: 'Impact (Days)', dataIndex: 'schedule_impact_days', key: 'schedule_impact_days', width: 120 },
  { title: 'Cost Impact', dataIndex: 'cost_impact', key: 'cost_impact', width: 120 },
  { title: 'Actions', key: 'actions', width: 120 },
];

async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = data.items || data.results || [];
  } catch { message.error('Failed to load projects'); }
}

async function fetchRFIs() {
  loading.value = true;
  try {
    const params = { page: page.value, page_size: pageSize.value };
    if (projectId.value) params.project_id = projectId.value;
    if (filterStatus.value) params.status = filterStatus.value;
    if (filterPriority.value) params.priority = filterPriority.value;
    if (searchText.value) params.search = searchText.value;

    const data = await requestClient.get(`${BASE}/rfis`, { params });
    rfis.value = data.items || [];
    total.value = data.total || 0;
  } catch { message.error('Failed to load RFIs'); }
  finally { loading.value = false; }
}

function goToDetail(record) {
  router.push({ path: '/agcm/rfi/detail', query: { id: record.id } });
}

function goToForm(record) {
  const query = record ? { id: record.id } : {};
  if (projectId.value && !record) query.project_id = projectId.value;
  router.push({ path: '/agcm/rfi/form', query });
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/rfis/${record.id}`);
    message.success('RFI deleted');
    fetchRFIs();
  } catch { message.error('Failed to delete RFI'); }
}

watch(projectId, () => { page.value = 1; fetchRFIs(); });

onMounted(async () => {
  await fetchProjects();
  fetchRFIs();
});
</script>

<template>
  <Page title="Requests for Information" description="Track and manage RFIs across projects">
    <Card>
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <Select v-model:value="projectId" placeholder="All Projects" style="width: 260px" allow-clear show-search option-filter-prop="label">
          <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.sequence_name }} - {{ p.name }}</SelectOption>
        </Select>
        <Input v-model:value="searchText" placeholder="Search..." style="width: 180px" allow-clear @press-enter="fetchRFIs">
          <template #prefix><SearchOutlined /></template>
        </Input>
        <Select v-model:value="filterStatus" placeholder="Status" style="width: 130px" allow-clear @change="fetchRFIs">
          <SelectOption v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</SelectOption>
        </Select>
        <Select v-model:value="filterPriority" placeholder="Priority" style="width: 120px" allow-clear @change="fetchRFIs">
          <SelectOption v-for="p in priorityOptions" :key="p.value" :value="p.value">{{ p.label }}</SelectOption>
        </Select>
        <div class="flex-1" />
        <Button @click="fetchRFIs"><template #icon><ReloadOutlined /></template>Refresh</Button>
        <Button type="primary" @click="goToForm()"><template #icon><PlusOutlined /></template>New RFI</Button>
      </div>

      <Table
        :columns="columns"
        :data-source="rfis"
        :loading="loading"
        row-key="id"
        size="middle"
        :pagination="{ current: page, pageSize, total, showSizeChanger: true, showTotal: (t) => `${t} RFIs` }"
        @change="(p) => { page = p.current; pageSize = p.pageSize; fetchRFIs(); }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'priority'">
            <Tag :color="priorityColors[record.priority]">{{ record.priority }}</Tag>
          </template>
          <template v-else-if="column.key === 'status'">
            <Badge :status="statusColors[record.status] || 'default'" :text="(record.status || '').replace(/_/g, ' ')" />
          </template>
          <template v-else-if="column.key === 'cost_impact'">
            {{ record.cost_impact ? `$${Number(record.cost_impact).toLocaleString()}` : '-' }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="goToDetail(record)"><EyeOutlined /></Button>
              <Popconfirm title="Delete this RFI?" @confirm="handleDelete(record)">
                <Button type="link" size="small" danger><DeleteOutlined /></Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>
  </Page>
</template>
