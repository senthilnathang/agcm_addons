<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import * as echarts from 'echarts';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Empty,
  Input,
  message,
  Popconfirm,
  Progress,
  RadioButton,
  RadioGroup,
  Select,
  Space,
  Table,
  Tag,
} from 'ant-design-vue';
import {
  BarChartOutlined,
  DeleteOutlined,
  EditOutlined,
  FullscreenExitOutlined,
  FullscreenOutlined,
  OrderedListOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
  WarningOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMTaskSchedule' });

const router = useRouter();
const BASE = '/agcm_schedule';
const DAY_MS = 86400000;

// --- Shared state ---
const viewMode = ref('list');
const loading = ref(false);
const projects = ref([]);
const schedules = ref([]);
const selectedProjectId = ref(null);
const selectedScheduleId = ref(null);
const statusFilter = ref(null);
const searchText = ref('');

// List state
const listItems = ref([]);
const listPage = ref(1);
const listPageSize = ref(20);
const listTotal = ref(0);

// Gantt state
const ganttTasks = ref([]);
const ganttDeps = ref([]);
const ganttWbs = ref([]);
const ganttChartRef = ref(null);
const ganttExpanded = ref(false);
let ganttChart = null;

const statusOptions = [
  { value: 'todo', label: 'To Do' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'in_review', label: 'In Review' },
  { value: 'completed', label: 'Completed' },
];

const statusColors = { todo: 'default', in_progress: 'processing', in_review: 'warning', completed: 'success' };
const statusHex = { todo: '#bfbfbf', in_progress: '#1890ff', in_review: '#faad14', completed: '#52c41a' };
const criticalHex = '#ff4d4f';
const statusLabels = { todo: 'To Do', in_progress: 'In Progress', in_review: 'In Review', completed: 'Completed' };
const typeLabels = { task: 'Task', milestone: 'Milestone', start_milestone: 'Start MS', finish_milestone: 'Finish MS' };

const columns = [
  { title: 'Seq #', dataIndex: 'sequence_name', key: 'sequence_name', width: 110 },
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Type', key: 'task_type', width: 100 },
  { title: 'Status', key: 'status', width: 110 },
  { title: 'Progress', key: 'progress', width: 140 },
  { title: 'Planned Start', dataIndex: 'planned_start', key: 'planned_start', width: 120 },
  { title: 'Planned End', dataIndex: 'planned_end', key: 'planned_end', width: 120 },
  { title: 'Critical', key: 'is_critical', width: 80 },
  { title: 'Actions', key: 'actions', width: 120, fixed: 'right' },
];

// ===================== DATA FETCHING =====================

async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = (data.items || data.results || []).map(p => ({ value: p.id, label: `${p.sequence_name || ''} - ${p.name}` }));
    if (projects.value.length > 0 && !selectedProjectId.value) {
      selectedProjectId.value = projects.value[0].value;
    }
  } catch { message.error('Failed to load projects'); }
}

async function fetchSchedules() {
  if (!selectedProjectId.value) { schedules.value = []; return; }
  try {
    const data = await requestClient.get(`${BASE}/schedules`, { params: { project_id: selectedProjectId.value } });
    schedules.value = (data.items || data || []).map(s => ({
      value: s.id,
      label: `${s.sequence_name || ''} - ${s.name}${s.is_active ? ' (Active)' : ''}`,
      is_active: s.is_active,
    }));
    const active = schedules.value.find(s => s.is_active);
    selectedScheduleId.value = active ? active.value : (schedules.value[0]?.value || null);
  } catch { message.error('Failed to load schedules'); }
}

async function fetchListData() {
  if (!selectedProjectId.value) return;
  loading.value = true;
  try {
    const params = {
      page: listPage.value, page_size: listPageSize.value,
      project_id: selectedProjectId.value,
      schedule_id: selectedScheduleId.value || undefined,
      status: statusFilter.value || undefined,
      search: searchText.value || undefined,
    };
    const data = await requestClient.get(`${BASE}/tasks`, { params });
    listItems.value = data.items || [];
    listTotal.value = data.total || 0;
  } catch { message.error('Failed to load tasks'); }
  finally { loading.value = false; }
}

async function fetchGanttData() {
  if (!selectedProjectId.value || !selectedScheduleId.value) {
    ganttTasks.value = []; ganttDeps.value = []; ganttWbs.value = [];
    return;
  }
  loading.value = true;
  try {
    const data = await requestClient.get(`${BASE}/gantt`, {
      params: { project_id: selectedProjectId.value, schedule_id: selectedScheduleId.value },
    });
    ganttTasks.value = data.tasks || [];
    ganttDeps.value = data.dependencies || [];
    ganttWbs.value = data.wbs_items || [];
    await nextTick();
    renderGanttChart();
  } catch { message.error('Failed to load Gantt data'); }
  finally { loading.value = false; }
}

function fetchData() {
  if (viewMode.value === 'list') fetchListData();
  else fetchGanttData();
}

function handleSearch() { listPage.value = 1; fetchData(); }
function onTableChange(pag) { listPage.value = pag.current; listPageSize.value = pag.pageSize; fetchListData(); }

// ===================== TASK ACTIONS =====================

function handleCreate() {
  const query = {};
  if (selectedProjectId.value) query.project_id = selectedProjectId.value;
  if (selectedScheduleId.value) query.schedule_id = selectedScheduleId.value;
  router.push({ path: '/agcm/schedule/tasks/form', query });
}

function handleEdit(record) {
  router.push({ path: '/agcm/schedule/tasks/form', query: { id: record.id } });
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/tasks/${record.id}`);
    message.success('Task deleted');
    fetchData();
  } catch { message.error('Failed to delete task'); }
}

// ===================== ECHARTS GANTT =====================

function renderGanttChart() {
  if (!ganttChartRef.value || ganttTasks.value.length === 0) return;

  if (ganttChart) ganttChart.dispose();
  ganttChart = echarts.init(ganttChartRef.value);

  const tasks = ganttTasks.value;
  const deps = ganttDeps.value;
  const taskIdxMap = new Map(tasks.map((t, i) => [t.id, i]));

  // Category data (task names reversed for bottom-to-top display)
  const categories = tasks.map(t => {
    const prefix = t.is_critical ? '!! ' : '';
    const seq = t.sequence_name ? `${t.sequence_name} ` : '';
    return `${prefix}${seq}${t.name}`;
  }).reverse();

  // Compute date range
  const allDates = tasks.flatMap(t => [t.planned_start, t.planned_end, t.actual_start, t.actual_end].filter(Boolean));
  const dateTs = allDates.map(d => new Date(d).getTime());
  const minDate = dateTs.length ? Math.min(...dateTs) - 7 * DAY_MS : Date.now();
  const maxDate = dateTs.length ? Math.max(...dateTs) + 7 * DAY_MS : Date.now() + 90 * DAY_MS;

  // Build bar data — each task is a custom renderItem
  const taskData = tasks.map((t, i) => {
    const start = t.planned_start ? new Date(t.planned_start).getTime() : null;
    const end = t.planned_end ? new Date(t.planned_end).getTime() : start;
    const isMilestone = ['milestone', 'start_milestone', 'finish_milestone'].includes(t.task_type);
    return {
      value: [tasks.length - 1 - i, start, end || start, t.progress || 0],
      task: t,
      isMilestone,
      itemStyle: {
        color: t.is_critical ? criticalHex : (statusHex[t.status] || statusHex.todo),
      },
    };
  }).filter(d => d.value[1] !== null);

  // Actual progress overlay data
  const progressData = taskData.filter(d => !d.isMilestone && d.task.progress > 0).map(d => {
    const start = d.value[1];
    const end = d.value[2];
    const dur = end - start;
    const progressEnd = start + dur * (d.task.progress / 100);
    return {
      value: [d.value[0], start, progressEnd, d.task.progress],
      itemStyle: {
        color: d.task.is_critical ? '#ff7875' : (statusHex[d.task.status] || statusHex.todo),
        opacity: 0.9,
      },
    };
  });

  // Dependency arrow data for markLine
  const depArrows = deps.map(dep => {
    const fromIdx = taskIdxMap.get(dep.predecessor_id);
    const toIdx = taskIdxMap.get(dep.successor_id);
    if (fromIdx === undefined || toIdx === undefined) return null;
    const fromTask = tasks[fromIdx];
    const toTask = tasks[toIdx];
    if (!fromTask.planned_end || !toTask.planned_start) return null;
    return {
      from: [new Date(fromTask.planned_end).getTime(), tasks.length - 1 - fromIdx],
      to: [new Date(toTask.planned_start).getTime(), tasks.length - 1 - toIdx],
      type: dep.dependency_type,
    };
  }).filter(Boolean);

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        if (!params.data || !params.data.task) return '';
        const t = params.data.task;
        const status = statusLabels[t.status] || t.status;
        const type = typeLabels[t.task_type] || t.task_type;
        const start = t.planned_start || '-';
        const end = t.planned_end || '-';
        const critical = t.is_critical ? '<span style="color:#ff4d4f;font-weight:600">CRITICAL</span><br/>' : '';
        return `<div style="max-width:320px">
          <strong>${t.sequence_name || ''}</strong> ${t.name}<br/>
          ${critical}
          <b>Type:</b> ${type} &nbsp; <b>Status:</b> ${status}<br/>
          <b>Start:</b> ${start} &nbsp; <b>End:</b> ${end}<br/>
          <b>Duration:</b> ${t.duration_days || 0}d &nbsp; <b>Progress:</b> ${t.progress || 0}%<br/>
          ${t.total_float !== undefined ? `<b>Float:</b> ${t.total_float}d` : ''}
        </div>`;
      },
    },
    grid: {
      left: 260,
      right: 40,
      top: 50,
      bottom: 80,
      containLabel: false,
    },
    xAxis: {
      type: 'time',
      min: minDate,
      max: maxDate,
      axisLabel: {
        formatter: (val) => {
          const d = new Date(val);
          return `${d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
        },
        fontSize: 10,
      },
      splitLine: { show: true, lineStyle: { color: '#f0f0f0', type: 'dashed' } },
    },
    yAxis: {
      type: 'category',
      data: categories,
      axisLabel: {
        fontSize: 11,
        width: 240,
        overflow: 'truncate',
        formatter: (val) => {
          if (val.startsWith('!! ')) return `{critical|${val.substring(3)}}`;
          return val;
        },
        rich: {
          critical: { color: criticalHex, fontWeight: 'bold', fontSize: 11 },
        },
      },
      axisTick: { show: false },
      splitLine: { show: true, lineStyle: { color: '#f8f8f8' } },
    },
    dataZoom: [
      {
        type: 'slider',
        xAxisIndex: 0,
        filterMode: 'none',
        height: 24,
        bottom: 10,
        borderColor: '#ddd',
        handleStyle: { color: '#1890ff' },
        textStyle: { fontSize: 10 },
        labelFormatter: (val) => new Date(val).toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
      },
      {
        type: 'inside',
        xAxisIndex: 0,
        filterMode: 'none',
        zoomOnMouseWheel: 'ctrl',
        moveOnMouseWheel: true,
      },
      {
        type: 'slider',
        yAxisIndex: 0,
        filterMode: 'none',
        width: 16,
        right: 8,
        borderColor: '#ddd',
        handleStyle: { color: '#1890ff' },
      },
    ],
    series: [
      // Background bars (full planned duration)
      {
        type: 'custom',
        renderItem: (params, api) => {
          const catIdx = api.value(0);
          const start = api.coord([api.value(1), catIdx]);
          const end = api.coord([api.value(2), catIdx]);
          const barHeight = 18;
          const isMilestone = params.dataIndex < taskData.length && taskData[params.dataIndex]?.isMilestone;

          if (isMilestone) {
            // Diamond shape for milestones
            const cx = start[0];
            const cy = start[1];
            const size = 10;
            return {
              type: 'polygon',
              shape: {
                points: [
                  [cx, cy - size],
                  [cx + size, cy],
                  [cx, cy + size],
                  [cx - size, cy],
                ],
              },
              style: api.style(),
              styleEmphasis: { shadowBlur: 6, shadowColor: 'rgba(0,0,0,0.3)' },
            };
          }

          const width = Math.max(end[0] - start[0], 4);
          return {
            type: 'rect',
            shape: {
              x: start[0],
              y: start[1] - barHeight / 2,
              width: width,
              height: barHeight,
              r: [3, 3, 3, 3],
            },
            style: { ...api.style(), opacity: 0.35 },
            styleEmphasis: { opacity: 0.5 },
          };
        },
        data: taskData,
        encode: { x: [1, 2], y: 0 },
        z: 10,
      },
      // Progress fill overlay
      {
        type: 'custom',
        renderItem: (params, api) => {
          const catIdx = api.value(0);
          const start = api.coord([api.value(1), catIdx]);
          const end = api.coord([api.value(2), catIdx]);
          const barHeight = 18;
          const width = Math.max(end[0] - start[0], 2);
          return {
            type: 'rect',
            shape: {
              x: start[0],
              y: start[1] - barHeight / 2,
              width: width,
              height: barHeight,
              r: [3, 0, 0, 3],
            },
            style: api.style(),
          };
        },
        data: progressData,
        encode: { x: [1, 2], y: 0 },
        z: 15,
        tooltip: { show: false },
      },
      // Progress % labels
      {
        type: 'custom',
        renderItem: (params, api) => {
          if (params.dataIndex >= taskData.length) return;
          const d = taskData[params.dataIndex];
          if (!d || d.isMilestone || !d.task.progress) return;
          const catIdx = api.value(0);
          const start = api.coord([api.value(1), catIdx]);
          const end = api.coord([api.value(2), catIdx]);
          const width = end[0] - start[0];
          if (width < 30) return; // Too narrow for label
          return {
            type: 'text',
            style: {
              text: `${d.task.progress}%`,
              x: start[0] + 6,
              y: start[1],
              fill: '#fff',
              fontSize: 9,
              fontWeight: 600,
              textVerticalAlign: 'middle',
            },
          };
        },
        data: taskData,
        encode: { x: [1, 2], y: 0 },
        z: 20,
        tooltip: { show: false },
      },
    ],
    // Today marker
    graphic: [
      {
        type: 'line',
        shape: {
          // Will be positioned via convertToPixel after chart ready
        },
        style: { stroke: '#ff4d4f', lineWidth: 1.5, lineDash: [4, 3] },
        z: 100,
        invisible: true, // Positioned dynamically below
      },
    ],
  };

  ganttChart.setOption(option, true);

  // Add today marker line after chart is rendered
  try {
    const todayTs = Date.now();
    if (todayTs >= minDate && todayTs <= maxDate) {
      const todayPixel = ganttChart.convertToPixel({ xAxisIndex: 0 }, todayTs);
      const gridRect = ganttChart.getModel().getComponent('grid').coordinateSystem.getRect();
      ganttChart.setOption({
        graphic: [
          {
            type: 'group',
            children: [
              {
                type: 'line',
                shape: { x1: todayPixel, y1: gridRect.y, x2: todayPixel, y2: gridRect.y + gridRect.height },
                style: { stroke: '#ff4d4f', lineWidth: 1.5, lineDash: [4, 3] },
              },
              {
                type: 'text',
                style: {
                  text: 'Today',
                  x: todayPixel + 4,
                  y: gridRect.y - 2,
                  fill: '#ff4d4f',
                  fontSize: 9,
                  fontWeight: 600,
                  textVerticalAlign: 'bottom',
                },
              },
            ],
            z: 100,
          },
        ],
      });
    }
  } catch (e) {
    // Today marker is non-critical
  }

  // Click handler — navigate to task form
  ganttChart.on('click', (params) => {
    if (params.data && params.data.task) {
      handleEdit(params.data.task);
    }
  });

  // Resize observer
  const resizeHandler = () => ganttChart?.resize();
  window.addEventListener('resize', resizeHandler);
  ganttChart._resizeHandler = resizeHandler;
}

function zoomGantt(direction) {
  if (!ganttChart) return;
  const opt = ganttChart.getOption();
  const dz = opt.dataZoom?.[0];
  if (!dz) return;
  const currentStart = dz.start || 0;
  const currentEnd = dz.end || 100;
  const range = currentEnd - currentStart;
  const center = (currentStart + currentEnd) / 2;
  const factor = direction === 'in' ? 0.7 : 1.4;
  const newRange = Math.min(100, Math.max(5, range * factor));
  const newStart = Math.max(0, center - newRange / 2);
  const newEnd = Math.min(100, center + newRange / 2);
  ganttChart.dispatchAction({ type: 'dataZoom', dataZoomIndex: 0, start: newStart, end: newEnd });
}

function toggleExpand() {
  ganttExpanded.value = !ganttExpanded.value;
  nextTick(() => ganttChart?.resize());
}

// ===================== WATCHERS =====================

watch(selectedProjectId, async () => { await fetchSchedules(); });
watch(selectedScheduleId, () => { listPage.value = 1; fetchData(); });
watch(viewMode, () => {
  fetchData();
  if (viewMode.value === 'gantt') nextTick(() => ganttChart?.resize());
});

onMounted(async () => { await fetchProjects(); });

onBeforeUnmount(() => {
  if (ganttChart) {
    if (ganttChart._resizeHandler) window.removeEventListener('resize', ganttChart._resizeHandler);
    ganttChart.dispose();
    ganttChart = null;
  }
});
</script>

<template>
  <Page title="Task Schedule" description="Manage and visualize project tasks">
    <Card>
      <!-- Toolbar -->
      <div class="mb-4 flex flex-wrap items-center gap-2">
        <Select
          v-model:value="selectedProjectId"
          :options="projects"
          placeholder="Select Project"
          show-search
          option-filter-prop="label"
          style="width: 280px"
        />
        <Select
          v-model:value="selectedScheduleId"
          :options="schedules"
          placeholder="Select Schedule"
          show-search
          option-filter-prop="label"
          style="width: 260px"
          allow-clear
        />
        <Select
          v-if="viewMode === 'list'"
          v-model:value="statusFilter"
          :options="statusOptions"
          placeholder="All Statuses"
          allow-clear
          style="width: 140px"
          @change="handleSearch"
        />
        <Input
          v-if="viewMode === 'list'"
          v-model:value="searchText"
          placeholder="Search tasks..."
          style="width: 200px"
          allow-clear
          @press-enter="handleSearch"
        >
          <template #prefix><SearchOutlined /></template>
        </Input>

        <div class="flex-1" />

        <!-- Gantt controls -->
        <template v-if="viewMode === 'gantt'">
          <Button size="small" @click="zoomGantt('in')" title="Zoom In"><ZoomInOutlined /></Button>
          <Button size="small" @click="zoomGantt('out')" title="Zoom Out"><ZoomOutOutlined /></Button>
          <Button size="small" @click="toggleExpand" :title="ganttExpanded ? 'Collapse' : 'Expand'">
            <FullscreenOutlined v-if="!ganttExpanded" />
            <FullscreenExitOutlined v-else />
          </Button>
        </template>

        <!-- View toggle -->
        <RadioGroup v-model:value="viewMode" button-style="solid" size="small">
          <RadioButton value="list"><OrderedListOutlined /> List</RadioButton>
          <RadioButton value="gantt"><BarChartOutlined /> Gantt</RadioButton>
        </RadioGroup>

        <Button @click="fetchData"><template #icon><ReloadOutlined /></template>Refresh</Button>
        <Button type="primary" @click="handleCreate"><template #icon><PlusOutlined /></template>New Task</Button>
      </div>

      <!-- ===================== LIST VIEW ===================== -->
      <template v-if="viewMode === 'list'">
        <Table
          :columns="columns"
          :data-source="listItems"
          :loading="loading"
          row-key="id"
          size="middle"
          :pagination="{ current: listPage, pageSize: listPageSize, total: listTotal, showSizeChanger: true, showTotal: (t) => `${t} tasks` }"
          @change="onTableChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'task_type'">
              <Tag>{{ typeLabels[record.task_type] || record.task_type }}</Tag>
            </template>
            <template v-else-if="column.key === 'status'">
              <Tag :color="statusColors[record.status] || 'default'">{{ statusLabels[record.status] || record.status }}</Tag>
            </template>
            <template v-else-if="column.key === 'progress'">
              <Progress :percent="record.progress || 0" size="small" :status="record.progress >= 100 ? 'success' : 'active'" />
            </template>
            <template v-else-if="column.key === 'is_critical'">
              <Tag v-if="record.is_critical" color="red"><WarningOutlined /> Critical</Tag>
            </template>
            <template v-else-if="column.key === 'actions'">
              <Space>
                <Button type="link" size="small" @click="handleEdit(record)"><EditOutlined /></Button>
                <Popconfirm title="Delete this task?" @confirm="handleDelete(record)">
                  <Button type="link" size="small" danger><DeleteOutlined /></Button>
                </Popconfirm>
              </Space>
            </template>
          </template>
        </Table>
      </template>

      <!-- ===================== GANTT VIEW ===================== -->
      <template v-else>
        <!-- Legend -->
        <div class="mb-3 flex flex-wrap items-center gap-2">
          <span class="gantt-legend-item"><span class="gantt-legend-swatch" style="background:#bfbfbf"></span> To Do</span>
          <span class="gantt-legend-item"><span class="gantt-legend-swatch" style="background:#1890ff"></span> In Progress</span>
          <span class="gantt-legend-item"><span class="gantt-legend-swatch" style="background:#faad14"></span> In Review</span>
          <span class="gantt-legend-item"><span class="gantt-legend-swatch" style="background:#52c41a"></span> Completed</span>
          <span class="gantt-legend-item"><span class="gantt-legend-swatch" style="background:#ff4d4f"></span> Critical</span>
          <span class="gantt-legend-item"><span class="gantt-legend-diamond"></span> Milestone</span>
          <span class="gantt-legend-item" style="margin-left:12px;color:#999;font-size:11px">Scroll to pan | Ctrl+Scroll to zoom | Click bar to edit</span>
        </div>

        <Empty v-if="ganttTasks.length === 0 && !loading" description="No tasks found for this schedule." />

        <div
          v-show="ganttTasks.length > 0"
          ref="ganttChartRef"
          :style="{ width: '100%', height: ganttExpanded ? '85vh' : `${Math.max(400, ganttTasks.length * 32 + 140)}px`, transition: 'height 0.3s' }"
        />
      </template>
    </Card>
  </Page>
</template>
