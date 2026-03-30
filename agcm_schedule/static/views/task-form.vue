<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Col,
  DatePicker,
  Divider,
  Form,
  FormItem,
  Input,
  InputNumber,
  message,
  Popconfirm,
  Row,
  Select,
  Slider,
  Space,
  Switch,
  Table,
  Textarea,
} from 'ant-design-vue';
import {
  ArrowLeftOutlined,
  DeleteOutlined,
  PlusOutlined,
  SaveOutlined,
} from '@ant-design/icons-vue';
import dayjs from 'dayjs';

import { getProjectsApi } from '#/api/agcm';
import {
  createDependencyApi,
  createTaskApi,
  deleteDependencyApi,
  getDependenciesApi,
  getSchedulesApi,
  getTaskApi,
  getTasksApi,
  getWbsApi,
  updateTaskApi,
} from '#/api/agcm_schedule';

defineOptions({ name: 'AGCMTaskForm' });

const router = useRouter();
const route = useRoute();

const taskId = computed(() => {
  const parts = (route.path || '').split('/');
  const last = parts[parts.length - 1];
  return last && last !== 'form' ? Number(last) : null;
});
const isEdit = computed(() => !!taskId.value);
const loading = ref(false);
const saving = ref(false);

const projects = ref<any[]>([]);
const schedules = ref<any[]>([]);
const wbsItems = ref<any[]>([]);
const allTasks = ref<any[]>([]);
const dependencies = ref<any[]>([]);

const form = ref({
  name: '',
  description: '',
  task_type: 'task',
  work_type: 'work',
  status: 'todo',
  planned_start: null as any,
  planned_end: null as any,
  actual_start: null as any,
  actual_end: null as any,
  duration_days: 0,
  progress: 0,
  total_float: 0,
  free_float: 0,
  is_critical: false,
  wbs_id: null as number | null,
  schedule_id: null as number | null,
  assigned_to: null as number | null,
  project_id: null as number | null,
});

const newDep = ref({
  task_id: null as number | null,
  dependency_type: 'FS',
  lag_days: 0,
  direction: 'predecessor',
});

const taskTypeOptions = [
  { value: 'task', label: 'Task' },
  { value: 'milestone', label: 'Milestone' },
  { value: 'start_milestone', label: 'Start Milestone' },
  { value: 'finish_milestone', label: 'Finish Milestone' },
];

const workTypeOptions = [
  { value: 'work', label: 'Work' },
  { value: 'delivery', label: 'Delivery' },
  { value: 'inspection', label: 'Inspection' },
  { value: 'roadblock', label: 'Roadblock' },
  { value: 'safety', label: 'Safety' },
  { value: 'downtime', label: 'Downtime' },
];

const statusOptions = [
  { value: 'todo', label: 'To Do' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'in_review', label: 'In Review' },
  { value: 'completed', label: 'Completed' },
];

const depTypeOptions = [
  { value: 'FS', label: 'Finish-to-Start (FS)' },
  { value: 'SS', label: 'Start-to-Start (SS)' },
  { value: 'FF', label: 'Finish-to-Finish (FF)' },
  { value: 'SF', label: 'Start-to-Finish (SF)' },
];

const depColumns = [
  { title: 'Direction', key: 'direction', width: 120 },
  { title: 'Task', key: 'task_name' },
  { title: 'Type', dataIndex: 'dependency_type', key: 'dependency_type', width: 80 },
  { title: 'Lag', dataIndex: 'lag_days', key: 'lag_days', width: 80 },
  { title: '', key: 'actions', width: 60 },
];

async function fetchProjects() {
  try {
    const res = await getProjectsApi({ page_size: 200 });
    projects.value = (res.items || []).map((p: any) => ({
      value: p.id,
      label: `${p.sequence_name || ''} - ${p.name}`,
    }));
  } catch (e) {
    console.error('Failed to fetch projects:', e);
  }
}

async function fetchSchedules(projectId: number) {
  try {
    const res = await getSchedulesApi({ project_id: projectId });
    schedules.value = (res.items || []).map((s: any) => ({
      value: s.id,
      label: `${s.sequence_name || ''} - ${s.name}`,
    }));
  } catch (e) {
    console.error('Failed to fetch schedules:', e);
  }
}

async function fetchWbs(scheduleId: number) {
  try {
    const res = await getWbsApi({ schedule_id: scheduleId });
    wbsItems.value = (res.items || []).map((w: any) => ({
      value: w.id,
      label: `${w.code} - ${w.name}`,
    }));
  } catch (e) {
    console.error('Failed to fetch WBS:', e);
  }
}

async function fetchAllTasks(scheduleId: number) {
  try {
    const res = await getTasksApi({ schedule_id: scheduleId, page_size: 200 });
    allTasks.value = (res.items || [])
      .filter((t: any) => t.id !== taskId.value)
      .map((t: any) => ({
        value: t.id,
        label: `${t.sequence_name || ''} - ${t.name}`,
      }));
  } catch (e) {
    console.error('Failed to fetch tasks:', e);
  }
}

async function fetchDependencies() {
  if (!taskId.value || !form.value.schedule_id) return;
  try {
    const res = await getDependenciesApi({ schedule_id: form.value.schedule_id });
    const allDeps = res.items || [];
    // Filter to deps involving this task
    dependencies.value = allDeps
      .filter((d: any) => d.predecessor_id === taskId.value || d.successor_id === taskId.value)
      .map((d: any) => {
        const isPredecessor = d.successor_id === taskId.value;
        const otherTaskId = isPredecessor ? d.predecessor_id : d.successor_id;
        const otherTask = allTasks.value.find((t: any) => t.value === otherTaskId);
        return {
          ...d,
          direction: isPredecessor ? 'Predecessor' : 'Successor',
          task_name: otherTask ? otherTask.label : `Task #${otherTaskId}`,
        };
      });
  } catch (e) {
    console.error('Failed to fetch dependencies:', e);
  }
}

async function loadTask() {
  if (!taskId.value) return;
  loading.value = true;
  try {
    const task = await getTaskApi(taskId.value);
    form.value = {
      name: task.name,
      description: task.description || '',
      task_type: task.task_type || 'task',
      work_type: task.work_type || 'work',
      status: task.status || 'todo',
      planned_start: task.planned_start ? dayjs(task.planned_start) : null,
      planned_end: task.planned_end ? dayjs(task.planned_end) : null,
      actual_start: task.actual_start ? dayjs(task.actual_start) : null,
      actual_end: task.actual_end ? dayjs(task.actual_end) : null,
      duration_days: task.duration_days || 0,
      progress: task.progress || 0,
      total_float: task.total_float || 0,
      free_float: task.free_float || 0,
      is_critical: task.is_critical || false,
      wbs_id: task.wbs_id,
      schedule_id: task.schedule_id,
      assigned_to: task.assigned_to,
      project_id: task.project_id,
    };

    if (task.project_id) {
      await fetchSchedules(task.project_id);
    }
    if (task.schedule_id) {
      await fetchWbs(task.schedule_id);
      await fetchAllTasks(task.schedule_id);
      await fetchDependencies();
    }
  } catch (e) {
    console.error('Failed to load task:', e);
    message.error('Failed to load task');
  } finally {
    loading.value = false;
  }
}

async function handleSave() {
  if (!form.value.name) {
    message.warning('Task name is required');
    return;
  }
  if (!form.value.project_id) {
    message.warning('Project is required');
    return;
  }
  if (!form.value.schedule_id) {
    message.warning('Schedule is required');
    return;
  }

  saving.value = true;
  try {
    const payload: any = {
      ...form.value,
      planned_start: form.value.planned_start ? dayjs(form.value.planned_start).format('YYYY-MM-DD') : null,
      planned_end: form.value.planned_end ? dayjs(form.value.planned_end).format('YYYY-MM-DD') : null,
      actual_start: form.value.actual_start ? dayjs(form.value.actual_start).format('YYYY-MM-DD') : null,
      actual_end: form.value.actual_end ? dayjs(form.value.actual_end).format('YYYY-MM-DD') : null,
    };

    if (isEdit.value) {
      await updateTaskApi(taskId.value, payload);
      message.success('Task updated');
    } else {
      await createTaskApi(payload);
      message.success('Task created');
    }
    router.push('/agcm/schedule/tasks');
  } catch (e) {
    console.error('Save failed:', e);
    message.error('Failed to save task');
  } finally {
    saving.value = false;
  }
}

async function handleAddDependency() {
  if (!newDep.value.task_id || !taskId.value) return;
  try {
    const payload: any = {
      dependency_type: newDep.value.dependency_type,
      lag_days: newDep.value.lag_days,
    };
    if (newDep.value.direction === 'predecessor') {
      payload.predecessor_id = newDep.value.task_id;
      payload.successor_id = taskId.value;
    } else {
      payload.predecessor_id = taskId.value;
      payload.successor_id = newDep.value.task_id;
    }
    await createDependencyApi(payload);
    message.success('Dependency added');
    newDep.value = { task_id: null, dependency_type: 'FS', lag_days: 0, direction: 'predecessor' };
    await fetchDependencies();
  } catch (e) {
    console.error('Add dependency failed:', e);
    message.error('Failed to add dependency');
  }
}

async function handleDeleteDependency(dep: any) {
  try {
    await deleteDependencyApi(dep.id);
    message.success('Dependency removed');
    await fetchDependencies();
  } catch (e) {
    console.error('Delete dependency failed:', e);
    message.error('Failed to remove dependency');
  }
}

function handleProjectChange(projectId: number) {
  form.value.schedule_id = null;
  form.value.wbs_id = null;
  if (projectId) fetchSchedules(projectId);
}

function handleScheduleChange(scheduleId: number) {
  form.value.wbs_id = null;
  if (scheduleId) {
    fetchWbs(scheduleId);
    fetchAllTasks(scheduleId);
  }
}

function goBack() {
  router.push('/agcm/schedule/tasks');
}

onMounted(async () => {
  await fetchProjects();

  // Pre-populate from query params
  const qProjectId = route.query.project_id ? Number(route.query.project_id) : null;
  const qScheduleId = route.query.schedule_id ? Number(route.query.schedule_id) : null;
  if (qProjectId) {
    form.value.project_id = qProjectId;
    await fetchSchedules(qProjectId);
  }
  if (qScheduleId) {
    form.value.schedule_id = qScheduleId;
    await fetchWbs(qScheduleId);
  }

  if (isEdit.value) {
    await loadTask();
  }
});
</script>

<template>
  <Page :title="isEdit ? 'Edit Task' : 'New Task'" description="Create or edit a schedule task">
    <Card :loading="loading">
      <Form layout="vertical">
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Project" required>
              <Select
                v-model:value="form.project_id"
                :options="projects"
                placeholder="Select Project"
                show-search
                option-filter-prop="label"
                style="width: 100%"
                @change="handleProjectChange"
              />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Schedule" required>
              <Select
                v-model:value="form.schedule_id"
                :options="schedules"
                placeholder="Select Schedule"
                show-search
                option-filter-prop="label"
                style="width: 100%"
                @change="handleScheduleChange"
              />
            </FormItem>
          </Col>
        </Row>

        <Row :gutter="16">
          <Col :span="16">
            <FormItem label="Task Name" required>
              <Input v-model:value="form.name" placeholder="Enter task name" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="WBS">
              <Select
                v-model:value="form.wbs_id"
                :options="wbsItems"
                placeholder="Select WBS item"
                show-search
                option-filter-prop="label"
                allow-clear
                style="width: 100%"
              />
            </FormItem>
          </Col>
        </Row>

        <FormItem label="Description">
          <Textarea v-model:value="form.description" :rows="3" placeholder="Task description" />
        </FormItem>

        <Row :gutter="16">
          <Col :span="6">
            <FormItem label="Task Type">
              <Select v-model:value="form.task_type" :options="taskTypeOptions" style="width: 100%" />
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Work Type">
              <Select v-model:value="form.work_type" :options="workTypeOptions" style="width: 100%" />
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Status">
              <Select v-model:value="form.status" :options="statusOptions" style="width: 100%" />
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Duration (days)">
              <InputNumber v-model:value="form.duration_days" :min="0" style="width: 100%" />
            </FormItem>
          </Col>
        </Row>

        <Divider>Dates</Divider>

        <Row :gutter="16">
          <Col :span="6">
            <FormItem label="Planned Start">
              <DatePicker v-model:value="form.planned_start" style="width: 100%" />
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Planned End">
              <DatePicker v-model:value="form.planned_end" style="width: 100%" />
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Actual Start">
              <DatePicker v-model:value="form.actual_start" style="width: 100%" />
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Actual End">
              <DatePicker v-model:value="form.actual_end" style="width: 100%" />
            </FormItem>
          </Col>
        </Row>

        <Divider>Progress &amp; Float</Divider>

        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Progress">
              <Slider v-model:value="form.progress" :min="0" :max="100" :marks="{ 0: '0%', 50: '50%', 100: '100%' }" />
            </FormItem>
          </Col>
          <Col :span="4">
            <FormItem label="Total Float">
              <InputNumber v-model:value="form.total_float" style="width: 100%" />
            </FormItem>
          </Col>
          <Col :span="4">
            <FormItem label="Free Float">
              <InputNumber v-model:value="form.free_float" style="width: 100%" />
            </FormItem>
          </Col>
          <Col :span="4">
            <FormItem label="Critical Path">
              <Switch v-model:checked="form.is_critical" />
            </FormItem>
          </Col>
        </Row>

        <!-- Dependencies (only in edit mode) -->
        <template v-if="isEdit">
          <Divider>Dependencies</Divider>

          <div class="mb-3 flex items-center gap-2">
            <Select
              v-model:value="newDep.direction"
              :options="[{ value: 'predecessor', label: 'Predecessor' }, { value: 'successor', label: 'Successor' }]"
              style="width: 140px"
            />
            <Select
              v-model:value="newDep.task_id"
              :options="allTasks"
              placeholder="Select task"
              show-search
              option-filter-prop="label"
              style="width: 300px"
              allow-clear
            />
            <Select
              v-model:value="newDep.dependency_type"
              :options="depTypeOptions"
              style="width: 180px"
            />
            <InputNumber v-model:value="newDep.lag_days" placeholder="Lag" :min="0" style="width: 80px" />
            <Button type="primary" size="small" @click="handleAddDependency" :disabled="!newDep.task_id">
              <template #icon><PlusOutlined /></template>
              Add
            </Button>
          </div>

          <Table
            :columns="depColumns"
            :data-source="dependencies"
            :pagination="false"
            row-key="id"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'direction'">
                {{ record.direction }}
              </template>
              <template v-else-if="column.key === 'task_name'">
                {{ record.task_name }}
              </template>
              <template v-else-if="column.key === 'actions'">
                <Popconfirm title="Remove?" @confirm="handleDeleteDependency(record)">
                  <Button type="link" size="small" danger>
                    <template #icon><DeleteOutlined /></template>
                  </Button>
                </Popconfirm>
              </template>
            </template>
          </Table>
        </template>

        <Divider />

        <Space>
          <Button @click="goBack">
            <template #icon><ArrowLeftOutlined /></template>
            Back
          </Button>
          <Button type="primary" :loading="saving" @click="handleSave">
            <template #icon><SaveOutlined /></template>
            {{ isEdit ? 'Update' : 'Create' }}
          </Button>
        </Space>
      </Form>
    </Card>
  </Page>
</template>
