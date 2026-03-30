<script setup>
import { onMounted, ref, watch } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Col,
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
} from 'ant-design-vue';
import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMBudget' });

const BASE = '/agcm_finance';

const loading = ref(false);
const projectId = ref(null);
const projects = ref([]);
const costCodes = ref([]);
const summary = ref({ total_planned: 0, total_actual: 0, total_committed: 0, variance: 0, lines: [] });
const modalVisible = ref(false);
const editingId = ref(null);

const form = ref({
  description: '',
  cost_code_id: null,
  planned_amount: 0,
  actual_amount: 0,
  committed_amount: 0,
});

const columns = [
  { title: 'Description', dataIndex: 'description', key: 'description' },
  { title: 'Cost Code', dataIndex: 'cost_code_id', key: 'cost_code_id', width: 160 },
  { title: 'Planned', dataIndex: 'planned_amount', key: 'planned_amount', width: 140 },
  { title: 'Actual', dataIndex: 'actual_amount', key: 'actual_amount', width: 140 },
  { title: 'Committed', dataIndex: 'committed_amount', key: 'committed_amount', width: 140 },
  { title: 'Variance', key: 'variance', width: 140 },
  { title: 'Actions', key: 'actions', width: 120 },
];

function formatCurrency(val) {
  if (val == null) return '$0.00';
  return `$${Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function getVariance(record) {
  return (record.planned_amount || 0) - (record.actual_amount || 0) - (record.committed_amount || 0);
}

function getCostCodeLabel(id) {
  const cc = costCodes.value.find(c => c.id === id);
  return cc ? `${cc.code} - ${cc.name}` : '-';
}

async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = data.items || data.results || [];
  } catch { message.error('Failed to load projects'); }
}

async function fetchCostCodes() {
  if (!projectId.value) { costCodes.value = []; return; }
  try {
    const data = await requestClient.get(`${BASE}/cost-codes`, { params: { project_id: projectId.value } });
    costCodes.value = data || [];
  } catch { costCodes.value = []; }
}

async function fetchBudgetSummary() {
  if (!projectId.value) { summary.value = { total_planned: 0, total_actual: 0, total_committed: 0, variance: 0, lines: [] }; return; }
  loading.value = true;
  try {
    const data = await requestClient.get(`${BASE}/budget/summary`, { params: { project_id: projectId.value } });
    summary.value = data;
  } catch { message.error('Failed to load budget'); }
  finally { loading.value = false; }
}

function openModal(record) {
  if (record) {
    editingId.value = record.id;
    form.value = {
      description: record.description,
      cost_code_id: record.cost_code_id,
      planned_amount: record.planned_amount || 0,
      actual_amount: record.actual_amount || 0,
      committed_amount: record.committed_amount || 0,
    };
  } else {
    editingId.value = null;
    form.value = { description: '', cost_code_id: null, planned_amount: 0, actual_amount: 0, committed_amount: 0 };
  }
  modalVisible.value = true;
}

async function handleSave() {
  if (!form.value.description.trim()) { message.warning('Description is required'); return; }
  try {
    if (editingId.value) {
      await requestClient.put(`${BASE}/budgets/${editingId.value}`, form.value);
      message.success('Budget line updated');
    } else {
      await requestClient.post(`${BASE}/budgets`, { ...form.value, project_id: projectId.value });
      message.success('Budget line created');
    }
    modalVisible.value = false;
    fetchBudgetSummary();
  } catch { message.error('Failed to save budget line'); }
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/budgets/${record.id}`);
    message.success('Budget line deleted');
    fetchBudgetSummary();
  } catch { message.error('Failed to delete budget line'); }
}

watch(projectId, () => {
  fetchCostCodes();
  fetchBudgetSummary();
});

onMounted(async () => {
  await fetchProjects();
});
</script>

<template>
  <Page title="Budget" description="Project budget planning and tracking">
    <Card>
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <Select v-model:value="projectId" placeholder="Select Project" style="width: 280px" allow-clear show-search option-filter-prop="label">
          <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.sequence_name }} - {{ p.name }}</SelectOption>
        </Select>
        <div class="flex-1" />
        <Button @click="fetchBudgetSummary" :disabled="!projectId"><template #icon><ReloadOutlined /></template>Refresh</Button>
        <Button type="primary" :disabled="!projectId" @click="openModal(null)"><template #icon><PlusOutlined /></template>Add Budget Line</Button>
      </div>

      <Row :gutter="16" class="mb-4" v-if="projectId">
        <Col :span="6">
          <Card size="small">
            <Statistic title="Total Planned" :value="summary.total_planned" :precision="2" prefix="$" />
          </Card>
        </Col>
        <Col :span="6">
          <Card size="small">
            <Statistic title="Total Actual" :value="summary.total_actual" :precision="2" prefix="$" />
          </Card>
        </Col>
        <Col :span="6">
          <Card size="small">
            <Statistic title="Total Committed" :value="summary.total_committed" :precision="2" prefix="$" />
          </Card>
        </Col>
        <Col :span="6">
          <Card size="small">
            <Statistic title="Variance" :value="summary.variance" :precision="2" prefix="$" :value-style="{ color: summary.variance >= 0 ? '#3f8600' : '#cf1322' }" />
          </Card>
        </Col>
      </Row>

      <Table
        :columns="columns"
        :data-source="summary.lines"
        :loading="loading"
        row-key="id"
        size="middle"
        :pagination="false"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'cost_code_id'">
            {{ getCostCodeLabel(record.cost_code_id) }}
          </template>
          <template v-else-if="column.key === 'planned_amount'">
            {{ formatCurrency(record.planned_amount) }}
          </template>
          <template v-else-if="column.key === 'actual_amount'">
            {{ formatCurrency(record.actual_amount) }}
          </template>
          <template v-else-if="column.key === 'committed_amount'">
            {{ formatCurrency(record.committed_amount) }}
          </template>
          <template v-else-if="column.key === 'variance'">
            <span :style="{ color: getVariance(record) >= 0 ? '#3f8600' : '#cf1322' }">
              {{ formatCurrency(getVariance(record)) }}
            </span>
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="openModal(record)"><EditOutlined /></Button>
              <Popconfirm title="Delete this budget line?" @confirm="handleDelete(record)">
                <Button type="link" size="small" danger><DeleteOutlined /></Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <Modal
      v-model:open="modalVisible"
      :title="editingId ? 'Edit Budget Line' : 'New Budget Line'"
      @ok="handleSave"
      ok-text="Save"
    >
      <Form layout="vertical">
        <FormItem label="Description" required>
          <Input v-model:value="form.description" placeholder="Budget line description" />
        </FormItem>
        <FormItem label="Cost Code">
          <Select v-model:value="form.cost_code_id" placeholder="Select cost code" allow-clear style="width: 100%">
            <SelectOption v-for="c in costCodes" :key="c.id" :value="c.id">{{ c.code }} - {{ c.name }}</SelectOption>
          </Select>
        </FormItem>
        <Row :gutter="16">
          <Col :span="8">
            <FormItem label="Planned ($)">
              <InputNumber v-model:value="form.planned_amount" :min="0" :precision="2" style="width: 100%" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Actual ($)">
              <InputNumber v-model:value="form.actual_amount" :min="0" :precision="2" style="width: 100%" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Committed ($)">
              <InputNumber v-model:value="form.committed_amount" :min="0" :precision="2" style="width: 100%" />
            </FormItem>
          </Col>
        </Row>
      </Form>
    </Modal>
  </Page>
</template>
