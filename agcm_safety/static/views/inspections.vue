<script setup>
import { computed, onMounted, ref, watch } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Badge,
  Button,
  Card,
  Col,
  DatePicker,
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
  Table,
  Tag,
  Textarea,
} from 'ant-design-vue';
import {
  CheckOutlined,
  DeleteOutlined,
  EyeOutlined,
  PlayCircleOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMSafetyInspections' });

const BASE = '/agcm_safety';

const loading = ref(false);
const inspections = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const filterStatus = ref(null);
const projectId = ref(null);
const searchText = ref('');
const projects = ref([]);
const checklists = ref([]);

// Detail drawer
const drawerVisible = ref(false);
const drawerData = ref(null);

// Create modal
const modalVisible = ref(false);
const saving = ref(false);
const form = ref({
  project_id: null,
  template_id: null,
  inspector_name: '',
  inspector_company: '',
  inspection_type: '',
  scheduled_date: null,
  location: '',
  notes: '',
});

const statusOptions = [
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'passed', label: 'Passed' },
  { value: 'failed', label: 'Failed' },
  { value: 'conditional', label: 'Conditional' },
];

const statusColors = {
  scheduled: 'default',
  in_progress: 'processing',
  passed: 'success',
  failed: 'error',
  conditional: 'warning',
};

const resultColors = { pass: 'green', fail: 'red', na: 'default' };

const columns = [
  { title: 'Seq', dataIndex: 'sequence_name', key: 'sequence_name', width: 120 },
  { title: 'Inspector', dataIndex: 'inspector_name', key: 'inspector_name' },
  { title: 'Type', dataIndex: 'inspection_type', key: 'inspection_type', width: 130 },
  { title: 'Status', dataIndex: 'status', key: 'status', width: 130 },
  { title: 'Scheduled', dataIndex: 'scheduled_date', key: 'scheduled_date', width: 120 },
  { title: 'Result', dataIndex: 'overall_result', key: 'overall_result', width: 110 },
  { title: 'Actions', key: 'actions', width: 180 },
];

async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = data.items || data.results || [];
  } catch {}
}

async function fetchChecklists() {
  try {
    const data = await requestClient.get(`${BASE}/checklists`, { params: { page_size: 200, is_active: true } });
    checklists.value = data.items || [];
  } catch {}
}

async function fetchData() {
  loading.value = true;
  try {
    const params = { page: page.value, page_size: pageSize.value };
    if (projectId.value) params.project_id = projectId.value;
    if (filterStatus.value) params.status = filterStatus.value;
    if (searchText.value) params.search = searchText.value;

    const data = await requestClient.get(`${BASE}/inspections`, { params });
    inspections.value = data.items || [];
    total.value = data.total || 0;
  } catch { message.error('Failed to load inspections'); }
  finally { loading.value = false; }
}

async function openDetail(record) {
  try {
    drawerData.value = await requestClient.get(`${BASE}/inspections/${record.id}`);
    drawerVisible.value = true;
  } catch { message.error('Failed to load inspection details'); }
}

function openCreate() {
  form.value = {
    project_id: projectId.value,
    template_id: null,
    inspector_name: '',
    inspector_company: '',
    inspection_type: '',
    scheduled_date: null,
    location: '',
    notes: '',
  };
  modalVisible.value = true;
}

async function handleCreate() {
  if (!form.value.project_id) { message.warning('Project is required'); return; }
  if (!form.value.inspector_name.trim()) { message.warning('Inspector name is required'); return; }
  saving.value = true;
  try {
    const payload = { ...form.value };
    if (payload.scheduled_date) payload.scheduled_date = payload.scheduled_date.format ? payload.scheduled_date.format('YYYY-MM-DD') : payload.scheduled_date;
    await requestClient.post(`${BASE}/inspections`, payload);
    message.success('Inspection created');
    modalVisible.value = false;
    fetchData();
  } catch { message.error('Failed to create inspection'); }
  finally { saving.value = false; }
}

async function handleStart(record) {
  try {
    await requestClient.post(`${BASE}/inspections/${record.id}/start`);
    message.success('Inspection started');
    fetchData();
  } catch { message.error('Failed to start inspection'); }
}

async function handleComplete(record, result) {
  try {
    await requestClient.post(`${BASE}/inspections/${record.id}/complete`, { overall_result: result });
    message.success('Inspection completed');
    fetchData();
    if (drawerVisible.value) openDetail(record);
  } catch { message.error('Failed to complete inspection'); }
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/inspections/${record.id}`);
    message.success('Inspection deleted');
    fetchData();
  } catch { message.error('Failed to delete inspection'); }
}

watch(projectId, () => { page.value = 1; fetchData(); });

onMounted(async () => {
  await Promise.all([fetchProjects(), fetchChecklists()]);
  fetchData();
});
</script>

<template>
  <Page title="Inspections" description="Manage construction inspections and results">
    <Card>
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <Select v-model:value="projectId" placeholder="All Projects" style="width: 260px" allow-clear show-search option-filter-prop="label">
          <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.sequence_name }} - {{ p.name }}</SelectOption>
        </Select>
        <Input v-model:value="searchText" placeholder="Search..." style="width: 180px" allow-clear @press-enter="fetchData">
          <template #prefix><SearchOutlined /></template>
        </Input>
        <Select v-model:value="filterStatus" placeholder="Status" style="width: 140px" allow-clear @change="fetchData">
          <SelectOption v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</SelectOption>
        </Select>
        <div class="flex-1" />
        <Button @click="fetchData"><template #icon><ReloadOutlined /></template>Refresh</Button>
        <Button type="primary" @click="openCreate"><template #icon><PlusOutlined /></template>New Inspection</Button>
      </div>

      <Table
        :columns="columns"
        :data-source="inspections"
        :loading="loading"
        row-key="id"
        size="middle"
        :pagination="{ current: page, pageSize, total, showSizeChanger: true, showTotal: (t) => `${t} inspections` }"
        @change="(p) => { page = p.current; pageSize = p.pageSize; fetchData(); }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <Badge :status="statusColors[record.status] || 'default'" :text="(record.status || '').replace(/_/g, ' ')" />
          </template>
          <template v-else-if="column.key === 'overall_result'">
            <Tag v-if="record.overall_result" :color="resultColors[record.overall_result] || 'default'">{{ record.overall_result }}</Tag>
            <span v-else>-</span>
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="openDetail(record)"><EyeOutlined /></Button>
              <Button v-if="record.status === 'scheduled'" type="link" size="small" @click="handleStart(record)" title="Start"><PlayCircleOutlined /></Button>
              <Button v-if="record.status === 'in_progress'" type="link" size="small" style="color: green;" @click="handleComplete(record, 'pass')" title="Pass"><CheckOutlined /></Button>
              <Popconfirm title="Delete this inspection?" @confirm="handleDelete(record)">
                <Button type="link" size="small" danger><DeleteOutlined /></Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <!-- Create Modal -->
    <Modal v-model:open="modalVisible" title="New Inspection" :confirm-loading="saving" width="600px" @ok="handleCreate">
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
            <FormItem label="From Template">
              <Select v-model:value="form.template_id" placeholder="Optional" allow-clear>
                <SelectOption v-for="c in checklists" :key="c.id" :value="c.id">{{ c.name }}</SelectOption>
              </Select>
            </FormItem>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Inspector Name" required>
              <Input v-model:value="form.inspector_name" placeholder="Inspector name" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Inspector Company">
              <Input v-model:value="form.inspector_company" placeholder="Company" />
            </FormItem>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Type">
              <Input v-model:value="form.inspection_type" placeholder="e.g. foundation, framing" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Scheduled Date">
              <DatePicker v-model:value="form.scheduled_date" style="width: 100%;" />
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Location">
          <Input v-model:value="form.location" placeholder="Location" />
        </FormItem>
        <FormItem label="Notes">
          <Textarea v-model:value="form.notes" :rows="2" />
        </FormItem>
      </Form>
    </Modal>

    <!-- Detail Drawer -->
    <Drawer v-model:open="drawerVisible" :title="drawerData ? `Inspection ${drawerData.sequence_name || ''}` : 'Inspection'" width="600" placement="right">
      <template v-if="drawerData">
        <Descriptions :column="2" bordered size="small">
          <DescriptionsItem label="Inspector">{{ drawerData.inspector_name }}</DescriptionsItem>
          <DescriptionsItem label="Company">{{ drawerData.inspector_company || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Type">{{ drawerData.inspection_type || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Status">
            <Badge :status="statusColors[drawerData.status] || 'default'" :text="(drawerData.status || '').replace(/_/g, ' ')" />
          </DescriptionsItem>
          <DescriptionsItem label="Scheduled">{{ drawerData.scheduled_date || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Completed">{{ drawerData.completed_date || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Result" :span="2">
            <Tag v-if="drawerData.overall_result" :color="resultColors[drawerData.overall_result] || 'default'">{{ drawerData.overall_result }}</Tag>
            <span v-else>-</span>
          </DescriptionsItem>
          <DescriptionsItem label="Location" :span="2">{{ drawerData.location || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Notes" :span="2">{{ drawerData.notes || '-' }}</DescriptionsItem>
        </Descriptions>

        <div class="inspection-detail-items" v-if="drawerData.items && drawerData.items.length">
          <h4 style="margin: 16px 0 8px;">Checklist Items</h4>
          <div v-for="(item, idx) in drawerData.items" :key="item.id" class="inspection-item-row">
            <span style="min-width: 24px; color: #999;">{{ idx + 1 }}.</span>
            <span style="flex: 1;">{{ item.description }}</span>
            <Tag v-if="item.result" :color="resultColors[item.result] || 'default'">{{ item.result }}</Tag>
            <span v-else style="color: #ccc;">pending</span>
          </div>
        </div>

        <div v-if="drawerData.status === 'in_progress'" style="margin-top: 24px;">
          <Space>
            <Button type="primary" @click="handleComplete(drawerData, 'pass')">Mark Pass</Button>
            <Button danger @click="handleComplete(drawerData, 'fail')">Mark Fail</Button>
            <Button @click="handleComplete(drawerData, 'conditional')">Conditional</Button>
          </Space>
        </div>
      </template>
    </Drawer>
  </Page>
</template>
