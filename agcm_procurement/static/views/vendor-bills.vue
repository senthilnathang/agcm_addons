<script setup>
import { onMounted, ref, watch } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Badge,
  Button,
  Card,
  Col,
  Descriptions,
  DescriptionsItem,
  Drawer,
  Form,
  FormItem,
  Input,
  InputNumber,
  message,
  Modal,
  Popconfirm,
  Row,
  Select,
  SelectOption,
  Space,
  Table,
  Tag,
  DatePicker,
  Textarea,
} from 'ant-design-vue';
import {
  CheckOutlined,
  DeleteOutlined,
  DollarOutlined,
  EditOutlined,
  EyeOutlined,
  LinkOutlined,
  PlusOutlined,
  ReloadOutlined,
  WarningOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMVendorBills' });

const BASE = '/agcm_procurement';

const loading = ref(false);
const projectId = ref(null);
const projects = ref([]);
const items = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const filterStatus = ref(null);
const filterRecordType = ref(null);
const searchText = ref('');

const statusOptions = [
  { value: 'draft', label: 'Draft' },
  { value: 'pending_approval', label: 'Pending Approval' },
  { value: 'approved', label: 'Approved' },
  { value: 'partially_paid', label: 'Partially Paid' },
  { value: 'paid', label: 'Paid' },
  { value: 'overdue', label: 'Overdue' },
  { value: 'cancelled', label: 'Cancelled' },
];

const recordTypeOptions = [
  { value: 'bill', label: 'Bill' },
  { value: 'expense', label: 'Expense' },
  { value: 'vendor_credit', label: 'Vendor Credit' },
];

const statusColors = {
  draft: 'default',
  pending_approval: 'processing',
  approved: 'success',
  partially_paid: 'warning',
  paid: 'success',
  overdue: 'error',
  cancelled: 'error',
};

const columns = [
  { title: 'Seq', dataIndex: 'sequence_name', key: 'sequence_name', width: 100 },
  { title: 'Bill #', dataIndex: 'bill_number', key: 'bill_number', width: 110 },
  { title: 'Vendor', dataIndex: 'vendor_name', key: 'vendor_name' },
  { title: 'Type', dataIndex: 'record_type', key: 'record_type', width: 100 },
  { title: 'Status', dataIndex: 'status', key: 'status', width: 130 },
  { title: 'Total', dataIndex: 'total_amount', key: 'total_amount', width: 120 },
  { title: 'Due Date', dataIndex: 'due_date', key: 'due_date', width: 110 },
  { title: 'Paid', dataIndex: 'paid_amount', key: 'paid_amount', width: 110 },
  { title: 'Balance', dataIndex: 'balance_due', key: 'balance_due', width: 110 },
  { title: 'Dup?', dataIndex: 'duplicate_flag', key: 'duplicate_flag', width: 60 },
  { title: 'Actions', key: 'actions', width: 160 },
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
    if (filterRecordType.value) params.record_type = filterRecordType.value;
    if (searchText.value) params.search = searchText.value;

    const data = await requestClient.get(`${BASE}/vendor-bills`, { params });
    items.value = data.items || [];
    total.value = data.total || 0;
  } catch { message.error('Failed to load vendor bills'); }
  finally { loading.value = false; }
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/vendor-bills/${record.id}`);
    message.success('Vendor bill deleted');
    fetchItems();
  } catch { message.error('Failed to delete vendor bill'); }
}

async function handleApprove(record) {
  try {
    await requestClient.post(`${BASE}/vendor-bills/${record.id}/approve`);
    message.success('Bill approved');
    fetchItems();
  } catch { message.error('Failed to approve bill'); }
}

async function handleCheckDuplicate(record) {
  try {
    const result = await requestClient.post(`${BASE}/vendor-bills/${record.id}/check-duplicate`);
    if (result.is_duplicate) {
      message.warning(`Potential duplicate found (${result.duplicate_count} match${result.duplicate_count > 1 ? 'es' : ''})`);
    } else {
      message.success('No duplicates found');
    }
    fetchItems();
  } catch { message.error('Failed to check duplicates'); }
}

async function handleAutoMatchPO(record) {
  try {
    const result = await requestClient.post(`${BASE}/vendor-bills/${record.id}/auto-match-po`);
    if (result.matches && result.matches.length > 0) {
      const best = result.matches[0];
      message.success(`Best match: ${best.sequence_name} (${best.diff_pct}% diff)`);
    } else {
      message.info('No matching POs found');
    }
  } catch { message.error('Failed to auto-match PO'); }
}

// --- Detail Drawer ---
const showDrawer = ref(false);
const billDetail = ref(null);

async function openDetail(record) {
  try {
    billDetail.value = await requestClient.get(`${BASE}/vendor-bills/${record.id}`);
    showDrawer.value = true;
  } catch { message.error('Failed to load bill detail'); }
}

// --- Record Payment Modal ---
const showPaymentModal = ref(false);
const paymentBillId = ref(null);
const paymentForm = ref({
  payment_date: null,
  amount: 0,
  payment_method: 'check',
  reference_number: '',
  notes: '',
});

const paymentMethods = [
  { value: 'check', label: 'Check' },
  { value: 'wire', label: 'Wire' },
  { value: 'ach', label: 'ACH' },
  { value: 'cash', label: 'Cash' },
  { value: 'credit_card', label: 'Credit Card' },
];

function openPaymentModal(record) {
  paymentBillId.value = record.id;
  paymentForm.value = {
    payment_date: null,
    amount: record.balance_due || 0,
    payment_method: 'check',
    reference_number: '',
    notes: '',
  };
  showPaymentModal.value = true;
}

async function recordPayment() {
  if (!paymentForm.value.payment_date || !paymentForm.value.amount) {
    message.warning('Date and amount are required');
    return;
  }
  try {
    await requestClient.post(`${BASE}/vendor-bills/${paymentBillId.value}/record-payment`, paymentForm.value);
    message.success('Payment recorded');
    showPaymentModal.value = false;
    fetchItems();
    if (showDrawer.value && billDetail.value?.id === paymentBillId.value) {
      billDetail.value = await requestClient.get(`${BASE}/vendor-bills/${paymentBillId.value}`);
    }
  } catch { message.error('Failed to record payment'); }
}

// --- New Bill Modal ---
const showNewModal = ref(false);
const billForm = ref({
  project_id: null,
  vendor_name: '',
  bill_number: '',
  record_type: 'bill',
  description: '',
  issue_date: null,
  due_date: null,
  payment_terms: '',
  vendor_invoice_ref: '',
  notes: '',
});

function openNewModal() {
  billForm.value = {
    project_id: projectId.value,
    vendor_name: '',
    bill_number: '',
    record_type: 'bill',
    description: '',
    issue_date: null,
    due_date: null,
    payment_terms: '',
    vendor_invoice_ref: '',
    notes: '',
  };
  showNewModal.value = true;
}

async function createBill() {
  if (!billForm.value.project_id || !billForm.value.vendor_name) {
    message.warning('Project and vendor name are required');
    return;
  }
  try {
    await requestClient.post(`${BASE}/vendor-bills`, billForm.value);
    message.success('Vendor bill created');
    showNewModal.value = false;
    fetchItems();
  } catch { message.error('Failed to create bill'); }
}

watch(projectId, () => { page.value = 1; fetchItems(); });

onMounted(async () => {
  await fetchProjects();
  fetchItems();
});
</script>

<template>
  <Page title="Vendor Bills" description="Manage vendor bills with payments, duplicate detection, and PO matching">
    <Card>
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <Select v-model:value="projectId" placeholder="All Projects" style="width: 260px" allow-clear show-search option-filter-prop="label">
          <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.sequence_name }} - {{ p.name }}</SelectOption>
        </Select>
        <Select v-model:value="filterStatus" placeholder="Status" style="width: 150px" allow-clear @change="fetchItems">
          <SelectOption v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</SelectOption>
        </Select>
        <Select v-model:value="filterRecordType" placeholder="Type" style="width: 130px" allow-clear @change="fetchItems">
          <SelectOption v-for="r in recordTypeOptions" :key="r.value" :value="r.value">{{ r.label }}</SelectOption>
        </Select>
        <Input.Search v-model:value="searchText" placeholder="Search..." style="width: 200px" allow-clear @search="fetchItems" @pressEnter="fetchItems" />
        <div class="flex-1" />
        <Button @click="fetchItems"><template #icon><ReloadOutlined /></template>Refresh</Button>
        <Button type="primary" @click="openNewModal"><template #icon><PlusOutlined /></template>New Bill</Button>
      </div>

      <Table
        :columns="columns"
        :data-source="items"
        :loading="loading"
        row-key="id"
        size="middle"
        :pagination="{ current: page, pageSize, total, showSizeChanger: true, showTotal: (t) => `${t} bills` }"
        @change="(p) => { page = p.current; pageSize = p.pageSize; fetchItems(); }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <Badge :status="statusColors[record.status] || 'default'" :text="formatStatus(record.status)" />
          </template>
          <template v-else-if="column.key === 'record_type'">
            {{ formatStatus(record.record_type) }}
          </template>
          <template v-else-if="['total_amount', 'paid_amount', 'balance_due'].includes(column.key)">
            {{ formatCurrency(record[column.dataIndex]) }}
          </template>
          <template v-else-if="column.key === 'duplicate_flag'">
            <Tag v-if="record.duplicate_flag" color="warning"><WarningOutlined /> Dup</Tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="openDetail(record)"><EyeOutlined /></Button>
              <Button type="link" size="small" @click="openPaymentModal(record)"><DollarOutlined /></Button>
              <Button type="link" size="small" @click="handleCheckDuplicate(record)" title="Check Duplicate"><WarningOutlined /></Button>
              <Button type="link" size="small" @click="handleAutoMatchPO(record)" title="Auto-Match PO"><LinkOutlined /></Button>
              <Popconfirm title="Delete?" @confirm="handleDelete(record)">
                <Button type="link" size="small" danger><DeleteOutlined /></Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <!-- Bill Detail Drawer -->
    <Drawer v-model:open="showDrawer" title="Bill Detail" :width="700" v-if="billDetail">
      <Descriptions :column="2" bordered size="small" class="mb-4">
        <DescriptionsItem label="Sequence">{{ billDetail.sequence_name }}</DescriptionsItem>
        <DescriptionsItem label="Bill #">{{ billDetail.bill_number || '-' }}</DescriptionsItem>
        <DescriptionsItem label="Vendor">{{ billDetail.vendor_name }}</DescriptionsItem>
        <DescriptionsItem label="Status"><Badge :status="statusColors[billDetail.status] || 'default'" :text="formatStatus(billDetail.status)" /></DescriptionsItem>
        <DescriptionsItem label="Record Type">{{ formatStatus(billDetail.record_type) }}</DescriptionsItem>
        <DescriptionsItem label="Invoice Ref">{{ billDetail.vendor_invoice_ref || '-' }}</DescriptionsItem>
        <DescriptionsItem label="Issue Date">{{ billDetail.issue_date || '-' }}</DescriptionsItem>
        <DescriptionsItem label="Due Date">{{ billDetail.due_date || '-' }}</DescriptionsItem>
        <DescriptionsItem label="Subtotal">{{ formatCurrency(billDetail.subtotal) }}</DescriptionsItem>
        <DescriptionsItem label="Tax">{{ formatCurrency(billDetail.tax_amount) }}</DescriptionsItem>
        <DescriptionsItem label="Total">{{ formatCurrency(billDetail.total_amount) }}</DescriptionsItem>
        <DescriptionsItem label="Paid">{{ formatCurrency(billDetail.paid_amount) }}</DescriptionsItem>
        <DescriptionsItem label="Balance Due">{{ formatCurrency(billDetail.balance_due) }}</DescriptionsItem>
        <DescriptionsItem label="Payment Terms">{{ billDetail.payment_terms || '-' }}</DescriptionsItem>
        <DescriptionsItem label="Duplicate?" :span="2">
          <Tag v-if="billDetail.duplicate_flag" color="warning">Potential Duplicate</Tag>
          <span v-else>No</span>
        </DescriptionsItem>
      </Descriptions>

      <h4 class="mb-2 font-semibold">Line Items ({{ billDetail.line_count || 0 }})</h4>
      <Table :data-source="billDetail.lines || []" row-key="id" size="small" :pagination="false" class="mb-4">
        <template #columns>
          <Table.Column title="Description" dataIndex="description" />
          <Table.Column title="Type" dataIndex="line_type" width="100">
            <template #default="{ record }">{{ formatStatus(record.line_type) }}</template>
          </Table.Column>
          <Table.Column title="Qty" dataIndex="quantity" width="60" />
          <Table.Column title="Unit Cost" dataIndex="unit_cost" width="100">
            <template #default="{ record }">{{ formatCurrency(record.unit_cost) }}</template>
          </Table.Column>
          <Table.Column title="Amount" dataIndex="amount" width="110">
            <template #default="{ record }">{{ formatCurrency(record.amount) }}</template>
          </Table.Column>
        </template>
      </Table>

      <h4 class="mb-2 font-semibold">Payments ({{ billDetail.payment_count || 0 }})</h4>
      <Table :data-source="billDetail.payments || []" row-key="id" size="small" :pagination="false">
        <template #columns>
          <Table.Column title="Date" dataIndex="payment_date" width="110" />
          <Table.Column title="Amount" dataIndex="amount" width="120">
            <template #default="{ record }">{{ formatCurrency(record.amount) }}</template>
          </Table.Column>
          <Table.Column title="Method" dataIndex="payment_method" width="100" />
          <Table.Column title="Reference" dataIndex="reference_number" />
        </template>
      </Table>

      <div class="mt-4">
        <Space>
          <Button v-if="billDetail.status === 'draft' || billDetail.status === 'pending_approval'" type="primary" @click="handleApprove(billDetail); showDrawer = false;"><CheckOutlined /> Approve</Button>
          <Button @click="openPaymentModal(billDetail)"><DollarOutlined /> Record Payment</Button>
        </Space>
      </div>
    </Drawer>

    <!-- Record Payment Modal -->
    <Modal v-model:open="showPaymentModal" title="Record Payment" @ok="recordPayment">
      <Form layout="vertical">
        <FormItem label="Payment Date" required>
          <DatePicker v-model:value="paymentForm.payment_date" style="width: 100%" value-format="YYYY-MM-DD" />
        </FormItem>
        <FormItem label="Amount" required>
          <InputNumber v-model:value="paymentForm.amount" :min="0.01" :precision="2" prefix="$" style="width: 100%" />
        </FormItem>
        <FormItem label="Payment Method">
          <Select v-model:value="paymentForm.payment_method" style="width: 100%">
            <SelectOption v-for="m in paymentMethods" :key="m.value" :value="m.value">{{ m.label }}</SelectOption>
          </Select>
        </FormItem>
        <FormItem label="Reference Number">
          <Input v-model:value="paymentForm.reference_number" />
        </FormItem>
        <FormItem label="Notes">
          <Textarea v-model:value="paymentForm.notes" :rows="2" />
        </FormItem>
      </Form>
    </Modal>

    <!-- New Bill Modal -->
    <Modal v-model:open="showNewModal" title="New Vendor Bill" @ok="createBill" width="600px">
      <Form layout="vertical">
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Project" required>
              <Select v-model:value="billForm.project_id" placeholder="Select project" show-search option-filter-prop="label" style="width: 100%">
                <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.sequence_name }} - {{ p.name }}</SelectOption>
              </Select>
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Record Type">
              <Select v-model:value="billForm.record_type" style="width: 100%">
                <SelectOption v-for="r in recordTypeOptions" :key="r.value" :value="r.value">{{ r.label }}</SelectOption>
              </Select>
            </FormItem>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12"><FormItem label="Vendor Name" required><Input v-model:value="billForm.vendor_name" /></FormItem></Col>
          <Col :span="12"><FormItem label="Bill Number"><Input v-model:value="billForm.bill_number" /></FormItem></Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12"><FormItem label="Vendor Invoice Ref"><Input v-model:value="billForm.vendor_invoice_ref" /></FormItem></Col>
          <Col :span="12"><FormItem label="Payment Terms"><Input v-model:value="billForm.payment_terms" placeholder="Net 30" /></FormItem></Col>
        </Row>
        <FormItem label="Description"><Textarea v-model:value="billForm.description" :rows="2" /></FormItem>
      </Form>
    </Modal>
  </Page>
</template>
