<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Badge,
  Button,
  Card,
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
} from 'ant-design-vue';
import {
  CheckCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons-vue';

import { getProjectsApi } from '#/api/agcm';
import {
  activateScheduleApi,
  createScheduleApi,
  deleteScheduleApi,
  getSchedulesApi,
  updateScheduleApi,
} from '#/api/agcm_schedule';

defineOptions({ name: 'AGCMSchedules' });

const loading = ref(false);
const items = ref<any[]>([]);
const projects = ref<any[]>([]);
const selectedProjectId = ref<number | null>(null);

const modalVisible = ref(false);
const editingId = ref<number | null>(null);
const formState = ref({ name: '', schedule_type: 'baseline' });

const typeOptions = [
  { value: 'baseline', label: 'Baseline' },
  { value: 'revised', label: 'Revised' },
  { value: 'current', label: 'Current' },
];

const typeColors: Record<string, string> = {
  baseline: 'blue',
  revised: 'orange',
  current: 'green',
};

const columns = computed(() => [
  { title: 'Seq #', dataIndex: 'sequence_name', key: 'sequence_name', width: 120 },
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Type', key: 'schedule_type', width: 120 },
  { title: 'Version', dataIndex: 'version', key: 'version', width: 90 },
  { title: 'Active', key: 'is_active', width: 90 },
  { title: 'Actions', key: 'actions', width: 200, fixed: 'right' as const },
]);

async function fetchProjects() {
  try {
    const res = await getProjectsApi({ page_size: 200 });
    projects.value = (res.items || []).map((p: any) => ({
      value: p.id,
      label: `${p.sequence_name || ''} - ${p.name}`,
    }));
    if (projects.value.length > 0 && !selectedProjectId.value) {
      selectedProjectId.value = projects.value[0].value;
    }
  } catch (e) {
    console.error('Failed to fetch projects:', e);
  }
}

async function fetchData() {
  if (!selectedProjectId.value) return;
  loading.value = true;
  try {
    const res = await getSchedulesApi({ project_id: selectedProjectId.value });
    items.value = res.items || [];
  } catch (e) {
    console.error('Failed to fetch schedules:', e);
    message.error('Failed to load schedules');
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  editingId.value = null;
  formState.value = { name: '', schedule_type: 'baseline' };
  modalVisible.value = true;
}

function openEdit(record: any) {
  editingId.value = record.id;
  formState.value = { name: record.name, schedule_type: record.schedule_type };
  modalVisible.value = true;
}

async function handleSave() {
  try {
    if (editingId.value) {
      await updateScheduleApi(editingId.value, formState.value);
      message.success('Schedule updated');
    } else {
      await createScheduleApi({
        ...formState.value,
        project_id: selectedProjectId.value,
      });
      message.success('Schedule created');
    }
    modalVisible.value = false;
    fetchData();
  } catch (e) {
    console.error('Save failed:', e);
    message.error('Failed to save schedule');
  }
}

async function handleActivate(record: any) {
  try {
    await activateScheduleApi(record.id);
    message.success('Schedule activated');
    fetchData();
  } catch (e) {
    console.error('Activate failed:', e);
    message.error('Failed to activate schedule');
  }
}

async function handleDelete(record: any) {
  try {
    await deleteScheduleApi(record.id);
    message.success('Schedule deleted');
    fetchData();
  } catch (e) {
    console.error('Delete failed:', e);
    message.error('Failed to delete schedule');
  }
}

watch(selectedProjectId, fetchData);
onMounted(async () => {
  await fetchProjects();
});
</script>

<template>
  <Page title="Schedule Versions" description="Manage schedule versions for construction projects">
    <Card>
      <!-- Toolbar -->
      <div class="mb-4 flex items-center justify-between">
        <Space>
          <Select
            v-model:value="selectedProjectId"
            :options="projects"
            placeholder="Select Project"
            show-search
            option-filter-prop="label"
            style="width: 350px"
          />
        </Space>
        <Space>
          <Button @click="fetchData">
            <template #icon><ReloadOutlined /></template>
            Refresh
          </Button>
          <Button type="primary" @click="openCreate" :disabled="!selectedProjectId">
            <template #icon><PlusOutlined /></template>
            New Schedule
          </Button>
        </Space>
      </div>

      <!-- Table -->
      <Table
        :columns="columns"
        :data-source="items"
        :loading="loading"
        :pagination="false"
        row-key="id"
        size="middle"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'schedule_type'">
            <Tag :color="typeColors[record.schedule_type] || 'default'">
              {{ (record.schedule_type || '').replace(/^\w/, (c: string) => c.toUpperCase()) }}
            </Tag>
          </template>
          <template v-else-if="column.key === 'is_active'">
            <Badge v-if="record.is_active" status="success" text="Active" />
            <span v-else class="text-gray-400">-</span>
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button
                v-if="!record.is_active"
                type="link"
                size="small"
                @click="handleActivate(record)"
                title="Activate"
              >
                <template #icon><ThunderboltOutlined /></template>
              </Button>
              <Button v-else type="link" size="small" disabled>
                <template #icon><CheckCircleOutlined style="color: #52c41a" /></template>
              </Button>
              <Button type="link" size="small" @click="openEdit(record)">
                <template #icon><EditOutlined /></template>
              </Button>
              <Popconfirm
                title="Delete this schedule and all its tasks?"
                ok-text="Yes"
                cancel-text="No"
                @confirm="handleDelete(record)"
              >
                <Button type="link" size="small" danger>
                  <template #icon><DeleteOutlined /></template>
                </Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <!-- Create/Edit Modal -->
    <Modal
      v-model:open="modalVisible"
      :title="editingId ? 'Edit Schedule' : 'Create Schedule'"
      @ok="handleSave"
      :ok-text="editingId ? 'Update' : 'Create'"
    >
      <Form layout="vertical" class="mt-4">
        <FormItem label="Name" required>
          <Input v-model:value="formState.name" placeholder="Schedule name" />
        </FormItem>
        <FormItem label="Type">
          <Select
            v-model:value="formState.schedule_type"
            :options="typeOptions"
            style="width: 100%"
          />
        </FormItem>
      </Form>
    </Modal>
  </Page>
</template>
