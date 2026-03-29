<script setup>
import { onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import {
  AlertOutlined,
  CalendarOutlined,
  CameraOutlined,
  CloudOutlined,
  SafetyOutlined,
  SearchOutlined,
  TeamOutlined,
} from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';

import { getDashboardDailylogApi, getDailyLogsApi, getProjectsApi } from '#/api/agcm';

defineOptions({ name: 'AGCMDashboardDailylog' });

const route = useRoute();
const loading = ref(false);
const data = ref(null);
const projects = ref([]);
const logs = ref([]);
const selectedProject = ref(null);
const selectedLog = ref(null);

const weatherIcons = { 1: '☀️', 2: '☁️', 3: '🌦️', 4: '🌧️', 5: '⛈️' };
const activityColors = ['#1677ff', '#52c41a', '#fa8c16', '#f5222d', '#722ed1', '#13c2c2', '#eb2f96', '#2f54eb', '#faad14'];

async function fetchProjects() {
  try {
    const res = await getProjectsApi({ page_size: 200 });
    projects.value = (res.items || []).map(p => ({ value: p.id, label: `${p.sequence_name} - ${p.name}` }));
    if (route.query.project_id) selectedProject.value = Number(route.query.project_id);
    else if (projects.value.length) selectedProject.value = projects.value[0].value;
  } catch {}
}

async function fetchLogs() {
  if (!selectedProject.value) return;
  try {
    const res = await getDailyLogsApi({ project_id: selectedProject.value, page_size: 100 });
    logs.value = (res.items || []).map(l => ({ value: l.id, label: `${l.sequence_name} — ${l.date}` }));
    if (route.query.log_id) selectedLog.value = Number(route.query.log_id);
    else if (logs.value.length) selectedLog.value = logs.value[0].value;
  } catch {}
}

async function fetchData() {
  if (!selectedLog.value) return;
  loading.value = true;
  try {
    data.value = await getDashboardDailylogApi(selectedLog.value);
  } catch (error) {
    console.error('Failed:', error);
    message.error('Failed to load daily log analytics');
  } finally {
    loading.value = false;
  }
}

watch(selectedProject, () => { fetchLogs(); data.value = null; });
watch(selectedLog, () => { if (selectedLog.value) fetchData(); });

onMounted(async () => {
  await fetchProjects();
  if (selectedProject.value) await fetchLogs();
  if (selectedLog.value) fetchData();
});
</script>

<template>
  <div class="p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold mb-1">Daily Log Analytics</h1>
        <p class="text-gray-500 m-0">Detailed breakdown of a single day's activities</p>
      </div>
      <ASpace>
        <ASelect
          v-model:value="selectedProject"
          :options="projects"
          placeholder="Select Project"
          show-search
          :filter-option="(input, opt) => (opt?.label || '').toLowerCase().includes(input.toLowerCase())"
          style="width: 280px;"
        />
        <ASelect
          v-model:value="selectedLog"
          :options="logs"
          placeholder="Select Daily Log"
          show-search
          :filter-option="(input, opt) => (opt?.label || '').toLowerCase().includes(input.toLowerCase())"
          style="width: 240px;"
        />
      </ASpace>
    </div>

    <ASpin :spinning="loading">
      <template v-if="data">
        <!-- Log Info -->
        <ACard size="small" class="mb-4" style="border-radius: 8px; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white;">
          <div class="flex items-center justify-between">
            <div>
              <h2 style="color: white; margin: 0;">{{ data.log?.sequence_name }}</h2>
              <span style="opacity: 0.9;">{{ data.log?.date }} | {{ data.log?.project_name }}</span>
            </div>
          </div>
        </ACard>

        <!-- KPI Cards -->
        <ARow :gutter="[12, 12]" class="mb-6">
          <ACol v-for="(val, key) in data.kpis" :key="key" :xs="8" :md="4" :lg="3">
            <ACard size="small" style="border-radius: 8px; text-align: center;">
              <div style="font-size: 24px; font-weight: 700; color: #333;">{{ val }}</div>
              <div style="font-size: 11px; color: #888;">{{ key }}</div>
            </ACard>
          </ACol>
        </ARow>

        <!-- Weather Strip -->
        <ACard title="Weather Forecast" size="small" class="mb-6" style="border-radius: 8px;" v-if="data.weather_strip?.length">
          <div style="display: flex; gap: 10px; flex-wrap: wrap;">
            <div v-for="w in data.weather_strip" :key="w.time"
                 style="flex: 1; min-width: 95px; max-width: 140px; background: #f5f7fa; border-radius: 10px; padding: 14px 8px; text-align: center;">
              <div style="font-size: 10px; color: #888;">
                {{ w.time ? w.time.split('T')[1] || w.time : '' }}
              </div>
              <div style="font-size: 30px; line-height: 1.2;">{{ weatherIcons[w.weather_code] || '🌡️' }}</div>
              <div style="font-size: 20px; font-weight: 700;">{{ w.temperature || 0 }}°F</div>
              <div style="font-size: 10px; color: #555;">{{ w.label }}</div>
              <div style="font-size: 9px; color: #aaa; margin-top: 4px;">
                💧{{ w.humidity || 0 }}% &nbsp; 💨{{ w.wind || 0 }}
              </div>
            </div>
          </div>
        </ACard>

        <!-- Row: Activity Donut + Manpower by Location -->
        <ARow :gutter="16" class="mb-6">
          <ACol :span="10">
            <ACard title="Activity Distribution" size="small" style="border-radius: 8px;">
              <div style="padding: 8px 0;">
                <div v-for="(item, i) in data.activity_donut" :key="i"
                     style="display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f5f5f5;">
                  <ASpace>
                    <div :style="{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: activityColors[i % activityColors.length] }" />
                    <span style="font-size: 12px;">{{ item.name }}</span>
                  </ASpace>
                  <ATag :color="activityColors[i % activityColors.length]" style="min-width: 40px; text-align: center;">
                    {{ item.value }}
                  </ATag>
                </div>
                <AEmpty v-if="!data.activity_donut?.length" description="No activity" />
              </div>
            </ACard>
          </ACol>
          <ACol :span="14">
            <ACard title="Manpower by Location" size="small" style="border-radius: 8px;">
              <div style="padding: 8px 0;">
                <div v-for="(item, i) in data.manpower_by_location" :key="i" style="margin-bottom: 10px;">
                  <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 2px;">
                    <span>{{ item.name }}</span>
                    <strong>{{ item.value }} hrs</strong>
                  </div>
                  <AProgress
                    :percent="Math.round((item.value / Math.max(data.manpower_by_location[0]?.value || 1, 1)) * 100)"
                    :show-info="false"
                    :stroke-color="activityColors[i % activityColors.length]"
                    size="small"
                  />
                </div>
                <AEmpty v-if="!data.manpower_by_location?.length" description="No manpower" />
              </div>
            </ACard>
          </ACol>
        </ARow>

        <!-- Row: Manpower Detail + Safety + Inspections -->
        <ARow :gutter="16" class="mb-6">
          <ACol :span="14">
            <ACard title="Manpower Detail" size="small" style="border-radius: 8px;">
              <ATable
                :data-source="data.manpower_data"
                :columns="[
                  { title: 'Activity', dataIndex: 'name' },
                  { title: 'Location', dataIndex: 'location', width: 120 },
                  { title: 'Workers', dataIndex: 'workers', width: 80 },
                  { title: 'Hours', dataIndex: 'hours', width: 70 },
                  { title: 'Total', dataIndex: 'total_hours', width: 80 },
                ]"
                :pagination="false"
                size="small"
                row-key="name"
              />
            </ACard>
          </ACol>
          <ACol :span="10">
            <ACard title="Inspections" size="small" style="border-radius: 8px; margin-bottom: 16px;">
              <div v-for="(item, i) in data.inspection_chart" :key="i"
                   style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #f5f5f5;">
                <ATag :color="item.name === 'Pass' ? 'green' : item.name === 'Fail' ? 'red' : 'orange'">{{ item.name }}</ATag>
                <strong>{{ item.value }}</strong>
              </div>
              <AEmpty v-if="!data.inspection_chart?.length" description="No inspections" />
            </ACard>
            <ACard title="Safety Observations" size="small" style="border-radius: 8px;">
              <div v-for="(item, i) in data.safety_list" :key="i"
                   style="padding: 6px 0; border-bottom: 1px solid #f5f5f5; font-size: 11px;">
                <div style="font-weight: 500;">{{ item.name }}</div>
                <div style="color: #888;">{{ item.notice }}</div>
              </div>
              <AEmpty v-if="!data.safety_list?.length" description="No safety observations" />
            </ACard>
          </ACol>
        </ARow>
      </template>

      <AEmpty v-else-if="!loading && !selectedLog" description="Select a project and daily log to view analytics" />
    </ASpin>
  </div>
</template>
