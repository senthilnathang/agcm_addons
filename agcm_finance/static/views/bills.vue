<script setup>
import { onMounted, ref, watch } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Badge,
  Button,
  Card,
  message,
  Popconfirm,
  Select,
  SelectOption,
  Space,
  Table,
} from 'ant-design-vue';
import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';
import { useRouter } from 'vue-router';

defineOptions({ name: 'AGCMBills' });

const router = useRouter();
const BASE = '/agcm_finance';

const loading = ref(false);
const projectId = ref(null);
const projects = ref([]);
const bills = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const filterStatus = ref(null);

const statusOptions = [
  { value: 'draft', label: 'Draft' },
  { value: 'received', label: 'Received' },
  { value: 'approved', label: 'Approved' },
  { value: 'paid', label: 'Paid' },
  { value: 'overdue', label: 'Overdue' },
];

const statusColors = {
  draft: 'default',
  received: 'processing',
  approved: 'success',
  paid: 'success',
  overdue: 'error',
};

const columns = [
  { title: 'Seq', dataIndex: 'sequence_name', key: 'sequence_name', width: 120 },
  { title: 'Bill #', dataIndex: 'bill_number', key: 'bill_number', width: 130 },
  { title: 'Vendor', dataIndex: 'vendor_name', key: 'vendor_name' },
  { title: 'Status', dataIndex: 'status', key: 'status', width: 110 },
  { title: 'Total', dataIndex: 'total_amount', key: 'total_amount', width: 130 },
  { title: 'Paid', dataIndex: 'paid_amount', key: 'paid_amount', width: 130 },
  { title: 'Due Date', dataIndex: 'due_date', key: 'due_date', width: 120 },
  { title: 'Actions', key: 'actions', width: 120 },
];

function formatCurrency(val) {
  if (val == null) return '$0.00';
  return `$${Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = data.items || data.results || [];
  } catch { message.error('Failed to load projects'); }
}

async function fetchBills() {
  loading.value = true;
  try {
    const params = { page: page.value, page_size: pageSize.value };
    if (projectId.value) params.project_id = projectId.value;
    if (filterStatus.value) params.status = filterStatus.value;

    const data = await requestClient.get(`${BASE}/bills`, { params });
    bills.value = data.items || [];
    total.value = data.total || 0;
  } catch { message.error('Failed to load bills'); }
  finally { loading.value = false; }
}

function goToForm(record) {
  const query = record ? { id: record.id } : {};
  if (projectId.value && !record) query.project_id = projectId.value;
  router.push({ path: '/agcm/finance/bills/form', query });
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/bills/${record.id}`);
    message.success('Bill deleted');
    fetchBills();
  } catch { message.error('Failed to delete bill'); }
}

watch(projectId, () => { page.value = 1; fetchBills(); });

onMounted(async () => {
  await fetchProjects();
  fetchBills();
});
</script>

<template>
  <Page title="Bills" description="Manage vendor bills">
    <Card>
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <Select v-model:value="projectId" placeholder="All Projects" style="width: 260px" allow-clear show-search option-filter-prop="label">
          <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.sequence_name }} - {{ p.name }}</SelectOption>
        </Select>
        <Select v-model:value="filterStatus" placeholder="Status" style="width: 130px" allow-clear @change="fetchBills">
          <SelectOption v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</SelectOption>
        </Select>
        <div class="flex-1" />
        <Button @click="fetchBills"><template #icon><ReloadOutlined /></template>Refresh</Button>
        <Button type="primary" @click="goToForm()"><template #icon><PlusOutlined /></template>New Bill</Button>
      </div>

      <Table
        :columns="columns"
        :data-source="bills"
        :loading="loading"
        row-key="id"
        size="middle"
        :pagination="{ current: page, pageSize, total, showSizeChanger: true, showTotal: (t) => `${t} bills` }"
        @change="(p) => { page = p.current; pageSize = p.pageSize; fetchBills(); }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <Badge :status="statusColors[record.status] || 'default'" :text="record.status" />
          </template>
          <template v-else-if="column.key === 'total_amount'">
            {{ formatCurrency(record.total_amount) }}
          </template>
          <template v-else-if="column.key === 'paid_amount'">
            {{ formatCurrency(record.paid_amount) }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="goToForm(record)"><EditOutlined /></Button>
              <Popconfirm title="Delete this bill?" @confirm="handleDelete(record)">
                <Button type="link" size="small" danger><DeleteOutlined /></Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>
  </Page>
</template>
