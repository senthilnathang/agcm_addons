<script lang="ts" setup>
import { computed, onMounted, reactive, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Col,
  DatePicker,
  Drawer,
  Form,
  FormItem,
  Input,
  InputNumber,
  message,
  Popconfirm,
  Row,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Textarea,
} from 'ant-design-vue';
import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
} from '@ant-design/icons-vue';

import {
  createWorkerApi,
  deleteWorkerApi,
  getWorkersApi,
  updateWorkerApi,
} from '#/api/agcm_resource';

defineOptions({ name: 'AGCMWorkers' });

const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  pageSizeOptions: ['10', '20', '50', '100'],
  showTotal: (total: number) => `Total ${total} workers`,
});

const loading = ref(false);
const items = ref<any[]>([]);
const searchText = ref('');
const statusFilter = ref<string | null>(null);
const tradeFilter = ref<string | null>(null);

const drawerVisible = ref(false);
const drawerTitle = ref('New Worker');
const editingId = ref<number | null>(null);
const saving = ref(false);

const form = reactive({
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  status: 'active',
  skill_level: null as string | null,
  trade: '',
  hourly_rate: 0,
  overtime_rate: 0,
  certifications: '',
  emergency_contact: '',
  emergency_phone: '',
  hire_date: null as string | null,
  is_subcontractor: false,
  notes: '',
});

const statusOptions = [
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
  { value: 'on_leave', label: 'On Leave' },
];

const skillOptions = [
  { value: 'apprentice', label: 'Apprentice' },
  { value: 'journeyman', label: 'Journeyman' },
  { value: 'master', label: 'Master' },
  { value: 'foreman', label: 'Foreman' },
  { value: 'superintendent', label: 'Superintendent' },
];

const statusColors: Record<string, string> = {
  active: 'green',
  inactive: 'default',
  on_leave: 'orange',
};

const columns = computed(() => [
  { title: 'Seq #', dataIndex: 'sequence_name', key: 'sequence_name', width: 120 },
  { title: 'Name', dataIndex: 'full_name', key: 'full_name', sorter: true },
  { title: 'Trade', dataIndex: 'trade', key: 'trade', width: 130 },
  { title: 'Skill Level', key: 'skill_level', width: 130 },
  { title: 'Status', key: 'status', width: 110 },
  { title: 'Hourly Rate', dataIndex: 'hourly_rate', key: 'hourly_rate', width: 120 },
  { title: 'Phone', dataIndex: 'phone', key: 'phone', width: 140 },
  { title: 'Subcontractor', key: 'is_subcontractor', width: 120 },
  { title: 'Actions', key: 'actions', width: 120, fixed: 'right' as const },
]);

async function fetchData() {
  loading.value = true;
  try {
    const params: any = {
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
      search: searchText.value || undefined,
      status: statusFilter.value || undefined,
      trade: tradeFilter.value || undefined,
    };
    const response = await getWorkersApi(params);
    items.value = response.items || [];
    pagination.value.total = response.total || 0;
  } catch (error) {
    console.error('Failed to fetch workers:', error);
    message.error('Failed to load workers');
  } finally {
    loading.value = false;
  }
}

function onTableChange(pag: any) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

function handleSearch() {
  pagination.value.current = 1;
  fetchData();
}

function resetForm() {
  Object.assign(form, {
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    status: 'active',
    skill_level: null,
    trade: '',
    hourly_rate: 0,
    overtime_rate: 0,
    certifications: '',
    emergency_contact: '',
    emergency_phone: '',
    hire_date: null,
    is_subcontractor: false,
    notes: '',
  });
}

function handleCreate() {
  editingId.value = null;
  drawerTitle.value = 'New Worker';
  resetForm();
  drawerVisible.value = true;
}

function handleEdit(record: any) {
  editingId.value = record.id;
  drawerTitle.value = 'Edit Worker';
  Object.assign(form, {
    first_name: record.first_name || '',
    last_name: record.last_name || '',
    email: record.email || '',
    phone: record.phone || '',
    status: record.status || 'active',
    skill_level: record.skill_level || null,
    trade: record.trade || '',
    hourly_rate: record.hourly_rate || 0,
    overtime_rate: record.overtime_rate || 0,
    certifications: record.certifications || '',
    emergency_contact: record.emergency_contact || '',
    emergency_phone: record.emergency_phone || '',
    hire_date: record.hire_date || null,
    is_subcontractor: record.is_subcontractor || false,
    notes: record.notes || '',
  });
  drawerVisible.value = true;
}

async function handleSave() {
  if (!form.first_name || !form.last_name) {
    message.warning('First name and last name are required');
    return;
  }
  saving.value = true;
  try {
    const payload = { ...form };
    if (editingId.value) {
      await updateWorkerApi(editingId.value, payload);
      message.success('Worker updated successfully');
    } else {
      await createWorkerApi(payload);
      message.success('Worker created successfully');
    }
    drawerVisible.value = false;
    fetchData();
  } catch (error) {
    console.error('Failed to save worker:', error);
    message.error('Failed to save worker');
  } finally {
    saving.value = false;
  }
}

async function handleDelete(record: any) {
  try {
    await deleteWorkerApi(record.id);
    message.success('Worker deleted successfully');
    fetchData();
  } catch (error) {
    console.error('Failed to delete:', error);
    message.error('Failed to delete worker');
  }
}

function formatSkillLevel(val: string) {
  if (!val) return '-';
  return val.charAt(0).toUpperCase() + val.slice(1);
}

onMounted(fetchData);
</script>

<template>
  <Page title="Workers" description="Manage construction workforce roster">
    <Card>
      <!-- Toolbar -->
      <div class="mb-4 flex items-center justify-between">
        <Space>
          <Input
            v-model:value="searchText"
            placeholder="Search workers..."
            style="width: 240px"
            @press-enter="handleSearch"
          >
            <template #prefix>
              <SearchOutlined />
            </template>
          </Input>
          <Select
            v-model:value="statusFilter"
            :options="statusOptions"
            placeholder="All Statuses"
            allow-clear
            style="width: 140px"
            @change="handleSearch"
          />
          <Input
            v-model:value="tradeFilter"
            placeholder="Filter by trade"
            style="width: 160px"
            allow-clear
            @press-enter="handleSearch"
          />
          <Button @click="handleSearch">Search</Button>
        </Space>
        <Space>
          <Button @click="fetchData">
            <template #icon><ReloadOutlined /></template>
            Refresh
          </Button>
          <Button type="primary" @click="handleCreate">
            <template #icon><PlusOutlined /></template>
            New Worker
          </Button>
        </Space>
      </div>

      <!-- Table -->
      <Table
        :columns="columns"
        :data-source="items"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        size="middle"
        :scroll="{ x: 1100 }"
        @change="onTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <Tag :color="statusColors[record.status] || 'default'">
              {{ record.status === 'on_leave' ? 'On Leave' : (record.status || '').replace(/^\w/, (c: string) => c.toUpperCase()) }}
            </Tag>
          </template>
          <template v-else-if="column.key === 'skill_level'">
            {{ formatSkillLevel(record.skill_level) }}
          </template>
          <template v-else-if="column.key === 'is_subcontractor'">
            <Tag v-if="record.is_subcontractor" color="purple">Sub</Tag>
            <span v-else>-</span>
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="handleEdit(record)">
                <template #icon><EditOutlined /></template>
              </Button>
              <Popconfirm
                title="Delete this worker?"
                ok-text="Yes"
                cancel-text="No"
                @confirm="handleDelete(record)"
              >
                <Button type="link" size="small" danger>
                  <template #icon><DeleteOutlined /></template>
                </Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <!-- Drawer for create/edit -->
    <Drawer
      v-model:open="drawerVisible"
      :title="drawerTitle"
      width="560"
      :body-style="{ paddingBottom: '80px' }"
    >
      <Form layout="vertical">
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="First Name" required>
              <Input v-model:value="form.first_name" placeholder="First name" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Last Name" required>
              <Input v-model:value="form.last_name" placeholder="Last name" />
            </FormItem>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Email">
              <Input v-model:value="form.email" placeholder="Email address" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Phone">
              <Input v-model:value="form.phone" placeholder="Phone number" />
            </FormItem>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Status">
              <Select v-model:value="form.status" :options="statusOptions" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Skill Level">
              <Select v-model:value="form.skill_level" :options="skillOptions" allow-clear placeholder="Select skill level" />
            </FormItem>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Trade">
              <Input v-model:value="form.trade" placeholder="e.g. Electrician, Plumber" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Hire Date">
              <DatePicker v-model:value="form.hire_date" style="width: 100%" value-format="YYYY-MM-DD" />
            </FormItem>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Hourly Rate ($)">
              <InputNumber v-model:value="form.hourly_rate" :min="0" :max="9999.99" :precision="2" style="width: 100%" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Overtime Rate ($)">
              <InputNumber v-model:value="form.overtime_rate" :min="0" :max="9999.99" :precision="2" style="width: 100%" />
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Subcontractor">
          <Switch v-model:checked="form.is_subcontractor" />
        </FormItem>
        <FormItem label="Certifications">
          <Textarea v-model:value="form.certifications" :rows="2" placeholder="JSON list of certifications" />
        </FormItem>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Emergency Contact">
              <Input v-model:value="form.emergency_contact" placeholder="Contact name" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Emergency Phone">
              <Input v-model:value="form.emergency_phone" placeholder="Contact phone" />
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Notes">
          <Textarea v-model:value="form.notes" :rows="3" placeholder="Additional notes" />
        </FormItem>
      </Form>
      <div class="drawer-footer">
        <Space>
          <Button @click="drawerVisible = false">Cancel</Button>
          <Button type="primary" :loading="saving" @click="handleSave">
            {{ editingId ? 'Update' : 'Create' }}
          </Button>
        </Space>
      </div>
    </Drawer>
  </Page>
</template>
