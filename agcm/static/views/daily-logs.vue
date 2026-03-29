<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  DatePicker,
  Input,
  message,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
} from 'ant-design-vue';
import {
  CopyOutlined,
  DeleteOutlined,
  EyeOutlined,
  FilePdfOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
} from '@ant-design/icons-vue';

import { deleteDailyLogApi, getDailyLogsApi, getProjectsApi, exportDailyLogHtmlUrl } from '#/api/agcm';

defineOptions({ name: 'AGCMDailyLogs' });

const route = useRoute();
const router = useRouter();

const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  pageSizeOptions: ['10', '20', '50', '100'],
  showTotal: (total: number) => `Total ${total} logs`,
});

const loading = ref(false);
const items = ref<any[]>([]);
const projectFilter = ref<number | null>(Number(route.query.project_id) || null);
const projects = ref<any[]>([]);

const columns = computed(() => [
  { title: 'Seq #', dataIndex: 'sequence_name', key: 'sequence_name', width: 120 },
  { title: 'Date', dataIndex: 'date', key: 'date', width: 120, sorter: true },
  { title: 'Project', key: 'project_id', width: 200 },
  { title: 'Copied From', key: 'copy_id', width: 120 },
  { title: 'Created', dataIndex: 'created_at', key: 'created_at', width: 150 },
  { title: 'Actions', key: 'actions', width: 180, fixed: 'right' as const },
]);

async function fetchProjects() {
  try {
    const data = await getProjectsApi({ page_size: 200 });
    projects.value = (data.items || []).map((p: any) => ({
      value: p.id,
      label: `${p.sequence_name || ''} - ${p.name}`,
    }));
  } catch {}
}

async function fetchData() {
  loading.value = true;
  try {
    const params: any = {
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
      project_id: projectFilter.value || undefined,
    };
    const response = await getDailyLogsApi(params);
    items.value = response.items || [];
    pagination.value.total = response.total || 0;
  } catch (error) {
    console.error('Failed to fetch daily logs:', error);
    message.error('Failed to load daily logs');
  } finally {
    loading.value = false;
  }
}

function onTableChange(pag: any) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

function handleFilterChange() {
  pagination.value.current = 1;
  fetchData();
}

function handleCreate() {
  const query = projectFilter.value ? `?project_id=${projectFilter.value}` : '';
  router.push(`/agcm/daily-logs/form${query}`);
}

function handleView(record: any) {
  router.push(`/agcm/daily-logs/detail/${record.id}`);
}

function handleCopy(record: any) {
  router.push(`/agcm/daily-logs/copy/${record.id}`);
}

async function handleDelete(record: any) {
  try {
    await deleteDailyLogApi(record.id);
    message.success('Daily log deleted');
    fetchData();
  } catch (error) {
    console.error('Failed to delete:', error);
    message.error('Failed to delete daily log');
  }
}

function handleExportPdf(record: any) {
  const url = exportDailyLogHtmlUrl(record.id);
  window.open(url, '_blank');
}

function getProjectName(projectId: number) {
  const p = projects.value.find((x: any) => x.value === projectId);
  return p ? p.label : `#${projectId}`;
}

onMounted(() => {
  fetchProjects();
  fetchData();
});
</script>

<template>
  <Page title="Daily Activity Logs" description="Daily construction activity records">
    <Card>
      <!-- Toolbar -->
      <div class="mb-4 flex items-center justify-between">
        <Space>
          <Select
            v-model:value="projectFilter"
            :options="projects"
            placeholder="All Projects"
            allow-clear
            show-search
            :filter-option="(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
            style="width: 300px"
            @change="handleFilterChange"
          />
        </Space>
        <Space>
          <Button @click="fetchData">
            <template #icon><ReloadOutlined /></template>
            Refresh
          </Button>
          <Button type="primary" @click="handleCreate">
            <template #icon><PlusOutlined /></template>
            New Daily Log
          </Button>
        </Space>
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
          <template v-if="column.key === 'project_id'">
            {{ getProjectName(record.project_id) }}
          </template>
          <template v-else-if="column.key === 'copy_id'">
            <Tag v-if="record.copy_id" color="blue">Copied</Tag>
            <span v-else>-</span>
          </template>
          <template v-else-if="column.key === 'created_at'">
            {{ record.created_at ? new Date(record.created_at).toLocaleDateString() : '-' }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="handleView(record)">
                <template #icon><EyeOutlined /></template>
              </Button>
              <Button type="link" size="small" @click="handleExportPdf(record)" title="Export PDF">
                <template #icon><FilePdfOutlined /></template>
              </Button>
              <Button type="link" size="small" @click="handleCopy(record)">
                <template #icon><CopyOutlined /></template>
              </Button>
              <Popconfirm
                title="Delete this daily log and all its entries?"
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
