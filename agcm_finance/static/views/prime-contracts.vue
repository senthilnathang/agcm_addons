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
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMPrimeContracts' });

const BASE = '/agcm_finance';

const loading = ref(false);
const contracts = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const projectId = ref(null);
const modalVisible = ref(false);
const editingId = ref(null);
const form = ref({});

const statusColors = { draft: 'default', executed: 'blue', active: 'green', complete: 'orange', closed: 'red' };
const contractTypes = ['lump_sum', 'cost_plus', 'gmp', 'time_and_material', 'unit_price'];

const columns = [
  { title: 'Seq', dataIndex: 'sequence_name', width: 110 },
  { title: 'Title', dataIndex: 'title', ellipsis: true },
  { title: 'Owner', dataIndex: 'owner_name', width: 150 },
  { title: 'Status', dataIndex: 'status', width: 100 },
  { title: 'Original', dataIndex: 'original_value', width: 120 },
  { title: 'Revised', dataIndex: 'revised_value', width: 120 },
  { title: 'Actions', key: 'actions', width: 120 },
];

async function loadData() {
  if (!projectId.value) return;
  loading.value = true;
  try {
    const res = await requestClient.get(`${BASE}/prime-contracts?project_id=${projectId.value}&page=${page.value}&page_size=${pageSize.value}`);
    contracts.value = res.items || [];
    total.value = res.total || 0;
  } catch { message.error('Failed to load contracts'); }
  finally { loading.value = false; }
}

function openCreate() {
  editingId.value = null;
  form.value = { project_id: projectId.value, title: '', owner_name: '', status: 'draft', original_value: 0, approved_changes: 0, retainage_pct: 0, contract_type: 'lump_sum', notes: '' };
  modalVisible.value = true;
}

function openEdit(r) { editingId.value = r.id; form.value = { ...r }; modalVisible.value = true; }

async function handleSave() {
  try {
    if (editingId.value) { await requestClient.put(`${BASE}/prime-contracts/${editingId.value}`, form.value); message.success('Updated'); }
    else { await requestClient.post(`${BASE}/prime-contracts`, form.value); message.success('Created'); }
    modalVisible.value = false;
    loadData();
  } catch { message.error('Save failed'); }
}

async function handleDelete(id) {
  try { await requestClient.delete(`${BASE}/prime-contracts/${id}`); message.success('Deleted'); loadData(); }
  catch { message.error('Delete failed'); }
}

onMounted(() => { projectId.value = new URLSearchParams(window.location.search).get('project_id') || 1; loadData(); });
</script>

<template>
  <Page title="Prime Contracts" description="Manage owner-to-GC contracts">
    <Card>
      <Space style="margin-bottom: 16px; width: 100%; justify-content: space-between">
        <Button @click="loadData"><ReloadOutlined /> Refresh</Button>
        <Button type="primary" @click="openCreate"><PlusOutlined /> New Contract</Button>
      </Space>
      <Spin :spinning="loading">
        <Table :data-source="contracts" :columns="columns" row-key="id" :pagination="{ current: page, pageSize, total, onChange: (p) => { page = p; loadData(); } }" size="small">
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'status'"><Tag :color="statusColors[record.status] || 'default'">{{ record.status }}</Tag></template>
            <template v-if="column.dataIndex === 'original_value'">{{ (record.original_value || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD' }) }}</template>
            <template v-if="column.dataIndex === 'revised_value'">{{ (record.revised_value || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD' }) }}</template>
            <template v-if="column.key === 'actions'">
              <Space>
                <Button size="small" @click="openEdit(record)"><EditOutlined /></Button>
                <Popconfirm title="Delete?" @confirm="handleDelete(record.id)"><Button size="small" danger><DeleteOutlined /></Button></Popconfirm>
              </Space>
            </template>
          </template>
        </Table>
      </Spin>
    </Card>

    <Modal v-model:open="modalVisible" :title="editingId ? 'Edit Contract' : 'New Contract'" @ok="handleSave" width="600px">
      <Form layout="vertical">
        <FormItem label="Title"><Input v-model:value="form.title" /></FormItem>
        <FormItem label="Owner Name"><Input v-model:value="form.owner_name" /></FormItem>
        <FormItem label="Contract Number"><Input v-model:value="form.contract_number" /></FormItem>
        <FormItem label="Contract Type">
          <Select v-model:value="form.contract_type"><SelectOption v-for="t in contractTypes" :key="t" :value="t">{{ t.replace(/_/g, ' ') }}</SelectOption></Select>
        </FormItem>
        <FormItem label="Original Value"><InputNumber v-model:value="form.original_value" :min="0" style="width: 100%" :formatter="v => `$ ${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')" /></FormItem>
        <FormItem label="Approved Changes"><InputNumber v-model:value="form.approved_changes" style="width: 100%" /></FormItem>
        <FormItem label="Retainage %"><InputNumber v-model:value="form.retainage_pct" :min="0" :max="100" style="width: 100%" /></FormItem>
        <FormItem label="Notes"><Textarea v-model:value="form.notes" :rows="3" /></FormItem>
      </Form>
    </Modal>
  </Page>
</template>
