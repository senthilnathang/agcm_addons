<script setup>
import { computed, onMounted, ref, watch } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Input,
  message,
  Modal,
  Popconfirm,
  Select,
  SelectOption,
  Space,
  Table,
  Form,
  FormItem,
} from 'ant-design-vue';
import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMCostCodes' });

const BASE = '/agcm_finance';

const loading = ref(false);
const projectId = ref(null);
const projects = ref([]);
const treeData = ref([]);
const modalVisible = ref(false);
const editingId = ref(null);

const form = ref({
  code: '',
  name: '',
  category: '',
  parent_id: null,
});

const flatCodes = ref([]);

const columns = [
  { title: 'Code', dataIndex: 'code', key: 'code', width: 150 },
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Category', dataIndex: 'category', key: 'category', width: 160 },
  { title: 'Actions', key: 'actions', width: 140 },
];

async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = data.items || data.results || [];
  } catch { message.error('Failed to load projects'); }
}

async function fetchCostCodes() {
  if (!projectId.value) { treeData.value = []; flatCodes.value = []; return; }
  loading.value = true;
  try {
    const tree = await requestClient.get(`${BASE}/cost-codes`, { params: { project_id: projectId.value, tree: true } });
    treeData.value = tree || [];

    const flat = await requestClient.get(`${BASE}/cost-codes`, { params: { project_id: projectId.value } });
    flatCodes.value = flat || [];
  } catch { message.error('Failed to load cost codes'); }
  finally { loading.value = false; }
}

function openModal(record, parentId) {
  if (record) {
    editingId.value = record.id;
    form.value = { code: record.code, name: record.name, category: record.category || '', parent_id: record.parent_id };
  } else {
    editingId.value = null;
    form.value = { code: '', name: '', category: '', parent_id: parentId || null };
  }
  modalVisible.value = true;
}

async function handleSave() {
  if (!form.value.code.trim() || !form.value.name.trim()) {
    message.warning('Code and Name are required');
    return;
  }
  try {
    const payload = { ...form.value, project_id: projectId.value };
    if (!payload.category) payload.category = null;
    if (!payload.parent_id) payload.parent_id = null;

    if (editingId.value) {
      const { project_id, ...updateData } = payload;
      await requestClient.put(`${BASE}/cost-codes/${editingId.value}`, updateData);
      message.success('Cost code updated');
    } else {
      await requestClient.post(`${BASE}/cost-codes`, payload);
      message.success('Cost code created');
    }
    modalVisible.value = false;
    fetchCostCodes();
  } catch { message.error('Failed to save cost code'); }
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/cost-codes/${record.id}`);
    message.success('Cost code deleted');
    fetchCostCodes();
  } catch { message.error('Failed to delete cost code'); }
}

watch(projectId, fetchCostCodes);

onMounted(async () => {
  await fetchProjects();
});
</script>

<template>
  <Page title="Cost Codes" description="Manage hierarchical cost code structure per project">
    <Card>
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <Select v-model:value="projectId" placeholder="Select Project" style="width: 280px" allow-clear show-search option-filter-prop="label">
          <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.sequence_name }} - {{ p.name }}</SelectOption>
        </Select>
        <div class="flex-1" />
        <Button @click="fetchCostCodes" :disabled="!projectId"><template #icon><ReloadOutlined /></template>Refresh</Button>
        <Button type="primary" :disabled="!projectId" @click="openModal(null, null)"><template #icon><PlusOutlined /></template>Add Cost Code</Button>
      </div>

      <Table
        :columns="columns"
        :data-source="treeData"
        :loading="loading"
        row-key="id"
        size="middle"
        :pagination="false"
        :default-expand-all-rows="true"
        children-column-name="children"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="openModal(null, record.id)" title="Add Child"><PlusOutlined /></Button>
              <Button type="link" size="small" @click="openModal(record)"><EditOutlined /></Button>
              <Popconfirm title="Delete this cost code?" @confirm="handleDelete(record)">
                <Button type="link" size="small" danger><DeleteOutlined /></Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <Modal
      v-model:open="modalVisible"
      :title="editingId ? 'Edit Cost Code' : 'New Cost Code'"
      @ok="handleSave"
      ok-text="Save"
    >
      <Form layout="vertical">
        <FormItem label="Code" required>
          <Input v-model:value="form.code" placeholder="e.g. 01-100" />
        </FormItem>
        <FormItem label="Name" required>
          <Input v-model:value="form.name" placeholder="Cost code name" />
        </FormItem>
        <FormItem label="Category">
          <Input v-model:value="form.category" placeholder="Optional category" />
        </FormItem>
        <FormItem label="Parent">
          <Select v-model:value="form.parent_id" placeholder="None (root)" allow-clear style="width: 100%">
            <SelectOption v-for="c in flatCodes" :key="c.id" :value="c.id">{{ c.code }} - {{ c.name }}</SelectOption>
          </Select>
        </FormItem>
      </Form>
    </Modal>
  </Page>
</template>
