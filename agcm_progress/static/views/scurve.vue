<script lang="ts" setup>
import { nextTick, onMounted, ref, watch } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Col,
  DatePicker,
  Form,
  FormItem,
  InputNumber,
  message,
  Popconfirm,
  Row,
  Select,
  Space,
  Table,
  Tag,
} from 'ant-design-vue';
import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
  SaveOutlined,
} from '@ant-design/icons-vue';

import * as echarts from 'echarts';

import { getProjectsApi } from '#/api/agcm';
import {
  createScurveDataApi,
  deleteScurveDataApi,
  getScurveDataApi,
  updateScurveDataApi,
} from '#/api/agcm_progress';

import dayjs from 'dayjs';

defineOptions({ name: 'AGCMProgressSCurve' });

const loading = ref(false);
const items = ref<any[]>([]);
const projects = ref<any[]>([]);
const selectedProjectId = ref<number | null>(null);

const chartRef = ref<HTMLDivElement | null>(null);
let chartInstance: any = null;

const editingId = ref<number | null>(null);
const showForm = ref(false);
const form = ref({
  date: null as any,
  planned_physical_pct: 0,
  actual_physical_pct: 0,
  revised_physical_pct: 0,
  planned_financial_pct: 0,
  actual_financial_pct: 0,
  manpower_progress_pct: 0,
  machinery_progress_pct: 0,
  schedule_days_ahead: 0,
});

function resetForm() {
  editingId.value = null;
  form.value = {
    date: null,
    planned_physical_pct: 0,
    actual_physical_pct: 0,
    revised_physical_pct: 0,
    planned_financial_pct: 0,
    actual_financial_pct: 0,
    manpower_progress_pct: 0,
    machinery_progress_pct: 0,
    schedule_days_ahead: 0,
  };
}

async function loadProjects() {
  try {
    const res = await getProjectsApi({ page: 1, page_size: 200 });
    projects.value = res.items || [];
    if (projects.value.length > 0 && !selectedProjectId.value) {
      selectedProjectId.value = projects.value[0].id;
    }
  } catch (e: any) {
    message.error('Failed to load projects');
  }
}

async function fetchData() {
  if (!selectedProjectId.value) return;
  loading.value = true;
  try {
    const res = await getScurveDataApi({ project_id: selectedProjectId.value });
    items.value = res.items || [];
    await nextTick();
    renderChart();
  } catch (e: any) {
    message.error('Failed to load S-curve data');
  } finally {
    loading.value = false;
  }
}

function renderChart() {
  if (!chartRef.value) return;

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value);
  }

  const dates = items.value.map(d => d.date);
  const plannedPhysical = items.value.map(d => d.planned_physical_pct);
  const actualPhysical = items.value.map(d => d.actual_physical_pct);
  const revisedPhysical = items.value.map(d => d.revised_physical_pct);
  const plannedFinancial = items.value.map(d => d.planned_financial_pct);
  const actualFinancial = items.value.map(d => d.actual_financial_pct);

  const option = {
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['Planned Physical', 'Actual Physical', 'Revised Physical', 'Planned Financial', 'Actual Financial'],
      bottom: 0,
    },
    grid: { left: 60, right: 30, top: 40, bottom: 60 },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { rotate: 45, fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      name: 'Progress (%)',
      min: 0,
      max: 100,
      axisLabel: { formatter: '{value}%' },
    },
    series: [
      { name: 'Planned Physical', type: 'line', data: plannedPhysical, smooth: true, lineStyle: { type: 'solid', width: 2 } },
      { name: 'Actual Physical', type: 'line', data: actualPhysical, smooth: true, lineStyle: { type: 'solid', width: 2 } },
      { name: 'Revised Physical', type: 'line', data: revisedPhysical, smooth: true, lineStyle: { type: 'dashed', width: 2 } },
      { name: 'Planned Financial', type: 'line', data: plannedFinancial, smooth: true, lineStyle: { type: 'solid', width: 1 } },
      { name: 'Actual Financial', type: 'line', data: actualFinancial, smooth: true, lineStyle: { type: 'dashed', width: 1 } },
    ],
  };

  chartInstance.setOption(option, true);
}

function onProjectChange(val: number) {
  selectedProjectId.value = val;
  fetchData();
}

function openNewForm() {
  resetForm();
  showForm.value = true;
}

function editRow(record: any) {
  editingId.value = record.id;
  form.value = {
    date: record.date ? dayjs(record.date) : null,
    planned_physical_pct: record.planned_physical_pct || 0,
    actual_physical_pct: record.actual_physical_pct || 0,
    revised_physical_pct: record.revised_physical_pct || 0,
    planned_financial_pct: record.planned_financial_pct || 0,
    actual_financial_pct: record.actual_financial_pct || 0,
    manpower_progress_pct: record.manpower_progress_pct || 0,
    machinery_progress_pct: record.machinery_progress_pct || 0,
    schedule_days_ahead: record.schedule_days_ahead || 0,
  };
  showForm.value = true;
}

async function handleSave() {
  if (!form.value.date) {
    message.warning('Date is required');
    return;
  }
  try {
    const payload: any = {
      date: dayjs(form.value.date).format('YYYY-MM-DD'),
      planned_physical_pct: form.value.planned_physical_pct,
      actual_physical_pct: form.value.actual_physical_pct,
      revised_physical_pct: form.value.revised_physical_pct,
      planned_financial_pct: form.value.planned_financial_pct,
      actual_financial_pct: form.value.actual_financial_pct,
      manpower_progress_pct: form.value.manpower_progress_pct,
      machinery_progress_pct: form.value.machinery_progress_pct,
      schedule_days_ahead: form.value.schedule_days_ahead,
    };

    if (editingId.value) {
      await updateScurveDataApi(editingId.value, payload);
      message.success('Data point updated');
    } else {
      payload.project_id = selectedProjectId.value;
      await createScurveDataApi(payload);
      message.success('Data point added');
    }
    showForm.value = false;
    resetForm();
    fetchData();
  } catch (e: any) {
    message.error(e?.message || 'Failed to save');
  }
}

async function handleDelete(id: number) {
  try {
    await deleteScurveDataApi(id);
    message.success('Data point deleted');
    fetchData();
  } catch (e: any) {
    message.error('Failed to delete');
  }
}

onMounted(async () => {
  await loadProjects();
  if (selectedProjectId.value) fetchData();

  window.addEventListener('resize', () => {
    chartInstance?.resize();
  });
});
</script>

<template>
  <Page title="S-Curve" description="Project progress visualization over time">
    <Card>
      <div style="display: flex; justify-content: space-between; margin-bottom: 16px; flex-wrap: wrap; gap: 8px;">
        <Space>
          <Select
            v-model:value="selectedProjectId"
            style="width: 300px"
            placeholder="Select Project"
            show-search
            option-filter-prop="label"
            :options="projects.map(p => ({ value: p.id, label: p.name }))"
            @change="onProjectChange"
          />
          <Button @click="fetchData">
            <template #icon><ReloadOutlined /></template>
          </Button>
        </Space>
        <Button type="primary" @click="openNewForm" :disabled="!selectedProjectId">
          <template #icon><PlusOutlined /></template>
          Add Data Point
        </Button>
      </div>

      <!-- Chart -->
      <div ref="chartRef" style="width: 100%; height: 400px; margin-bottom: 24px;"></div>

      <!-- Schedule indicator -->
      <div v-if="items.length > 0" style="margin-bottom: 16px; text-align: center;">
        <Tag
          :color="items[items.length - 1]?.schedule_days_ahead > 0 ? 'green' : items[items.length - 1]?.schedule_days_ahead < 0 ? 'red' : 'blue'"
          style="font-size: 14px; padding: 4px 12px;"
        >
          Schedule: {{ Math.abs(items[items.length - 1]?.schedule_days_ahead || 0) }} days
          {{ (items[items.length - 1]?.schedule_days_ahead || 0) >= 0 ? 'ahead' : 'behind' }}
        </Tag>
      </div>

      <!-- Data entry form -->
      <Card v-if="showForm" size="small" :title="editingId ? 'Edit Data Point' : 'Add Data Point'" style="margin-bottom: 16px;">
        <Form layout="vertical">
          <Row :gutter="12">
            <Col :span="6">
              <FormItem label="Date" required>
                <DatePicker v-model:value="form.date" style="width: 100%" />
              </FormItem>
            </Col>
            <Col :span="6">
              <FormItem label="Planned Physical %">
                <InputNumber v-model:value="form.planned_physical_pct" :min="0" :max="100" :precision="2" style="width: 100%" />
              </FormItem>
            </Col>
            <Col :span="6">
              <FormItem label="Actual Physical %">
                <InputNumber v-model:value="form.actual_physical_pct" :min="0" :max="100" :precision="2" style="width: 100%" />
              </FormItem>
            </Col>
            <Col :span="6">
              <FormItem label="Revised Physical %">
                <InputNumber v-model:value="form.revised_physical_pct" :min="0" :max="100" :precision="2" style="width: 100%" />
              </FormItem>
            </Col>
          </Row>
          <Row :gutter="12">
            <Col :span="6">
              <FormItem label="Planned Financial %">
                <InputNumber v-model:value="form.planned_financial_pct" :min="0" :max="100" :precision="2" style="width: 100%" />
              </FormItem>
            </Col>
            <Col :span="6">
              <FormItem label="Actual Financial %">
                <InputNumber v-model:value="form.actual_financial_pct" :min="0" :max="100" :precision="2" style="width: 100%" />
              </FormItem>
            </Col>
            <Col :span="6">
              <FormItem label="Manpower %">
                <InputNumber v-model:value="form.manpower_progress_pct" :min="0" :max="100" :precision="2" style="width: 100%" />
              </FormItem>
            </Col>
            <Col :span="6">
              <FormItem label="Schedule Days Ahead">
                <InputNumber v-model:value="form.schedule_days_ahead" style="width: 100%" />
              </FormItem>
            </Col>
          </Row>
          <Space>
            <Button type="primary" @click="handleSave">
              <template #icon><SaveOutlined /></template>
              {{ editingId ? 'Update' : 'Save' }}
            </Button>
            <Button @click="showForm = false; resetForm();">Cancel</Button>
          </Space>
        </Form>
      </Card>

      <!-- Data table -->
      <Table
        :data-source="items"
        :pagination="false"
        row-key="id"
        size="small"
        :scroll="{ x: 1200 }"
      >
        <Table.Column title="Date" data-index="date" key="date" :width="110" />
        <Table.Column title="Planned Phys %" data-index="planned_physical_pct" key="pp" :width="110" align="right" />
        <Table.Column title="Actual Phys %" data-index="actual_physical_pct" key="ap" :width="110" align="right" />
        <Table.Column title="Revised Phys %" data-index="revised_physical_pct" key="rp" :width="110" align="right" />
        <Table.Column title="Planned Fin %" data-index="planned_financial_pct" key="pf" :width="110" align="right" />
        <Table.Column title="Actual Fin %" data-index="actual_financial_pct" key="af" :width="100" align="right" />
        <Table.Column title="Days +/-" data-index="schedule_days_ahead" key="days" :width="80" align="right" />
        <Table.Column title="Actions" key="actions" :width="100" fixed="right">
          <template #default="{ record }">
            <Space>
              <Button size="small" @click="editRow(record)">
                <template #icon><EditOutlined /></template>
              </Button>
              <Popconfirm title="Delete?" @confirm="handleDelete(record.id)">
                <Button size="small" danger>
                  <template #icon><DeleteOutlined /></template>
                </Button>
              </Popconfirm>
            </Space>
          </template>
        </Table.Column>
      </Table>
    </Card>
  </Page>
</template>
