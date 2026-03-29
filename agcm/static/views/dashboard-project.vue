<script setup>
import { onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  BarChartOutlined,
  CalendarOutlined,
  CameraOutlined,
  SafetyOutlined,
  SearchOutlined,
  TeamOutlined,
} from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';

import { getDashboardProjectApi, getProjectsApi } from '#/api/agcm';

defineOptions({ name: 'AGCMDashboardProject' });

const route = useRoute();
const router = useRouter();
const loading = ref(false);
const data = ref(null);
const projects = ref([]);
const selectedProject = ref(null);
const dateRange = ref([]);

async function fetchProjects() {
  try {
    const res = await getProjectsApi({ page_size: 200 });
    projects.value = (res.items || []).map(p => ({ value: p.id, label: `${p.sequence_name} - ${p.name}` }));
    if (route.query.project_id) {
      selectedProject.value = Number(route.query.project_id);
    } else if (projects.value.length > 0) {
      selectedProject.value = projects.value[0].value;
    }
  } catch {}
}

async function fetchData() {
  if (!selectedProject.value) return;
  loading.value = true;
  try {
    const params = {};
    if (dateRange.value?.length === 2) {
      params.date_from = dateRange.value[0];
      params.date_to = dateRange.value[1];
    }
    data.value = await getDashboardProjectApi(selectedProject.value, params);
  } catch (error) {
    console.error('Failed:', error);
    message.error('Failed to load project analytics');
  } finally {
    loading.value = false;
  }
}

watch(selectedProject, () => { if (selectedProject.value) fetchData(); });

const funnelColors = ['#faad14', '#fa8c16', '#f5222d', '#a61d24'];

onMounted(async () => {
  await fetchProjects();
  if (selectedProject.value) fetchData();
});
</script>

<template>
  <div class="p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold mb-1">Project Analytics</h1>
        <p class="text-gray-500 m-0">Deep-dive analytics for a single project</p>
      </div>
      <ASpace>
        <ASelect
          v-model:value="selectedProject"
          :options="projects"
          placeholder="Select Project"
          show-search
          :filter-option="(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
          style="width: 320px;"
        />
        <ARangePicker
          :value="dateRange"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          @change="(d) => { dateRange = d || []; fetchData(); }"
          style="width: 260px;"
        />
      </ASpace>
    </div>

    <ASpin :spinning="loading">
      <template v-if="data">
        <!-- Project Info Banner -->
        <ACard size="small" class="mb-4" style="border-radius: 8px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
          <div class="flex items-center justify-between">
            <div>
              <h2 style="color: white; margin: 0;">{{ data.project?.name }}</h2>
              <span style="opacity: 0.8;">{{ data.project?.ref_number }} | {{ data.project?.city }}, {{ data.project?.state }}</span>
            </div>
            <ATag :color="data.project?.status === 'inprogress' ? 'orange' : data.project?.status === 'completed' ? 'green' : 'blue'" style="font-size: 14px; padding: 4px 16px;">
              {{ data.project?.status === 'inprogress' ? 'In Progress' : (data.project?.status || '').replace(/^\w/, c => c.toUpperCase()) }}
            </ATag>
          </div>
        </ACard>

        <!-- KPI Cards -->
        <ARow :gutter="[16, 16]" class="mb-6">
          <ACol :span="4">
            <ACard size="small" style="border-radius: 8px;">
              <AStatistic title="Daily Logs" :value="data.kpis.total_logs" :value-style="{ color: '#52c41a', fontWeight: 700 }">
                <template #prefix><CalendarOutlined /></template>
              </AStatistic>
            </ACard>
          </ACol>
          <ACol :span="4">
            <ACard size="small" style="border-radius: 8px;">
              <AStatistic title="Man-Hours" :value="data.kpis.total_manpower_hours" :value-style="{ color: '#fa8c16', fontWeight: 700 }">
                <template #prefix><BarChartOutlined /></template>
              </AStatistic>
            </ACard>
          </ACol>
          <ACol :span="4">
            <ACard size="small" style="border-radius: 8px;">
              <AStatistic title="Avg Workers/Day" :value="data.kpis.avg_workers_per_day" :value-style="{ color: '#722ed1', fontWeight: 700 }">
                <template #prefix><TeamOutlined /></template>
              </AStatistic>
            </ACard>
          </ACol>
          <ACol :span="4">
            <ACard size="small" style="border-radius: 8px;">
              <AStatistic title="Safety Incidents" :value="data.kpis.safety_incidents" :value-style="{ color: '#f5222d', fontWeight: 700 }">
                <template #prefix><SafetyOutlined /></template>
              </AStatistic>
            </ACard>
          </ACol>
          <ACol :span="4">
            <ACard size="small" style="border-radius: 8px;">
              <AStatistic title="Inspections" :value="data.kpis.inspections" :value-style="{ color: '#13c2c2', fontWeight: 700 }">
                <template #prefix><SearchOutlined /></template>
              </AStatistic>
            </ACard>
          </ACol>
          <ACol :span="4">
            <ACard size="small" style="border-radius: 8px;">
              <AStatistic title="Photos" :value="data.kpis.photos" :value-style="{ color: '#eb2f96', fontWeight: 700 }">
                <template #prefix><CameraOutlined /></template>
              </AStatistic>
            </ACard>
          </ACol>
        </ARow>

        <!-- Row 2: Manpower Weekly + Inspection Results -->
        <ARow :gutter="16" class="mb-6">
          <ACol :span="14">
            <ACard title="Manpower Hours by Week" size="small" style="border-radius: 8px;">
              <div style="padding: 8px 0;">
                <div v-for="(item, i) in data.manpower_weekly" :key="i" style="margin-bottom: 8px;">
                  <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 2px;">
                    <span>{{ item.name }}</span>
                    <strong>{{ item.value.toLocaleString() }} hrs</strong>
                  </div>
                  <AProgress
                    :percent="Math.round((item.value / Math.max(data.manpower_weekly[0]?.value || 1, 1)) * 100)"
                    :show-info="false"
                    :stroke-color="['#1677ff','#52c41a','#fa8c16','#722ed1','#13c2c2','#eb2f96'][i % 6]"
                    size="small"
                  />
                </div>
                <AEmpty v-if="!data.manpower_weekly?.length" description="No manpower data" />
              </div>
            </ACard>
          </ACol>
          <ACol :span="10">
            <ACard title="Inspection Results" size="small" style="border-radius: 8px; margin-bottom: 16px;">
              <div style="padding: 12px 0;">
                <div v-for="(item, i) in data.inspection_results" :key="i"
                     style="display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f5f5f5;">
                  <ASpace>
                    <ATag :color="item.name === 'Pass' ? 'green' : item.name === 'Fail' ? 'red' : 'orange'">
                      {{ item.name }}
                    </ATag>
                  </ASpace>
                  <strong>{{ item.value }}</strong>
                </div>
                <AEmpty v-if="!data.inspection_results?.length" description="No inspections" />
              </div>
            </ACard>
            <ACard title="Weather Summary" size="small" style="border-radius: 8px;">
              <div v-if="data.weather_summary?.avg_temperature" style="display: flex; align-items: center; justify-content: space-around; padding: 10px 0;">
                <div style="text-align: center;">
                  <div style="font-size: 28px;">🌡️</div>
                  <div style="font-size: 22px; font-weight: 700; color: #fa8c16;">{{ data.weather_summary.avg_temperature }}°F</div>
                  <div style="font-size: 10px; color: #888;">Avg Temp</div>
                </div>
                <div style="text-align: center;">
                  <div style="font-size: 28px;">💧</div>
                  <div style="font-size: 22px; font-weight: 700; color: #1890ff;">{{ data.weather_summary.avg_humidity }}%</div>
                  <div style="font-size: 10px; color: #888;">Humidity</div>
                </div>
                <div style="text-align: center;">
                  <div style="font-size: 28px;">🌧️</div>
                  <div style="font-size: 22px; font-weight: 700; color: #722ed1;">{{ data.weather_summary.rainy_readings }}</div>
                  <div style="font-size: 10px; color: #888;">Rainy</div>
                </div>
              </div>
              <AEmpty v-else description="No weather data" />
            </ACard>
          </ACol>
        </ARow>

        <!-- Row 3: Severity Funnel (full width) -->
        <ARow :gutter="16">
          <ACol :span="24">
            <ACard title="Issue Severity Funnel" size="small" style="border-radius: 8px;">
              <div style="padding: 16px 0;">
                <div v-for="(item, i) in data.severity_funnel" :key="i" style="margin-bottom: 6px;">
                  <div style="display: flex; align-items: center;">
                    <div :style="{
                      width: Math.max(10, (item.value / Math.max(data.severity_funnel[0]?.value || 1, 1)) * 100) + '%',
                      height: '36px',
                      backgroundColor: funnelColors[i],
                      borderRadius: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      paddingLeft: '12px',
                      color: 'white',
                      fontSize: '12px',
                      fontWeight: 600,
                      transition: 'width 0.5s ease',
                    }">
                      {{ item.name }}: {{ item.value }}
                    </div>
                  </div>
                </div>
              </div>
            </ACard>
          </ACol>
        </ARow>
      </template>
    </ASpin>
  </div>
</template>
