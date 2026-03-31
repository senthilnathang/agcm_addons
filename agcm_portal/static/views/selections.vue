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
  Tag,
  Textarea,
} from 'ant-design-vue';
import {
  CheckOutlined,
  CloseOutlined,
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  PlusOutlined,
  ReloadOutlined,
  StarOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMPortalSelections' });

const BASE_URL = '/agcm_portal';

const loading = ref(false);
const items = ref([]);
const pagination = ref({ current: 1, pageSize: 20, total: 0 });
const searchText = ref('');
const statusFilter = ref(null);
const categoryFilter = ref(null);
const projectFilter = ref(null);
const projects = ref([]);

// Modal state
const modalVisible = ref(false);
const modalTitle = ref('');
const saving = ref(false);
const editingId = ref(null);
const form = ref({
  project_id: null,
  name: '',
  category: '',
  description: '',
  location: '',
  due_date: null,
  budget_amount: 0,
  notes: '',
  options: [],
});

// Detail drawer
const drawerVisible = ref(false);
const detailItem = ref(null);

const categoryOptions = [
  'Flooring', 'Countertops', 'Fixtures', 'Paint', 'Tile',
  'Cabinets', 'Lighting', 'Appliances', 'Hardware', 'Other',
];

const statusColors = {
  pending: 'default',
  presented: 'processing',
  approved: 'success',
  rejected: 'error',
};

const columns = computed(() => [
  { title: 'Project', dataIndex: 'project_id', key: 'project_id', width: 100 },
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Category', dataIndex: 'category', key: 'category', width: 120 },
  { title: 'Status', key: 'status', width: 110 },
  { title: 'Due Date', dataIndex: 'due_date', key: 'due_date', width: 120 },
  { title: 'Budget', dataIndex: 'budget_amount', key: 'budget_amount', width: 120 },
  { title: 'Selected', dataIndex: 'selected_amount', key: 'selected_amount', width: 120 },
  { title: 'Impact', key: 'budget_impact', width: 120 },
  { title: 'Options', key: 'options_count', width: 80 },
  { title: 'Actions', key: 'actions', width: 200, fixed: 'right' },
]);

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
      category: categoryFilter.value || undefined,
      project_id: projectFilter.value || undefined,
    };
    const data = await requestClient.get(`${BASE_URL}/selections`, { params });
    items.value = data.items || [];
    pagination.value.total = data.total || 0;
  } catch {
    message.error('Failed to load selections');
  } finally {
    loading.value = false;
  }
}

function handleTableChange(pag) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

function openCreate() {
  editingId.value = null;
  form.value = {
    project_id: projectFilter.value,
    name: '', category: '', description: '', location: '',
    due_date: null, budget_amount: 0, notes: '', options: [],
  };
  modalTitle.value = 'New Selection';
  modalVisible.value = true;
}

function openEdit(record) {
  editingId.value = record.id;
  form.value = { ...record, options: [] };
  modalTitle.value = 'Edit Selection';
  modalVisible.value = true;
}

async function handleSave() {
  if (!form.value.name || !form.value.category || !form.value.project_id) {
    message.warning('Name, category, and project are required');
    return;
  }
  saving.value = true;
  try {
    if (editingId.value) {
      await requestClient.put(`${BASE_URL}/selections/${editingId.value}`, form.value);
      message.success('Selection updated');
    } else {
      await requestClient.post(`${BASE_URL}/selections`, form.value);
      message.success('Selection created');
    }
    modalVisible.value = false;
    fetchData();
  } catch {
    message.error('Failed to save selection');
  } finally {
    saving.value = false;
  }
}

async function handleDelete(id) {
  try {
    await requestClient.delete(`${BASE_URL}/selections/${id}`);
    message.success('Selection deleted');
    fetchData();
  } catch {
    message.error('Failed to delete selection');
  }
}

async function openDetail(record) {
  try {
    const data = await requestClient.get(`${BASE_URL}/selections/${record.id}`);
    detailItem.value = data;
    drawerVisible.value = true;
  } catch {
    message.error('Failed to load selection details');
  }
}

async function handleApprove(selectionId, optionId) {
  try {
    await requestClient.post(`${BASE_URL}/selections/${selectionId}/approve`, null, {
      params: { option_id: optionId },
    });
    message.success('Selection approved');
    const data = await requestClient.get(`${BASE_URL}/selections/${selectionId}`);
    detailItem.value = data;
    fetchData();
  } catch {
    message.error('Failed to approve selection');
  }
}

async function handleReject(selectionId) {
  try {
    await requestClient.post(`${BASE_URL}/selections/${selectionId}/reject`);
    message.success('Selection rejected');
    drawerVisible.value = false;
    fetchData();
  } catch {
    message.error('Failed to reject selection');
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
  <Page title="Selections" description="Material and finish selections for client approval">
    <Card>
      <div style="margin-bottom: 16px; display: flex; gap: 12px; flex-wrap: wrap; align-items: center">
        <Input
          v-model:value="searchText"
          placeholder="Search selections..."
          style="width: 220px"
          allow-clear
          @press-enter="fetchData"
        >
          <template #prefix><SearchOutlined /></template>
        </Input>
        <Select
          v-model:value="projectFilter"
          placeholder="All Projects"
          style="width: 200px"
          allow-clear
          @change="fetchData"
        >
          <SelectOption v-for="p in projects" :key="p.id" :value="p.id">
            {{ p.name }}
          </SelectOption>
        </Select>
        <Select
          v-model:value="statusFilter"
          placeholder="All Statuses"
          style="width: 150px"
          allow-clear
          @change="fetchData"
        >
          <SelectOption value="pending">Pending</SelectOption>
          <SelectOption value="presented">Presented</SelectOption>
          <SelectOption value="approved">Approved</SelectOption>
          <SelectOption value="rejected">Rejected</SelectOption>
        </Select>
        <Select
          v-model:value="categoryFilter"
          placeholder="All Categories"
          style="width: 160px"
          allow-clear
          @change="fetchData"
        >
          <SelectOption v-for="cat in categoryOptions" :key="cat" :value="cat.toLowerCase()">
            {{ cat }}
          </SelectOption>
        </Select>
        <div style="flex: 1" />
        <Button @click="fetchData"><ReloadOutlined /> Refresh</Button>
        <Button type="primary" @click="openCreate"><PlusOutlined /> New Selection</Button>
      </div>

      <Table
        :columns="columns"
        :data-source="items"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        size="small"
        :scroll="{ x: 1200 }"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <Badge :status="statusColors[record.status] || 'default'" :text="record.status" />
          </template>
          <template v-else-if="column.key === 'budget_impact'">
            <span :style="{ color: record.budget_impact > 0 ? '#cf1322' : record.budget_impact < 0 ? '#3f8600' : '' }">
              {{ formatCurrency(record.budget_impact) }}
            </span>
          </template>
          <template v-else-if="column.key === 'options_count'">
            {{ (record.options || []).length }}
          </template>
          <template v-else-if="column.key === 'budget_amount' || column.key === 'selected_amount'">
            {{ formatCurrency(record[column.dataIndex]) }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button size="small" @click="openDetail(record)"><EyeOutlined /></Button>
              <Button size="small" @click="openEdit(record)"><EditOutlined /></Button>
              <Popconfirm title="Delete this selection?" @confirm="handleDelete(record.id)">
                <Button size="small" danger><DeleteOutlined /></Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <!-- Create/Edit Modal -->
    <Modal
      v-model:open="modalVisible"
      :title="modalTitle"
      :confirm-loading="saving"
      @ok="handleSave"
      width="600px"
    >
      <Form layout="vertical">
        <FormItem label="Project" required>
          <Select v-model:value="form.project_id" placeholder="Select project" :disabled="!!editingId">
            <SelectOption v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</SelectOption>
          </Select>
        </FormItem>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Name" required>
              <Input v-model:value="form.name" placeholder="Selection name" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Category" required>
              <Select v-model:value="form.category" placeholder="Select category">
                <SelectOption v-for="cat in categoryOptions" :key="cat" :value="cat.toLowerCase()">
                  {{ cat }}
                </SelectOption>
              </Select>
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Location">
          <Input v-model:value="form.location" placeholder="e.g. Master Bathroom" />
        </FormItem>
        <FormItem label="Description">
          <Textarea v-model:value="form.description" :rows="3" />
        </FormItem>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Budget Amount">
              <InputNumber v-model:value="form.budget_amount" :min="0" :precision="2" prefix="$" style="width: 100%" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Due Date">
              <Input v-model:value="form.due_date" type="date" style="width: 100%" />
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Notes">
          <Textarea v-model:value="form.notes" :rows="2" />
        </FormItem>
      </Form>
    </Modal>

    <!-- Detail Drawer -->
    <Drawer
      v-model:open="drawerVisible"
      :title="detailItem ? detailItem.name : 'Selection Detail'"
      width="680"
      placement="right"
    >
      <template v-if="detailItem">
        <Descriptions :column="2" bordered size="small">
          <DescriptionsItem label="Category">{{ detailItem.category }}</DescriptionsItem>
          <DescriptionsItem label="Status">
            <Badge :status="statusColors[detailItem.status] || 'default'" :text="detailItem.status" />
          </DescriptionsItem>
          <DescriptionsItem label="Location">{{ detailItem.location || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Due Date">{{ detailItem.due_date || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Budget">{{ formatCurrency(detailItem.budget_amount) }}</DescriptionsItem>
          <DescriptionsItem label="Selected">{{ formatCurrency(detailItem.selected_amount) }}</DescriptionsItem>
          <DescriptionsItem label="Impact" :span="2">
            <span :style="{ color: detailItem.budget_impact > 0 ? '#cf1322' : detailItem.budget_impact < 0 ? '#3f8600' : '' }">
              {{ formatCurrency(detailItem.budget_impact) }}
            </span>
          </DescriptionsItem>
          <DescriptionsItem label="Description" :span="2">{{ detailItem.description || '-' }}</DescriptionsItem>
        </Descriptions>

        <Divider>Options</Divider>

        <Row :gutter="[16, 16]">
          <Col :span="12" v-for="opt in (detailItem.options || [])" :key="opt.id">
            <Card
              size="small"
              :style="{
                border: opt.is_selected ? '2px solid #52c41a' : '1px solid #d9d9d9',
              }"
            >
              <template #title>
                <Space>
                  <span>{{ opt.name }}</span>
                  <Tag v-if="opt.is_recommended" color="blue"><StarOutlined /> Recommended</Tag>
                  <Tag v-if="opt.is_selected" color="green"><CheckOutlined /> Selected</Tag>
                </Space>
              </template>
              <p v-if="opt.description">{{ opt.description }}</p>
              <p><strong>Price:</strong> {{ formatCurrency(opt.price) }} <span v-if="opt.unit">/ {{ opt.unit }}</span></p>
              <div v-if="detailItem.status === 'pending' || detailItem.status === 'presented'" style="margin-top: 8px">
                <Popconfirm
                  :title="`Approve and select '${opt.name}'?`"
                  @confirm="handleApprove(detailItem.id, opt.id)"
                >
                  <Button size="small" type="primary"><CheckOutlined /> Select</Button>
                </Popconfirm>
              </div>
            </Card>
          </Col>
        </Row>

        <div v-if="detailItem.status === 'pending' || detailItem.status === 'presented'" style="margin-top: 24px; text-align: right">
          <Popconfirm title="Reject this selection?" @confirm="handleReject(detailItem.id)">
            <Button danger><CloseOutlined /> Reject Selection</Button>
          </Popconfirm>
        </div>
      </template>
    </Drawer>
  </Page>
</template>
