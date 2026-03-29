<script setup>
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import {
  BarChartOutlined,
  BuildOutlined,
  CameraOutlined,
  CalendarOutlined,
  FileTextOutlined,
  SafetyOutlined,
  SearchOutlined,
  TeamOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';

import { getDashboardOverviewApi, getProjectsApi } from '#/api/agcm';

defineOptions({ name: 'AGCMDashboardOverview' });

const router = useRouter();
const loading = ref(false);
const data = ref(null);
const dateRange = ref([]);

async function fetchData() {
  loading.value = true;
  try {
    const params = {};
    if (dateRange.value && dateRange.value.length === 2) {
      params.date_from = dateRange.value[0];
      params.date_to = dateRange.value[1];
    }
    data.value = await getDashboardOverviewApi(params);
  } catch (error) {
    console.error('Dashboard fetch failed:', error);
    message.error('Failed to load dashboard data');
  } finally {
    loading.value = false;
  }
}

function handleDateChange(dates) {
  dateRange.value = dates || [];
  fetchData();
}

function handleExportPdf() {
  const content = document.querySelector('.dashboard-print-area');
  if (!content) return;
  const clone = content.cloneNode(true);
  const win = window.open('', '_blank');
  const doc = win.document;
  const style = doc.createElement('style');
  style.textContent = '* { box-sizing: border-box; } body { font-family: Arial, sans-serif; margin: 20px; color: #333; } @page { size: landscape; margin: 0.5in; }';
  doc.head.appendChild(style);
  const title = doc.createElement('title');
  title.textContent = 'Construction Dashboard';
  doc.head.appendChild(title);
  doc.body.appendChild(clone);
  setTimeout(() => { win.print(); }, 500);
}

const kpiConfig = [
  { key: 'total_projects', label: 'Projects', icon: 'BuildOutlined', color: '#1677ff' },
  { key: 'total_daily_logs', label: 'Daily Logs', icon: 'CalendarOutlined', color: '#52c41a' },
  { key: 'total_workers', label: 'Total Workers', icon: 'TeamOutlined', color: '#722ed1' },
  { key: 'total_manpower_hours', label: 'Man-Hours', icon: 'BarChartOutlined', color: '#fa8c16' },
  { key: 'total_safety_incidents', label: 'Safety Incidents', icon: 'SafetyOutlined', color: '#f5222d' },
  { key: 'total_inspections', label: 'Inspections', icon: 'SearchOutlined', color: '#13c2c2' },
  { key: 'total_photos', label: 'Photos', icon: 'CameraOutlined', color: '#eb2f96' },
  { key: 'total_visitors', label: 'Visitors', icon: 'FileTextOutlined', color: '#2f54eb' },
];

const iconMap = {
  BuildOutlined, CalendarOutlined, TeamOutlined, BarChartOutlined,
  SafetyOutlined, SearchOutlined, CameraOutlined, FileTextOutlined,
};

onMounted(fetchData);
</script>

<template>
  <div class="p-6">
    <ASpin :spinning="loading">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold mb-1">Construction Dashboard</h1>
          <p class="text-gray-500 m-0">Executive overview of all projects and activities</p>
        </div>
        <ASpace>
          <ARangePicker
            :value="dateRange"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="handleDateChange"
            style="width: 280px;"
          />
          <AButton @click="handleExportPdf">Export PDF</AButton>
        </ASpace>
      </div>

      <div v-if="data" class="dashboard-print-area">
        <!-- KPI Cards -->
        <ARow :gutter="[16, 16]" class="mb-6">
          <ACol v-for="kpi in kpiConfig" :key="kpi.key" :xs="12" :sm="8" :md="6" :lg="3">
            <ACard size="small" :bordered="true" style="border-radius: 8px;">
              <AStatistic
                :title="kpi.label"
                :value="data.kpis[kpi.key] || 0"
                :value-style="{ color: kpi.color, fontSize: '22px', fontWeight: 700 }"
              >
                <template #prefix>
                  <component :is="iconMap[kpi.icon]" :style="{ color: kpi.color }" />
                </template>
              </AStatistic>
            </ACard>
          </ACol>
        </ARow>

        <!-- Row 1: Project Status + Weather Avg + Manpower by Project -->
        <ARow :gutter="16" class="mb-6">
          <ACol :span="8">
            <ACard title="Project Status" size="small" style="border-radius: 8px; margin-bottom: 16px;">
              <div style="display: flex; align-items: center; justify-content: center; padding: 12px 0;">
                <AProgress
                  v-for="(item, i) in data.project_status_chart"
                  :key="i"
                  type="circle"
                  :percent="Math.round((item.value / Math.max(data.kpis.total_projects, 1)) * 100)"
                  :width="80"
                  :stroke-color="['#1677ff', '#fa8c16', '#52c41a'][i] || '#ccc'"
                  style="margin: 0 8px;"
                >
                  <template #format>
                    <div style="text-align: center;">
                      <div style="font-size: 16px; font-weight: bold;">{{ item.value }}</div>
                      <div style="font-size: 9px; color: #888;">{{ item.name }}</div>
                    </div>
                  </template>
                </AProgress>
              </div>
            </ACard>
            <ACard title="Weather Avg" size="small" style="border-radius: 8px;" v-if="data.weather_summary?.avg_temperature">
              <div style="display: flex; align-items: center; justify-content: space-around; padding: 8px 0;">
                <div style="text-align: center;">
                  <div style="font-size: 28px;">🌡️</div>
                  <div style="font-size: 22px; font-weight: 700; color: #fa8c16;">
                    {{ data.weather_summary.avg_temperature }}°F
                  </div>
                  <div style="font-size: 10px; color: #888;">Avg Temp</div>
                </div>
                <div style="text-align: center;">
                  <div style="font-size: 28px;">💧</div>
                  <div style="font-size: 22px; font-weight: 700; color: #1890ff;">
                    {{ data.weather_summary.avg_humidity }}%
                  </div>
                  <div style="font-size: 10px; color: #888;">Humidity</div>
                </div>
                <div style="text-align: center;">
                  <div style="font-size: 28px;">💨</div>
                  <div style="font-size: 22px; font-weight: 700; color: #52c41a;">
                    {{ data.weather_summary.avg_wind }}
                  </div>
                  <div style="font-size: 10px; color: #888;">Wind mph</div>
                </div>
              </div>
            </ACard>
          </ACol>
          <ACol :span="16">
            <ACard title="Manpower Hours by Project" size="small" style="border-radius: 8px;">
              <div style="padding: 12px 0;">
                <div v-for="(item, i) in data.manpower_by_project" :key="i" style="margin-bottom: 10px;">
                  <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 2px;">
                    <span>{{ item.name }}</span>
                    <strong>{{ item.value.toLocaleString() }} hrs</strong>
                  </div>
                  <AProgress
                    :percent="Math.round((item.value / Math.max(data.manpower_by_project[0]?.value || 1, 1)) * 100)"
                    :show-info="false"
                    :stroke-color="['#1677ff','#52c41a','#fa8c16','#722ed1','#13c2c2','#eb2f96','#f5222d','#2f54eb','#faad14','#a0d911'][i] || '#1677ff'"
                    size="small"
                  />
                </div>
              </div>
            </ACard>
          </ACol>
        </ARow>

        <!-- Row 2: Safety Trend + Activity Distribution -->
        <ARow :gutter="16" class="mb-6">
          <ACol :span="14">
            <ACard title="Safety Incidents Trend" size="small" style="border-radius: 8px;">
              <ATable
                :data-source="(data.safety_trend?.categories || []).map((cat, i) => ({
                  key: i,
                  month: cat,
                  accidents: data.safety_trend.series[0]?.data[i] || 0,
                  violations: data.safety_trend.series[1]?.data[i] || 0,
                  total: (data.safety_trend.series[0]?.data[i] || 0) + (data.safety_trend.series[1]?.data[i] || 0),
                }))"
                :columns="[
                  { title: 'Month', dataIndex: 'month', width: 80 },
                  { title: 'Accidents', dataIndex: 'accidents', width: 100 },
                  { title: 'Violations', dataIndex: 'violations', width: 100 },
                  { title: 'Total', dataIndex: 'total', width: 80 },
                ]"
                :pagination="false"
                size="small"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.dataIndex === 'accidents'">
                    <ATag :color="record.accidents > 0 ? 'red' : 'default'">{{ record.accidents }}</ATag>
                  </template>
                  <template v-else-if="column.dataIndex === 'violations'">
                    <ATag :color="record.violations > 0 ? 'orange' : 'default'">{{ record.violations }}</ATag>
                  </template>
                  <template v-else-if="column.dataIndex === 'total'">
                    <strong>{{ record.total }}</strong>
                  </template>
                </template>
              </ATable>
            </ACard>
          </ACol>
          <ACol :span="10">
            <ACard title="Activity Distribution" size="small" style="border-radius: 8px;">
              <div style="padding: 8px 0;">
                <div v-for="(item, i) in data.activity_by_type" :key="i"
                     style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #f5f5f5;">
                  <ASpace>
                    <div :style="{
                      width: '10px', height: '10px', borderRadius: '50%',
                      backgroundColor: ['#1677ff','#52c41a','#13c2c2','#2f54eb','#f5222d','#fa8c16','#722ed1','#eb2f96','#faad14'][i]
                    }" />
                    <span style="font-size: 12px;">{{ item.name }}</span>
                  </ASpace>
                  <strong style="font-size: 12px;">{{ item.value.toLocaleString() }}</strong>
                </div>
              </div>
            </ACard>
          </ACol>
        </ARow>

        <!-- Row 3: Recent Logs (full width) -->
        <ARow :gutter="16">
          <ACol :span="24">
            <ACard title="Recent Daily Logs" size="small" style="border-radius: 8px;">
              <ATable
                :data-source="data.recent_logs"
                :columns="[
                  { title: 'Seq #', dataIndex: 'sequence_name', width: 100 },
                  { title: 'Date', dataIndex: 'date', width: 110 },
                  { title: 'Project', dataIndex: 'project_name' },
                ]"
                :pagination="false"
                size="small"
                :row-class-name="() => 'cursor-pointer'"
                :custom-row="(record) => ({ onClick: () => router.push(`/agcm/daily-logs/detail/${record.id}`) })"
              />
            </ACard>
          </ACol>
        </ARow>
      </div>
    </ASpin>
  </div>
</template>
