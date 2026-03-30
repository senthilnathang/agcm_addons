<script setup>
import { onMounted, ref, watch } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Badge,
  Button,
  Card,
  Input,
  message,
  Popconfirm,
  Select,
  SelectOption,
  Space,
  Table,
} from 'ant-design-vue';
import {
  DeleteOutlined,
  EyeOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';
import { useRouter } from 'vue-router';

defineOptions({ name: 'AGCMSubcontracts' });

const router = useRouter();
const BASE = '/agcm_procurement';

const loading = ref(false);
const projectId = ref(null);
const projects = ref([]);
const items = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const filterStatus = ref(null);
const searchText = ref('');

const statusOptions = [
  { value: 'draft', label: 'Draft' },
  { value: 'pending_approval', label: 'Pending Approval' },
  { value: 'approved', label: 'Approved' },
  { value: 'active', label: 'Active' },
  { value: 'complete', label: 'Complete' },
  { value: 'closed', label: 'Closed' },
  { value: 'cancelled', label: 'Cancelled' },
];

const statusColors = {
  draft: 'default',
  pending_approval: 'processing',
  approved: 'success',
  active: 'processing',
  complete: 'success',
  closed: 'default',
  cancelled: 'error',
};

const columns = [
  { title: 'Seq', dataIndex: 'sequence_name', key: 'sequence_name', width: 110 },
  { title: 'Contract #', dataIndex: 'contract_number', key: 'contract_number', width: 120 },
  { title: 'Vendor', dataIndex: 'vendor_name', key: 'vendor_name' },
  { title: 'Status', dataIndex: 'status', key: 'status', width: 130 },
  { title: 'Original Amt', dataIndex: 'original_amount', key: 'original_amount', width: 130 },
  { title: 'Revised Amt', dataIndex: 'revised_amount', key: 'revised_amount', width: 130 },
  { title: 'Billed', dataIndex: 'billed_to_date', key: 'billed_to_date', width: 120 },
  { title: 'Balance', dataIndex: 'balance_remaining', key: 'balance_remaining', width: 120 },
  { title: 'Actions', key: 'actions', width: 100 },
];

function formatCurrency(val) {
  if (val == null) return '$0.00';
  return `$${Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatStatus(s) {
  return (s || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = data.items || data.results || [];
  } catch { message.error('Failed to load projects'); }
}

async function fetchItems() {
  loading.value = true;
  try {
    const params = { page: page.value, page_size: pageSize.value };
    if (projectId.value) params.project_id = projectId.value;
    if (filterStatus.value) params.status = filterStatus.value;
    if (searchText.value) params.search = searchText.value;

    const data = await requestClient.get(`${BASE}/subcontracts`, { params });
    items.value = data.items || [];
    total.value = data.total || 0;
  } catch { message.error('Failed to load subcontracts'); }
  finally { loading.value = false; }
}

function goToDetail(record) {
  router.push({ path: '/agcm/procurement/subcontracts/detail', query: { id: record.id } });
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/subcontracts/${record.id}`);
    message.success('Subcontract deleted');
    fetchItems();
  } catch { message.error('Failed to delete subcontract'); }
}

watch(projectId, () => { page.value = 1; fetchItems(); });

onMounted(async () => {
  await fetchProjects();
  fetchItems();
});
</script>

<template>
  <Page title="Subcontracts" description="Manage subcontracts for construction projects">
    <Card>
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <Select v-model:value="projectId" placeholder="All Projects" style="width: 260px" allow-clear show-search option-filter-prop="label">
          <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.sequence_name }} - {{ p.name }}</SelectOption>
        </Select>
        <Select v-model:value="filterStatus" placeholder="Status" style="width: 160px" allow-clear @change="fetchItems">
          <SelectOption v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</SelectOption>
        </Select>
        <Input.Search v-model:value="searchText" placeholder="Search..." style="width: 200px" allow-clear @search="fetchItems" @pressEnter="fetchItems" />
        <div class="flex-1" />
        <Button @click="fetchItems"><template #icon><ReloadOutlined /></template>Refresh</Button>
        <Button type="primary" @click="goToDetail({ id: 'new' })"><template #icon><PlusOutlined /></template>New Subcontract</Button>
      </div>

      <Table
        :columns="columns"
        :data-source="items"
        :loading="loading"
        row-key="id"
        size="middle"
        :pagination="{ current: page, pageSize, total, showSizeChanger: true, showTotal: (t) => `${t} subcontracts` }"
        @change="(p) => { page = p.current; pageSize = p.pageSize; fetchItems(); }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <Badge :status="statusColors[record.status] || 'default'" :text="formatStatus(record.status)" />
          </template>
          <template v-else-if="['original_amount', 'revised_amount', 'billed_to_date', 'balance_remaining'].includes(column.key)">
            {{ formatCurrency(record[column.dataIndex]) }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="goToDetail(record)"><EyeOutlined /></Button>
              <Popconfirm title="Delete this subcontract?" @confirm="handleDelete(record)">
                <Button type="link" size="small" danger><DeleteOutlined /></Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>
  </Page>
</template>
