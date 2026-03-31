<script setup>
import { computed, onMounted, ref, watch } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Badge,
  Button,
  Card,
  Checkbox,
  Col,
  DatePicker,
  Descriptions,
  DescriptionsItem,
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
  DeleteOutlined,
  EyeOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMSafetyIncidents' });

const BASE = '/agcm_safety';

const loading = ref(false);
const incidents = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const filterSeverity = ref(null);
const filterStatus = ref(null);
const projectId = ref(null);
const searchText = ref('');
const projects = ref([]);

// Detail drawer
const drawerVisible = ref(false);
const drawerData = ref(null);

// Create modal
const modalVisible = ref(false);
const saving = ref(false);
const form = ref({
  project_id: null,
  title: '',
  description: '',
  severity: null,
  incident_date: null,
  incident_time: '',
  location: '',
  injured_party: '',
  injury_description: '',
  witness_names: '',
  osha_recordable: false,
  notes: '',
});

// Investigate modal
const investigateVisible = ref(false);
const investigateId = ref(null);
const investigateForm = ref({ root_cause: '', corrective_action: '' });
const investigateSaving = ref(false);

// Close modal
const closeVisible = ref(false);
const closeId = ref(null);
const closeForm = ref({ days_lost: 0 });
const closeSaving = ref(false);

const severityOptions = [
  { value: 'near_miss', label: 'Near Miss' },
  { value: 'first_aid', label: 'First Aid' },
  { value: 'medical', label: 'Medical' },
  { value: 'lost_time', label: 'Lost Time' },
  { value: 'fatality', label: 'Fatality' },
];

const statusOptions = [
  { value: 'reported', label: 'Reported' },
  { value: 'investigating', label: 'Investigating' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'closed', label: 'Closed' },
];

const severityColors = {
  near_miss: 'green',
  first_aid: 'blue',
  medical: 'orange',
  lost_time: 'red',
  fatality: '#a8071a',
};

const statusColors = {
  reported: 'warning',
  investigating: 'processing',
  resolved: 'success',
  closed: 'default',
};

const columns = [
  { title: 'Seq', dataIndex: 'sequence_name', key: 'sequence_name', width: 110 },
  { title: 'Title', dataIndex: 'title', key: 'title' },
  { title: 'Severity', dataIndex: 'severity', key: 'severity', width: 120 },
  { title: 'Status', dataIndex: 'status', key: 'status', width: 130 },
  { title: 'Date', dataIndex: 'incident_date', key: 'incident_date', width: 120 },
  { title: 'OSHA', dataIndex: 'osha_recordable', key: 'osha_recordable', width: 80 },
  { title: 'Actions', key: 'actions', width: 180 },
];

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
    if (filterSeverity.value) params.severity = filterSeverity.value;
    if (filterStatus.value) params.status = filterStatus.value;
    if (searchText.value) params.search = searchText.value;

    const data = await requestClient.get(`${BASE}/incidents`, { params });
    incidents.value = data.items || [];
    total.value = data.total || 0;
  } catch { message.error('Failed to load incidents'); }
  finally { loading.value = false; }
}

function openCreate() {
  form.value = {
    project_id: projectId.value,
    title: '',
    description: '',
    severity: null,
    incident_date: null,
    incident_time: '',
    location: '',
    injured_party: '',
    injury_description: '',
    witness_names: '',
    osha_recordable: false,
    notes: '',
  };
  modalVisible.value = true;
}

async function handleCreate() {
  if (!form.value.project_id) { message.warning('Project is required'); return; }
  if (!form.value.title.trim()) { message.warning('Title is required'); return; }
  if (!form.value.description.trim()) { message.warning('Description is required'); return; }
  if (!form.value.severity) { message.warning('Severity is required'); return; }
  if (!form.value.incident_date) { message.warning('Incident date is required'); return; }
  saving.value = true;
  try {
    const payload = { ...form.value };
    if (payload.incident_date && payload.incident_date.format) payload.incident_date = payload.incident_date.format('YYYY-MM-DD');
    await requestClient.post(`${BASE}/incidents`, payload);
    message.success('Incident reported');
    modalVisible.value = false;
    fetchData();
  } catch { message.error('Failed to create incident'); }
  finally { saving.value = false; }
}

async function openDetail(record) {
  try {
    drawerData.value = await requestClient.get(`${BASE}/incidents/${record.id}`);
    drawerVisible.value = true;
  } catch { message.error('Failed to load incident'); }
}

function openInvestigate(record) {
  investigateId.value = record.id;
  investigateForm.value = { root_cause: record.root_cause || '', corrective_action: record.corrective_action || '' };
  investigateVisible.value = true;
}

async function handleInvestigate() {
  if (!investigateForm.value.root_cause.trim()) { message.warning('Root cause is required'); return; }
  if (!investigateForm.value.corrective_action.trim()) { message.warning('Corrective action is required'); return; }
  investigateSaving.value = true;
  try {
    await requestClient.post(`${BASE}/incidents/${investigateId.value}/investigate`, investigateForm.value);
    message.success('Investigation recorded');
    investigateVisible.value = false;
    fetchData();
    if (drawerVisible.value && drawerData.value?.id === investigateId.value) {
      openDetail({ id: investigateId.value });
    }
  } catch { message.error('Failed to save investigation'); }
  finally { investigateSaving.value = false; }
}

function openClose(record) {
  closeId.value = record.id;
  closeForm.value = { days_lost: record.days_lost || 0 };
  closeVisible.value = true;
}

async function handleClose() {
  closeSaving.value = true;
  try {
    await requestClient.post(`${BASE}/incidents/${closeId.value}/close`, closeForm.value);
    message.success('Incident closed');
    closeVisible.value = false;
    fetchData();
    if (drawerVisible.value && drawerData.value?.id === closeId.value) {
      openDetail({ id: closeId.value });
    }
  } catch { message.error('Failed to close incident'); }
  finally { closeSaving.value = false; }
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/incidents/${record.id}`);
    message.success('Incident deleted');
    fetchData();
  } catch { message.error('Failed to delete incident'); }
}

function formatSeverity(val) {
  return (val || '').replace(/_/g, ' ');
}

watch(projectId, () => { page.value = 1; fetchData(); });

onMounted(async () => {
  await fetchProjects();
  fetchData();
});
</script>

<template>
  <Page title="Incident Reports" description="Report and track safety incidents">
    <Card>
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <Select v-model:value="projectId" placeholder="All Projects" style="width: 260px" allow-clear show-search option-filter-prop="label">
          <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.sequence_name }} - {{ p.name }}</SelectOption>
        </Select>
        <Input v-model:value="searchText" placeholder="Search..." style="width: 180px" allow-clear @press-enter="fetchData">
          <template #prefix><SearchOutlined /></template>
        </Input>
        <Select v-model:value="filterSeverity" placeholder="Severity" style="width: 130px" allow-clear @change="fetchData">
          <SelectOption v-for="s in severityOptions" :key="s.value" :value="s.value">{{ s.label }}</SelectOption>
        </Select>
        <Select v-model:value="filterStatus" placeholder="Status" style="width: 130px" allow-clear @change="fetchData">
          <SelectOption v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</SelectOption>
        </Select>
        <div class="flex-1" />
        <Button @click="fetchData"><template #icon><ReloadOutlined /></template>Refresh</Button>
        <Button type="primary" danger @click="openCreate"><template #icon><PlusOutlined /></template>Report Incident</Button>
      </div>

      <Table
        :columns="columns"
        :data-source="incidents"
        :loading="loading"
        row-key="id"
        size="middle"
        :pagination="{ current: page, pageSize, total, showSizeChanger: true, showTotal: (t) => `${t} incidents` }"
        @change="(p) => { page = p.current; pageSize = p.pageSize; fetchData(); }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'severity'">
            <Tag :color="severityColors[record.severity] || 'default'" class="severity-tag">{{ formatSeverity(record.severity) }}</Tag>
          </template>
          <template v-else-if="column.key === 'status'">
            <Badge :status="statusColors[record.status] || 'default'" :text="record.status" />
          </template>
          <template v-else-if="column.key === 'osha_recordable'">
            <Tag v-if="record.osha_recordable" color="red">Yes</Tag>
            <span v-else>No</span>
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="openDetail(record)"><EyeOutlined /></Button>
              <Button v-if="record.status === 'reported'" type="link" size="small" @click="openInvestigate(record)" title="Investigate">Inv</Button>
              <Button v-if="record.status === 'investigating' || record.status === 'resolved'" type="link" size="small" @click="openClose(record)" title="Close">Close</Button>
              <Popconfirm title="Delete this incident?" @confirm="handleDelete(record)">
                <Button type="link" size="small" danger><DeleteOutlined /></Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <!-- Create Modal -->
    <Modal v-model:open="modalVisible" title="Report Incident" :confirm-loading="saving" width="700px" @ok="handleCreate">
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
            <FormItem label="Severity" required>
              <Select v-model:value="form.severity" placeholder="Select severity">
                <SelectOption v-for="s in severityOptions" :key="s.value" :value="s.value">{{ s.label }}</SelectOption>
              </Select>
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Title" required>
          <Input v-model:value="form.title" placeholder="Brief incident title" />
        </FormItem>
        <FormItem label="Description" required>
          <Textarea v-model:value="form.description" :rows="3" placeholder="Detailed incident description" />
        </FormItem>
        <Row :gutter="16">
          <Col :span="8">
            <FormItem label="Date" required>
              <DatePicker v-model:value="form.incident_date" style="width: 100%;" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Time">
              <Input v-model:value="form.incident_time" placeholder="HH:MM" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Location">
              <Input v-model:value="form.location" placeholder="Location" />
            </FormItem>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Injured Party">
              <Input v-model:value="form.injured_party" placeholder="Name of injured person" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Witness Names">
              <Input v-model:value="form.witness_names" placeholder="Witness names" />
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Injury Description">
          <Textarea v-model:value="form.injury_description" :rows="2" />
        </FormItem>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="OSHA Recordable">
              <Checkbox v-model:checked="form.osha_recordable">Yes</Checkbox>
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Notes">
          <Textarea v-model:value="form.notes" :rows="2" />
        </FormItem>
      </Form>
    </Modal>

    <!-- Investigate Modal -->
    <Modal v-model:open="investigateVisible" title="Investigate Incident" :confirm-loading="investigateSaving" @ok="handleInvestigate">
      <Form layout="vertical" style="margin-top: 16px;">
        <FormItem label="Root Cause" required>
          <Textarea v-model:value="investigateForm.root_cause" :rows="3" placeholder="Describe the root cause" />
        </FormItem>
        <FormItem label="Corrective Action" required>
          <Textarea v-model:value="investigateForm.corrective_action" :rows="3" placeholder="Describe corrective actions taken" />
        </FormItem>
      </Form>
    </Modal>

    <!-- Close Modal -->
    <Modal v-model:open="closeVisible" title="Close Incident" :confirm-loading="closeSaving" @ok="handleClose">
      <Form layout="vertical" style="margin-top: 16px;">
        <FormItem label="Days Lost">
          <InputNumber v-model:value="closeForm.days_lost" :min="0" style="width: 100%;" />
        </FormItem>
      </Form>
    </Modal>

    <!-- Detail Drawer -->
    <Drawer v-model:open="drawerVisible" :title="drawerData ? `Incident ${drawerData.sequence_name || ''}` : 'Incident'" width="640" placement="right">
      <template v-if="drawerData">
        <Descriptions :column="2" bordered size="small">
          <DescriptionsItem label="Title" :span="2">{{ drawerData.title }}</DescriptionsItem>
          <DescriptionsItem label="Severity">
            <Tag :color="severityColors[drawerData.severity] || 'default'" class="severity-tag">{{ formatSeverity(drawerData.severity) }}</Tag>
          </DescriptionsItem>
          <DescriptionsItem label="Status">
            <Badge :status="statusColors[drawerData.status] || 'default'" :text="drawerData.status" />
          </DescriptionsItem>
          <DescriptionsItem label="Date">{{ drawerData.incident_date || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Time">{{ drawerData.incident_time || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Location" :span="2">{{ drawerData.location || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Description" :span="2">{{ drawerData.description }}</DescriptionsItem>
          <DescriptionsItem label="Injured Party">{{ drawerData.injured_party || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Witnesses">{{ drawerData.witness_names || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Injury Description" :span="2">{{ drawerData.injury_description || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Root Cause" :span="2">{{ drawerData.root_cause || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Corrective Action" :span="2">{{ drawerData.corrective_action || '-' }}</DescriptionsItem>
          <DescriptionsItem label="OSHA Recordable">
            <Tag v-if="drawerData.osha_recordable" color="red">Yes</Tag>
            <span v-else>No</span>
          </DescriptionsItem>
          <DescriptionsItem label="Days Lost">{{ drawerData.days_lost || 0 }}</DescriptionsItem>
          <DescriptionsItem label="Investigation Date">{{ drawerData.investigation_date || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Closed Date">{{ drawerData.closed_date || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Notes" :span="2">{{ drawerData.notes || '-' }}</DescriptionsItem>
        </Descriptions>

        <div style="margin-top: 24px;">
          <Space>
            <Button v-if="drawerData.status === 'reported'" type="primary" @click="openInvestigate(drawerData)">Investigate</Button>
            <Button v-if="drawerData.status === 'investigating' || drawerData.status === 'resolved'" @click="openClose(drawerData)">Close Incident</Button>
          </Space>
        </div>
      </template>
    </Drawer>
  </Page>
</template>
