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

defineOptions({ name: 'AGCMChangeOrders' });

const router = useRouter();
const BASE = '/agcm_change_order';

const loading = ref(false);
const projectId = ref(null);
const projects = ref([]);
const changeOrders = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const filterStatus = ref(null);
const searchText = ref('');

const statusOptions = [
  { value: 'draft', label: 'Draft' },
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'void', label: 'Void' },
];

const statusColors = {
  draft: 'default',
  pending: 'processing',
  approved: 'success',
  rejected: 'error',
  void: 'default',
};

const columns = [
  { title: 'Seq', dataIndex: 'sequence_name', key: 'sequence_name', width: 120 },
  { title: 'Title', dataIndex: 'title', key: 'title' },
  { title: 'Status', dataIndex: 'status', key: 'status', width: 130 },
  { title: 'Cost Impact', dataIndex: 'cost_impact', key: 'cost_impact', width: 140 },
  { title: 'Schedule Impact', dataIndex: 'schedule_impact_days', key: 'schedule_impact_days', width: 140 },
  { title: 'Requested Date', dataIndex: 'requested_date', key: 'requested_date', width: 140 },
  { title: 'Actions', key: 'actions', width: 120 },
];

async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = data.items || data.results || [];
  } catch { message.error('Failed to load projects'); }
}

async function fetchChangeOrders() {
  loading.value = true;
  try {
    const params = { page: page.value, page_size: pageSize.value };
    if (projectId.value) params.project_id = projectId.value;
    if (filterStatus.value) params.status = filterStatus.value;
    if (searchText.value) params.search = searchText.value;

    const data = await requestClient.get(`${BASE}/change-orders`, { params });
    changeOrders.value = data.items || [];
    total.value = data.total || 0;
  } catch { message.error('Failed to load change orders'); }
  finally { loading.value = false; }
}

function goToDetail(record) {
  router.push({ path: '/agcm/change-orders/detail', query: { id: record.id } });
}

function goToForm(record) {
  const query = record ? { id: record.id } : {};
  if (projectId.value && !record) query.project_id = projectId.value;
  router.push({ path: '/agcm/change-orders/form', query });
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/change-orders/${record.id}`);
    message.success('Change order deleted');
    fetchChangeOrders();
  } catch { message.error('Failed to delete change order'); }
}

function formatCurrency(val) {
  if (val == null) return '-';
  return `$${Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

watch(projectId, () => { page.value = 1; fetchChangeOrders(); });

onMounted(async () => {
  await fetchProjects();
  fetchChangeOrders();
});
</script>

<template>
  <Page title="Change Orders" description="Track and manage construction change orders">
    <Card>
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <Select v-model:value="projectId" placeholder="All Projects" style="width: 260px" allow-clear show-search option-filter-prop="label">
          <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.sequence_name }} - {{ p.name }}</SelectOption>
        </Select>
        <Input v-model:value="searchText" placeholder="Search..." style="width: 180px" allow-clear @press-enter="fetchChangeOrders">
          <template #prefix><SearchOutlined /></template>
        </Input>
        <Select v-model:value="filterStatus" placeholder="Status" style="width: 130px" allow-clear @change="fetchChangeOrders">
          <SelectOption v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</SelectOption>
        </Select>
        <div class="flex-1" />
        <Button @click="fetchChangeOrders"><template #icon><ReloadOutlined /></template>Refresh</Button>
        <Button type="primary" @click="goToForm()"><template #icon><PlusOutlined /></template>New Change Order</Button>
      </div>

      <Table
        :columns="columns"
        :data-source="changeOrders"
        :loading="loading"
        row-key="id"
        size="middle"
        :pagination="{ current: page, pageSize, total, showSizeChanger: true, showTotal: (t) => `${t} change orders` }"
        @change="(p) => { page = p.current; pageSize = p.pageSize; fetchChangeOrders(); }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <Badge :status="statusColors[record.status] || 'default'" :text="(record.status || '').replace(/_/g, ' ')" />
          </template>
          <template v-else-if="column.key === 'cost_impact'">
            {{ formatCurrency(record.cost_impact) }}
          </template>
          <template v-else-if="column.key === 'schedule_impact_days'">
            {{ record.schedule_impact_days != null ? `${record.schedule_impact_days} days` : '-' }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="goToDetail(record)"><EyeOutlined /></Button>
              <Popconfirm title="Delete this change order?" @confirm="handleDelete(record)">
                <Button type="link" size="small" danger><DeleteOutlined /></Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>
  </Page>
</template>
