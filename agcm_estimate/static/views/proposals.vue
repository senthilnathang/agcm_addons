<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { requestClient } from '#/api/request';
import { message } from 'ant-design-vue';
import {
  CheckOutlined,
  CloseOutlined,
  DeleteOutlined,
  DownloadOutlined,
  EyeOutlined,
  PlusOutlined,
  ReloadOutlined,
  SendOutlined,
} from '@ant-design/icons-vue';

defineOptions({ name: 'AGCMProposals' });

const BASE = '/agcm_estimate';

const loading = ref(false);
const items = ref([]);
const projects = ref([]);
const projectFilter = ref(null);
const statusFilter = ref(null);

const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showTotal: (total) => `Total ${total} proposals`,
});

const statusOptions = [
  { value: 'draft', label: 'Draft' },
  { value: 'sent', label: 'Sent' },
  { value: 'viewed', label: 'Viewed' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'expired', label: 'Expired' },
];

const statusColors = {
  draft: 'default',
  sent: 'processing',
  viewed: 'warning',
  approved: 'success',
  rejected: 'error',
  expired: 'default',
};

function fmtCurrency(val) {
  if (val == null) return '$0.00';
  return Number(val).toLocaleString('en-US', { style: 'currency', currency: 'USD' });
}

function fmtLabel(str) {
  if (!str) return '';
  return str.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

const columns = computed(() => [
  { title: 'Seq #', dataIndex: 'sequence_name', key: 'sequence_name', width: 120 },
  { title: 'Name', dataIndex: 'name', key: 'name', ellipsis: true },
  { title: 'Client', dataIndex: 'client_name', key: 'client_name', width: 180 },
  { title: 'Status', key: 'status', width: 120 },
  { title: 'Grand Total', key: 'grand_total', width: 150, align: 'right' },
  { title: 'Valid Until', dataIndex: 'valid_until', key: 'valid_until', width: 120 },
  { title: 'Actions', key: 'actions', width: 100, fixed: 'right' },
]);

// Detail drawer
const detailVisible = ref(false);
const detailLoading = ref(false);
const detailRecord = ref(null);

// Create modal
const createVisible = ref(false);
const createSaving = ref(false);
const estimates = ref([]);
const createForm = reactive({
  estimate_id: null,
  name: '',
  client_name: '',
  client_email: '',
  client_phone: '',
  client_company: '',
  scope_of_work: '',
  terms_and_conditions: '',
  exclusions: '',
  payment_schedule: '',
  valid_until: null,
  show_line_items: true,
  show_unit_prices: false,
  show_markup: false,
  show_groups: true,
});

async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = (data.items || []).map(p => ({
      value: p.id, label: `${p.sequence_name || ''} - ${p.name}`,
    }));
  } catch { /* ignore */ }
}

async function fetchData() {
  loading.value = true;
  try {
    const params = {
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
      project_id: projectFilter.value || undefined,
      status: statusFilter.value || undefined,
    };
    const res = await requestClient.get(`${BASE}/proposals`, { params });
    items.value = res.items || [];
    pagination.value.total = res.total || 0;
  } catch {
    message.error('Failed to load proposals');
  } finally {
    loading.value = false;
  }
}

function onTableChange(pag) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

function handleFilterChange() {
  pagination.value.current = 1;
  fetchData();
}

async function openDetail(record) {
  detailLoading.value = true;
  detailVisible.value = true;
  try {
    detailRecord.value = await requestClient.get(`${BASE}/proposals/${record.id}`);
  } catch {
    message.error('Failed to load proposal');
    detailRecord.value = record;
  } finally {
    detailLoading.value = false;
  }
}

async function openCreateModal() {
  try {
    const res = await requestClient.get(`${BASE}/estimates`, { params: { page_size: 200, status: 'approved' } });
    estimates.value = (res.items || []).map(e => ({
      value: e.id, label: `${e.sequence_name || ''} - ${e.name}`,
    }));
  } catch {
    estimates.value = [];
  }
  Object.assign(createForm, {
    estimate_id: null, name: '', client_name: '', client_email: '', client_phone: '',
    client_company: '', scope_of_work: '', terms_and_conditions: '', exclusions: '',
    payment_schedule: '', valid_until: null, show_line_items: true,
    show_unit_prices: false, show_markup: false, show_groups: true,
  });
  createVisible.value = true;
}

async function handleCreate() {
  if (!createForm.estimate_id) { message.warning('Please select an estimate'); return; }
  if (!createForm.name) { message.warning('Name is required'); return; }
  createSaving.value = true;
  try {
    await requestClient.post(`${BASE}/proposals`, { ...createForm });
    message.success('Proposal created');
    createVisible.value = false;
    fetchData();
  } catch {
    message.error('Failed to create proposal');
  } finally {
    createSaving.value = false;
  }
}

async function handleSend(record) {
  try {
    await requestClient.post(`${BASE}/proposals/${record.id}/send`);
    message.success('Proposal sent');
    if (detailRecord.value && detailRecord.value.id === record.id) {
      detailRecord.value.status = 'sent';
    }
    fetchData();
  } catch { message.error('Failed to send proposal'); }
}

async function handleApprove(record) {
  try {
    await requestClient.post(`${BASE}/proposals/${record.id}/approve`);
    message.success('Proposal approved');
    if (detailRecord.value && detailRecord.value.id === record.id) {
      detailRecord.value.status = 'approved';
    }
    fetchData();
  } catch { message.error('Failed to approve proposal'); }
}

async function handleReject(record) {
  try {
    await requestClient.post(`${BASE}/proposals/${record.id}/reject`);
    message.success('Proposal rejected');
    if (detailRecord.value && detailRecord.value.id === record.id) {
      detailRecord.value.status = 'rejected';
    }
    fetchData();
  } catch { message.error('Failed to reject proposal'); }
}

async function handleDownloadPdf(record) {
  try {
    const blob = await requestClient.get(`${BASE}/proposals/${record.id}/pdf`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `proposal-${record.sequence_name || record.id}.pdf`;
    a.click();
    window.URL.revokeObjectURL(url);
  } catch { message.error('Failed to download PDF'); }
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/proposals/${record.id}`);
    message.success('Proposal deleted');
    fetchData();
  } catch { message.error('Failed to delete proposal'); }
}

const statusSteps = computed(() => {
  if (!detailRecord.value) return [];
  const order = ['draft', 'sent', 'viewed', 'approved'];
  const current = order.indexOf(detailRecord.value.status);
  return order.map((s, i) => ({
    title: fmtLabel(s),
    status: i < current ? 'finish' : i === current ? 'process' : 'wait',
  }));
});

onMounted(() => {
  fetchProjects();
  fetchData();
});
</script>

<template>
  <Page title="Proposals" description="Client proposals generated from estimates">
    <ACard>
      <div class="mb-4 flex items-center justify-between">
        <ASpace>
          <ASelect
            v-model:value="projectFilter"
            :options="projects"
            placeholder="All Projects"
            allow-clear
            show-search
            :filter-option="(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
            style="width: 280px"
            @change="handleFilterChange"
          />
          <ASelect
            v-model:value="statusFilter"
            :options="statusOptions"
            placeholder="All Statuses"
            allow-clear
            style="width: 150px"
            @change="handleFilterChange"
          />
        </ASpace>
        <ASpace>
          <AButton @click="fetchData">
            <template #icon><ReloadOutlined /></template>
            Refresh
          </AButton>
          <AButton type="primary" @click="openCreateModal">
            <template #icon><PlusOutlined /></template>
            New Proposal
          </AButton>
        </ASpace>
      </div>

      <ATable
        :columns="columns"
        :data-source="items"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        size="middle"
        :custom-row="(record) => ({ onClick: () => openDetail(record) })"
        @change="onTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <ABadge :status="statusColors[record.status] || 'default'" :text="fmtLabel(record.status)" />
          </template>
          <template v-else-if="column.key === 'grand_total'">
            {{ fmtCurrency(record.grand_total) }}
          </template>
          <template v-else-if="column.key === 'valid_until'">
            {{ record.valid_until ? new Date(record.valid_until).toLocaleDateString() : '-' }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <ASpace>
              <AButton type="link" size="small" @click.stop="openDetail(record)">
                <template #icon><EyeOutlined /></template>
              </AButton>
              <APopconfirm title="Delete this proposal?" ok-text="Yes" cancel-text="No" @confirm="handleDelete(record)">
                <AButton type="link" size="small" danger @click.stop>
                  <template #icon><DeleteOutlined /></template>
                </AButton>
              </APopconfirm>
            </ASpace>
          </template>
        </template>
      </ATable>
    </ACard>

    <!-- Proposal Detail Drawer -->
    <ADrawer
      :open="detailVisible"
      :title="detailRecord ? detailRecord.name : 'Proposal'"
      :width="600"
      @close="detailVisible = false"
    >
      <ASpin :spinning="detailLoading">
        <template v-if="detailRecord">
          <!-- Status Timeline -->
          <ASteps :current="-1" size="small" class="proposal-timeline" style="margin-bottom: 24px">
            <AStep
              v-for="step in statusSteps"
              :key="step.title"
              :title="step.title"
              :status="step.status"
            />
          </ASteps>

          <ADescriptions :column="2" bordered size="small">
            <ADescriptionsItem label="Status" :span="2">
              <ABadge :status="statusColors[detailRecord.status] || 'default'" :text="fmtLabel(detailRecord.status)" />
            </ADescriptionsItem>
            <ADescriptionsItem label="Client">{{ detailRecord.client_name || '-' }}</ADescriptionsItem>
            <ADescriptionsItem label="Company">{{ detailRecord.client_company || '-' }}</ADescriptionsItem>
            <ADescriptionsItem label="Email">{{ detailRecord.client_email || '-' }}</ADescriptionsItem>
            <ADescriptionsItem label="Phone">{{ detailRecord.client_phone || '-' }}</ADescriptionsItem>
            <ADescriptionsItem label="Grand Total" :span="2">
              <span style="font-size: 18px; font-weight: 600">{{ fmtCurrency(detailRecord.grand_total) }}</span>
            </ADescriptionsItem>
            <ADescriptionsItem label="Valid Until" :span="2">
              {{ detailRecord.valid_until ? new Date(detailRecord.valid_until).toLocaleDateString() : '-' }}
            </ADescriptionsItem>
          </ADescriptions>

          <ADivider>Scope of Work</ADivider>
          <p style="white-space: pre-wrap">{{ detailRecord.scope_of_work || 'Not specified' }}</p>

          <ADivider>Terms & Conditions</ADivider>
          <p style="white-space: pre-wrap">{{ detailRecord.terms_and_conditions || 'Not specified' }}</p>

          <ADivider>Exclusions</ADivider>
          <p style="white-space: pre-wrap">{{ detailRecord.exclusions || 'None' }}</p>

          <ADivider>Payment Schedule</ADivider>
          <p style="white-space: pre-wrap">{{ detailRecord.payment_schedule || 'Not specified' }}</p>

          <ADivider>Display Options</ADivider>
          <ASpace direction="vertical">
            <ACheckbox :checked="detailRecord.show_line_items" disabled>Show Line Items</ACheckbox>
            <ACheckbox :checked="detailRecord.show_unit_prices" disabled>Show Unit Prices</ACheckbox>
            <ACheckbox :checked="detailRecord.show_markup" disabled>Show Markup</ACheckbox>
            <ACheckbox :checked="detailRecord.show_groups" disabled>Show Groups</ACheckbox>
          </ASpace>

          <ADivider />
          <ASpace>
            <AButton
              v-if="detailRecord.status === 'draft'"
              type="primary"
              @click="handleSend(detailRecord)"
            >
              <template #icon><SendOutlined /></template>
              Send
            </AButton>
            <AButton
              v-if="['sent', 'viewed'].includes(detailRecord.status)"
              type="primary"
              style="background: #52c41a; border-color: #52c41a"
              @click="handleApprove(detailRecord)"
            >
              <template #icon><CheckOutlined /></template>
              Approve
            </AButton>
            <AButton
              v-if="['sent', 'viewed'].includes(detailRecord.status)"
              danger
              @click="handleReject(detailRecord)"
            >
              <template #icon><CloseOutlined /></template>
              Reject
            </AButton>
            <AButton @click="handleDownloadPdf(detailRecord)">
              <template #icon><DownloadOutlined /></template>
              Download PDF
            </AButton>
          </ASpace>
        </template>
      </ASpin>
    </ADrawer>

    <!-- Create Proposal Modal -->
    <AModal
      v-model:open="createVisible"
      title="New Proposal"
      :width="600"
      :confirm-loading="createSaving"
      ok-text="Create"
      @ok="handleCreate"
    >
      <AForm layout="vertical">
        <AFormItem label="Estimate" required>
          <ASelect
            v-model:value="createForm.estimate_id"
            :options="estimates"
            placeholder="Select approved estimate"
            show-search
            :filter-option="(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
          />
        </AFormItem>
        <AFormItem label="Proposal Name" required>
          <AInput v-model:value="createForm.name" />
        </AFormItem>
        <div style="display: flex; gap: 16px">
          <AFormItem label="Client Name" style="flex: 1">
            <AInput v-model:value="createForm.client_name" />
          </AFormItem>
          <AFormItem label="Client Company" style="flex: 1">
            <AInput v-model:value="createForm.client_company" />
          </AFormItem>
        </div>
        <div style="display: flex; gap: 16px">
          <AFormItem label="Email" style="flex: 1">
            <AInput v-model:value="createForm.client_email" />
          </AFormItem>
          <AFormItem label="Phone" style="flex: 1">
            <AInput v-model:value="createForm.client_phone" />
          </AFormItem>
        </div>
        <AFormItem label="Scope of Work">
          <ATextarea v-model:value="createForm.scope_of_work" :rows="3" />
        </AFormItem>
        <AFormItem label="Terms & Conditions">
          <ATextarea v-model:value="createForm.terms_and_conditions" :rows="3" />
        </AFormItem>
        <AFormItem label="Exclusions">
          <ATextarea v-model:value="createForm.exclusions" :rows="2" />
        </AFormItem>
        <AFormItem label="Payment Schedule">
          <ATextarea v-model:value="createForm.payment_schedule" :rows="2" />
        </AFormItem>
        <AFormItem label="Valid Until">
          <ADatePicker v-model:value="createForm.valid_until" style="width: 100%" />
        </AFormItem>
        <ADivider>Display Options</ADivider>
        <ASpace>
          <ACheckbox v-model:checked="createForm.show_line_items">Line Items</ACheckbox>
          <ACheckbox v-model:checked="createForm.show_unit_prices">Unit Prices</ACheckbox>
          <ACheckbox v-model:checked="createForm.show_markup">Markup</ACheckbox>
          <ACheckbox v-model:checked="createForm.show_groups">Groups</ACheckbox>
        </ASpace>
      </AForm>
    </AModal>
  </Page>
</template>
