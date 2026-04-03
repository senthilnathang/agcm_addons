<script setup>
import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Col,
  Descriptions,
  DescriptionsItem,
  Form,
  FormItem,
  Input,
  InputNumber,
  message,
  Modal,
  Row,
  Select,
  SelectOption,
  Table,
  Tag,
} from 'ant-design-vue';
import { EditOutlined, SaveOutlined } from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMModuleSettings' });

const BASE = '/agcm';
const loading = ref(false);
const modules = ref([]);
const editingModule = ref(null);
const modalVisible = ref(false);
const form = ref({});

const moduleLabels = {
  finance: 'Finance', procurement: 'Procurement', estimate: 'Estimating',
  schedule: 'Schedule', safety: 'Safety', resource: 'Resources',
  document: 'Documents', reporting: 'Reporting', portal: 'Portal',
  bim: 'BIM', general: 'General',
};

const columns = [
  { title: 'Module', dataIndex: 'module_name', key: 'module_name', width: 150 },
  { title: 'Retention %', dataIndex: 'default_retention_pct', key: 'retention', width: 120 },
  { title: 'Markup %', dataIndex: 'default_markup_pct', key: 'markup', width: 120 },
  { title: 'Tax Rate %', dataIndex: 'default_tax_rate_pct', key: 'tax', width: 120 },
  { title: 'Payment Terms', dataIndex: 'default_payment_terms', key: 'terms', width: 140 },
  { title: 'Currency', dataIndex: 'currency_code', key: 'currency', width: 100 },
  { title: 'Status', key: 'status', width: 100 },
  { title: 'Actions', key: 'actions', width: 80, fixed: 'right' },
];

async function fetchModules() {
  loading.value = true;
  try {
    modules.value = await requestClient.get(`${BASE}/settings/modules`);
  } catch { message.error('Failed to load settings'); }
  finally { loading.value = false; }
}

function openEdit(record) {
  editingModule.value = record.module_name;
  form.value = { ...record };
  modalVisible.value = true;
}

async function handleSave() {
  try {
    await requestClient.put(`${BASE}/settings/modules/${editingModule.value}`, form.value);
    message.success('Settings saved');
    modalVisible.value = false;
    fetchModules();
  } catch { message.error('Failed to save settings'); }
}

onMounted(fetchModules);
</script>

<template>
  <Page title="Module Settings" description="Configure defaults for each construction module">
    <Card>
      <Table
        :columns="columns"
        :dataSource="modules"
        :loading="loading"
        :pagination="false"
        row-key="module_name"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'module_name'">
            <strong>{{ moduleLabels[record.module_name] || record.module_name }}</strong>
          </template>
          <template v-if="column.key === 'status'">
            <Tag :color="record.is_default ? 'default' : 'green'">
              {{ record.is_default ? 'Default' : 'Configured' }}
            </Tag>
          </template>
          <template v-if="column.key === 'actions'">
            <Button type="link" size="small" @click="openEdit(record)"><EditOutlined /></Button>
          </template>
        </template>
      </Table>
    </Card>

    <Modal
      v-model:open="modalVisible"
      :title="`${moduleLabels[editingModule] || editingModule} Settings`"
      :width="640"
      @ok="handleSave"
    >
      <Form layout="vertical" style="margin-top: 16px;">
        <Row :gutter="16">
          <Col :span="8">
            <FormItem label="Retention %">
              <AInputNumber v-model:value="form.default_retention_pct" :min="0" :max="100" :step="0.5" style="width: 100%;" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Markup %">
              <AInputNumber v-model:value="form.default_markup_pct" :min="0" :max="1000" :step="1" style="width: 100%;" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Tax Rate %">
              <AInputNumber v-model:value="form.default_tax_rate_pct" :min="0" :max="100" :step="0.25" style="width: 100%;" />
            </FormItem>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="8">
            <FormItem label="Payment Terms">
              <AInput v-model:value="form.default_payment_terms" placeholder="Net 30" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Currency">
              <AInput v-model:value="form.currency_code" placeholder="USD" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Working Hours/Day">
              <AInputNumber v-model:value="form.working_hours_per_day" :min="1" :max="24" :step="0.5" style="width: 100%;" />
            </FormItem>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="8">
            <FormItem label="PO Prefix">
              <AInput v-model:value="form.po_number_prefix" placeholder="PO" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Invoice Prefix">
              <AInput v-model:value="form.invoice_number_prefix" placeholder="INV" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="OT Multiplier">
              <AInputNumber v-model:value="form.overtime_multiplier" :min="1" :max="5" :step="0.1" style="width: 100%;" />
            </FormItem>
          </Col>
        </Row>
      </Form>
    </Modal>
  </Page>
</template>
