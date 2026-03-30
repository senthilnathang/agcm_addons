<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Empty,
  Select,
  Space,
  Tag,
  Tooltip,
} from 'ant-design-vue';
import {
  ReloadOutlined,
} from '@ant-design/icons-vue';

import { getProjectsApi } from '#/api/agcm';
import {
  getGanttDataApi,
  getSchedulesApi,
} from '#/api/agcm_schedule';

defineOptions({ name: 'AGCMScheduleGantt' });

const loading = ref(false);
const projects = ref<any[]>([]);
const schedules = ref<any[]>([]);
const selectedProjectId = ref<number | null>(null);
const selectedScheduleId = ref<number | null>(null);

const tasks = ref<any[]>([]);
const dependencies = ref<any[]>([]);
const wbsItems = ref<any[]>([]);

const statusColors: Record<string, string> = {
  todo: '#d9d9d9',
  in_progress: '#1890ff',
  in_review: '#faad14',
  completed: '#52c41a',
};

const statusLabels: Record<string, string> = {
  todo: 'To Do',
  in_progress: 'In Progress',
  in_review: 'In Review',
  completed: 'Completed',
};

// Compute timeline range
const timelineStart = computed(() => {
  const dates = tasks.value
    .map((t: any) => t.planned_start)
    .filter(Boolean)
    .map((d: string) => new Date(d).getTime());
  if (dates.length === 0) return new Date();
  const min = new Date(Math.min(...dates));
  // Start 7 days before earliest task
  min.setDate(min.getDate() - 7);
  return min;
});

const timelineEnd = computed(() => {
  const dates = tasks.value
    .map((t: any) => t.planned_end || t.planned_start)
    .filter(Boolean)
    .map((d: string) => new Date(d).getTime());
  if (dates.length === 0) {
    const d = new Date();
    d.setDate(d.getDate() + 30);
    return d;
  }
  const max = new Date(Math.max(...dates));
  // End 7 days after latest task
  max.setDate(max.getDate() + 7);
  return max;
});

const totalDays = computed(() => {
  const diff = timelineEnd.value.getTime() - timelineStart.value.getTime();
  return Math.max(Math.ceil(diff / (1000 * 60 * 60 * 24)), 1);
});

// Generate month headers
const monthHeaders = computed(() => {
  const headers: { label: string; left: number; width: number }[] = [];
  const start = new Date(timelineStart.value);
  start.setDate(1);

  while (start < timelineEnd.value) {
    const monthStart = new Date(Math.max(start.getTime(), timelineStart.value.getTime()));
    const nextMonth = new Date(start.getFullYear(), start.getMonth() + 1, 1);
    const monthEnd = new Date(Math.min(nextMonth.getTime(), timelineEnd.value.getTime()));

    const leftDay = Math.max(0, (monthStart.getTime() - timelineStart.value.getTime()) / (1000 * 60 * 60 * 24));
    const widthDays = (monthEnd.getTime() - monthStart.getTime()) / (1000 * 60 * 60 * 24);

    const label = start.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });

    headers.push({
      label,
      left: (leftDay / totalDays.value) * 100,
      width: (widthDays / totalDays.value) * 100,
    });

    start.setMonth(start.getMonth() + 1);
    start.setDate(1);
  }
  return headers;
});

function getBarStyle(task: any) {
  if (!task.planned_start) return { display: 'none' };

  const start = new Date(task.planned_start);
  const end = task.planned_end ? new Date(task.planned_end) : start;
  const startDay = (start.getTime() - timelineStart.value.getTime()) / (1000 * 60 * 60 * 24);
  const durationDays = Math.max((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24), 1);

  return {
    left: `${(startDay / totalDays.value) * 100}%`,
    width: `${(durationDays / totalDays.value) * 100}%`,
  };
}

function getBarColor(task: any) {
  return statusColors[task.status] || '#d9d9d9';
}

function isMilestone(task: any) {
  return task.task_type === 'milestone'
    || task.task_type === 'start_milestone'
    || task.task_type === 'finish_milestone';
}

function getMilestoneStyle(task: any) {
  if (!task.planned_start) return { display: 'none' };

  const start = new Date(task.planned_start);
  const startDay = (start.getTime() - timelineStart.value.getTime()) / (1000 * 60 * 60 * 24);

  return {
    left: `${(startDay / totalDays.value) * 100}%`,
  };
}

// Dependency lines (simplified: just show as info, CSS arrows are complex)
const depLines = computed(() => {
  const taskMap = new Map(tasks.value.map((t: any, i: number) => [t.id, i]));
  return dependencies.value
    .filter((d: any) => taskMap.has(d.predecessor_id) && taskMap.has(d.successor_id))
    .map((d: any) => ({
      from: taskMap.get(d.predecessor_id),
      to: taskMap.get(d.successor_id),
      type: d.dependency_type,
    }));
});

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
      is_active: s.is_active,
    }));
    // Auto-select active schedule, else first
    const active = schedules.value.find((s: any) => s.is_active);
    selectedScheduleId.value = active ? active.value : (schedules.value[0]?.value || null);
  } catch (e) {
    console.error('Failed to fetch schedules:', e);
  }
}

async function fetchGanttData() {
  if (!selectedProjectId.value || !selectedScheduleId.value) {
    tasks.value = [];
    dependencies.value = [];
    wbsItems.value = [];
    return;
  }
  loading.value = true;
  try {
    const res = await getGanttDataApi({
      project_id: selectedProjectId.value,
      schedule_id: selectedScheduleId.value,
    });
    tasks.value = res.tasks || [];
    dependencies.value = res.dependencies || [];
    wbsItems.value = res.wbs_items || [];
  } catch (e) {
    console.error('Failed to fetch Gantt data:', e);
  } finally {
    loading.value = false;
  }
}

watch(selectedProjectId, async () => {
  await fetchSchedules();
});

watch(selectedScheduleId, () => {
  fetchGanttData();
});

onMounted(async () => {
  await fetchProjects();
});
</script>

<template>
  <Page title="Gantt Chart" description="Visual project schedule timeline">
    <Card :loading="loading">
      <!-- Toolbar -->
      <div class="mb-4 flex items-center justify-between">
        <Space>
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
        </Space>
        <Space>
          <Tag color="default">To Do</Tag>
          <Tag color="processing">In Progress</Tag>
          <Tag color="warning">In Review</Tag>
          <Tag color="success">Completed</Tag>
          <Button @click="fetchGanttData">
            <template #icon><ReloadOutlined /></template>
            Refresh
          </Button>
        </Space>
      </div>

      <Empty v-if="tasks.length === 0 && !loading" description="No tasks found. Create tasks in the Tasks view." />

      <!-- Gantt Chart -->
      <div v-if="tasks.length > 0" class="gantt-container">
        <!-- Header: month labels -->
        <div class="gantt-header">
          <div class="gantt-label-col gantt-header-cell" style="font-weight: 600">Task</div>
          <div class="gantt-timeline-col" style="position: relative">
            <div
              v-for="(mh, idx) in monthHeaders"
              :key="idx"
              class="gantt-month-header"
              :style="{ left: mh.left + '%', width: mh.width + '%' }"
            >
              {{ mh.label }}
            </div>
          </div>
        </div>

        <!-- Rows -->
        <div
          v-for="(task, index) in tasks"
          :key="task.id"
          class="gantt-row"
          :class="{ 'gantt-row-critical': task.is_critical, 'gantt-row-alt': index % 2 === 1 }"
        >
          <!-- Label -->
          <div class="gantt-label-col">
            <Tooltip :title="`${task.sequence_name || ''} - ${task.name}`">
              <div class="gantt-task-label">
                <span class="gantt-task-seq">{{ task.sequence_name }}</span>
                <span class="gantt-task-name">{{ task.name }}</span>
              </div>
            </Tooltip>
          </div>

          <!-- Timeline -->
          <div class="gantt-timeline-col">
            <!-- Milestone diamond -->
            <template v-if="isMilestone(task)">
              <Tooltip :title="`${task.name} (${statusLabels[task.status] || task.status})`">
                <div
                  class="gantt-milestone"
                  :style="getMilestoneStyle(task)"
                >
                  <div class="gantt-diamond" :style="{ backgroundColor: getBarColor(task) }" />
                </div>
              </Tooltip>
            </template>

            <!-- Task bar -->
            <template v-else>
              <Tooltip
                :title="`${task.name}: ${task.progress}% (${statusLabels[task.status] || task.status})`"
              >
                <div
                  class="gantt-bar"
                  :style="{ ...getBarStyle(task), backgroundColor: getBarColor(task) + '33', borderColor: getBarColor(task) }"
                >
                  <!-- Progress fill -->
                  <div
                    class="gantt-bar-progress"
                    :style="{ width: task.progress + '%', backgroundColor: getBarColor(task) }"
                  />
                  <span class="gantt-bar-text">{{ task.progress }}%</span>
                </div>
              </Tooltip>
            </template>

            <!-- Dependency arrows (simplified: small indicator) -->
            <template v-for="dep in depLines.filter((d: any) => d.to === index)" :key="dep.from + '-' + dep.to">
              <div class="gantt-dep-indicator" :title="`Depends on task row ${dep.from + 1} (${dep.type})`">
                &#8594;
              </div>
            </template>
          </div>
        </div>
      </div>
    </Card>
  </Page>
</template>

<style scoped>
.gantt-container {
  overflow-x: auto;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
}

.gantt-header {
  display: flex;
  border-bottom: 2px solid #e8e8e8;
  background: #fafafa;
  min-height: 36px;
}

.gantt-header-cell {
  padding: 8px 12px;
  font-size: 13px;
}

.gantt-label-col {
  width: 260px;
  min-width: 260px;
  padding: 6px 12px;
  border-right: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
}

.gantt-timeline-col {
  flex: 1;
  min-width: 600px;
  position: relative;
  height: 36px;
}

.gantt-month-header {
  position: absolute;
  top: 0;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 500;
  color: #666;
  border-right: 1px solid #f0f0f0;
}

.gantt-row {
  display: flex;
  border-bottom: 1px solid #f5f5f5;
  min-height: 36px;
  transition: background 0.15s;
}

.gantt-row:hover {
  background: #e6f7ff22;
}

.gantt-row-alt {
  background: #fafafa;
}

.gantt-row-critical .gantt-label-col {
  border-left: 3px solid #ff4d4f;
}

.gantt-task-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  max-width: 240px;
}

.gantt-task-seq {
  color: #999;
  margin-right: 6px;
  font-size: 11px;
}

.gantt-task-name {
  color: #333;
}

.gantt-bar {
  position: absolute;
  top: 6px;
  height: 24px;
  border-radius: 4px;
  border: 1px solid;
  overflow: hidden;
  cursor: pointer;
  min-width: 8px;
  display: flex;
  align-items: center;
}

.gantt-bar-progress {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  border-radius: 3px 0 0 3px;
  transition: width 0.3s;
}

.gantt-bar-text {
  position: relative;
  z-index: 1;
  font-size: 10px;
  color: #333;
  padding-left: 6px;
  font-weight: 500;
}

.gantt-milestone {
  position: absolute;
  top: 8px;
  cursor: pointer;
}

.gantt-diamond {
  width: 16px;
  height: 16px;
  transform: rotate(45deg);
  border-radius: 2px;
  margin-left: -8px;
}

.gantt-dep-indicator {
  position: absolute;
  left: 2px;
  top: 10px;
  font-size: 12px;
  color: #999;
}
</style>
