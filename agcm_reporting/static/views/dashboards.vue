<script setup>
import { computed, onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Col,
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
  Statistic,
  Switch,
  Table,
  Tabs,
  TabPane,
  Tag,
  Textarea,
} from 'ant-design-vue';
import {
  AppstoreOutlined,
  BarChartOutlined,
  DashboardOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ProjectOutlined,
  ReloadOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMReportingDashboards' });

const BASE_URL = '/agcm_reporting';

const activeTab = ref('kpis');
const loading = ref(false);

// KPI data
const portfolioKpis = ref(null);
const kpiLoading = ref(false);
const projectKpis = ref(null);
const projectKpiLoading = ref(false);
const selectedProjectId = ref(null);
const projects = ref([]);

// Layout list
const layouts = ref([]);
const layoutPagination = ref({ current: 1, pageSize: 20, total: 0 });

// Layout modal
const layoutModalVisible = ref(false);
const layoutSaving = ref(false);
const editingLayoutId = ref(null);
const layoutForm = ref({ name: '', layout_type: 'executive', is_default: false });

// Widget modal
const widgetModalVisible = ref(false);
const widgetSaving = ref(false);
const editingWidgetId = ref(null);
const activeLayoutId = ref(null);
const widgetForm = ref({
  widget_type: 'kpi_card', title: '', config: '',
  data_source: 'portfolio_kpis',
  position_x: 0, position_y: 0, width: 6, height: 4, display_order: 0,
});

// Layout detail
const detailDrawerVisible = ref(false);
const detailLayout = ref(null);

const widgetTypes = [
  { value: 'kpi_card', label: 'KPI Card' },
  { value: 'bar_chart', label: 'Bar Chart' },
  { value: 'line_chart', label: 'Line Chart' },
  { value: 'pie_chart', label: 'Pie Chart' },
  { value: 'table', label: 'Table' },
  { value: 'progress_bar', label: 'Progress Bar' },
  { value: 'stat_group', label: 'Stat Group' },
];

const widgetDataSources = [
  { value: 'portfolio_kpis', label: 'Portfolio KPIs' },
  { value: 'project_kpis', label: 'Project KPIs' },
  { value: 'financial_summary', label: 'Financial Summary' },
  { value: 'projects', label: 'Projects' },
  { value: 'daily_logs', label: 'Daily Logs' },
  { value: 'manpower', label: 'Manpower' },
  { value: 'safety', label: 'Safety' },
];

const layoutColumns = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Type', dataIndex: 'layout_type', key: 'layout_type', width: 120 },
  { title: 'Default', key: 'is_default', width: 80 },
  { title: 'Widgets', key: 'widget_count', width: 80 },
  { title: 'Actions', key: 'actions', width: 180 },
];

const widgetColumns = [
  { title: 'Title', dataIndex: 'title', key: 'title' },
  { title: 'Type', key: 'widget_type', width: 120 },
  { title: 'Data Source', dataIndex: 'data_source', key: 'data_source', width: 140 },
  { title: 'Position', key: 'position', width: 100 },
  { title: 'Size', key: 'size', width: 100 },
  { title: 'Actions', key: 'actions', width: 120 },
];

async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = data.items || data.results || [];
  } catch { /* ignore */ }
}

async function fetchPortfolioKpis() {
  kpiLoading.value = true;
  try {
    portfolioKpis.value = await requestClient.get(`${BASE_URL}/kpis/portfolio`);
  } catch {
    message.error('Failed to load portfolio KPIs');
  } finally {
    kpiLoading.value = false;
  }
}

async function fetchProjectKpis() {
  if (!selectedProjectId.value) return;
  projectKpiLoading.value = true;
  try {
    projectKpis.value = await requestClient.get(`${BASE_URL}/kpis/project/${selectedProjectId.value}`);
  } catch {
    message.error('Failed to load project KPIs');
  } finally {
    projectKpiLoading.value = false;
  }
}

async function fetchLayouts() {
  loading.value = true;
  try {
    const data = await requestClient.get(`${BASE_URL}/dashboard-layouts`, {
      params: { page: layoutPagination.value.current, page_size: layoutPagination.value.pageSize },
    });
    layouts.value = data.items || [];
    layoutPagination.value.total = data.total || 0;
  } catch {
    message.error('Failed to load layouts');
  } finally {
    loading.value = false;
  }
}

// Layout CRUD
function openCreateLayout() {
  editingLayoutId.value = null;
  layoutForm.value = { name: '', layout_type: 'executive', is_default: false };
  layoutModalVisible.value = true;
}

function openEditLayout(record) {
  editingLayoutId.value = record.id;
  layoutForm.value = { name: record.name, layout_type: record.layout_type, is_default: record.is_default };
  layoutModalVisible.value = true;
}

async function handleSaveLayout() {
  if (!layoutForm.value.name) { message.warning('Name is required'); return; }
  layoutSaving.value = true;
  try {
    if (editingLayoutId.value) {
      await requestClient.put(`${BASE_URL}/dashboard-layouts/${editingLayoutId.value}`, layoutForm.value);
      message.success('Layout updated');
    } else {
      await requestClient.post(`${BASE_URL}/dashboard-layouts`, layoutForm.value);
      message.success('Layout created');
    }
    layoutModalVisible.value = false;
    fetchLayouts();
  } catch {
    message.error('Failed to save layout');
  } finally {
    layoutSaving.value = false;
  }
}

async function handleDeleteLayout(id) {
  try {
    await requestClient.delete(`${BASE_URL}/dashboard-layouts/${id}`);
    message.success('Layout deleted');
    fetchLayouts();
  } catch {
    message.error('Failed to delete layout');
  }
}

async function openLayoutDetail(record) {
  try {
    detailLayout.value = await requestClient.get(`${BASE_URL}/dashboard-layouts/${record.id}`);
    detailDrawerVisible.value = true;
  } catch {
    message.error('Failed to load layout');
  }
}

// Widget CRUD
function openCreateWidget(layoutId) {
  activeLayoutId.value = layoutId;
  editingWidgetId.value = null;
  widgetForm.value = {
    widget_type: 'kpi_card', title: '', config: '',
    data_source: 'portfolio_kpis',
    position_x: 0, position_y: 0, width: 6, height: 4, display_order: 0,
  };
  widgetModalVisible.value = true;
}

function openEditWidget(widget) {
  activeLayoutId.value = widget.layout_id;
  editingWidgetId.value = widget.id;
  widgetForm.value = { ...widget };
  widgetModalVisible.value = true;
}

async function handleSaveWidget() {
  if (!widgetForm.value.title || !widgetForm.value.data_source) {
    message.warning('Title and data source are required');
    return;
  }
  widgetSaving.value = true;
  try {
    if (editingWidgetId.value) {
      await requestClient.put(`${BASE_URL}/widgets/${editingWidgetId.value}`, widgetForm.value);
      message.success('Widget updated');
    } else {
      await requestClient.post(`${BASE_URL}/dashboard-layouts/${activeLayoutId.value}/widgets`, widgetForm.value);
      message.success('Widget added');
    }
    widgetModalVisible.value = false;
    if (detailLayout.value) {
      detailLayout.value = await requestClient.get(`${BASE_URL}/dashboard-layouts/${detailLayout.value.id}`);
    }
    fetchLayouts();
  } catch {
    message.error('Failed to save widget');
  } finally {
    widgetSaving.value = false;
  }
}

async function handleDeleteWidget(widgetId) {
  try {
    await requestClient.delete(`${BASE_URL}/widgets/${widgetId}`);
    message.success('Widget deleted');
    if (detailLayout.value) {
      detailLayout.value = await requestClient.get(`${BASE_URL}/dashboard-layouts/${detailLayout.value.id}`);
    }
    fetchLayouts();
  } catch {
    message.error('Failed to delete widget');
  }
}

onMounted(() => {
  fetchProjects();
  fetchPortfolioKpis();
  fetchLayouts();
});
</script>

<template>
  <Page title="Dashboards" description="Executive dashboards and KPI monitoring">
    <Tabs v-model:activeKey="activeTab">
      <!-- KPI Tab -->
      <TabPane key="kpis" tab="KPI Overview">
        <Card title="Portfolio KPIs" :loading="kpiLoading" style="margin-bottom: 16px">
          <template v-if="portfolioKpis">
            <Row :gutter="[16, 16]">
              <Col :xs="12" :sm="8" :md="6" :lg="4">
                <Statistic title="Total Projects" :value="portfolioKpis.total_projects">
                  <template #prefix><ProjectOutlined /></template>
                </Statistic>
              </Col>
              <Col :xs="12" :sm="8" :md="6" :lg="4">
                <Statistic title="Active Projects" :value="portfolioKpis.active_projects" value-style="color: #1890ff" />
              </Col>
              <Col :xs="12" :sm="8" :md="6" :lg="4">
                <Statistic title="Completed" :value="portfolioKpis.completed_projects" value-style="color: #52c41a" />
              </Col>
              <Col :xs="12" :sm="8" :md="6" :lg="4">
                <Statistic title="Daily Logs" :value="portfolioKpis.total_daily_logs" />
              </Col>
              <Col :xs="12" :sm="8" :md="6" :lg="4">
                <Statistic title="Accidents" :value="portfolioKpis.total_accidents" value-style="color: #cf1322" />
              </Col>
              <Col :xs="12" :sm="8" :md="6" :lg="4">
                <Statistic title="Completion Rate" :value="portfolioKpis.completion_rate" suffix="%" />
              </Col>
            </Row>
          </template>
          <template v-else>
            <div style="text-align: center; padding: 24px; color: #999">Loading KPIs...</div>
          </template>
        </Card>

        <Card title="Project KPIs">
          <div style="margin-bottom: 16px; display: flex; gap: 12px; align-items: center">
            <Select
              v-model:value="selectedProjectId"
              placeholder="Select a project"
              style="width: 300px"
              show-search
              option-filter-prop="children"
              @change="fetchProjectKpis"
            >
              <SelectOption v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</SelectOption>
            </Select>
            <Button @click="fetchProjectKpis" :disabled="!selectedProjectId"><ReloadOutlined /></Button>
          </div>

          <template v-if="projectKpis">
            <Row :gutter="[16, 16]">
              <Col :xs="12" :sm="8" :md="6">
                <Statistic title="Daily Logs" :value="projectKpis.total_daily_logs" />
              </Col>
              <Col :xs="12" :sm="8" :md="6">
                <Statistic title="Inspections" :value="projectKpis.total_inspections" />
              </Col>
              <Col :xs="12" :sm="8" :md="6">
                <Statistic title="Accidents" :value="projectKpis.total_accidents" value-style="color: #cf1322" />
              </Col>
              <Col :xs="12" :sm="8" :md="6">
                <Statistic title="Deficiencies" :value="projectKpis.total_deficiencies" value-style="color: #fa8c16" />
              </Col>
              <Col :xs="12" :sm="8" :md="6">
                <Statistic title="Delays" :value="projectKpis.total_delays" />
              </Col>
              <Col :xs="12" :sm="8" :md="6">
                <Statistic title="Safety Violations" :value="projectKpis.total_safety_violations" value-style="color: #cf1322" />
              </Col>
              <Col :xs="12" :sm="8" :md="6">
                <Statistic title="Safety Score" :value="projectKpis.safety_score" suffix="/100">
                  <template #prefix><SafetyCertificateOutlined /></template>
                </Statistic>
              </Col>
            </Row>
          </template>
          <template v-else>
            <div style="text-align: center; padding: 24px; color: #999">
              Select a project to view KPIs
            </div>
          </template>
        </Card>
      </TabPane>

      <!-- Layouts Tab -->
      <TabPane key="layouts" tab="Dashboard Layouts">
        <Card>
          <div style="margin-bottom: 16px; display: flex; justify-content: space-between">
            <Button @click="fetchLayouts"><ReloadOutlined /> Refresh</Button>
            <Button type="primary" @click="openCreateLayout"><PlusOutlined /> New Layout</Button>
          </div>

          <Table
            :columns="layoutColumns"
            :data-source="layouts"
            :loading="loading"
            :pagination="layoutPagination"
            row-key="id"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'is_default'">
                <Tag v-if="record.is_default" color="green">Yes</Tag>
                <span v-else>-</span>
              </template>
              <template v-else-if="column.key === 'widget_count'">
                {{ (record.widgets || []).length }}
              </template>
              <template v-else-if="column.key === 'actions'">
                <Space>
                  <Button size="small" @click="openLayoutDetail(record)"><AppstoreOutlined /></Button>
                  <Button size="small" @click="openEditLayout(record)"><EditOutlined /></Button>
                  <Popconfirm title="Delete this layout?" @confirm="handleDeleteLayout(record.id)">
                    <Button size="small" danger><DeleteOutlined /></Button>
                  </Popconfirm>
                </Space>
              </template>
            </template>
          </Table>
        </Card>
      </TabPane>
    </Tabs>

    <!-- Layout Modal -->
    <Modal
      v-model:open="layoutModalVisible"
      :title="editingLayoutId ? 'Edit Layout' : 'New Layout'"
      :confirm-loading="layoutSaving"
      @ok="handleSaveLayout"
    >
      <Form layout="vertical">
        <FormItem label="Name" required>
          <Input v-model:value="layoutForm.name" placeholder="Layout name" />
        </FormItem>
        <FormItem label="Type">
          <Select v-model:value="layoutForm.layout_type">
            <SelectOption value="executive">Executive</SelectOption>
            <SelectOption value="project">Project</SelectOption>
            <SelectOption value="financial">Financial</SelectOption>
          </Select>
        </FormItem>
        <FormItem label="Default">
          <Switch v-model:checked="layoutForm.is_default" />
        </FormItem>
      </Form>
    </Modal>

    <!-- Widget Modal -->
    <Modal
      v-model:open="widgetModalVisible"
      :title="editingWidgetId ? 'Edit Widget' : 'New Widget'"
      :confirm-loading="widgetSaving"
      @ok="handleSaveWidget"
      width="600px"
    >
      <Form layout="vertical">
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Title" required>
              <Input v-model:value="widgetForm.title" placeholder="Widget title" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Widget Type">
              <Select v-model:value="widgetForm.widget_type">
                <SelectOption v-for="wt in widgetTypes" :key="wt.value" :value="wt.value">{{ wt.label }}</SelectOption>
              </Select>
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Data Source" required>
          <Select v-model:value="widgetForm.data_source">
            <SelectOption v-for="ds in widgetDataSources" :key="ds.value" :value="ds.value">{{ ds.label }}</SelectOption>
          </Select>
        </FormItem>
        <Row :gutter="16">
          <Col :span="6">
            <FormItem label="X"><InputNumber v-model:value="widgetForm.position_x" :min="0" style="width: 100%" /></FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Y"><InputNumber v-model:value="widgetForm.position_y" :min="0" style="width: 100%" /></FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Width"><InputNumber v-model:value="widgetForm.width" :min="1" :max="24" style="width: 100%" /></FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Height"><InputNumber v-model:value="widgetForm.height" :min="1" style="width: 100%" /></FormItem>
          </Col>
        </Row>
        <FormItem label="Display Order">
          <InputNumber v-model:value="widgetForm.display_order" :min="0" style="width: 120px" />
        </FormItem>
        <FormItem label="Config (JSON)">
          <Textarea v-model:value="widgetForm.config" :rows="3" placeholder='{"color":"#1890ff","icon":"bar-chart"}' />
        </FormItem>
      </Form>
    </Modal>

    <!-- Layout Detail Drawer -->
    <Drawer
      v-model:open="detailDrawerVisible"
      :title="detailLayout ? detailLayout.name : 'Layout'"
      width="800"
      placement="right"
    >
      <template v-if="detailLayout">
        <div style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center">
          <Space>
            <Tag>{{ detailLayout.layout_type }}</Tag>
            <Tag v-if="detailLayout.is_default" color="green">Default</Tag>
          </Space>
          <Button type="primary" size="small" @click="openCreateWidget(detailLayout.id)">
            <PlusOutlined /> Add Widget
          </Button>
        </div>

        <Table
          :columns="widgetColumns"
          :data-source="detailLayout.widgets || []"
          row-key="id"
          size="small"
          :pagination="false"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'widget_type'">
              <Tag>{{ record.widget_type }}</Tag>
            </template>
            <template v-else-if="column.key === 'position'">
              ({{ record.position_x }}, {{ record.position_y }})
            </template>
            <template v-else-if="column.key === 'size'">
              {{ record.width }} x {{ record.height }}
            </template>
            <template v-else-if="column.key === 'actions'">
              <Space>
                <Button size="small" @click="openEditWidget(record)"><EditOutlined /></Button>
                <Popconfirm title="Delete widget?" @confirm="handleDeleteWidget(record.id)">
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
