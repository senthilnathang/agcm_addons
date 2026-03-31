<script setup>
import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  DatePicker,
  Form,
  FormItem,
  InputNumber,
  message,
  Modal,
  Popconfirm,
  Select,
  SelectOption,
  Space,
  Spin,
  Table,
  Tag,
  Textarea,
} from 'ant-design-vue';
import {
  CheckOutlined,
  DeleteOutlined,
  EyeOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMPaymentApplications' });

const BASE = '/agcm_procurement';

const loading = ref(false);
const items = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const projectId = ref(null);
const modalVisible = ref(false);
const form = ref({});

const statusColors = { draft: 'default', submitted: 'blue', certified: 'green', paid: 'cyan', rejected: 'red' };

const columns = [
  { title: 'Seq', dataIndex: 'sequence_name', width: 110 },
  { title: '#', dataIndex: 'application_number', width: 60 },
  { title: 'Period', key: 'period', width: 200 },
  { title: 'Status', dataIndex: 'status', width: 100 },
  { title: 'Current Billed', dataIndex: 'current_billed', width: 130 },
  { title: 'Net Due', dataIndex: 'net_payment_due', width: 130 },
  { title: 'Actions', key: 'actions', width: 140 },
];

async function loadData() {
  if (!projectId.value) return;
  loading.value = true;
  try {
    const res = await requestClient.get(`${BASE}/payment-applications?project_id=${projectId.value}&page=${page.value}`);
    items.value = res.items || [];
    total.value = res.total || 0;
  } catch { message.error('Failed to load'); }
  finally { loading.value = false; }
}

function openCreate() {
  form.value = { project_id: projectId.value, subcontract_id: null, application_number: 1, period_from: null, period_to: null, notes: '' };
  modalVisible.value = true;
}

async function handleSave() {
  try {
    await requestClient.post(`${BASE}/payment-applications`, form.value);
    message.success('Created');
    modalVisible.value = false;
    loadData();
  } catch { message.error('Save failed'); }
}

async function handleCertify(id) {
  try {
    await requestClient.post(`${BASE}/payment-applications/${id}/certify`);
    message.success('Certified');
    loadData();
  } catch { message.error('Certify failed'); }
}

async function handleDelete(id) {
  try { await requestClient.delete(`${BASE}/payment-applications/${id}`); message.success('Deleted'); loadData(); }
  catch { message.error('Delete failed'); }
}

onMounted(() => { projectId.value = new URLSearchParams(window.location.search).get('project_id') || 1; loadData(); });
</script>

<template>
  <Page title="Payment Applications" description="AIA G702/G703 progress billing">
    <Card>
      <Space style="margin-bottom: 16px; width: 100%; justify-content: space-between">
        <Button @click="loadData"><ReloadOutlined /> Refresh</Button>
        <Button type="primary" @click="openCreate"><PlusOutlined /> New Pay App</Button>
      </Space>
      <Spin :spinning="loading">
        <Table :data-source="items" :columns="columns" row-key="id" :pagination="{ current: page, pageSize, total, onChange: (p) => { page = p; loadData(); } }" size="small">
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'period'">{{ record.period_from }} to {{ record.period_to }}</template>
            <template v-if="column.dataIndex === 'status'"><Tag :color="statusColors[record.status] || 'default'">{{ record.status }}</Tag></template>
            <template v-if="column.dataIndex === 'current_billed'">{{ (record.current_billed || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD' }) }}</template>
            <template v-if="column.dataIndex === 'net_payment_due'">{{ (record.net_payment_due || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD' }) }}</template>
            <template v-if="column.key === 'actions'">
              <Space>
                <Button size="small" title="Certify" @click="handleCertify(record.id)" :disabled="record.status === 'certified'"><CheckOutlined /></Button>
                <Popconfirm title="Delete?" @confirm="handleDelete(record.id)"><Button size="small" danger><DeleteOutlined /></Button></Popconfirm>
              </Space>
            </template>
          </template>
        </Table>
      </Spin>
    </Card>

    <Modal v-model:open="modalVisible" title="New Payment Application" @ok="handleSave" width="500px">
      <Form layout="vertical">
        <FormItem label="Subcontract ID"><InputNumber v-model:value="form.subcontract_id" :min="1" style="width: 100%" /></FormItem>
        <FormItem label="Application #"><InputNumber v-model:value="form.application_number" :min="1" style="width: 100%" /></FormItem>
        <FormItem label="Period From"><DatePicker v-model:value="form.period_from" style="width: 100%" /></FormItem>
        <FormItem label="Period To"><DatePicker v-model:value="form.period_to" style="width: 100%" /></FormItem>
        <FormItem label="Notes"><Textarea v-model:value="form.notes" :rows="3" /></FormItem>
      </Form>
    </Modal>
  </Page>
</template>
