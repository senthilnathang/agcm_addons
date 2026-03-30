<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue';

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
  Space,
  Table,
  Tag,
  Textarea,
} from 'ant-design-vue';
import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
  SubnodeOutlined,
} from '@ant-design/icons-vue';

import { getProjectsApi } from '#/api/agcm';
import {
  createEstimationItemApi,
  deleteEstimationItemApi,
  getEstimationTreeApi,
  updateEstimationItemApi,
} from '#/api/agcm_progress';

defineOptions({ name: 'AGCMProgressEstimation' });

const loading = ref(false);
const treeData = ref<any[]>([]);
const grandTotal = ref(0);
const projects = ref<any[]>([]);
const selectedProjectId = ref<number | null>(null);

const modalVisible = ref(false);
const editingItem = ref<any>(null);
const parentIdForNew = ref<number | null>(null);
const form = ref({
  name: '',
  description: '',
  cost_type: 'material',
  quantity: 0,
  unit: '',
  unit_cost: 0,
  total_cost: 0,
  status: 'incomplete',
});

const costTypeOptions = [
  { value: 'fee', label: 'Fee' },
  { value: 'subcontractor', label: 'Subcontractor' },
  { value: 'material', label: 'Material' },
  { value: 'labor', label: 'Labor' },
  { value: 'equipment', label: 'Equipment' },
  { value: 'allowance', label: 'Allowance' },
  { value: 'group', label: 'Group' },
];

const statusOptions = [
  { value: 'incomplete', label: 'Incomplete' },
  { value: 'complete', label: 'Complete' },
  { value: 'not_relevant', label: 'Not Relevant' },
];

const statusColors: Record<string, string> = {
  incomplete: 'orange',
  complete: 'green',
  not_relevant: 'default',
};

const columns = computed(() => [
  { title: 'Name', dataIndex: 'name', key: 'name', width: 250 },
  { title: 'Cost Type', key: 'cost_type', width: 120 },
  { title: 'Qty', dataIndex: 'quantity', key: 'quantity', width: 80, align: 'right' as const },
  { title: 'Unit', dataIndex: 'unit', key: 'unit', width: 80 },
  { title: 'Unit Cost', key: 'unit_cost', width: 120, align: 'right' as const },
  { title: 'Total Cost', key: 'total_cost', width: 130, align: 'right' as const },
  { title: 'Status', key: 'status', width: 110 },
  { title: 'Actions', key: 'actions', width: 150, fixed: 'right' as const },
]);

function formatCurrency(val: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val || 0);
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
    const res = await getEstimationTreeApi({ project_id: selectedProjectId.value });
    treeData.value = res.items || [];
    grandTotal.value = res.grand_total || 0;
  } catch (e: any) {
    message.error('Failed to load estimation');
  } finally {
    loading.value = false;
  }
}

function onProjectChange(val: number) {
  selectedProjectId.value = val;
  fetchData();
}

function openAddModal(parentId: number | null = null) {
  editingItem.value = null;
  parentIdForNew.value = parentId;
  form.value = { name: '', description: '', cost_type: parentId ? 'material' : 'group', quantity: 0, unit: '', unit_cost: 0, total_cost: 0, status: 'incomplete' };
  modalVisible.value = true;
}

function openEditModal(record: any) {
  editingItem.value = record;
  parentIdForNew.value = null;
  form.value = {
    name: record.name,
    description: record.description || '',
    cost_type: record.cost_type || 'material',
    quantity: record.quantity || 0,
    unit: record.unit || '',
    unit_cost: record.unit_cost || 0,
    total_cost: record.total_cost || 0,
    status: record.status || 'incomplete',
  };
  modalVisible.value = true;
}

async function handleSave() {
  if (!form.value.name) {
    message.warning('Name is required');
    return;
  }
  try {
    const payload: any = {
      name: form.value.name,
      description: form.value.description || null,
      cost_type: form.value.cost_type,
      quantity: form.value.quantity,
      unit: form.value.unit || null,
      unit_cost: form.value.unit_cost,
      total_cost: form.value.total_cost,
      status: form.value.status,
    };

    if (editingItem.value) {
      await updateEstimationItemApi(editingItem.value.id, payload);
      message.success('Item updated');
    } else {
      payload.project_id = selectedProjectId.value;
      payload.parent_id = parentIdForNew.value;
      await createEstimationItemApi(payload);
      message.success('Item created');
    }
    modalVisible.value = false;
    fetchData();
  } catch (e: any) {
    message.error(e?.message || 'Failed to save');
  }
}

async function handleDelete(id: number) {
  try {
    await deleteEstimationItemApi(id);
    message.success('Item deleted');
    fetchData();
  } catch (e: any) {
    message.error('Failed to delete');
  }
}

onMounted(async () => {
  await loadProjects();
  if (selectedProjectId.value) fetchData();
});
</script>

<template>
  <Page title="Estimation" description="Hierarchical cost estimation for projects">
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
        <Button type="primary" @click="openAddModal(null)" :disabled="!selectedProjectId">
          <template #icon><PlusOutlined /></template>
          Add Root Item
        </Button>
      </div>

      <Table
        :columns="columns"
        :data-source="treeData"
        :loading="loading"
        :pagination="false"
        row-key="id"
        size="middle"
        :scroll="{ x: 900 }"
        :default-expand-all-rows="true"
        children-column-name="children"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'cost_type'">
            <Tag>{{ record.cost_type }}</Tag>
          </template>
          <template v-if="column.key === 'unit_cost'">
            {{ formatCurrency(record.unit_cost) }}
          </template>
          <template v-if="column.key === 'total_cost'">
            <strong v-if="record.children && record.children.length">{{ formatCurrency(record.rollup_total) }}</strong>
            <span v-else>{{ formatCurrency(record.total_cost) }}</span>
          </template>
          <template v-if="column.key === 'status'">
            <Tag :color="statusColors[record.status] || 'default'">{{ record.status }}</Tag>
          </template>
          <template v-if="column.key === 'actions'">
            <Space>
              <Button size="small" title="Add child" @click="openAddModal(record.id)">
                <template #icon><SubnodeOutlined /></template>
              </Button>
              <Button size="small" @click="openEditModal(record)">
                <template #icon><EditOutlined /></template>
              </Button>
              <Popconfirm title="Delete this item and children?" @confirm="handleDelete(record.id)">
                <Button size="small" danger>
                  <template #icon><DeleteOutlined /></template>
                </Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
        <template #summary>
          <tr>
            <td colspan="5" style="text-align: right; font-weight: bold; padding: 8px 16px;">Grand Total:</td>
            <td style="text-align: right; font-weight: bold; padding: 8px 16px;">{{ formatCurrency(grandTotal) }}</td>
            <td colspan="2"></td>
          </tr>
        </template>
      </Table>
    </Card>

    <Modal
      v-model:open="modalVisible"
      :title="editingItem ? 'Edit Item' : (parentIdForNew ? 'Add Child Item' : 'Add Root Item')"
      @ok="handleSave"
      :width="560"
    >
      <Form layout="vertical" style="margin-top: 16px">
        <FormItem label="Name" required>
          <Input v-model:value="form.name" placeholder="Item name" />
        </FormItem>
        <FormItem label="Description">
          <Textarea v-model:value="form.description" :rows="2" placeholder="Description" />
        </FormItem>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
          <FormItem label="Cost Type">
            <Select v-model:value="form.cost_type" :options="costTypeOptions" />
          </FormItem>
          <FormItem label="Status">
            <Select v-model:value="form.status" :options="statusOptions" />
          </FormItem>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 16px;">
          <FormItem label="Quantity">
            <InputNumber v-model:value="form.quantity" :min="0" style="width: 100%" />
          </FormItem>
          <FormItem label="Unit">
            <Input v-model:value="form.unit" placeholder="e.g. m2" />
          </FormItem>
          <FormItem label="Unit Cost">
            <InputNumber v-model:value="form.unit_cost" :min="0" :precision="2" style="width: 100%" />
          </FormItem>
          <FormItem label="Total Cost">
            <InputNumber v-model:value="form.total_cost" :min="0" :precision="2" style="width: 100%" />
          </FormItem>
        </div>
      </Form>
    </Modal>
  </Page>
</template>
