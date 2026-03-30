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

defineOptions({ name: 'AGCMExpenses' });

const router = useRouter();
const BASE = '/agcm_finance';

const loading = ref(false);
const projectId = ref(null);
const projects = ref([]);
const expenses = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const filterStatus = ref(null);

const statusOptions = [
  { value: 'draft', label: 'Draft' },
  { value: 'submitted', label: 'Submitted' },
  { value: 'approved', label: 'Approved' },
  { value: 'paid', label: 'Paid' },
];

const statusColors = {
  draft: 'default',
  submitted: 'processing',
  approved: 'success',
  paid: 'success',
};

const columns = [
  { title: 'Seq', dataIndex: 'sequence_name', key: 'sequence_name', width: 120 },
  { title: 'Description', dataIndex: 'description', key: 'description' },
  { title: 'Vendor', dataIndex: 'vendor', key: 'vendor', width: 180 },
  { title: 'Status', dataIndex: 'status', key: 'status', width: 120 },
  { title: 'Actions', key: 'actions', width: 120 },
];

async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = data.items || data.results || [];
  } catch { message.error('Failed to load projects'); }
}

async function fetchExpenses() {
  loading.value = true;
  try {
    const params = { page: page.value, page_size: pageSize.value };
    if (projectId.value) params.project_id = projectId.value;
    if (filterStatus.value) params.status = filterStatus.value;

    const data = await requestClient.get(`${BASE}/expenses`, { params });
    expenses.value = data.items || [];
    total.value = data.total || 0;
  } catch { message.error('Failed to load expenses'); }
  finally { loading.value = false; }
}

function goToForm(record) {
  const query = record ? { id: record.id } : {};
  if (projectId.value && !record) query.project_id = projectId.value;
  router.push({ path: '/agcm/finance/expenses/form', query });
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/expenses/${record.id}`);
    message.success('Expense deleted');
    fetchExpenses();
  } catch { message.error('Failed to delete expense'); }
}

watch(projectId, () => { page.value = 1; fetchExpenses(); });

onMounted(async () => {
  await fetchProjects();
  fetchExpenses();
});
</script>

<template>
  <Page title="Expenses" description="Track project expenses">
    <Card>
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <Select v-model:value="projectId" placeholder="All Projects" style="width: 260px" allow-clear show-search option-filter-prop="label">
          <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.sequence_name }} - {{ p.name }}</SelectOption>
        </Select>
        <Select v-model:value="filterStatus" placeholder="Status" style="width: 130px" allow-clear @change="fetchExpenses">
          <SelectOption v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</SelectOption>
        </Select>
        <div class="flex-1" />
        <Button @click="fetchExpenses"><template #icon><ReloadOutlined /></template>Refresh</Button>
        <Button type="primary" @click="goToForm()"><template #icon><PlusOutlined /></template>New Expense</Button>
      </div>

      <Table
        :columns="columns"
        :data-source="expenses"
        :loading="loading"
        row-key="id"
        size="middle"
        :pagination="{ current: page, pageSize, total, showSizeChanger: true, showTotal: (t) => `${t} expenses` }"
        @change="(p) => { page = p.current; pageSize = p.pageSize; fetchExpenses(); }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <Badge :status="statusColors[record.status] || 'default'" :text="record.status" />
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="goToForm(record)"><EditOutlined /></Button>
              <Popconfirm title="Delete this expense?" @confirm="handleDelete(record)">
                <Button type="link" size="small" danger><DeleteOutlined /></Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>
  </Page>
</template>
