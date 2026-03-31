<script setup>
import { computed, onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Badge,
  Button,
  Card,
  Col,
  Descriptions,
  DescriptionsItem,
  Divider,
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
  Tabs,
  TabPane,
  Tag,
  Textarea,
} from 'ant-design-vue';
import {
  CheckOutlined,
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  PlusOutlined,
  ReloadOutlined,
  TrophyOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMPortalBids' });

const BASE_URL = '/agcm_portal';

const loading = ref(false);
const items = ref([]);
const pagination = ref({ current: 1, pageSize: 20, total: 0 });
const searchText = ref('');
const statusFilter = ref(null);
const projectFilter = ref(null);
const projects = ref([]);

// Package Modal
const pkgModalVisible = ref(false);
const pkgModalTitle = ref('');
const pkgSaving = ref(false);
const editingPkgId = ref(null);
const pkgForm = ref({
  project_id: null, name: '', description: '', trade: '',
  due_date: null, status: 'open', notes: '',
});

// Submission Modal
const subModalVisible = ref(false);
const subSaving = ref(false);
const editingSubId = ref(null);
const activeBidPackageId = ref(null);
const subForm = ref({
  vendor_name: '', vendor_email: '', vendor_phone: '',
  total_amount: 0, scope_description: '', exclusions: '',
  submitted_date: null, document_url: '', notes: '',
});

// Detail Drawer
const drawerVisible = ref(false);
const detailItem = ref(null);

const statusColors = {
  open: 'processing',
  closed: 'default',
  awarded: 'success',
};

const bidStatusColors = {
  invited: 'default',
  draft: 'default',
  submitted: 'processing',
  under_review: 'warning',
  awarded: 'success',
  rejected: 'error',
  withdrawn: 'default',
};

const columns = computed(() => [
  { title: 'Seq #', dataIndex: 'sequence_name', key: 'sequence_name', width: 110 },
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Trade', dataIndex: 'trade', key: 'trade', width: 120 },
  { title: 'Status', key: 'status', width: 100 },
  { title: 'Due Date', dataIndex: 'due_date', key: 'due_date', width: 120 },
  { title: 'Submissions', key: 'sub_count', width: 110 },
  { title: 'Actions', key: 'actions', width: 180, fixed: 'right' },
]);

const subColumns = [
  { title: 'Vendor', dataIndex: 'vendor_name', key: 'vendor_name' },
  { title: 'Status', key: 'status', width: 120 },
  { title: 'Amount', key: 'total_amount', width: 130 },
  { title: 'Submitted', dataIndex: 'submitted_date', key: 'submitted_date', width: 120 },
  { title: 'Awarded', key: 'is_awarded', width: 90 },
  { title: 'Actions', key: 'actions', width: 180 },
];

async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = data.items || data.results || [];
  } catch { /* ignore */ }
}

async function fetchData() {
  loading.value = true;
  try {
    const params = {
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
      search: searchText.value || undefined,
      status: statusFilter.value || undefined,
      project_id: projectFilter.value || undefined,
    };
    const data = await requestClient.get(`${BASE_URL}/bid-packages`, { params });
    items.value = data.items || [];
    pagination.value.total = data.total || 0;
  } catch {
    message.error('Failed to load bid packages');
  } finally {
    loading.value = false;
  }
}

function handleTableChange(pag) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

function openCreatePkg() {
  editingPkgId.value = null;
  pkgForm.value = {
    project_id: projectFilter.value, name: '', description: '', trade: '',
    due_date: null, status: 'open', notes: '',
  };
  pkgModalTitle.value = 'New Bid Package';
  pkgModalVisible.value = true;
}

function openEditPkg(record) {
  editingPkgId.value = record.id;
  pkgForm.value = { ...record };
  pkgModalTitle.value = 'Edit Bid Package';
  pkgModalVisible.value = true;
}

async function handleSavePkg() {
  if (!pkgForm.value.name || !pkgForm.value.project_id) {
    message.warning('Name and project are required');
    return;
  }
  pkgSaving.value = true;
  try {
    if (editingPkgId.value) {
      await requestClient.put(`${BASE_URL}/bid-packages/${editingPkgId.value}`, pkgForm.value);
      message.success('Bid package updated');
    } else {
      await requestClient.post(`${BASE_URL}/bid-packages`, pkgForm.value);
      message.success('Bid package created');
    }
    pkgModalVisible.value = false;
    fetchData();
  } catch {
    message.error('Failed to save bid package');
  } finally {
    pkgSaving.value = false;
  }
}

async function handleDeletePkg(id) {
  try {
    await requestClient.delete(`${BASE_URL}/bid-packages/${id}`);
    message.success('Bid package deleted');
    fetchData();
  } catch {
    message.error('Failed to delete bid package');
  }
}

async function openDetail(record) {
  try {
    const data = await requestClient.get(`${BASE_URL}/bid-packages/${record.id}`);
    detailItem.value = data;
    drawerVisible.value = true;
  } catch {
    message.error('Failed to load bid package details');
  }
}

// --- Submissions ---

function openCreateSub(bidPackageId) {
  activeBidPackageId.value = bidPackageId;
  editingSubId.value = null;
  subForm.value = {
    vendor_name: '', vendor_email: '', vendor_phone: '',
    total_amount: 0, scope_description: '', exclusions: '',
    submitted_date: null, document_url: '', notes: '',
  };
  subModalVisible.value = true;
}

function openEditSub(sub) {
  activeBidPackageId.value = sub.bid_package_id;
  editingSubId.value = sub.id;
  subForm.value = { ...sub };
  subModalVisible.value = true;
}

async function handleSaveSub() {
  if (!subForm.value.vendor_name) {
    message.warning('Vendor name is required');
    return;
  }
  subSaving.value = true;
  try {
    if (editingSubId.value) {
      await requestClient.put(`${BASE_URL}/submissions/${editingSubId.value}`, subForm.value);
      message.success('Submission updated');
    } else {
      await requestClient.post(`${BASE_URL}/bid-packages/${activeBidPackageId.value}/submissions`, subForm.value);
      message.success('Submission created');
    }
    subModalVisible.value = false;
    // Refresh detail
    if (detailItem.value) {
      const data = await requestClient.get(`${BASE_URL}/bid-packages/${detailItem.value.id}`);
      detailItem.value = data;
    }
    fetchData();
  } catch {
    message.error('Failed to save submission');
  } finally {
    subSaving.value = false;
  }
}

async function handleDeleteSub(subId) {
  try {
    await requestClient.delete(`${BASE_URL}/submissions/${subId}`);
    message.success('Submission deleted');
    if (detailItem.value) {
      const data = await requestClient.get(`${BASE_URL}/bid-packages/${detailItem.value.id}`);
      detailItem.value = data;
    }
    fetchData();
  } catch {
    message.error('Failed to delete submission');
  }
}

async function handleAward(subId) {
  try {
    await requestClient.post(`${BASE_URL}/submissions/${subId}/award`);
    message.success('Bid awarded');
    if (detailItem.value) {
      const data = await requestClient.get(`${BASE_URL}/bid-packages/${detailItem.value.id}`);
      detailItem.value = data;
    }
    fetchData();
  } catch {
    message.error('Failed to award bid');
  }
}

function formatCurrency(val) {
  if (val == null) return '$0.00';
  return `$${Number(val).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

onMounted(() => {
  fetchProjects();
  fetchData();
});
</script>

<template>
  <Page title="Bid Packages" description="Manage bid requests and subcontractor submissions">
    <Card>
      <div style="margin-bottom: 16px; display: flex; gap: 12px; flex-wrap: wrap; align-items: center">
        <Input
          v-model:value="searchText"
          placeholder="Search bid packages..."
          style="width: 220px"
          allow-clear
          @press-enter="fetchData"
        />
        <Select
          v-model:value="projectFilter"
          placeholder="All Projects"
          style="width: 200px"
          allow-clear
          @change="fetchData"
        >
          <SelectOption v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</SelectOption>
        </Select>
        <Select
          v-model:value="statusFilter"
          placeholder="All Statuses"
          style="width: 150px"
          allow-clear
          @change="fetchData"
        >
          <SelectOption value="open">Open</SelectOption>
          <SelectOption value="closed">Closed</SelectOption>
          <SelectOption value="awarded">Awarded</SelectOption>
        </Select>
        <div style="flex: 1" />
        <Button @click="fetchData"><ReloadOutlined /> Refresh</Button>
        <Button type="primary" @click="openCreatePkg"><PlusOutlined /> New Bid Package</Button>
      </div>

      <Table
        :columns="columns"
        :data-source="items"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        size="small"
        :scroll="{ x: 1000 }"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <Badge :status="statusColors[record.status] || 'default'" :text="record.status" />
          </template>
          <template v-else-if="column.key === 'sub_count'">
            {{ (record.submissions || []).length }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button size="small" @click="openDetail(record)"><EyeOutlined /></Button>
              <Button size="small" @click="openEditPkg(record)"><EditOutlined /></Button>
              <Popconfirm title="Delete this bid package?" @confirm="handleDeletePkg(record.id)">
                <Button size="small" danger><DeleteOutlined /></Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <!-- Bid Package Modal -->
    <Modal
      v-model:open="pkgModalVisible"
      :title="pkgModalTitle"
      :confirm-loading="pkgSaving"
      @ok="handleSavePkg"
      width="600px"
    >
      <Form layout="vertical">
        <FormItem label="Project" required>
          <Select v-model:value="pkgForm.project_id" placeholder="Select project" :disabled="!!editingPkgId">
            <SelectOption v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</SelectOption>
          </Select>
        </FormItem>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Name" required>
              <Input v-model:value="pkgForm.name" placeholder="Bid package name" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Trade">
              <Input v-model:value="pkgForm.trade" placeholder="e.g. Electrical" />
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Description">
          <Textarea v-model:value="pkgForm.description" :rows="3" />
        </FormItem>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Due Date">
              <Input v-model:value="pkgForm.due_date" type="date" style="width: 100%" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Status">
              <Select v-model:value="pkgForm.status">
                <SelectOption value="open">Open</SelectOption>
                <SelectOption value="closed">Closed</SelectOption>
                <SelectOption value="awarded">Awarded</SelectOption>
              </Select>
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Notes">
          <Textarea v-model:value="pkgForm.notes" :rows="2" />
        </FormItem>
      </Form>
    </Modal>

    <!-- Submission Modal -->
    <Modal
      v-model:open="subModalVisible"
      :title="editingSubId ? 'Edit Submission' : 'New Submission'"
      :confirm-loading="subSaving"
      @ok="handleSaveSub"
      width="600px"
    >
      <Form layout="vertical">
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Vendor Name" required>
              <Input v-model:value="subForm.vendor_name" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Total Amount">
              <InputNumber v-model:value="subForm.total_amount" :min="0" :precision="2" prefix="$" style="width: 100%" />
            </FormItem>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Email">
              <Input v-model:value="subForm.vendor_email" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Phone">
              <Input v-model:value="subForm.vendor_phone" />
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Scope Description">
          <Textarea v-model:value="subForm.scope_description" :rows="3" />
        </FormItem>
        <FormItem label="Exclusions">
          <Textarea v-model:value="subForm.exclusions" :rows="2" />
        </FormItem>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Submitted Date">
              <Input v-model:value="subForm.submitted_date" type="date" style="width: 100%" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Document URL">
              <Input v-model:value="subForm.document_url" />
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Notes">
          <Textarea v-model:value="subForm.notes" :rows="2" />
        </FormItem>
      </Form>
    </Modal>

    <!-- Detail Drawer -->
    <Drawer
      v-model:open="drawerVisible"
      :title="detailItem ? `${detailItem.sequence_name} - ${detailItem.name}` : 'Bid Package'"
      width="800"
      placement="right"
    >
      <template v-if="detailItem">
        <Descriptions :column="2" bordered size="small">
          <DescriptionsItem label="Trade">{{ detailItem.trade || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Status">
            <Badge :status="statusColors[detailItem.status] || 'default'" :text="detailItem.status" />
          </DescriptionsItem>
          <DescriptionsItem label="Due Date">{{ detailItem.due_date || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Submissions">{{ (detailItem.submissions || []).length }}</DescriptionsItem>
          <DescriptionsItem label="Description" :span="2">{{ detailItem.description || '-' }}</DescriptionsItem>
        </Descriptions>

        <Divider>
          Submissions
          <Button size="small" type="link" @click="openCreateSub(detailItem.id)"><PlusOutlined /> Add</Button>
        </Divider>

        <Table
          :columns="subColumns"
          :data-source="detailItem.submissions || []"
          row-key="id"
          size="small"
          :pagination="false"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <Tag :color="bidStatusColors[record.status] || 'default'">{{ record.status }}</Tag>
            </template>
            <template v-else-if="column.key === 'total_amount'">
              {{ formatCurrency(record.total_amount) }}
            </template>
            <template v-else-if="column.key === 'is_awarded'">
              <Tag v-if="record.is_awarded" color="gold"><TrophyOutlined /> Yes</Tag>
              <span v-else>-</span>
            </template>
            <template v-else-if="column.key === 'actions'">
              <Space>
                <Button size="small" @click="openEditSub(record)"><EditOutlined /></Button>
                <Popconfirm v-if="!record.is_awarded" title="Award this bid?" @confirm="handleAward(record.id)">
                  <Button size="small" type="primary"><TrophyOutlined /></Button>
                </Popconfirm>
                <Popconfirm title="Delete this submission?" @confirm="handleDeleteSub(record.id)">
                  <Button size="small" danger><DeleteOutlined /></Button>
                </Popconfirm>
              </Space>
            </template>
          </template>
        </Table>
      </template>
    </Drawer>
  </Page>
</template>
