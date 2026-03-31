<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Checkbox,
  Col,
  Divider,
  Form,
  FormItem,
  Input,
  message,
  Row,
  Select,
  SelectOption,
  Space,
  Table,
  Tag,
  Textarea,
} from 'ant-design-vue';
import {
  ArrowLeftOutlined,
  PlayCircleOutlined,
  SaveOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMReportBuilder' });

const route = useRoute();
const router = useRouter();
const BASE_URL = '/agcm_reporting';

const loading = ref(false);
const saving = ref(false);
const previewLoading = ref(false);
const editingId = ref(null);

const form = ref({
  name: '',
  description: '',
  report_type: 'custom',
  data_source: 'projects',
  columns: '',
  filters: '',
  sort_by: '',
  sort_order: 'desc',
  group_by: '',
  is_shared: true,
});

const previewData = ref(null);

const reportTypes = [
  { value: 'financial', label: 'Financial' },
  { value: 'schedule', label: 'Schedule' },
  { value: 'safety', label: 'Safety' },
  { value: 'resource', label: 'Resource' },
  { value: 'custom', label: 'Custom' },
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

// Available columns based on data source
const availableColumns = ref([]);

const previewColumns = computed(() => {
  if (!previewData.value || !previewData.value.columns) return [];
  return previewData.value.columns.map(c => ({
    title: c.title || c.key,
    dataIndex: c.key,
    key: c.key,
    width: 150,
  }));
});

async function loadReport() {
  const id = route.query.id;
  if (!id) return;

  loading.value = true;
  try {
    const data = await requestClient.get(`${BASE_URL}/reports/${id}`);
    editingId.value = data.id;
    form.value = {
      name: data.name || '',
      description: data.description || '',
      report_type: data.report_type || 'custom',
      data_source: data.data_source || 'projects',
      columns: data.columns || '',
      filters: data.filters || '',
      sort_by: data.sort_by || '',
      sort_order: data.sort_order || 'desc',
      group_by: data.group_by || '',
      is_shared: data.is_shared ?? true,
    };
  } catch {
    message.error('Failed to load report');
  } finally {
    loading.value = false;
  }
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
      const result = await requestClient.post(`${BASE_URL}/reports`, form.value);
      editingId.value = result.id;
      message.success('Report created');
    }
  } catch {
    message.error('Failed to save report');
  } finally {
    saving.value = false;
  }
}

async function handlePreview() {
  if (!editingId.value) {
    // Save first then preview
    await handleSave();
    if (!editingId.value) return;
  }
  previewLoading.value = true;
  previewData.value = null;
  try {
    let filters = {};
    if (form.value.filters) {
      try {
        filters = JSON.parse(form.value.filters);
      } catch { /* ignore */ }
    }
    const data = await requestClient.post(`${BASE_URL}/reports/${editingId.value}/execute`, filters);
    previewData.value = data;
  } catch {
    message.error('Failed to execute report');
  } finally {
    previewLoading.value = false;
  }
}

function goBack() {
  router.push('/agcm/reporting/reports');
}

onMounted(() => {
  loadReport();
});
</script>

<template>
  <Page title="Report Builder" description="Configure and preview custom reports">
    <Card>
      <div style="margin-bottom: 16px; display: flex; gap: 12px; align-items: center">
        <Button @click="goBack"><ArrowLeftOutlined /> Back to Reports</Button>
        <div style="flex: 1" />
        <Button @click="handlePreview" :loading="previewLoading">
          <PlayCircleOutlined /> Preview
        </Button>
        <Button type="primary" @click="handleSave" :loading="saving">
          <SaveOutlined /> Save Report
        </Button>
      </div>

      <Form layout="vertical" :loading="loading">
        <Row :gutter="24">
          <Col :span="16">
            <!-- Configuration panel -->
            <Card title="Report Configuration" size="small">
              <Row :gutter="16">
                <Col :span="16">
                  <FormItem label="Report Name" required>
                    <Input v-model:value="form.name" placeholder="Enter report name" />
                  </FormItem>
                </Col>
                <Col :span="8">
                  <FormItem label="Type">
                    <Select v-model:value="form.report_type">
                      <SelectOption v-for="t in reportTypes" :key="t.value" :value="t.value">
                        {{ t.label }}
                      </SelectOption>
                    </Select>
                  </FormItem>
                </Col>
              </Row>

              <FormItem label="Description">
                <Textarea v-model:value="form.description" :rows="2" placeholder="Report description" />
              </FormItem>

              <Divider orientation="left">Data</Divider>

              <Row :gutter="16">
                <Col :span="8">
                  <FormItem label="Data Source" required>
                    <Select v-model:value="form.data_source">
                      <SelectOption v-for="ds in dataSources" :key="ds.value" :value="ds.value">
                        {{ ds.label }}
                      </SelectOption>
                    </Select>
                  </FormItem>
                </Col>
                <Col :span="8">
                  <FormItem label="Sort By">
                    <Input v-model:value="form.sort_by" placeholder="Column name" />
                  </FormItem>
                </Col>
                <Col :span="4">
                  <FormItem label="Order">
                    <Select v-model:value="form.sort_order">
                      <SelectOption value="asc">ASC</SelectOption>
                      <SelectOption value="desc">DESC</SelectOption>
                    </Select>
                  </FormItem>
                </Col>
                <Col :span="4">
                  <FormItem label="Group By">
                    <Input v-model:value="form.group_by" placeholder="Column" />
                  </FormItem>
                </Col>
              </Row>

              <Divider orientation="left">Columns & Filters</Divider>

              <FormItem label="Column Definitions (JSON array)">
                <Textarea
                  v-model:value="form.columns"
                  :rows="4"
                  placeholder='[{"key":"id","title":"ID"},{"key":"name","title":"Project Name"},{"key":"status","title":"Status"}]'
                />
              </FormItem>

              <FormItem label="Filters (JSON object)">
                <Textarea
                  v-model:value="form.filters"
                  :rows="3"
                  placeholder='{"project_id": 1, "date_from": "2026-01-01", "date_to": "2026-12-31"}'
                />
              </FormItem>

              <FormItem label="Shared">
                <Checkbox v-model:checked="form.is_shared">Allow other users to view this report</Checkbox>
              </FormItem>
            </Card>
          </Col>

          <Col :span="8">
            <!-- Info sidebar -->
            <Card title="Data Sources" size="small">
              <p style="color: #666; font-size: 12px; margin-bottom: 8px">
                Available data sources for querying:
              </p>
              <div v-for="ds in dataSources" :key="ds.value" style="margin-bottom: 4px">
                <Tag>{{ ds.value }}</Tag> {{ ds.label }}
              </div>
            </Card>

            <Card title="Filter Parameters" size="small" style="margin-top: 16px">
              <p style="color: #666; font-size: 12px">
                Available filter keys:
              </p>
              <ul style="font-size: 12px; padding-left: 16px">
                <li><code>project_id</code> - Filter by project</li>
                <li><code>date_from</code> - Start date</li>
                <li><code>date_to</code> - End date</li>
              </ul>
            </Card>
          </Col>
        </Row>
      </Form>

      <!-- Preview section -->
      <template v-if="previewData">
        <Divider>Preview Results ({{ previewData.total || 0 }} rows)</Divider>
        <Table
          :columns="previewColumns"
          :data-source="previewData.rows || []"
          row-key="id"
          size="small"
          :scroll="{ x: true }"
          :pagination="{ pageSize: 25 }"
        />
      </template>
    </Card>
  </Page>
</template>
