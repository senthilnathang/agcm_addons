<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  ArrowLeftOutlined,
  CalendarOutlined,
  EditOutlined,
  EnvironmentOutlined,
  FileTextOutlined,
  PlusOutlined,
  TeamOutlined,
} from '@ant-design/icons-vue';

import { getProjectApi } from '#/api/agcm';

defineOptions({ name: 'AGCMProjectDetail' });

const route = useRoute();
const router = useRouter();
const projectId = computed(() => route.params.id);

const loading = ref(false);
const project = ref(null);
const activeTab = ref('details');

function getAccessToken() {
  try {
    return localStorage?.getItem('accessToken') || '';
  } catch {
    return '';
  }
}

const statusColors = {
  new: 'blue',
  inprogress: 'orange',
  completed: 'green',
};

async function fetchProject() {
  if (!projectId.value) return;
  loading.value = true;
  try {
    project.value = await getProjectApi(projectId.value);
    if (project.value?.name) {
      window.dispatchEvent(new CustomEvent('fastvue:set-record-name', { detail: { name: project.value.name } }));
    }
  } catch (error) {
    console.error('Failed to load project:', error);
  } finally {
    loading.value = false;
  }
}

function handleEdit() {
  router.push(`/agcm/projects/form/${projectId.value}`);
}

function handleBack() {
  router.push('/agcm/projects');
}

function handleViewLogs() {
  router.push(`/agcm/daily-logs?project_id=${projectId.value}`);
}

function handleNewLog() {
  router.push(`/agcm/daily-logs/form?project_id=${projectId.value}`);
}

onMounted(fetchProject);
</script>

<template>
  <div class="p-6">
<ASpin :spinning="loading">
      <!-- Teleport actions into ModuleView toolbar -->
      <Teleport to="#fv-toolbar-actions" v-if="project">
        <AButton size="small" @click="handleEdit"><EditOutlined /> Edit</AButton>
        <AButton size="small" type="primary" @click="handleNewLog"><PlusOutlined /> New Daily Log</AButton>
      </Teleport>

      <template v-if="project">
        <!-- Title Card -->
        <ACard class="mb-4">
          <div class="flex items-start justify-between">
            <div>
              <h1 class="text-2xl font-bold mb-1">
                {{ project.name }}
              </h1>
              <p class="text-gray-500 mb-2">
                {{ project.sequence_name }} | {{ project.ref_number }}
              </p>
              <ASpace wrap>
                <ATag :color="statusColors[project.status] || 'default'">
                  {{ project.status === 'inprogress' ? 'In Progress' : (project.status || '').replace(/^\w/, c => c.toUpperCase()) }}
                </ATag>
                <ATag v-if="project.agcm_office" color="purple">
                  {{ (project.agcm_office || '').replace(/^\w/, c => c.toUpperCase()) }} Office
                </ATag>
              </ASpace>
            </div>
            <div class="text-right">
              <div class="text-3xl font-bold text-blue-600">{{ project.daily_log_count || 0 }}</div>
              <div class="text-gray-500 text-sm">Daily Logs</div>
            </div>
          </div>
        </ACard>

        <!-- Stats Row -->
        <ARow :gutter="16" class="mb-4">
          <ACol :span="6">
            <ACard size="small">
              <AStatistic title="Start Date" :value="project.start_date || '-'">
                <template #prefix><CalendarOutlined /></template>
              </AStatistic>
            </ACard>
          </ACol>
          <ACol :span="6">
            <ACard size="small">
              <AStatistic title="End Date" :value="project.end_date || '-'">
                <template #prefix><CalendarOutlined /></template>
              </AStatistic>
            </ACard>
          </ACol>
          <ACol :span="6">
            <ACard size="small">
              <AStatistic title="Team Members" :value="(project.user_ids || []).length">
                <template #prefix><TeamOutlined /></template>
              </AStatistic>
            </ACard>
          </ACol>
          <ACol :span="6">
            <ACard size="small">
              <AStatistic title="Contractors" :value="(project.partner_ids || []).length">
                <template #prefix><TeamOutlined /></template>
              </AStatistic>
            </ACard>
          </ACol>
        </ARow>

        <!-- Location -->
        <ACard title="Location" class="mb-4">
          <ADescriptions :column="3" bordered size="small">
            <ADescriptionsItem label="Street">{{ project.street || '-' }}</ADescriptionsItem>
            <ADescriptionsItem label="City">{{ project.city || '-' }}</ADescriptionsItem>
            <ADescriptionsItem label="State">{{ project.state || '-' }}</ADescriptionsItem>
            <ADescriptionsItem label="ZIP">{{ project.zip || '-' }}</ADescriptionsItem>
            <ADescriptionsItem label="Country">{{ project.country || '-' }}</ADescriptionsItem>
            <ADescriptionsItem label="Coordinates">
              <template v-if="project.project_latitude && project.project_longitude">
                <EnvironmentOutlined class="mr-1" />
                {{ project.project_latitude?.toFixed(4) }}, {{ project.project_longitude?.toFixed(4) }}
              </template>
              <span v-else>-</span>
            </ADescriptionsItem>
          </ADescriptions>
        </ACard>

        <!-- Daily Logs Link -->
        <ACard title="Daily Activity Logs">
          <div class="flex items-center justify-between">
            <p class="text-gray-500">
              <FileTextOutlined class="mr-1" />
              {{ project.daily_log_count || 0 }} daily logs recorded for this project
            </p>
            <AButton type="primary" ghost @click="handleViewLogs">
              View All Logs
            </AButton>
          </div>
        </ACard>

        <!-- Activity Tab -->
        <ACard class="mt-4">
          <ATabs v-model:activeKey="activeTab">
            <ATabs.TabPane key="details" tab="Details">
              <!-- Details content is above -->
            </ATabs.TabPane>
            <ATabs.TabPane key="activity" tab="Activity">
              <ActivityThread
                :model-name="'agcm_projects'"
                :record-id="projectId"
                :access-token="getAccessToken()"
                :api-base="'/api/v1'"
                :show-messages="true"
                :show-activities="true"
              />
            </ATabs.TabPane>
          </ATabs>
        </ACard>
      </template>

      <AEmpty v-else-if="!loading" description="Project not found" />
    </ASpin>
  </div>
</template>
