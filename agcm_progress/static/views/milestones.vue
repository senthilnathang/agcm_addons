<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  DatePicker,
  Form,
  FormItem,
  Input,
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
  CheckCircleOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';

import { getProjectsApi } from '#/api/agcm';
import {
  createMilestoneApi,
  deleteMilestoneApi,
  getMilestonesApi,
  toggleMilestoneCompletedApi,
  updateMilestoneApi,
} from '#/api/agcm_progress';

import dayjs from 'dayjs';

defineOptions({ name: 'AGCMProgressMilestones' });

const loading = ref(false);
const items = ref<any[]>([]);
const projects = ref<any[]>([]);
const selectedProjectId = ref<number | null>(null);

const modalVisible = ref(false);
const editingItem = ref<any>(null);
const form = ref({
  name: '',
  description: '',
  planned_date: null as any,
  actual_date: null as any,
  is_completed: false,
});

const columns = computed(() => [
  { title: 'Seq #', dataIndex: 'sequence_name', key: 'sequence_name', width: 110 },
  { title: 'Milestone', dataIndex: 'name', key: 'name' },
  { title: 'Description', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: 'Planned Date', dataIndex: 'planned_date', key: 'planned_date', width: 130 },
  { title: 'Actual Date', dataIndex: 'actual_date', key: 'actual_date', width: 130 },
  { title: 'Status', key: 'status', width: 120 },
  { title: 'Actions', key: 'actions', width: 180, fixed: 'right' as const },
]);

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
    const res = await getMilestonesApi({ project_id: selectedProjectId.value });
    items.value = res.items || [];
  } catch (e: any) {
    message.error('Failed to load milestones');
  } finally {
    loading.value = false;
  }
}

function onProjectChange(val: number) {
  selectedProjectId.value = val;
  fetchData();
}

function openAddModal() {
  editingItem.value = null;
  form.value = { name: '', description: '', planned_date: null, actual_date: null, is_completed: false };
  modalVisible.value = true;
}

function openEditModal(record: any) {
  editingItem.value = record;
  form.value = {
    name: record.name,
    description: record.description || '',
    planned_date: record.planned_date ? dayjs(record.planned_date) : null,
    actual_date: record.actual_date ? dayjs(record.actual_date) : null,
    is_completed: record.is_completed,
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
      planned_date: form.value.planned_date ? dayjs(form.value.planned_date).format('YYYY-MM-DD') : null,
      actual_date: form.value.actual_date ? dayjs(form.value.actual_date).format('YYYY-MM-DD') : null,
      is_completed: form.value.is_completed,
    };
    if (editingItem.value) {
      await updateMilestoneApi(editingItem.value.id, payload);
      message.success('Milestone updated');
    } else {
      payload.project_id = selectedProjectId.value;
      await createMilestoneApi(payload);
      message.success('Milestone created');
    }
    modalVisible.value = false;
    fetchData();
  } catch (e: any) {
    message.error(e?.message || 'Failed to save');
  }
}

async function handleToggle(record: any) {
  try {
    await toggleMilestoneCompletedApi(record.id);
    message.success(record.is_completed ? 'Marked as incomplete' : 'Marked as completed');
    fetchData();
  } catch (e: any) {
    message.error('Failed to toggle');
  }
}

async function handleDelete(id: number) {
  try {
    await deleteMilestoneApi(id);
    message.success('Milestone deleted');
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
  <Page title="Milestones" description="Track project milestones and target dates">
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
        <Button type="primary" @click="openAddModal" :disabled="!selectedProjectId">
          <template #icon><PlusOutlined /></template>
          Add Milestone
        </Button>
      </div>

      <Table
        :columns="columns"
        :data-source="items"
        :loading="loading"
        :pagination="false"
        row-key="id"
        size="middle"
        :scroll="{ x: 800 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <Tag v-if="record.is_completed" color="green">
              <CheckCircleOutlined /> Completed
            </Tag>
            <Tag v-else color="blue">
              <ClockCircleOutlined /> Pending
            </Tag>
          </template>
          <template v-if="column.key === 'actions'">
            <Space>
              <Button size="small" @click="handleToggle(record)">
                <template #icon>
                  <CheckCircleOutlined v-if="!record.is_completed" />
                  <ClockCircleOutlined v-else />
                </template>
              </Button>
              <Button size="small" @click="openEditModal(record)">
                <template #icon><EditOutlined /></template>
              </Button>
              <Popconfirm title="Delete this milestone?" @confirm="handleDelete(record.id)">
                <Button size="small" danger>
                  <template #icon><DeleteOutlined /></template>
                </Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <Modal
      v-model:open="modalVisible"
      :title="editingItem ? 'Edit Milestone' : 'Add Milestone'"
      @ok="handleSave"
      :width="520"
    >
      <Form layout="vertical" style="margin-top: 16px">
        <FormItem label="Name" required>
          <Input v-model:value="form.name" placeholder="Milestone name" />
        </FormItem>
        <FormItem label="Description">
          <Textarea v-model:value="form.description" :rows="3" placeholder="Description" />
        </FormItem>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
          <FormItem label="Planned Date">
            <DatePicker v-model:value="form.planned_date" style="width: 100%" />
          </FormItem>
          <FormItem label="Actual Date">
            <DatePicker v-model:value="form.actual_date" style="width: 100%" />
          </FormItem>
        </div>
      </Form>
    </Modal>
  </Page>
</template>
