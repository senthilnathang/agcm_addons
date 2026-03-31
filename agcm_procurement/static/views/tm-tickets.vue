<script setup>
import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Form,
  FormItem,
  Input,
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
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMTMTickets' });

const BASE = '/agcm_procurement';

const loading = ref(false);
const tickets = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const projectId = ref(null);
const modalVisible = ref(false);
const editingId = ref(null);
const form = ref({});

const statusColors = { draft: 'default', submitted: 'blue', approved: 'green', billed: 'cyan', void: 'red' };

const columns = [
  { title: 'Seq', dataIndex: 'sequence_name', width: 110 },
  { title: 'Date', dataIndex: 'date', width: 110 },
  { title: 'Vendor', dataIndex: 'vendor_name', width: 150 },
  { title: 'Status', dataIndex: 'status', width: 100 },
  { title: 'Total', dataIndex: 'total_amount', width: 120 },
  { title: 'Actions', key: 'actions', width: 140 },
];

async function loadData() {
  if (!projectId.value) return;
  loading.value = true;
  try {
    const res = await requestClient.get(`${BASE}/tm-tickets?project_id=${projectId.value}&page=${page.value}`);
    tickets.value = res.items || [];
    total.value = res.total || 0;
  } catch { message.error('Failed to load'); }
  finally { loading.value = false; }
}

function openCreate() {
  editingId.value = null;
  form.value = { project_id: projectId.value, date: new Date().toISOString().slice(0, 10), description: '', vendor_name: '', markup_pct: 0, notes: '', lines: [] };
  modalVisible.value = true;
}

function openEdit(r) { editingId.value = r.id; form.value = { ...r }; modalVisible.value = true; }

async function handleSave() {
  try {
    if (editingId.value) { await requestClient.put(`${BASE}/tm-tickets/${editingId.value}`, form.value); message.success('Updated'); }
    else { await requestClient.post(`${BASE}/tm-tickets`, form.value); message.success('Created'); }
    modalVisible.value = false;
    loadData();
  } catch { message.error('Save failed'); }
}

async function handleApprove(id) {
  try { await requestClient.post(`${BASE}/tm-tickets/${id}/approve`); message.success('Approved'); loadData(); }
  catch { message.error('Approve failed'); }
}

async function handleDelete(id) {
  try { await requestClient.delete(`${BASE}/tm-tickets/${id}`); message.success('Deleted'); loadData(); }
  catch { message.error('Delete failed'); }
}

onMounted(() => { projectId.value = new URLSearchParams(window.location.search).get('project_id') || 1; loadData(); });
</script>

<template>
  <Page title="T&M Tickets" description="Time and Material tracking">
    <Card>
      <Space style="margin-bottom: 16px; width: 100%; justify-content: space-between">
        <Button @click="loadData"><ReloadOutlined /> Refresh</Button>
        <Button type="primary" @click="openCreate"><PlusOutlined /> New Ticket</Button>
      </Space>
      <Spin :spinning="loading">
        <Table :data-source="tickets" :columns="columns" row-key="id" :pagination="{ current: page, pageSize, total, onChange: (p) => { page = p; loadData(); } }" size="small">
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'status'"><Tag :color="statusColors[record.status] || 'default'">{{ record.status }}</Tag></template>
            <template v-if="column.dataIndex === 'total_amount'">{{ (record.total_amount || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD' }) }}</template>
            <template v-if="column.key === 'actions'">
              <Space>
                <Button size="small" @click="openEdit(record)"><EditOutlined /></Button>
                <Button size="small" title="Approve" @click="handleApprove(record.id)" :disabled="record.status === 'approved'"><CheckOutlined /></Button>
                <Popconfirm title="Delete?" @confirm="handleDelete(record.id)"><Button size="small" danger><DeleteOutlined /></Button></Popconfirm>
              </Space>
            </template>
          </template>
        </Table>
      </Spin>
    </Card>

    <Modal v-model:open="modalVisible" :title="editingId ? 'Edit T&M Ticket' : 'New T&M Ticket'" @ok="handleSave" width="600px">
      <Form layout="vertical">
        <FormItem label="Date"><Input v-model:value="form.date" type="date" /></FormItem>
        <FormItem label="Vendor"><Input v-model:value="form.vendor_name" /></FormItem>
        <FormItem label="Ticket Number"><Input v-model:value="form.ticket_number" /></FormItem>
        <FormItem label="Markup %"><InputNumber v-model:value="form.markup_pct" :min="0" :max="100" style="width: 100%" /></FormItem>
        <FormItem label="Description"><Textarea v-model:value="form.description" :rows="3" /></FormItem>
        <FormItem label="Notes"><Textarea v-model:value="form.notes" :rows="2" /></FormItem>
      </Form>
    </Modal>
  </Page>
</template>
