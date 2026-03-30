<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Input,
  message,
  Popconfirm,
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
} from '@ant-design/icons-vue';

import { getProjectsApi } from '#/api/agcm';
import { deleteIssueApi, getIssuesApi } from '#/api/agcm_progress';

defineOptions({ name: 'AGCMProgressIssues' });

const router = useRouter();

const loading = ref(false);
const items = ref<any[]>([]);
const projects = ref<any[]>([]);
const selectedProjectId = ref<number | null>(null);
const statusFilter = ref<string | null>(null);
const severityFilter = ref<string | null>(null);
const priorityFilter = ref<string | null>(null);
const searchText = ref('');

const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `Total ${total} issues`,
});

const severityColors: Record<string, string> = {
  critical: 'red',
  major: 'orange',
  minor: 'blue',
  trivial: 'default',
};

const statusColors: Record<string, string> = {
  open: 'blue',
  in_progress: 'processing',
  resolved: 'green',
  closed: 'default',
};

const priorityColors: Record<string, string> = {
  high: 'red',
  medium: 'orange',
  low: 'default',
};

const statusOptions = [
  { value: 'open', label: 'Open' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'closed', label: 'Closed' },
];

const severityOptions = [
  { value: 'critical', label: 'Critical' },
  { value: 'major', label: 'Major' },
  { value: 'minor', label: 'Minor' },
  { value: 'trivial', label: 'Trivial' },
];

const priorityOptions = [
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
];

const columns = computed(() => [
  { title: 'Seq #', dataIndex: 'sequence_name', key: 'sequence_name', width: 110 },
  { title: 'Title', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: 'Severity', key: 'severity', width: 100 },
  { title: 'Status', key: 'status', width: 110 },
  { title: 'Priority', key: 'priority', width: 100 },
  { title: 'Location', dataIndex: 'location', key: 'location', width: 150, ellipsis: true },
  { title: 'Due Date', dataIndex: 'due_date', key: 'due_date', width: 120 },
  { title: 'Assigned To', dataIndex: 'assigned_to', key: 'assigned_to', width: 110 },
  { title: 'Actions', key: 'actions', width: 120, fixed: 'right' as const },
]);

async function loadProjects() {
  try {
    const res = await getProjectsApi({ page: 1, page_size: 200 });
    projects.value = res.items || [];
    if (projects.value.length > 0 && !selectedProjectId.value) {
      selectedProjectId.value = projects.value[0].id;
    }
  } catch (e: any) {
    message.error('Failed to load projects');
  }
}

async function fetchData() {
  if (!selectedProjectId.value) return;
  loading.value = true;
  try {
    const params: any = {
      project_id: selectedProjectId.value,
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
    };
    if (statusFilter.value) params.status = statusFilter.value;
    if (severityFilter.value) params.severity = severityFilter.value;
    if (priorityFilter.value) params.priority = priorityFilter.value;
    if (searchText.value) params.search = searchText.value;

    const res = await getIssuesApi(params);
    items.value = res.items || [];
    pagination.value.total = res.total || 0;
  } catch (e: any) {
    message.error('Failed to load issues');
  } finally {
    loading.value = false;
  }
}

function onProjectChange(val: number) {
  selectedProjectId.value = val;
  pagination.value.current = 1;
  fetchData();
}

function onFilterChange() {
  pagination.value.current = 1;
  fetchData();
}

function handleTableChange(pag: any) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

function navigateToForm(id?: number) {
  const query: any = { project_id: selectedProjectId.value };
  if (id) query.id = id;
  router.push({ path: '/agcm/issues/form', query });
}

async function handleDelete(id: number) {
  try {
    await deleteIssueApi(id);
    message.success('Issue deleted');
    fetchData();
  } catch (e: any) {
    message.error('Failed to delete');
  }
}

onMounted(async () => {
  await loadProjects();
  if (selectedProjectId.value) fetchData();
});
</script>

<template>
  <Page title="Issues" description="Track and manage project issues">
    <Card>
      <div style="display: flex; justify-content: space-between; margin-bottom: 16px; flex-wrap: wrap; gap: 8px;">
        <Space wrap>
          <Select
            v-model:value="selectedProjectId"
            style="width: 250px"
            placeholder="Select Project"
            show-search
            option-filter-prop="label"
            :options="projects.map(p => ({ value: p.id, label: p.name }))"
            @change="onProjectChange"
          />
          <Select
            v-model:value="statusFilter"
            style="width: 140px"
            placeholder="Status"
            allow-clear
            :options="statusOptions"
            @change="onFilterChange"
          />
          <Select
            v-model:value="severityFilter"
            style="width: 140px"
            placeholder="Severity"
            allow-clear
            :options="severityOptions"
            @change="onFilterChange"
          />
          <Select
            v-model:value="priorityFilter"
            style="width: 140px"
            placeholder="Priority"
            allow-clear
            :options="priorityOptions"
            @change="onFilterChange"
          />
          <Input
            v-model:value="searchText"
            placeholder="Search..."
            style="width: 180px"
            allow-clear
            @pressEnter="onFilterChange"
          >
            <template #prefix><SearchOutlined /></template>
          </Input>
          <Button @click="fetchData">
            <template #icon><ReloadOutlined /></template>
          </Button>
        </Space>
        <Button type="primary" @click="navigateToForm()" :disabled="!selectedProjectId">
          <template #icon><PlusOutlined /></template>
          New Issue
        </Button>
      </div>

      <Table
        :columns="columns"
        :data-source="items"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        size="middle"
        :scroll="{ x: 1000 }"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'severity'">
            <Tag :color="severityColors[record.severity] || 'default'">
              {{ record.severity }}
            </Tag>
          </template>
          <template v-if="column.key === 'status'">
            <Tag :color="statusColors[record.status] || 'default'">
              {{ (record.status || '').replace('_', ' ') }}
            </Tag>
          </template>
          <template v-if="column.key === 'priority'">
            <Tag :color="priorityColors[record.priority] || 'default'">
              {{ record.priority }}
            </Tag>
          </template>
          <template v-if="column.key === 'actions'">
            <Space>
              <Button size="small" @click="navigateToForm(record.id)">
                <template #icon><EditOutlined /></template>
              </Button>
              <Popconfirm title="Delete this issue?" @confirm="handleDelete(record.id)">
                <Button size="small" danger>
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
