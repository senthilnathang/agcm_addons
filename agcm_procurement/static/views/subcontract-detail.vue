<script setup>
import { onMounted, ref } from 'vue';

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
  Tag,
} from 'ant-design-vue';
import {
  ArrowLeftOutlined,
  CheckOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  SaveOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';
import { useRoute, useRouter } from 'vue-router';

defineOptions({ name: 'AGCMSubcontractDetail' });

const route = useRoute();
const router = useRouter();
const BASE = '/agcm_procurement';

const loading = ref(false);
const saving = ref(false);
const isNew = ref(false);
const detail = ref(null);
const projects = ref([]);

const form = ref({
  project_id: null,
  contract_number: '',
  vendor_name: '',
  vendor_contact: '',
  status: 'draft',
  scope_of_work: '',
  start_date: null,
  end_date: null,
  original_amount: 0,
  approved_cos: 0,
  retainage_pct: 5.0,
  notes: '',
});

const statusColors = {
  draft: 'default',
  pending_approval: 'processing',
  approved: 'success',
  active: 'processing',
  complete: 'success',
  closed: 'default',
  cancelled: 'error',
};

const sovColumns = [
  { title: '#', dataIndex: 'display_order', key: 'display_order', width: 40 },
  { title: 'Cost Code', dataIndex: 'cost_code', key: 'cost_code', width: 90 },
  { title: 'Description', dataIndex: 'description', key: 'description' },
  { title: 'Scheduled Value', dataIndex: 'scheduled_value', key: 'scheduled_value', width: 130 },
  { title: 'Previous', dataIndex: 'billed_previous', key: 'billed_previous', width: 110 },
  { title: 'Current', dataIndex: 'billed_current', key: 'billed_current', width: 110 },
  { title: 'Materials', dataIndex: 'stored_materials', key: 'stored_materials', width: 100 },
  { title: 'Completed', dataIndex: 'total_completed', key: 'total_completed', width: 110 },
  { title: '%', dataIndex: 'pct_complete', key: 'pct_complete', width: 60 },
  { title: 'Retainage', dataIndex: 'retainage', key: 'retainage', width: 100 },
  { title: 'Balance', dataIndex: 'balance_to_finish', key: 'balance_to_finish', width: 110 },
  { title: 'Actions', key: 'actions', width: 80 },
];

const complianceColumns = [
  { title: 'Type', dataIndex: 'doc_type', key: 'doc_type', width: 130 },
  { title: 'Status', dataIndex: 'status', key: 'status', width: 100 },
  { title: 'Description', dataIndex: 'description', key: 'description' },
  { title: 'Expiration', dataIndex: 'expiration_date', key: 'expiration_date', width: 120 },
  { title: 'File', dataIndex: 'file_name', key: 'file_name', width: 150 },
  { title: 'Actions', key: 'actions', width: 80 },
];

const docTypeOptions = [
  { value: 'insurance_coi', label: 'Insurance COI' },
  { value: 'workers_comp', label: "Workers' Comp" },
  { value: 'bond', label: 'Bond' },
  { value: 'license', label: 'License' },
  { value: 'permit', label: 'Permit' },
  { value: 'lien_waiver', label: 'Lien Waiver' },
  { value: 'w9', label: 'W-9' },
  { value: 'safety_cert', label: 'Safety Cert' },
  { value: 'other', label: 'Other' },
];

const docStatusOptions = [
  { value: 'required', label: 'Required' },
  { value: 'submitted', label: 'Submitted' },
  { value: 'approved', label: 'Approved' },
  { value: 'expired', label: 'Expired' },
  { value: 'rejected', label: 'Rejected' },
];

const docStatusColors = {
  required: 'orange',
  submitted: 'blue',
  approved: 'green',
  expired: 'red',
  rejected: 'red',
};

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
    return;
  }
  loading.value = true;
  try {
    const data = await requestClient.get(`${BASE}/subcontracts/${id}`);
    detail.value = data;
    isNew.value = false;
  } catch { message.error('Failed to load subcontract'); }
  finally { loading.value = false; }
}

async function handleSave() {
  saving.value = true;
  try {
    if (isNew.value) {
      const sc = await requestClient.post(`${BASE}/subcontracts`, form.value);
      message.success('Subcontract created');
      router.replace({ path: '/agcm/procurement/subcontracts/detail', query: { id: sc.id } });
      await fetchDetail();
    } else {
      await requestClient.put(`${BASE}/subcontracts/${detail.value.id}`, form.value);
      message.success('Subcontract updated');
      await fetchDetail();
    }
  } catch { message.error('Failed to save subcontract'); }
  finally { saving.value = false; }
}

async function handleApprove() {
  try {
    await requestClient.post(`${BASE}/subcontracts/${detail.value.id}/approve`);
    message.success('Subcontract approved');
    await fetchDetail();
  } catch { message.error('Failed to approve'); }
}

// --- Update Billing Modal ---
const showBillingModal = ref(false);
const billingLines = ref([]);

function openBillingModal() {
  billingLines.value = (detail.value.sov_lines || []).map(l => ({
    line_id: l.id,
    description: l.description,
    scheduled_value: l.scheduled_value,
    billed_previous: l.billed_previous,
    billed_current: l.billed_current,
    stored_materials: l.stored_materials,
  }));
  showBillingModal.value = true;
}

async function handleUpdateBilling() {
  try {
    const updates = billingLines.value.map(l => ({
      line_id: l.line_id,
      billed_current: l.billed_current,
      stored_materials: l.stored_materials,
    }));
    await requestClient.post(`${BASE}/subcontracts/${detail.value.id}/update-billing`, { sov_updates: updates });
    message.success('Billing updated');
    showBillingModal.value = false;
    await fetchDetail();
  } catch { message.error('Failed to update billing'); }
}

// --- SOV Line Modal ---
const showSovModal = ref(false);
const editingSov = ref(null);
const sovForm = ref({
  cost_code: '', description: '', scheduled_value: 0,
  billed_previous: 0, billed_current: 0, stored_materials: 0,
  display_order: 0, source_type: 'original',
});

function openSovModal(line = null) {
  if (line) {
    editingSov.value = line;
    sovForm.value = { ...line };
  } else {
    editingSov.value = null;
    sovForm.value = {
      cost_code: '', description: '', scheduled_value: 0,
      billed_previous: 0, billed_current: 0, stored_materials: 0,
      display_order: (detail.value.sov_lines || []).length, source_type: 'original',
    };
  }
  showSovModal.value = true;
}

async function saveSov() {
  try {
    if (editingSov.value) {
      await requestClient.put(`${BASE}/sov-lines/${editingSov.value.id}`, sovForm.value);
      message.success('SOV line updated');
    } else {
      await requestClient.post(`${BASE}/sov-lines`, sovForm.value, { params: { subcontract_id: detail.value.id } });
      message.success('SOV line added');
    }
    showSovModal.value = false;
    await fetchDetail();
  } catch { message.error('Failed to save SOV line'); }
}

async function deleteSov(lineId) {
  try {
    await requestClient.delete(`${BASE}/sov-lines/${lineId}`);
    message.success('SOV line deleted');
    await fetchDetail();
  } catch { message.error('Failed to delete SOV line'); }
}

// --- Compliance Doc Modal ---
const showDocModal = ref(false);
const editingDoc = ref(null);
const docForm = ref({
  subcontract_id: null,
  doc_type: 'insurance_coi',
  status: 'required',
  description: '',
  expiration_date: null,
  document_url: '',
  file_name: '',
  notes: '',
});

function openDocModal(doc = null) {
  if (doc) {
    editingDoc.value = doc;
    docForm.value = { ...doc };
  } else {
    editingDoc.value = null;
    docForm.value = {
      subcontract_id: detail.value.id,
      doc_type: 'insurance_coi', status: 'required',
      description: '', expiration_date: null,
      document_url: '', file_name: '', notes: '',
    };
  }
  showDocModal.value = true;
}

async function saveDoc() {
  try {
    if (editingDoc.value) {
      await requestClient.put(`${BASE}/compliance-docs/${editingDoc.value.id}`, docForm.value);
      message.success('Document updated');
    } else {
      docForm.value.subcontract_id = detail.value.id;
      await requestClient.post(`${BASE}/compliance-docs`, docForm.value);
      message.success('Document added');
    }
    showDocModal.value = false;
    await fetchDetail();
  } catch { message.error('Failed to save document'); }
}

async function deleteDoc(docId) {
  try {
    await requestClient.delete(`${BASE}/compliance-docs/${docId}`);
    message.success('Document deleted');
    await fetchDetail();
  } catch { message.error('Failed to delete document'); }
}

function goBack() {
  router.push('/agcm/procurement/subcontracts');
}

onMounted(async () => {
  await fetchProjects();
  await fetchDetail();
});
</script>

<template>
  <Page :title="isNew ? 'New Subcontract' : `Subcontract: ${detail?.sequence_name || ''}`" description="Subcontract details, SOV, and compliance">
    <template #extra>
      <Space>
        <Button @click="goBack"><ArrowLeftOutlined /> Back</Button>
        <template v-if="!isNew && detail">
          <Button v-if="detail.status === 'draft' || detail.status === 'pending_approval'" type="primary" @click="handleApprove"><CheckOutlined /> Approve</Button>
          <Button @click="openBillingModal">Update Billing</Button>
        </template>
      </Space>
    </template>

    <!-- NEW Form -->
    <Card v-if="isNew" title="Create Subcontract" :loading="loading">
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
              <Input v-model:value="form.vendor_name" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Contract Number">
              <Input v-model:value="form.contract_number" />
            </FormItem>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="8"><FormItem label="Original Amount"><InputNumber v-model:value="form.original_amount" :min="0" :precision="2" prefix="$" style="width: 100%" /></FormItem></Col>
          <Col :span="8"><FormItem label="Retainage %"><InputNumber v-model:value="form.retainage_pct" :min="0" :max="100" :precision="1" style="width: 100%" /></FormItem></Col>
          <Col :span="8"><FormItem label="Vendor Contact"><Input v-model:value="form.vendor_contact" /></FormItem></Col>
        </Row>
        <Row :gutter="16">
          <Col :span="24"><FormItem label="Scope of Work"><Textarea v-model:value="form.scope_of_work" :rows="3" /></FormItem></Col>
        </Row>
        <Button type="primary" :loading="saving" @click="handleSave"><SaveOutlined /> Create</Button>
      </Form>
    </Card>

    <!-- DETAIL View -->
    <template v-if="!isNew && detail">
      <Row :gutter="16" class="mb-4">
        <Col :span="4"><Card><Statistic title="Original" :value="detail.original_amount" :precision="2" prefix="$" /></Card></Col>
        <Col :span="3"><Card><Statistic title="Change Orders" :value="detail.approved_cos" :precision="2" prefix="$" /></Card></Col>
        <Col :span="4"><Card><Statistic title="Revised" :value="detail.revised_amount" :precision="2" prefix="$" /></Card></Col>
        <Col :span="3"><Card><Statistic title="Billed" :value="detail.billed_to_date" :precision="2" prefix="$" /></Card></Col>
        <Col :span="3"><Card><Statistic title="Paid" :value="detail.paid_to_date" :precision="2" prefix="$" /></Card></Col>
        <Col :span="4"><Card><Statistic title="Balance" :value="detail.balance_remaining" :precision="2" prefix="$" /></Card></Col>
        <Col :span="3"><Card><Statistic title="Retainage" :value="detail.retainage_held" :precision="2" prefix="$" /></Card></Col>
      </Row>

      <Card title="Contract Info" :loading="loading" class="mb-4">
        <Descriptions :column="3" bordered size="small">
          <DescriptionsItem label="Sequence">{{ detail.sequence_name }}</DescriptionsItem>
          <DescriptionsItem label="Contract #">{{ detail.contract_number || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Status"><Badge :status="statusColors[detail.status] || 'default'" :text="formatStatus(detail.status)" /></DescriptionsItem>
          <DescriptionsItem label="Vendor">{{ detail.vendor_name }}</DescriptionsItem>
          <DescriptionsItem label="Start Date">{{ detail.start_date || '-' }}</DescriptionsItem>
          <DescriptionsItem label="End Date">{{ detail.end_date || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Scope" :span="3">{{ detail.scope_of_work || '-' }}</DescriptionsItem>
        </Descriptions>
      </Card>

      <!-- SOV Lines -->
      <Card title="Schedule of Values (AIA G702)" class="mb-4">
        <template #extra>
          <Button type="primary" size="small" @click="openSovModal()"><PlusOutlined /> Add SOV Line</Button>
        </template>
        <Table :columns="sovColumns" :data-source="detail.sov_lines || []" row-key="id" size="small" :pagination="false" :scroll="{ x: 1200 }">
          <template #bodyCell="{ column, record }">
            <template v-if="['scheduled_value', 'billed_previous', 'billed_current', 'stored_materials', 'total_completed', 'retainage', 'balance_to_finish'].includes(column.key)">
              {{ formatCurrency(record[column.dataIndex]) }}
            </template>
            <template v-else-if="column.key === 'pct_complete'">
              {{ record.pct_complete?.toFixed(1) }}%
            </template>
            <template v-else-if="column.key === 'actions'">
              <Space>
                <Button type="link" size="small" @click="openSovModal(record)"><EditOutlined /></Button>
                <Popconfirm title="Delete?" @confirm="deleteSov(record.id)">
                  <Button type="link" size="small" danger><DeleteOutlined /></Button>
                </Popconfirm>
              </Space>
            </template>
          </template>
        </Table>
      </Card>

      <!-- Compliance Docs -->
      <Card title="Compliance Documents">
        <template #extra>
          <Button type="primary" size="small" @click="openDocModal()"><PlusOutlined /> Add Document</Button>
        </template>
        <Table :columns="complianceColumns" :data-source="detail.compliance_docs || []" row-key="id" size="small" :pagination="false">
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'doc_type'">
              {{ formatStatus(record.doc_type) }}
            </template>
            <template v-else-if="column.key === 'status'">
              <Tag :color="docStatusColors[record.status] || 'default'">{{ formatStatus(record.status) }}</Tag>
            </template>
            <template v-else-if="column.key === 'file_name'">
              <a v-if="record.document_url" :href="record.document_url" target="_blank">{{ record.file_name || 'View' }}</a>
              <span v-else>-</span>
            </template>
            <template v-else-if="column.key === 'actions'">
              <Space>
                <Button type="link" size="small" @click="openDocModal(record)"><EditOutlined /></Button>
                <Popconfirm title="Delete?" @confirm="deleteDoc(record.id)">
                  <Button type="link" size="small" danger><DeleteOutlined /></Button>
                </Popconfirm>
              </Space>
            </template>
          </template>
        </Table>
      </Card>
    </template>

    <!-- SOV Line Modal -->
    <Modal v-model:open="showSovModal" :title="editingSov ? 'Edit SOV Line' : 'Add SOV Line'" @ok="saveSov" width="600px">
      <Form layout="vertical">
        <Row :gutter="16">
          <Col :span="8"><FormItem label="Cost Code"><Input v-model:value="sovForm.cost_code" /></FormItem></Col>
          <Col :span="16"><FormItem label="Description" required><Input v-model:value="sovForm.description" /></FormItem></Col>
        </Row>
        <Row :gutter="16">
          <Col :span="8"><FormItem label="Scheduled Value"><InputNumber v-model:value="sovForm.scheduled_value" :min="0" :precision="2" prefix="$" style="width: 100%" /></FormItem></Col>
          <Col :span="8">
            <FormItem label="Source Type">
              <Select v-model:value="sovForm.source_type" style="width: 100%">
                <SelectOption value="original">Original</SelectOption>
                <SelectOption value="change_order">Change Order</SelectOption>
              </Select>
            </FormItem>
          </Col>
          <Col :span="8"><FormItem label="Order"><InputNumber v-model:value="sovForm.display_order" :min="0" style="width: 100%" /></FormItem></Col>
        </Row>
      </Form>
    </Modal>

    <!-- Compliance Doc Modal -->
    <Modal v-model:open="showDocModal" :title="editingDoc ? 'Edit Document' : 'Add Document'" @ok="saveDoc" width="600px">
      <Form layout="vertical">
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Document Type">
              <Select v-model:value="docForm.doc_type" style="width: 100%">
                <SelectOption v-for="t in docTypeOptions" :key="t.value" :value="t.value">{{ t.label }}</SelectOption>
              </Select>
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Status">
              <Select v-model:value="docForm.status" style="width: 100%">
                <SelectOption v-for="s in docStatusOptions" :key="s.value" :value="s.value">{{ s.label }}</SelectOption>
              </Select>
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Description" required><Input v-model:value="docForm.description" /></FormItem>
        <Row :gutter="16">
          <Col :span="12"><FormItem label="Document URL"><Input v-model:value="docForm.document_url" placeholder="https://..." /></FormItem></Col>
          <Col :span="12"><FormItem label="File Name"><Input v-model:value="docForm.file_name" /></FormItem></Col>
        </Row>
        <FormItem label="Notes"><Textarea v-model:value="docForm.notes" :rows="2" /></FormItem>
      </Form>
    </Modal>

    <!-- Billing Update Modal -->
    <Modal v-model:open="showBillingModal" title="Update Billing" @ok="handleUpdateBilling" width="800px">
      <Table :data-source="billingLines" row-key="line_id" size="small" :pagination="false">
        <template #columns>
          <Table.Column title="Description" dataIndex="description" />
          <Table.Column title="Scheduled" dataIndex="scheduled_value" width="120">
            <template #default="{ record }">{{ formatCurrency(record.scheduled_value) }}</template>
          </Table.Column>
          <Table.Column title="Previous" dataIndex="billed_previous" width="120">
            <template #default="{ record }">{{ formatCurrency(record.billed_previous) }}</template>
          </Table.Column>
          <Table.Column title="Current" key="billed_current" width="140">
            <template #default="{ record }">
              <InputNumber v-model:value="record.billed_current" :min="0" :precision="2" prefix="$" size="small" style="width: 100%" />
            </template>
          </Table.Column>
          <Table.Column title="Materials" key="stored_materials" width="140">
            <template #default="{ record }">
              <InputNumber v-model:value="record.stored_materials" :min="0" :precision="2" prefix="$" size="small" style="width: 100%" />
            </template>
          </Table.Column>
        </template>
      </Table>
    </Modal>
  </Page>
</template>
