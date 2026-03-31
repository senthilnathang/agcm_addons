<script setup>
import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Form,
  FormItem,
  Input,
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
  SearchOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMDrawings' });

const BASE = '/agcm_document';

const loading = ref(false);
const drawings = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const projectId = ref(null);
const filterDiscipline = ref(undefined);
const searchText = ref('');
const modalVisible = ref(false);
const editingId = ref(null);
const form = ref({
  project_id: null,
  sheet_number: '',
  title: '',
  discipline: null,
  description: '',
  current_revision: '0',
  status: 'current',
  received_date: null,
});

const disciplines = [
  'architectural', 'structural', 'mechanical', 'electrical',
  'plumbing', 'civil', 'landscape',
];

const columns = [
  { title: 'Seq', dataIndex: 'sequence_name', width: 120 },
  { title: 'Sheet #', dataIndex: 'sheet_number', width: 100 },
  { title: 'Title', dataIndex: 'title', ellipsis: true },
  { title: 'Discipline', dataIndex: 'discipline', width: 120 },
  { title: 'Rev', dataIndex: 'current_revision', width: 60 },
  { title: 'Status', dataIndex: 'status', width: 100 },
  { title: 'Actions', key: 'actions', width: 120 },
];

async function loadDrawings() {
  if (!projectId.value) return;
  loading.value = true;
  try {
    const params = new URLSearchParams({ project_id: projectId.value, page: page.value, page_size: pageSize.value });
    if (filterDiscipline.value) params.append('discipline', filterDiscipline.value);
    if (searchText.value) params.append('search', searchText.value);
    const res = await requestClient.get(`${BASE}/drawings?${params}`);
    drawings.value = res.items || [];
    total.value = res.total || 0;
  } catch (e) {
    message.error('Failed to load drawings');
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  editingId.value = null;
  form.value = { project_id: projectId.value, sheet_number: '', title: '', discipline: null, description: '', current_revision: '0', status: 'current', received_date: null };
  modalVisible.value = true;
}

function openEdit(record) {
  editingId.value = record.id;
  form.value = { ...record };
  modalVisible.value = true;
}

async function handleSave() {
  try {
    if (editingId.value) {
      await requestClient.put(`${BASE}/drawings/${editingId.value}`, form.value);
      message.success('Drawing updated');
    } else {
      await requestClient.post(`${BASE}/drawings`, form.value);
      message.success('Drawing created');
    }
    modalVisible.value = false;
    loadDrawings();
  } catch (e) {
    message.error('Save failed');
  }
}

async function handleDelete(id) {
  try {
    await requestClient.delete(`${BASE}/drawings/${id}`);
    message.success('Deleted');
    loadDrawings();
  } catch (e) {
    message.error('Delete failed');
  }
}

onMounted(() => {
  const params = new URLSearchParams(window.location.search);
  projectId.value = params.get('project_id') || 1;
  loadDrawings();
});
</script>

<template>
  <Page title="Drawings" description="Manage construction drawings and plans">
    <Card>
      <Space style="margin-bottom: 16px; width: 100%; justify-content: space-between">
        <Space>
          <Input v-model:value="searchText" placeholder="Search..." :prefix="h(SearchOutlined)" allow-clear style="width: 200px" @press-enter="loadDrawings" />
          <Select v-model:value="filterDiscipline" placeholder="Discipline" allow-clear style="width: 150px" @change="loadDrawings">
            <SelectOption v-for="d in disciplines" :key="d" :value="d">{{ d }}</SelectOption>
          </Select>
          <Button @click="loadDrawings"><ReloadOutlined /></Button>
        </Space>
        <Button type="primary" @click="openCreate"><PlusOutlined /> New Drawing</Button>
      </Space>
      <Spin :spinning="loading">
        <Table :data-source="drawings" :columns="columns" row-key="id" :pagination="{ current: page, pageSize, total, onChange: (p) => { page = p; loadDrawings(); } }" size="small">
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'status'">
              <Tag :color="record.status === 'current' ? 'green' : record.status === 'superseded' ? 'orange' : 'red'">{{ record.status }}</Tag>
            </template>
            <template v-if="column.key === 'actions'">
              <Space>
                <Button size="small" @click="openEdit(record)"><EditOutlined /></Button>
                <Popconfirm title="Delete?" @confirm="handleDelete(record.id)">
                  <Button size="small" danger><DeleteOutlined /></Button>
                </Popconfirm>
              </Space>
            </template>
          </template>
        </Table>
      </Spin>
    </Card>

    <Modal v-model:open="modalVisible" :title="editingId ? 'Edit Drawing' : 'New Drawing'" @ok="handleSave" width="600px">
      <Form layout="vertical">
        <FormItem label="Sheet Number"><Input v-model:value="form.sheet_number" /></FormItem>
        <FormItem label="Title"><Input v-model:value="form.title" /></FormItem>
        <FormItem label="Discipline">
          <Select v-model:value="form.discipline" placeholder="Select discipline" allow-clear>
            <SelectOption v-for="d in disciplines" :key="d" :value="d">{{ d }}</SelectOption>
          </Select>
        </FormItem>
        <FormItem label="Description"><Textarea v-model:value="form.description" :rows="3" /></FormItem>
        <FormItem label="Current Revision"><Input v-model:value="form.current_revision" /></FormItem>
        <FormItem label="Status">
          <Select v-model:value="form.status">
            <SelectOption value="current">Current</SelectOption>
            <SelectOption value="superseded">Superseded</SelectOption>
            <SelectOption value="void">Void</SelectOption>
          </Select>
        </FormItem>
      </Form>
    </Modal>
  </Page>
</template>
