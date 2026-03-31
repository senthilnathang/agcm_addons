<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

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
  message,
  Modal,
  Popconfirm,
  Row,
  Select,
  SelectOption,
  Space,
  Switch,
  Table,
  Tag,
  Textarea,
} from 'ant-design-vue';
import {
  DeleteOutlined,
  DownloadOutlined,
  EditOutlined,
  EyeOutlined,
  PlayCircleOutlined,
  PlusOutlined,
  ReloadOutlined,
  ScheduleOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMReportingReports' });

const router = useRouter();
const BASE_URL = '/agcm_reporting';

const loading = ref(false);
const items = ref([]);
const pagination = ref({ current: 1, pageSize: 20, total: 0 });
const searchText = ref('');
const typeFilter = ref(null);

// Modal state
const modalVisible = ref(false);
const modalTitle = ref('');
const saving = ref(false);
const editingId = ref(null);
const form = ref({
  name: '', description: '', report_type: 'custom',
  data_source: 'projects', columns: '', filters: '',
  sort_by: '', sort_order: 'desc', group_by: '',
  is_shared: true,
});

// Execute drawer
const execDrawerVisible = ref(false);
const execLoading = ref(false);
const execResult = ref(null);
const execReportId = ref(null);

const reportTypes = [
  { value: 'financial', label: 'Financial', color: 'green' },
  { value: 'schedule', label: 'Schedule', color: 'blue' },
  { value: 'safety', label: 'Safety', color: 'red' },
  { value: 'resource', label: 'Resource', color: 'orange' },
  { value: 'custom', label: 'Custom', color: 'default' },
];

const dataSources = [
  { value: 'projects', label: 'Projects' },
  { value: 'daily_logs', label: 'Daily Logs' },
  { value: 'manpower', label: 'Manpower' },
  { value: 'inspections', label: 'Inspections' },
  { value: 'accidents', label: 'Accidents' },
  { value: 'visitors', label: 'Visitors' },
  { value: 'safety_violations', label: 'Safety Violations' },
  { value: 'delays', label: 'Delays' },
  { value: 'deficiencies', label: 'Deficiencies' },
];

const typeColorMap = Object.fromEntries(reportTypes.map(t => [t.value, t.color]));

const columns = computed(() => [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Type', key: 'report_type', width: 110 },
  { title: 'Data Source', dataIndex: 'data_source', key: 'data_source', width: 140 },
  { title: 'Shared', key: 'is_shared', width: 80 },
  { title: 'System', key: 'is_system', width: 80 },
  { title: 'Schedules', key: 'schedules_count', width: 100 },
  { title: 'Actions', key: 'actions', width: 220, fixed: 'right' },
]);

async function fetchData() {
  loading.value = true;
  try {
    const params = {
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
      search: searchText.value || undefined,
      report_type: typeFilter.value || undefined,
    };
    const data = await requestClient.get(`${BASE_URL}/reports`, { params });
    items.value = data.items || [];
    pagination.value.total = data.total || 0;
  } catch {
    message.error('Failed to load reports');
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
    name: '', description: '', report_type: 'custom',
    data_source: 'projects', columns: '', filters: '',
    sort_by: '', sort_order: 'desc', group_by: '',
    is_shared: true,
  };
  modalTitle.value = 'New Report';
  modalVisible.value = true;
}

function openEdit(record) {
  editingId.value = record.id;
  form.value = { ...record };
  modalTitle.value = 'Edit Report';
  modalVisible.value = true;
}

async function handleSave() {
  if (!form.value.name || !form.value.data_source) {
    message.warning('Name and data source are required');
    return;
  }
  saving.value = true;
  try {
    if (editingId.value) {
      await requestClient.put(`${BASE_URL}/reports/${editingId.value}`, form.value);
      message.success('Report updated');
    } else {
      await requestClient.post(`${BASE_URL}/reports`, form.value);
      message.success('Report created');
    }
    modalVisible.value = false;
    fetchData();
  } catch {
    message.error('Failed to save report');
  } finally {
    saving.value = false;
  }
}

async function handleDelete(id) {
  try {
    await requestClient.delete(`${BASE_URL}/reports/${id}`);
    message.success('Report deleted');
    fetchData();
  } catch {
    message.error('Failed to delete report');
  }
}

async function handleExecute(record) {
  execReportId.value = record.id;
  execLoading.value = true;
  execDrawerVisible.value = true;
  execResult.value = null;
  try {
    const data = await requestClient.post(`${BASE_URL}/reports/${record.id}/execute`, {});
    execResult.value = data;
  } catch {
    message.error('Failed to execute report');
  } finally {
    execLoading.value = false;
  }
}

function handleExport(record) {
  const token = localStorage.getItem('accessToken') || '';
  const params = new URLSearchParams({ format: 'csv' });
  if (token) params.append('token', token);
  window.open(`/api/v1${BASE_URL}/reports/${record.id}/export?${params.toString()}`, '_blank');
}

function openBuilder(record) {
  router.push({ path: '/agcm/reporting/report-builder', query: { id: record?.id } });
}

onMounted(() => {
  fetchData();
});
</script>

<template>
  <Page title="Reports" description="Custom report definitions and execution">
    <Card>
      <div style="margin-bottom: 16px; display: flex; gap: 12px; flex-wrap: wrap; align-items: center">
        <Input
          v-model:value="searchText"
          placeholder="Search reports..."
          style="width: 220px"
          allow-clear
          @press-enter="fetchData"
        />
        <Select
          v-model:value="typeFilter"
          placeholder="All Types"
          style="width: 150px"
          allow-clear
          @change="fetchData"
        >
          <SelectOption v-for="t in reportTypes" :key="t.value" :value="t.value">{{ t.label }}</SelectOption>
        </Select>
        <div style="flex: 1" />
        <Button @click="fetchData"><ReloadOutlined /> Refresh</Button>
        <Button type="primary" @click="openCreate"><PlusOutlined /> New Report</Button>
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
          <template v-if="column.key === 'report_type'">
            <Tag :color="typeColorMap[record.report_type] || 'default'">{{ record.report_type }}</Tag>
          </template>
          <template v-else-if="column.key === 'is_shared'">
            <Badge :status="record.is_shared ? 'success' : 'default'" :text="record.is_shared ? 'Yes' : 'No'" />
          </template>
          <template v-else-if="column.key === 'is_system'">
            <Tag v-if="record.is_system" color="purple">System</Tag>
            <span v-else>-</span>
          </template>
          <template v-else-if="column.key === 'schedules_count'">
            {{ (record.schedules || []).length }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button size="small" type="primary" ghost @click="handleExecute(record)">
                <PlayCircleOutlined /> Run
              </Button>
              <Button size="small" @click="handleExport(record)"><DownloadOutlined /></Button>
              <Button size="small" @click="openEdit(record)" :disabled="record.is_system"><EditOutlined /></Button>
              <Popconfirm title="Delete this report?" @confirm="handleDelete(record.id)">
                <Button size="small" danger :disabled="record.is_system"><DeleteOutlined /></Button>
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
      width="640px"
    >
      <Form layout="vertical">
        <Row :gutter="16">
          <Col :span="16">
            <FormItem label="Name" required>
              <Input v-model:value="form.name" placeholder="Report name" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Type">
              <Select v-model:value="form.report_type">
                <SelectOption v-for="t in reportTypes" :key="t.value" :value="t.value">{{ t.label }}</SelectOption>
              </Select>
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Description">
          <Textarea v-model:value="form.description" :rows="2" />
        </FormItem>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Data Source" required>
              <Select v-model:value="form.data_source">
                <SelectOption v-for="ds in dataSources" :key="ds.value" :value="ds.value">{{ ds.label }}</SelectOption>
              </Select>
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Sort By">
              <Input v-model:value="form.sort_by" placeholder="column name" />
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Sort Order">
              <Select v-model:value="form.sort_order">
                <SelectOption value="asc">Ascending</SelectOption>
                <SelectOption value="desc">Descending</SelectOption>
              </Select>
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Group By">
          <Input v-model:value="form.group_by" placeholder="Optional grouping column" />
        </FormItem>
        <FormItem label="Columns (JSON)">
          <Textarea v-model:value="form.columns" :rows="3" placeholder='[{"key":"name","title":"Name"},...]' />
        </FormItem>
        <FormItem label="Filters (JSON)">
          <Textarea v-model:value="form.filters" :rows="2" placeholder='{"project_id":1}' />
        </FormItem>
        <FormItem label="Shared">
          <Switch v-model:checked="form.is_shared" />
        </FormItem>
      </Form>
    </Modal>

    <!-- Execute Drawer -->
    <Drawer
      v-model:open="execDrawerVisible"
      title="Report Results"
      width="900"
      placement="right"
    >
      <div v-if="execLoading" style="text-align: center; padding: 48px">Loading...</div>
      <template v-else-if="execResult">
        <div style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center">
          <span><strong>{{ execResult.report_name }}</strong> - {{ execResult.total }} rows</span>
          <Button v-if="execReportId" size="small" @click="handleExport({ id: execReportId })">
            <DownloadOutlined /> Export CSV
          </Button>
        </div>
        <Table
          :columns="(execResult.columns || []).map(c => ({ title: c.title || c.key, dataIndex: c.key, key: c.key }))"
          :data-source="execResult.rows || []"
          row-key="id"
          size="small"
          :scroll="{ x: true }"
          :pagination="{ pageSize: 50 }"
        />
      </template>
      <div v-else style="text-align: center; padding: 48px; color: #999">No data</div>
    </Drawer>
  </Page>
</template>
