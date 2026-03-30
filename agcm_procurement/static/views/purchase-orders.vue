<script setup>
import { onMounted, ref, watch } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Badge,
  Button,
  Card,
  Input,
  message,
  Modal,
  Popconfirm,
  Select,
  SelectOption,
  Space,
  Table,
  Form,
  FormItem,
} from 'ant-design-vue';
import {
  DeleteOutlined,
  EyeOutlined,
  PlusOutlined,
  ReloadOutlined,
  CopyOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';
import { useRouter } from 'vue-router';

defineOptions({ name: 'AGCMPurchaseOrders' });

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
  { value: 'partially_received', label: 'Partially Received' },
  { value: 'received', label: 'Received' },
  { value: 'closed', label: 'Closed' },
  { value: 'cancelled', label: 'Cancelled' },
];

const statusColors = {
  draft: 'default',
  pending_approval: 'processing',
  approved: 'success',
  partially_received: 'warning',
  received: 'success',
  closed: 'default',
  cancelled: 'error',
};

const columns = [
  { title: 'Seq', dataIndex: 'sequence_name', key: 'sequence_name', width: 110 },
  { title: 'PO #', dataIndex: 'po_number', key: 'po_number', width: 120 },
  { title: 'Vendor', dataIndex: 'vendor_name', key: 'vendor_name' },
  { title: 'Status', dataIndex: 'status', key: 'status', width: 140 },
  { title: 'Total', dataIndex: 'total_amount', key: 'total_amount', width: 130 },
  { title: 'Expected Delivery', dataIndex: 'expected_delivery', key: 'expected_delivery', width: 150 },
  { title: 'Actions', key: 'actions', width: 120 },
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

    const data = await requestClient.get(`${BASE}/purchase-orders`, { params });
    items.value = data.items || [];
    total.value = data.total || 0;
  } catch { message.error('Failed to load purchase orders'); }
  finally { loading.value = false; }
}

function goToDetail(record) {
  router.push({ path: '/agcm/procurement/purchase-orders/detail', query: { id: record.id } });
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/purchase-orders/${record.id}`);
    message.success('Purchase order deleted');
    fetchItems();
  } catch { message.error('Failed to delete purchase order'); }
}

// --- Create from Estimate modal ---
const showEstimateModal = ref(false);
const estimateForm = ref({ estimate_id: null, vendor_name: '' });
const estimates = ref([]);

async function openEstimateModal() {
  showEstimateModal.value = true;
  try {
    const data = await requestClient.get('/agcm_estimate/estimates', { params: { page_size: 200, project_id: projectId.value } });
    estimates.value = data.items || [];
  } catch { estimates.value = []; }
}

async function createFromEstimate() {
  if (!estimateForm.value.estimate_id || !estimateForm.value.vendor_name) {
    message.warning('Please select an estimate and enter a vendor name');
    return;
  }
  try {
    await requestClient.post(`${BASE}/purchase-orders/from-estimate`, estimateForm.value);
    message.success('Purchase order created from estimate');
    showEstimateModal.value = false;
    estimateForm.value = { estimate_id: null, vendor_name: '' };
    fetchItems();
  } catch { message.error('Failed to create PO from estimate'); }
}

watch(projectId, () => { page.value = 1; fetchItems(); });

onMounted(async () => {
  await fetchProjects();
  fetchItems();
});
</script>

<template>
  <Page title="Purchase Orders" description="Manage purchase orders for construction projects">
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
        <Button @click="openEstimateModal"><template #icon><CopyOutlined /></template>From Estimate</Button>
        <Button type="primary" @click="goToDetail({ id: 'new' })"><template #icon><PlusOutlined /></template>New PO</Button>
      </div>

      <Table
        :columns="columns"
        :data-source="items"
        :loading="loading"
        row-key="id"
        size="middle"
        :pagination="{ current: page, pageSize, total, showSizeChanger: true, showTotal: (t) => `${t} purchase orders` }"
        @change="(p) => { page = p.current; pageSize = p.pageSize; fetchItems(); }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <Badge :status="statusColors[record.status] || 'default'" :text="formatStatus(record.status)" />
          </template>
          <template v-else-if="column.key === 'total_amount'">
            {{ formatCurrency(record.total_amount) }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="goToDetail(record)"><EyeOutlined /></Button>
              <Popconfirm title="Delete this PO?" @confirm="handleDelete(record)">
                <Button type="link" size="small" danger><DeleteOutlined /></Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <Modal v-model:open="showEstimateModal" title="Create PO from Estimate" @ok="createFromEstimate">
      <Form layout="vertical">
        <FormItem label="Estimate">
          <Select v-model:value="estimateForm.estimate_id" placeholder="Select estimate" style="width: 100%" show-search option-filter-prop="label">
            <SelectOption v-for="e in estimates" :key="e.id" :value="e.id" :label="e.name">{{ e.sequence_name }} - {{ e.name }}</SelectOption>
          </Select>
        </FormItem>
        <FormItem label="Vendor Name">
          <Input v-model:value="estimateForm.vendor_name" placeholder="Enter vendor name" />
        </FormItem>
      </Form>
    </Modal>
  </Page>
</template>
