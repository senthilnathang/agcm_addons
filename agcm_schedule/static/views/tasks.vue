<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Input,
  message,
  Popconfirm,
  Progress,
  Select,
  Space,
  Table,
  Tag,
} from 'ant-design-vue';
import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
  WarningOutlined,
} from '@ant-design/icons-vue';

import { getProjectsApi } from '#/api/agcm';
import {
  deleteTaskApi,
  getSchedulesApi,
  getTasksApi,
} from '#/api/agcm_schedule';

defineOptions({ name: 'AGCMTasks' });

const router = useRouter();

const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  pageSizeOptions: ['10', '20', '50', '100'],
  showTotal: (total: number) => `Total ${total} tasks`,
});

const loading = ref(false);
const items = ref<any[]>([]);
const projects = ref<any[]>([]);
const schedules = ref<any[]>([]);
const selectedProjectId = ref<number | null>(null);
const selectedScheduleId = ref<number | null>(null);
const statusFilter = ref<string | null>(null);
const searchText = ref('');

const statusOptions = [
  { value: 'todo', label: 'To Do' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'in_review', label: 'In Review' },
  { value: 'completed', label: 'Completed' },
];

const statusColors: Record<string, string> = {
  todo: 'default',
  in_progress: 'processing',
  in_review: 'warning',
  completed: 'success',
};

const statusLabels: Record<string, string> = {
  todo: 'To Do',
  in_progress: 'In Progress',
  in_review: 'In Review',
  completed: 'Completed',
};

const typeLabels: Record<string, string> = {
  task: 'Task',
  milestone: 'Milestone',
  start_milestone: 'Start MS',
  finish_milestone: 'Finish MS',
};

const columns = computed(() => [
  { title: 'Seq #', dataIndex: 'sequence_name', key: 'sequence_name', width: 110 },
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Type', key: 'task_type', width: 100 },
  { title: 'Status', key: 'status', width: 110 },
  { title: 'Progress', key: 'progress', width: 140 },
  { title: 'Planned Start', dataIndex: 'planned_start', key: 'planned_start', width: 120 },
  { title: 'Planned End', dataIndex: 'planned_end', key: 'planned_end', width: 120 },
  { title: 'Critical', key: 'is_critical', width: 80 },
  { title: 'Actions', key: 'actions', width: 120, fixed: 'right' as const },
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

async function fetchSchedules() {
  if (!selectedProjectId.value) {
    schedules.value = [];
    return;
  }
  try {
    const res = await getSchedulesApi({ project_id: selectedProjectId.value });
    schedules.value = (res.items || []).map((s: any) => ({
      value: s.id,
      label: `${s.sequence_name || ''} - ${s.name}${s.is_active ? ' (Active)' : ''}`,
    }));
    // Auto-select first schedule
    if (schedules.value.length > 0) {
      selectedScheduleId.value = schedules.value[0].value;
    } else {
      selectedScheduleId.value = null;
    }
  } catch (e) {
    console.error('Failed to fetch schedules:', e);
  }
}

async function fetchData() {
  loading.value = true;
  try {
    const params: any = {
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
      project_id: selectedProjectId.value || undefined,
      schedule_id: selectedScheduleId.value || undefined,
      status: statusFilter.value || undefined,
      search: searchText.value || undefined,
    };
    const res = await getTasksApi(params);
    items.value = res.items || [];
    pagination.value.total = res.total || 0;
  } catch (e) {
    console.error('Failed to fetch tasks:', e);
    message.error('Failed to load tasks');
  } finally {
    loading.value = false;
  }
}

function onTableChange(pag: any) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

function handleSearch() {
  pagination.value.current = 1;
  fetchData();
}

function handleCreate() {
  const query: any = {};
  if (selectedProjectId.value) query.project_id = selectedProjectId.value;
  if (selectedScheduleId.value) query.schedule_id = selectedScheduleId.value;
  router.push({ path: '/agcm/schedule/tasks/form', query });
}

function handleEdit(record: any) {
  router.push(`/agcm/schedule/tasks/form/${record.id}`);
}

async function handleDelete(record: any) {
  try {
    await deleteTaskApi(record.id);
    message.success('Task deleted');
    fetchData();
  } catch (e) {
    console.error('Delete failed:', e);
    message.error('Failed to delete task');
  }
}

watch(selectedProjectId, async () => {
  await fetchSchedules();
});

watch(selectedScheduleId, () => {
  pagination.value.current = 1;
  fetchData();
});

onMounted(async () => {
  await fetchProjects();
});
</script>

<template>
  <Page title="Tasks" description="Manage schedule tasks">
    <Card>
      <!-- Toolbar -->
      <div class="mb-4 flex flex-wrap items-center gap-2">
        <Select
          v-model:value="selectedProjectId"
          :options="projects"
          placeholder="Select Project"
          show-search
          option-filter-prop="label"
          style="width: 300px"
        />
        <Select
          v-model:value="selectedScheduleId"
          :options="schedules"
          placeholder="Select Schedule"
          show-search
          option-filter-prop="label"
          style="width: 300px"
          allow-clear
        />
        <Select
          v-model:value="statusFilter"
          :options="statusOptions"
          placeholder="All Statuses"
          allow-clear
          style="width: 140px"
          @change="handleSearch"
        />
        <Input
          v-model:value="searchText"
          placeholder="Search tasks..."
          style="width: 220px"
          @press-enter="handleSearch"
        >
          <template #prefix>
            <SearchOutlined />
          </template>
        </Input>
        <Button @click="handleSearch">Search</Button>
        <div class="flex-1" />
        <Button @click="fetchData">
          <template #icon><ReloadOutlined /></template>
          Refresh
        </Button>
        <Button type="primary" @click="handleCreate">
          <template #icon><PlusOutlined /></template>
          New Task
        </Button>
      </div>

      <!-- Table -->
      <Table
        :columns="columns"
        :data-source="items"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        size="middle"
        @change="onTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'task_type'">
            <Tag>{{ typeLabels[record.task_type] || record.task_type }}</Tag>
          </template>
          <template v-else-if="column.key === 'status'">
            <Tag :color="statusColors[record.status] || 'default'">
              {{ statusLabels[record.status] || record.status }}
            </Tag>
          </template>
          <template v-else-if="column.key === 'progress'">
            <Progress
              :percent="record.progress || 0"
              size="small"
              :status="record.progress >= 100 ? 'success' : 'active'"
            />
          </template>
          <template v-else-if="column.key === 'is_critical'">
            <Tag v-if="record.is_critical" color="red">
              <WarningOutlined /> Critical
            </Tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="handleEdit(record)">
                <template #icon><EditOutlined /></template>
              </Button>
              <Popconfirm
                title="Delete this task?"
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
  </Page>
</template>
