<script setup>
import { computed, onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Checkbox,
  Col,
  Collapse,
  CollapsePanel,
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
  Switch,
  Table,
  Tag,
  Textarea,
} from 'ant-design-vue';
import {
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  MinusCircleOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMSafetyChecklists' });

const BASE = '/agcm_safety';

const loading = ref(false);
const templates = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const searchText = ref('');
const filterCategory = ref(null);

const modalVisible = ref(false);
const modalTitle = ref('');
const saving = ref(false);
const editingId = ref(null);

const form = ref({
  name: '',
  description: '',
  category: null,
  is_active: true,
  items: [],
});

const categoryOptions = [
  { value: 'structural', label: 'Structural' },
  { value: 'electrical', label: 'Electrical' },
  { value: 'plumbing', label: 'Plumbing' },
  { value: 'fire_safety', label: 'Fire Safety' },
  { value: 'hvac', label: 'HVAC' },
  { value: 'roofing', label: 'Roofing' },
  { value: 'general', label: 'General' },
];

const categoryColors = {
  structural: 'blue',
  electrical: 'orange',
  plumbing: 'cyan',
  fire_safety: 'red',
  hvac: 'green',
  roofing: 'purple',
  general: 'default',
};

const columns = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Category', dataIndex: 'category', key: 'category', width: 140 },
  { title: 'Active', dataIndex: 'is_active', key: 'is_active', width: 80 },
  { title: 'Created', dataIndex: 'created_at', key: 'created_at', width: 120 },
  { title: 'Actions', key: 'actions', width: 150 },
];

// Expandable detail
const expandedKeys = ref([]);
const expandedData = ref({});

async function fetchData() {
  loading.value = true;
  try {
    const params = { page: page.value, page_size: pageSize.value };
    if (searchText.value) params.search = searchText.value;
    if (filterCategory.value) params.category = filterCategory.value;

    const data = await requestClient.get(`${BASE}/checklists`, { params });
    templates.value = data.items || [];
    total.value = data.total || 0;
  } catch { message.error('Failed to load checklists'); }
  finally { loading.value = false; }
}

async function loadDetail(templateId) {
  try {
    const data = await requestClient.get(`${BASE}/checklists/${templateId}`);
    expandedData.value[templateId] = data.items || [];
  } catch { message.error('Failed to load template details'); }
}

function onExpand(expanded, record) {
  if (expanded) {
    expandedKeys.value = [record.id];
    loadDetail(record.id);
  } else {
    expandedKeys.value = [];
  }
}

function resetForm() {
  form.value = { name: '', description: '', category: null, is_active: true, items: [] };
}

function openCreate() {
  editingId.value = null;
  resetForm();
  modalTitle.value = 'New Checklist Template';
  modalVisible.value = true;
}

async function openEdit(record) {
  editingId.value = record.id;
  modalTitle.value = 'Edit Checklist Template';
  try {
    const data = await requestClient.get(`${BASE}/checklists/${record.id}`);
    form.value = {
      name: data.name || '',
      description: data.description || '',
      category: data.category || null,
      is_active: data.is_active !== false,
      items: (data.items || []).map((i) => ({
        description: i.description,
        required: i.required !== false,
        display_order: i.display_order || 0,
      })),
    };
    modalVisible.value = true;
  } catch { message.error('Failed to load template'); }
}

function addItem() {
  form.value.items.push({ description: '', required: true, display_order: form.value.items.length });
}

function removeItem(idx) {
  form.value.items.splice(idx, 1);
}

async function handleSave() {
  if (!form.value.name.trim()) { message.warning('Name is required'); return; }
  saving.value = true;
  try {
    const payload = { ...form.value };
    if (editingId.value) {
      await requestClient.put(`${BASE}/checklists/${editingId.value}`, payload);
      message.success('Template updated');
    } else {
      await requestClient.post(`${BASE}/checklists`, payload);
      message.success('Template created');
    }
    modalVisible.value = false;
    fetchData();
  } catch { message.error('Failed to save template'); }
  finally { saving.value = false; }
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/checklists/${record.id}`);
    message.success('Template deleted');
    fetchData();
  } catch { message.error('Failed to delete template'); }
}

function formatDate(d) {
  if (!d) return '-';
  return new Date(d).toLocaleDateString();
}

onMounted(fetchData);
</script>

<template>
  <Page title="Checklist Templates" description="Manage reusable inspection checklist templates">
    <Card>
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <Input v-model:value="searchText" placeholder="Search..." style="width: 200px" allow-clear @press-enter="fetchData">
          <template #prefix><ReloadOutlined /></template>
        </Input>
        <Select v-model:value="filterCategory" placeholder="Category" style="width: 150px" allow-clear @change="fetchData">
          <SelectOption v-for="c in categoryOptions" :key="c.value" :value="c.value">{{ c.label }}</SelectOption>
        </Select>
        <div class="flex-1" />
        <Button @click="fetchData"><template #icon><ReloadOutlined /></template>Refresh</Button>
        <Button type="primary" @click="openCreate"><template #icon><PlusOutlined /></template>New Template</Button>
      </div>

      <Table
        :columns="columns"
        :data-source="templates"
        :loading="loading"
        row-key="id"
        size="middle"
        :expanded-row-keys="expandedKeys"
        @expand="onExpand"
        :pagination="{ current: page, pageSize, total, showSizeChanger: true, showTotal: (t) => `${t} templates` }"
        @change="(p) => { page = p.current; pageSize = p.pageSize; fetchData(); }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'category'">
            <Tag :color="categoryColors[record.category] || 'default'">{{ record.category || 'N/A' }}</Tag>
          </template>
          <template v-else-if="column.key === 'is_active'">
            <Tag :color="record.is_active ? 'green' : 'default'">{{ record.is_active ? 'Yes' : 'No' }}</Tag>
          </template>
          <template v-else-if="column.key === 'created_at'">
            {{ formatDate(record.created_at) }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="openEdit(record)"><EditOutlined /></Button>
              <Popconfirm title="Delete this template?" @confirm="handleDelete(record)">
                <Button type="link" size="small" danger><DeleteOutlined /></Button>
              </Popconfirm>
            </Space>
          </template>
        </template>

        <template #expandedRowRender="{ record }">
          <div class="checklist-items-list" style="padding: 8px 16px;">
            <div v-if="!expandedData[record.id] || expandedData[record.id].length === 0" style="color: #999;">No items</div>
            <div v-for="(item, idx) in (expandedData[record.id] || [])" :key="item.id" class="checklist-item-row">
              <span class="item-order">{{ idx + 1 }}.</span>
              <span>{{ item.description }}</span>
              <Tag v-if="item.required" color="red" size="small">Required</Tag>
            </div>
          </div>
        </template>
      </Table>
    </Card>

    <Modal
      v-model:open="modalVisible"
      :title="modalTitle"
      :confirm-loading="saving"
      width="700px"
      @ok="handleSave"
    >
      <Form layout="vertical" style="margin-top: 16px;">
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Name" required>
              <Input v-model:value="form.name" placeholder="Template name" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Category">
              <Select v-model:value="form.category" placeholder="Select" allow-clear>
                <SelectOption v-for="c in categoryOptions" :key="c.value" :value="c.value">{{ c.label }}</SelectOption>
              </Select>
            </FormItem>
          </Col>
          <Col :span="4">
            <FormItem label="Active">
              <Switch v-model:checked="form.is_active" />
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Description">
          <Textarea v-model:value="form.description" :rows="2" placeholder="Optional description" />
        </FormItem>

        <div class="mb-2 flex items-center justify-between">
          <strong>Checklist Items</strong>
          <Button size="small" @click="addItem"><template #icon><PlusOutlined /></template>Add Item</Button>
        </div>
        <div v-for="(item, idx) in form.items" :key="idx" class="checklist-item-row" style="margin-bottom: 8px;">
          <span class="item-order">{{ idx + 1 }}</span>
          <Input v-model:value="item.description" placeholder="Item description" style="flex: 1;" />
          <Checkbox v-model:checked="item.required">Req</Checkbox>
          <Button type="text" size="small" danger @click="removeItem(idx)"><MinusCircleOutlined /></Button>
        </div>
      </Form>
    </Modal>
  </Page>
</template>
