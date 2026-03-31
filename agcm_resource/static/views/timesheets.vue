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
  Table,
  Tag,
  Textarea,
} from 'ant-design-vue';
import {
  CheckOutlined,
  CloseOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
  SendOutlined,
} from '@ant-design/icons-vue';

import {
  approveTimesheetApi,
  createTimesheetApi,
  deleteTimesheetApi,
  getTimesheetsApi,
  rejectTimesheetApi,
  submitTimesheetApi,
  updateTimesheetApi,
} from '#/api/agcm_resource';
import { getProjectsApi } from '#/api/agcm';
import { getWorkersApi } from '#/api/agcm_resource';

defineOptions({ name: 'AGCMTimesheets' });

const RangePicker = DatePicker.RangePicker;

const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  pageSizeOptions: ['10', '20', '50', '100'],
  showTotal: (total: number) => `Total ${total} timesheets`,
});

const loading = ref(false);
const items = ref<any[]>([]);
const searchText = ref('');
const statusFilter = ref<string | null>(null);
const workerFilter = ref<number | null>(null);
const projectFilter = ref<number | null>(null);
const dateRange = ref<any>(null);

const workers = ref<any[]>([]);
const projects = ref<any[]>([]);

const drawerVisible = ref(false);
const drawerTitle = ref('New Timesheet');
const editingId = ref<number | null>(null);
const saving = ref(false);

const form = reactive({
  worker_id: null as number | null,
  project_id: null as number | null,
  date: null as string | null,
  regular_hours: 0,
  overtime_hours: 0,
  double_time_hours: 0,
  task_description: '',
  location: '',
  notes: '',
});

const statusOptions = [
  { value: 'draft', label: 'Draft' },
  { value: 'submitted', label: 'Submitted' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
];

const statusColors: Record<string, string> = {
  draft: 'default',
  submitted: 'blue',
  approved: 'green',
  rejected: 'red',
};

const columns = computed(() => [
  { title: 'Seq #', dataIndex: 'sequence_name', key: 'sequence_name', width: 110 },
  { title: 'Date', dataIndex: 'date', key: 'date', width: 110 },
  { title: 'Worker', dataIndex: 'worker_name', key: 'worker_name', width: 160 },
  { title: 'Project', dataIndex: 'project_name', key: 'project_name', width: 180 },
  { title: 'Regular', dataIndex: 'regular_hours', key: 'regular_hours', width: 85 },
  { title: 'OT', dataIndex: 'overtime_hours', key: 'overtime_hours', width: 70 },
  { title: 'Total Hrs', dataIndex: 'total_hours', key: 'total_hours', width: 90 },
  { title: 'Total Cost', key: 'total_cost', width: 110 },
  { title: 'Status', key: 'status', width: 110 },
  { title: 'Actions', key: 'actions', width: 180, fixed: 'right' as const },
]);

async function loadWorkers() {
  try {
    const res = await getWorkersApi({ page_size: 200, status: 'active' });
    workers.value = (res.items || []).map((w: any) => ({ value: w.id, label: w.full_name || `${w.first_name} ${w.last_name}` }));
  } catch (e) {
    console.error('Failed to load workers:', e);
  }
}

async function loadProjects() {
  try {
    const res = await getProjectsApi({ page_size: 200 });
    projects.value = (res.items || []).map((p: any) => ({ value: p.id, label: p.name }));
  } catch (e) {
    console.error('Failed to load projects:', e);
  }
}

async function fetchData() {
  loading.value = true;
  try {
    const params: any = {
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
      search: searchText.value || undefined,
      status: statusFilter.value || undefined,
      worker_id: workerFilter.value || undefined,
      project_id: projectFilter.value || undefined,
    };
    if (dateRange.value && dateRange.value.length === 2) {
      params.date_from = dateRange.value[0];
      params.date_to = dateRange.value[1];
    }
    const response = await getTimesheetsApi(params);
    items.value = response.items || [];
    pagination.value.total = response.total || 0;
  } catch (error) {
    console.error('Failed to fetch timesheets:', error);
    message.error('Failed to load timesheets');
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
    worker_id: null,
    project_id: null,
    date: null,
    regular_hours: 0,
    overtime_hours: 0,
    double_time_hours: 0,
    task_description: '',
    location: '',
    notes: '',
  });
}

function handleCreate() {
  editingId.value = null;
  drawerTitle.value = 'New Timesheet';
  resetForm();
  drawerVisible.value = true;
}

function handleEdit(record: any) {
  editingId.value = record.id;
  drawerTitle.value = 'Edit Timesheet';
  Object.assign(form, {
    worker_id: record.worker_id,
    project_id: record.project_id,
    date: record.date || null,
    regular_hours: record.regular_hours || 0,
    overtime_hours: record.overtime_hours || 0,
    double_time_hours: record.double_time_hours || 0,
    task_description: record.task_description || '',
    location: record.location || '',
    notes: record.notes || '',
  });
  drawerVisible.value = true;
}

async function handleSave() {
  if (!form.worker_id || !form.project_id || !form.date) {
    message.warning('Worker, project, and date are required');
    return;
  }
  saving.value = true;
  try {
    const payload = { ...form };
    if (editingId.value) {
      await updateTimesheetApi(editingId.value, payload);
      message.success('Timesheet updated successfully');
    } else {
      await createTimesheetApi(payload);
      message.success('Timesheet created successfully');
    }
    drawerVisible.value = false;
    fetchData();
  } catch (error) {
    console.error('Failed to save timesheet:', error);
    message.error('Failed to save timesheet');
  } finally {
    saving.value = false;
  }
}

async function handleDelete(record: any) {
  try {
    await deleteTimesheetApi(record.id);
    message.success('Timesheet deleted successfully');
    fetchData();
  } catch (error) {
    console.error('Failed to delete:', error);
    message.error('Failed to delete timesheet');
  }
}

async function handleSubmit(record: any) {
  try {
    await submitTimesheetApi(record.id);
    message.success('Timesheet submitted for approval');
    fetchData();
  } catch (error) {
    console.error('Failed to submit:', error);
    message.error('Failed to submit timesheet');
  }
}

async function handleApprove(record: any) {
  try {
    await approveTimesheetApi(record.id);
    message.success('Timesheet approved');
    fetchData();
  } catch (error) {
    console.error('Failed to approve:', error);
    message.error('Failed to approve timesheet');
  }
}

async function handleReject(record: any) {
  try {
    await rejectTimesheetApi(record.id);
    message.success('Timesheet rejected');
    fetchData();
  } catch (error) {
    console.error('Failed to reject:', error);
    message.error('Failed to reject timesheet');
  }
}

function formatCurrency(val: number) {
  return `$${(val || 0).toFixed(2)}`;
}

onMounted(() => {
  fetchData();
  loadWorkers();
  loadProjects();
});
</script>

<template>
  <Page title="Timesheets" description="Manage worker daily time entries">
    <Card>
      <!-- Toolbar -->
      <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
        <Space wrap>
          <Input
            v-model:value="searchText"
            placeholder="Search..."
            style="width: 200px"
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
            style="width: 130px"
            @change="handleSearch"
          />
          <Select
            v-model:value="workerFilter"
            :options="workers"
            placeholder="All Workers"
            allow-clear
            show-search
            :filter-option="(input: string, option: any) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
            style="width: 180px"
            @change="handleSearch"
          />
          <Select
            v-model:value="projectFilter"
            :options="projects"
            placeholder="All Projects"
            allow-clear
            show-search
            :filter-option="(input: string, option: any) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
            style="width: 180px"
            @change="handleSearch"
          />
          <RangePicker
            v-model:value="dateRange"
            value-format="YYYY-MM-DD"
            @change="handleSearch"
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
            New Timesheet
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
        :scroll="{ x: 1300 }"
        @change="onTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'total_cost'">
            {{ formatCurrency(record.total_cost) }}
          </template>
          <template v-else-if="column.key === 'status'">
            <Tag :color="statusColors[record.status] || 'default'">
              {{ (record.status || '').replace(/^\w/, (c: string) => c.toUpperCase()) }}
            </Tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button
                v-if="record.status === 'draft'"
                type="link"
                size="small"
                @click="handleSubmit(record)"
                title="Submit"
              >
                <template #icon><SendOutlined /></template>
              </Button>
              <Button
                v-if="record.status === 'submitted'"
                type="link"
                size="small"
                style="color: #52c41a"
                @click="handleApprove(record)"
                title="Approve"
              >
                <template #icon><CheckOutlined /></template>
              </Button>
              <Button
                v-if="record.status === 'submitted'"
                type="link"
                size="small"
                danger
                @click="handleReject(record)"
                title="Reject"
              >
                <template #icon><CloseOutlined /></template>
              </Button>
              <Button
                v-if="record.status === 'draft' || record.status === 'rejected'"
                type="link"
                size="small"
                @click="handleEdit(record)"
              >
                <template #icon><EditOutlined /></template>
              </Button>
              <Popconfirm
                v-if="record.status !== 'approved'"
                title="Delete this timesheet?"
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
      width="520"
      :body-style="{ paddingBottom: '80px' }"
    >
      <Form layout="vertical">
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Worker" required>
              <Select
                v-model:value="form.worker_id"
                :options="workers"
                placeholder="Select worker"
                show-search
                :filter-option="(input: string, option: any) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
              />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Project" required>
              <Select
                v-model:value="form.project_id"
                :options="projects"
                placeholder="Select project"
                show-search
                :filter-option="(input: string, option: any) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
              />
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Date" required>
          <DatePicker v-model:value="form.date" style="width: 100%" value-format="YYYY-MM-DD" />
        </FormItem>
        <Row :gutter="16">
          <Col :span="8">
            <FormItem label="Regular Hours">
              <InputNumber v-model:value="form.regular_hours" :min="0" :max="24" :precision="2" style="width: 100%" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Overtime Hours">
              <InputNumber v-model:value="form.overtime_hours" :min="0" :max="24" :precision="2" style="width: 100%" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Double Time">
              <InputNumber v-model:value="form.double_time_hours" :min="0" :max="24" :precision="2" style="width: 100%" />
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Task Description">
          <Textarea v-model:value="form.task_description" :rows="3" placeholder="Describe the work performed" />
        </FormItem>
        <FormItem label="Location">
          <Input v-model:value="form.location" placeholder="Work location" />
        </FormItem>
        <FormItem label="Notes">
          <Textarea v-model:value="form.notes" :rows="2" placeholder="Additional notes" />
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
