<script setup>
import { onMounted, ref, computed } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Badge,
  Button,
  Card,
  Col,
  Descriptions,
  DescriptionsItem,
  Divider,
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
  Statistic,
  Table,
  DatePicker,
  Textarea,
} from 'ant-design-vue';
import {
  ArrowLeftOutlined,
  CheckOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  SaveOutlined,
  TruckOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';
import { useRoute, useRouter } from 'vue-router';

defineOptions({ name: 'AGCMPODetail' });

const route = useRoute();
const router = useRouter();
const BASE = '/agcm_procurement';

const loading = ref(false);
const saving = ref(false);
const isNew = ref(false);
const detail = ref(null);
const projects = ref([]);

function getAccessToken() {
  try {
    return localStorage?.getItem('accessToken') || '';
  } catch {
    return '';
  }
}
const activeTab = ref('lines');

// Form data for new/edit
const form = ref({
  project_id: null,
  po_number: '',
  vendor_name: '',
  vendor_contact: '',
  status: 'draft',
  description: '',
  issue_date: null,
  expected_delivery: null,
  shipping_method: '',
  shipping_address: '',
  tax_amount: 0,
  retainage_pct: 0,
  notes: '',
});

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

const itemTypeOptions = [
  { value: 'material', label: 'Material' },
  { value: 'labor', label: 'Labor' },
  { value: 'equipment', label: 'Equipment' },
  { value: 'subcontractor', label: 'Subcontractor' },
  { value: 'fee', label: 'Fee' },
  { value: 'allowance', label: 'Allowance' },
];

const lineColumns = [
  { title: '#', dataIndex: 'display_order', key: 'display_order', width: 50 },
  { title: 'Cost Code', dataIndex: 'cost_code', key: 'cost_code', width: 100 },
  { title: 'Description', dataIndex: 'description', key: 'description' },
  { title: 'Type', dataIndex: 'item_type', key: 'item_type', width: 110 },
  { title: 'Qty', dataIndex: 'quantity', key: 'quantity', width: 80 },
  { title: 'Unit', dataIndex: 'unit', key: 'unit', width: 70 },
  { title: 'Unit Cost', dataIndex: 'unit_cost', key: 'unit_cost', width: 110 },
  { title: 'Total', dataIndex: 'total_cost', key: 'total_cost', width: 120 },
  { title: 'Received', dataIndex: 'received_qty', key: 'received_qty', width: 100 },
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
  } catch { /* ignore */ }
}

async function fetchDetail() {
  const id = route.query.id;
  if (!id || id === 'new') {
    isNew.value = true;
    if (route.query.project_id) form.value.project_id = Number(route.query.project_id);
    return;
  }
  loading.value = true;
  try {
    const data = await requestClient.get(`${BASE}/purchase-orders/${id}`);
    detail.value = data;
    isNew.value = false;
  } catch { message.error('Failed to load purchase order'); }
  finally { loading.value = false; }
}

async function handleSave() {
  saving.value = true;
  try {
    if (isNew.value) {
      const po = await requestClient.post(`${BASE}/purchase-orders`, form.value);
      message.success('Purchase order created');
      router.replace({ path: '/agcm/procurement/purchase-orders/detail', query: { id: po.id } });
      await fetchDetail();
    } else {
      await requestClient.put(`${BASE}/purchase-orders/${detail.value.id}`, form.value);
      message.success('Purchase order updated');
      await fetchDetail();
    }
  } catch { message.error('Failed to save purchase order'); }
  finally { saving.value = false; }
}

async function handleApprove() {
  try {
    await requestClient.post(`${BASE}/purchase-orders/${detail.value.id}/approve`);
    message.success('Purchase order approved');
    await fetchDetail();
  } catch { message.error('Failed to approve'); }
}

// --- Receive Delivery ---
const showReceiveModal = ref(false);
const receiveLines = ref([]);

function openReceiveModal() {
  receiveLines.value = (detail.value.lines || []).map(l => ({
    line_id: l.id,
    description: l.description,
    quantity: l.quantity,
    received_qty: l.received_qty,
  }));
  showReceiveModal.value = true;
}

async function handleReceive() {
  try {
    const updates = receiveLines.value.map(l => ({ line_id: l.line_id, received_qty: l.received_qty }));
    await requestClient.post(`${BASE}/purchase-orders/${detail.value.id}/receive`, { line_updates: updates });
    message.success('Delivery received');
    showReceiveModal.value = false;
    await fetchDetail();
  } catch { message.error('Failed to record delivery'); }
}

// --- Line management ---
const showLineModal = ref(false);
const editingLine = ref(null);
const lineForm = ref({
  cost_code: '', description: '', item_type: 'material',
  quantity: 0, unit: 'ea', unit_cost: 0, total_cost: 0, display_order: 0, notes: '',
});

function openLineModal(line = null) {
  if (line) {
    editingLine.value = line;
    lineForm.value = { ...line };
  } else {
    editingLine.value = null;
    lineForm.value = {
      cost_code: '', description: '', item_type: 'material',
      quantity: 0, unit: 'ea', unit_cost: 0, total_cost: 0,
      display_order: (detail.value.lines || []).length, notes: '',
    };
  }
  showLineModal.value = true;
}

async function saveLine() {
  try {
    lineForm.value.total_cost = lineForm.value.quantity * lineForm.value.unit_cost;
    if (editingLine.value) {
      await requestClient.put(`${BASE}/po-lines/${editingLine.value.id}`, lineForm.value);
      message.success('Line updated');
    } else {
      await requestClient.post(`${BASE}/po-lines`, lineForm.value, { params: { po_id: detail.value.id } });
      message.success('Line added');
    }
    showLineModal.value = false;
    await fetchDetail();
  } catch { message.error('Failed to save line'); }
}

async function deleteLine(lineId) {
  try {
    await requestClient.delete(`${BASE}/po-lines/${lineId}`);
    message.success('Line deleted');
    await fetchDetail();
  } catch { message.error('Failed to delete line'); }
}

function goBack() {
  router.push('/agcm/procurement/purchase-orders');
}

onMounted(async () => {
  await fetchProjects();
  await fetchDetail();
});
</script>

<template>
  <Page :title="isNew ? 'New Purchase Order' : `PO: ${detail?.sequence_name || ''}`" description="Purchase order details and line items">
    <template #extra>
      <Space>
        <Button @click="goBack"><ArrowLeftOutlined /> Back</Button>
        <template v-if="!isNew && detail">
          <Button v-if="detail.status === 'draft' || detail.status === 'pending_approval'" type="primary" @click="handleApprove"><CheckOutlined /> Approve</Button>
          <Button v-if="detail.status === 'approved' || detail.status === 'partially_received'" @click="openReceiveModal"><TruckOutlined /> Receive Delivery</Button>
        </template>
      </Space>
    </template>

    <!-- NEW PO Form -->
    <Card v-if="isNew" title="Create Purchase Order" :loading="loading">
      <Form layout="vertical">
        <Row :gutter="16">
          <Col :span="8">
            <FormItem label="Project" required>
              <Select v-model:value="form.project_id" placeholder="Select project" show-search option-filter-prop="label" style="width: 100%">
                <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.sequence_name }} - {{ p.name }}</SelectOption>
              </Select>
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Vendor Name" required>
              <Input v-model:value="form.vendor_name" placeholder="Vendor name" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="PO Number">
              <Input v-model:value="form.po_number" placeholder="Optional PO #" />
            </FormItem>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="8">
            <FormItem label="Vendor Contact">
              <Input v-model:value="form.vendor_contact" placeholder="Contact info" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Tax Amount">
              <InputNumber v-model:value="form.tax_amount" :min="0" :precision="2" prefix="$" style="width: 100%" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Retainage %">
              <InputNumber v-model:value="form.retainage_pct" :min="0" :max="100" :precision="1" style="width: 100%" />
            </FormItem>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="24">
            <FormItem label="Description">
              <Textarea v-model:value="form.description" :rows="2" />
            </FormItem>
          </Col>
        </Row>
        <Button type="primary" :loading="saving" @click="handleSave"><SaveOutlined /> Create</Button>
      </Form>
    </Card>

    <!-- DETAIL View -->
    <template v-if="!isNew && detail">
      <Row :gutter="16" class="mb-4">
        <Col :span="6"><Card><Statistic title="Subtotal" :value="detail.subtotal" :precision="2" prefix="$" /></Card></Col>
        <Col :span="6"><Card><Statistic title="Tax" :value="detail.tax_amount" :precision="2" prefix="$" /></Card></Col>
        <Col :span="6"><Card><Statistic title="Total" :value="detail.total_amount" :precision="2" prefix="$" /></Card></Col>
        <Col :span="6"><Card><Statistic title="Retainage" :value="detail.retainage_amount" :precision="2" prefix="$" /></Card></Col>
      </Row>

      <Card title="Purchase Order Info" :loading="loading">
        <Descriptions :column="3" bordered size="small">
          <DescriptionsItem label="Sequence">{{ detail.sequence_name }}</DescriptionsItem>
          <DescriptionsItem label="PO Number">{{ detail.po_number || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Status"><Badge :status="statusColors[detail.status] || 'default'" :text="formatStatus(detail.status)" /></DescriptionsItem>
          <DescriptionsItem label="Vendor">{{ detail.vendor_name }}</DescriptionsItem>
          <DescriptionsItem label="Vendor Contact">{{ detail.vendor_contact || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Issue Date">{{ detail.issue_date || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Expected Delivery">{{ detail.expected_delivery || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Actual Delivery">{{ detail.actual_delivery || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Shipping">{{ detail.shipping_method || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Received %" :span="3">{{ detail.received_pct }}%</DescriptionsItem>
          <DescriptionsItem label="Description" :span="3">{{ detail.description || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Notes" :span="3">{{ detail.notes || '-' }}</DescriptionsItem>
        </Descriptions>
      </Card>

      <Divider />

      <Card>
        <Tabs v-model:activeKey="activeTab">
          <Tabs.TabPane key="lines" tab="Line Items">
            <template #extra>
              <Button type="primary" size="small" @click="openLineModal()"><PlusOutlined /> Add Line</Button>
            </template>
            <Table
              :columns="lineColumns"
              :data-source="detail.lines || []"
              row-key="id"
              size="small"
              :pagination="false"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'unit_cost' || column.key === 'total_cost'">
                  {{ formatCurrency(record[column.dataIndex]) }}
                </template>
                <template v-else-if="column.key === 'item_type'">
                  {{ (record.item_type || '').replace(/_/g, ' ') }}
                </template>
                <template v-else-if="column.key === 'actions'">
                  <Space>
                    <Button type="link" size="small" @click="openLineModal(record)"><EditOutlined /></Button>
                    <Popconfirm title="Delete line?" @confirm="deleteLine(record.id)">
                      <Button type="link" size="small" danger><DeleteOutlined /></Button>
                    </Popconfirm>
                  </Space>
                </template>
              </template>
            </Table>
          </Tabs.TabPane>
          <Tabs.TabPane key="activity" tab="Activity">
            <ActivityThread
              :model-name="'agcm_purchase_orders'"
              :record-id="route.query.id"
              :access-token="getAccessToken()"
              :api-base="'/api/v1'"
              :show-messages="true"
              :show-activities="true"
            />
          </Tabs.TabPane>
        </Tabs>
      </Card>
    </template>

    <!-- Line Edit Modal -->
    <Modal v-model:open="showLineModal" :title="editingLine ? 'Edit Line' : 'Add Line'" @ok="saveLine" width="600px">
      <Form layout="vertical">
        <Row :gutter="16">
          <Col :span="8">
            <FormItem label="Cost Code"><Input v-model:value="lineForm.cost_code" /></FormItem>
          </Col>
          <Col :span="16">
            <FormItem label="Description" required><Input v-model:value="lineForm.description" /></FormItem>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="8">
            <FormItem label="Type">
              <Select v-model:value="lineForm.item_type" style="width: 100%">
                <SelectOption v-for="t in itemTypeOptions" :key="t.value" :value="t.value">{{ t.label }}</SelectOption>
              </Select>
            </FormItem>
          </Col>
          <Col :span="5"><FormItem label="Quantity"><InputNumber v-model:value="lineForm.quantity" :min="0" style="width: 100%" /></FormItem></Col>
          <Col :span="4"><FormItem label="Unit"><Input v-model:value="lineForm.unit" /></FormItem></Col>
          <Col :span="7"><FormItem label="Unit Cost"><InputNumber v-model:value="lineForm.unit_cost" :min="0" :precision="2" prefix="$" style="width: 100%" /></FormItem></Col>
        </Row>
      </Form>
    </Modal>

    <!-- Receive Delivery Modal -->
    <Modal v-model:open="showReceiveModal" title="Receive Delivery" @ok="handleReceive" width="600px">
      <Table :data-source="receiveLines" row-key="line_id" size="small" :pagination="false">
        <template #columns>
          <Table.Column title="Description" dataIndex="description" />
          <Table.Column title="Ordered" dataIndex="quantity" width="80" />
          <Table.Column title="Received" key="received_qty" width="120">
            <template #default="{ record }">
              <InputNumber v-model:value="record.received_qty" :min="0" :max="record.quantity" size="small" style="width: 100%" />
            </template>
          </Table.Column>
        </template>
      </Table>
    </Modal>
  </Page>
</template>
