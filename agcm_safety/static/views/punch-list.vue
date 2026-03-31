<script setup>
import { computed, onMounted, ref, watch } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Badge,
  Button,
  Card,
  Col,
  DatePicker,
  Form,
  FormItem,
  Input,
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
  CheckCircleOutlined,
  CheckOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
  UserAddOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMSafetyPunchList' });

const BASE = '/agcm_safety';

const loading = ref(false);
const items = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const filterStatus = ref(null);
const filterPriority = ref(null);
const projectId = ref(null);
const searchText = ref('');
const projects = ref([]);

const modalVisible = ref(false);
const modalTitle = ref('');
const saving = ref(false);
const editingId = ref(null);

const form = ref({
  project_id: null,
  title: '',
  description: '',
  priority: 'medium',
  location: '',
  trade: '',
  assigned_to: null,
  due_date: null,
  photo_before_url: '',
  notes: '',
});

const statusOptions = [
  { value: 'open', label: 'Open' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'verified', label: 'Verified' },
];

const priorityOptions = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' },
];

const statusColors = {
  open: 'default',
  in_progress: 'processing',
  completed: 'success',
  verified: 'cyan',
};

const priorityColors = {
  low: 'default',
  medium: 'blue',
  high: 'orange',
  critical: 'red',
};

const columns = [
  { title: 'Seq', dataIndex: 'sequence_name', key: 'sequence_name', width: 110 },
  { title: 'Title', dataIndex: 'title', key: 'title' },
  { title: 'Priority', dataIndex: 'priority', key: 'priority', width: 100 },
  { title: 'Status', dataIndex: 'status', key: 'status', width: 120 },
  { title: 'Location', dataIndex: 'location', key: 'location', width: 140 },
  { title: 'Due Date', dataIndex: 'due_date', key: 'due_date', width: 120 },
  { title: 'Actions', key: 'actions', width: 200 },
];

const statusCounts = computed(() => {
  const counts = { open: 0, in_progress: 0, completed: 0, verified: 0 };
  items.value.forEach((i) => { if (counts[i.status] !== undefined) counts[i.status]++; });
  return counts;
});

async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = data.items || data.results || [];
  } catch {}
}

async function fetchData() {
  loading.value = true;
  try {
    const params = { page: page.value, page_size: pageSize.value };
    if (projectId.value) params.project_id = projectId.value;
    if (filterStatus.value) params.status = filterStatus.value;
    if (filterPriority.value) params.priority = filterPriority.value;
    if (searchText.value) params.search = searchText.value;

    const data = await requestClient.get(`${BASE}/punch-list`, { params });
    items.value = data.items || [];
    total.value = data.total || 0;
  } catch { message.error('Failed to load punch list'); }
  finally { loading.value = false; }
}

function resetForm() {
  form.value = {
    project_id: projectId.value,
    title: '',
    description: '',
    priority: 'medium',
    location: '',
    trade: '',
    assigned_to: null,
    due_date: null,
    photo_before_url: '',
    notes: '',
  };
}

function openCreate() {
  editingId.value = null;
  resetForm();
  modalTitle.value = 'New Punch List Item';
  modalVisible.value = true;
}

function openEdit(record) {
  editingId.value = record.id;
  modalTitle.value = 'Edit Punch List Item';
  form.value = {
    project_id: record.project_id,
    title: record.title || '',
    description: record.description || '',
    priority: record.priority || 'medium',
    location: record.location || '',
    trade: record.trade || '',
    assigned_to: record.assigned_to,
    due_date: record.due_date,
    photo_before_url: record.photo_before_url || '',
    notes: record.notes || '',
  };
  modalVisible.value = true;
}

async function handleSave() {
  if (!form.value.project_id) { message.warning('Project is required'); return; }
  if (!form.value.title.trim()) { message.warning('Title is required'); return; }
  saving.value = true;
  try {
    const payload = { ...form.value };
    if (payload.due_date && payload.due_date.format) payload.due_date = payload.due_date.format('YYYY-MM-DD');
    if (editingId.value) {
      await requestClient.put(`${BASE}/punch-list/${editingId.value}`, payload);
      message.success('Item updated');
    } else {
      await requestClient.post(`${BASE}/punch-list`, payload);
      message.success('Item created');
    }
    modalVisible.value = false;
    fetchData();
  } catch { message.error('Failed to save item'); }
  finally { saving.value = false; }
}

async function handleComplete(record) {
  try {
    await requestClient.post(`${BASE}/punch-list/${record.id}/complete`);
    message.success('Item completed');
    fetchData();
  } catch { message.error('Failed to complete item'); }
}

async function handleVerify(record) {
  try {
    await requestClient.post(`${BASE}/punch-list/${record.id}/verify`);
    message.success('Item verified');
    fetchData();
  } catch { message.error('Failed to verify item'); }
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/punch-list/${record.id}`);
    message.success('Item deleted');
    fetchData();
  } catch { message.error('Failed to delete item'); }
}

watch(projectId, () => { page.value = 1; fetchData(); });

onMounted(async () => {
  await fetchProjects();
  fetchData();
});
</script>

<template>
  <Page title="Punch List" description="Track and resolve construction deficiencies">
    <Card>
      <!-- Status summary -->
      <div class="punch-stats">
        <div v-for="s in statusOptions" :key="s.value" class="punch-stat-card">
          <div class="stat-value">{{ statusCounts[s.value] || 0 }}</div>
          <div class="stat-label">{{ s.label }}</div>
        </div>
      </div>

      <div class="mb-4 flex flex-wrap items-center gap-3">
        <Select v-model:value="projectId" placeholder="All Projects" style="width: 260px" allow-clear show-search option-filter-prop="label">
          <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.sequence_name }} - {{ p.name }}</SelectOption>
        </Select>
        <Input v-model:value="searchText" placeholder="Search..." style="width: 180px" allow-clear @press-enter="fetchData">
          <template #prefix><SearchOutlined /></template>
        </Input>
        <Select v-model:value="filterStatus" placeholder="Status" style="width: 130px" allow-clear @change="fetchData">
          <SelectOption v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</SelectOption>
        </Select>
        <Select v-model:value="filterPriority" placeholder="Priority" style="width: 130px" allow-clear @change="fetchData">
          <SelectOption v-for="p in priorityOptions" :key="p.value" :value="p.value">{{ p.label }}</SelectOption>
        </Select>
        <div class="flex-1" />
        <Button @click="fetchData"><template #icon><ReloadOutlined /></template>Refresh</Button>
        <Button type="primary" @click="openCreate"><template #icon><PlusOutlined /></template>New Item</Button>
      </div>

      <Table
        :columns="columns"
        :data-source="items"
        :loading="loading"
        row-key="id"
        size="middle"
        :pagination="{ current: page, pageSize, total, showSizeChanger: true, showTotal: (t) => `${t} items` }"
        @change="(p) => { page = p.current; pageSize = p.pageSize; fetchData(); }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'priority'">
            <Tag :color="priorityColors[record.priority] || 'default'">{{ record.priority }}</Tag>
          </template>
          <template v-else-if="column.key === 'status'">
            <Badge :status="statusColors[record.status] || 'default'" :text="(record.status || '').replace(/_/g, ' ')" />
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="openEdit(record)"><EditOutlined /></Button>
              <Button v-if="record.status === 'open' || record.status === 'in_progress'" type="link" size="small" style="color: green;" @click="handleComplete(record)" title="Complete"><CheckOutlined /></Button>
              <Button v-if="record.status === 'completed'" type="link" size="small" style="color: #13c2c2;" @click="handleVerify(record)" title="Verify"><CheckCircleOutlined /></Button>
              <Popconfirm title="Delete this item?" @confirm="handleDelete(record)">
                <Button type="link" size="small" danger><DeleteOutlined /></Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <Modal v-model:open="modalVisible" :title="modalTitle" :confirm-loading="saving" width="650px" @ok="handleSave">
      <Form layout="vertical" style="margin-top: 16px;">
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Project" required>
              <Select v-model:value="form.project_id" placeholder="Select project" show-search option-filter-prop="label">
                <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.name }}</SelectOption>
              </Select>
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Priority">
              <Select v-model:value="form.priority">
                <SelectOption v-for="p in priorityOptions" :key="p.value" :value="p.value">{{ p.label }}</SelectOption>
              </Select>
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Title" required>
          <Input v-model:value="form.title" placeholder="Punch list item title" />
        </FormItem>
        <FormItem label="Description">
          <Textarea v-model:value="form.description" :rows="2" />
        </FormItem>
        <Row :gutter="16">
          <Col :span="8">
            <FormItem label="Location">
              <Input v-model:value="form.location" placeholder="Location" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Trade">
              <Input v-model:value="form.trade" placeholder="Trade" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Due Date">
              <DatePicker v-model:value="form.due_date" style="width: 100%;" />
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Notes">
          <Textarea v-model:value="form.notes" :rows="2" />
        </FormItem>
      </Form>
    </Modal>
  </Page>
</template>
