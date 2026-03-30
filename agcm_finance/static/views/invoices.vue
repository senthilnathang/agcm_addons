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

defineOptions({ name: 'AGCMInvoices' });

const router = useRouter();
const BASE = '/agcm_finance';

const loading = ref(false);
const projectId = ref(null);
const projects = ref([]);
const invoices = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const filterStatus = ref(null);

const statusOptions = [
  { value: 'draft', label: 'Draft' },
  { value: 'sent', label: 'Sent' },
  { value: 'paid', label: 'Paid' },
  { value: 'overdue', label: 'Overdue' },
  { value: 'void', label: 'Void' },
];

const statusColors = {
  draft: 'default',
  sent: 'processing',
  paid: 'success',
  overdue: 'error',
  void: 'default',
};

const columns = [
  { title: 'Seq', dataIndex: 'sequence_name', key: 'sequence_name', width: 120 },
  { title: 'Invoice #', dataIndex: 'invoice_number', key: 'invoice_number', width: 130 },
  { title: 'Client', dataIndex: 'client_name', key: 'client_name' },
  { title: 'Status', dataIndex: 'status', key: 'status', width: 110 },
  { title: 'Total', dataIndex: 'total_amount', key: 'total_amount', width: 130 },
  { title: 'Paid', dataIndex: 'paid_amount', key: 'paid_amount', width: 130 },
  { title: 'Balance', dataIndex: 'balance_due', key: 'balance_due', width: 130 },
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

async function fetchInvoices() {
  loading.value = true;
  try {
    const params = { page: page.value, page_size: pageSize.value };
    if (projectId.value) params.project_id = projectId.value;
    if (filterStatus.value) params.status = filterStatus.value;

    const data = await requestClient.get(`${BASE}/invoices`, { params });
    invoices.value = data.items || [];
    total.value = data.total || 0;
  } catch { message.error('Failed to load invoices'); }
  finally { loading.value = false; }
}

function goToForm(record) {
  const query = record ? { id: record.id } : {};
  if (projectId.value && !record) query.project_id = projectId.value;
  router.push({ path: '/agcm/finance/invoices/form', query });
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/invoices/${record.id}`);
    message.success('Invoice deleted');
    fetchInvoices();
  } catch { message.error('Failed to delete invoice'); }
}

watch(projectId, () => { page.value = 1; fetchInvoices(); });

onMounted(async () => {
  await fetchProjects();
  fetchInvoices();
});
</script>

<template>
  <Page title="Invoices" description="Manage customer invoices">
    <Card>
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <Select v-model:value="projectId" placeholder="All Projects" style="width: 260px" allow-clear show-search option-filter-prop="label">
          <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.sequence_name }} - {{ p.name }}</SelectOption>
        </Select>
        <Select v-model:value="filterStatus" placeholder="Status" style="width: 130px" allow-clear @change="fetchInvoices">
          <SelectOption v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</SelectOption>
        </Select>
        <div class="flex-1" />
        <Button @click="fetchInvoices"><template #icon><ReloadOutlined /></template>Refresh</Button>
        <Button type="primary" @click="goToForm()"><template #icon><PlusOutlined /></template>New Invoice</Button>
      </div>

      <Table
        :columns="columns"
        :data-source="invoices"
        :loading="loading"
        row-key="id"
        size="middle"
        :pagination="{ current: page, pageSize, total, showSizeChanger: true, showTotal: (t) => `${t} invoices` }"
        @change="(p) => { page = p.current; pageSize = p.pageSize; fetchInvoices(); }"
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
          <template v-else-if="column.key === 'balance_due'">
            <span :style="{ color: (record.balance_due || 0) > 0 ? '#cf1322' : '#3f8600' }">
              {{ formatCurrency(record.balance_due) }}
            </span>
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="goToForm(record)"><EditOutlined /></Button>
              <Popconfirm title="Delete this invoice?" @confirm="handleDelete(record)">
                <Button type="link" size="small" danger><DeleteOutlined /></Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>
  </Page>
</template>
