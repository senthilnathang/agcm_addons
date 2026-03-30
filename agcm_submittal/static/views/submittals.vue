<script setup>
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
  EyeOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMSubmittals' });

const router = useRouter();
const BASE = '/agcm_submittal';

const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  pageSizeOptions: ['10', '20', '50', '100'],
  showTotal: (total) => `Total ${total} submittals`,
});

const loading = ref(false);
const items = ref([]);
const searchText = ref('');
const statusFilter = ref(null);
const priorityFilter = ref(null);
const projectFilter = ref(null);
const projects = ref([]);

const statusOptions = [
  { value: 'draft', label: 'Draft' },
  { value: 'pending_review', label: 'Pending Review' },
  { value: 'in_review', label: 'In Review' },
  { value: 'approved', label: 'Approved' },
  { value: 'approved_with_comments', label: 'Approved w/ Comments' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'resubmitted', label: 'Resubmitted' },
];

const priorityOptions = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'urgent', label: 'Urgent' },
];

const statusColors = {
  draft: 'default',
  pending_review: 'processing',
  in_review: 'processing',
  approved: 'success',
  approved_with_comments: 'warning',
  rejected: 'error',
  resubmitted: 'cyan',
};

const statusLabels = {
  draft: 'Draft',
  pending_review: 'Pending Review',
  in_review: 'In Review',
  approved: 'Approved',
  approved_with_comments: 'Approved w/ Comments',
  rejected: 'Rejected',
  resubmitted: 'Resubmitted',
};

const priorityColors = {
  low: 'green',
  medium: 'blue',
  high: 'orange',
  urgent: 'red',
};

const columns = computed(() => [
  { title: 'Seq #', dataIndex: 'sequence_name', key: 'sequence_name', width: 120 },
  { title: 'Title', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: 'Package', dataIndex: 'package_name', key: 'package_name', width: 150 },
  { title: 'Type', dataIndex: 'type_name', key: 'type_name', width: 130 },
  { title: 'Status', key: 'status', width: 160 },
  { title: 'Priority', key: 'priority', width: 100 },
  { title: 'Rev', dataIndex: 'revision', key: 'revision', width: 60, align: 'center' },
  { title: 'Due Date', dataIndex: 'due_date', key: 'due_date', width: 120 },
  { title: 'Actions', key: 'actions', width: 150, fixed: 'right' },
]);

async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = (data.items || data || []).map((p) => ({
      value: p.id,
      label: p.name,
    }));
  } catch {}
}

async function fetchData() {
  loading.value = true;
  try {
    const params = {
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
      search: searchText.value || undefined,
      status: statusFilter.value || undefined,
      priority: priorityFilter.value || undefined,
      project_id: projectFilter.value || undefined,
    };
    const response = await requestClient.get(`${BASE}/submittals`, { params });
    items.value = response.items || [];
    pagination.value.total = response.total || 0;
  } catch (error) {
    console.error('Failed to fetch submittals:', error);
    message.error('Failed to load submittals');
  } finally {
    loading.value = false;
  }
}

function onTableChange(pag) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

function handleSearch() {
  pagination.value.current = 1;
  fetchData();
}

function handleCreate() {
  router.push('/agcm/submittals/form');
}

function handleEdit(record) {
  router.push(`/agcm/submittals/form/${record.id}`);
}

function handleView(record) {
  router.push(`/agcm/submittals/detail/${record.id}`);
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/submittals/${record.id}`);
    message.success('Submittal deleted');
    fetchData();
  } catch {
    message.error('Failed to delete submittal');
  }
}

onMounted(() => {
  fetchProjects();
  fetchData();
});
</script>

<template>
  <Page title="Submittals" description="Manage construction submittals">
    <Card>
      <!-- Toolbar -->
      <div class="mb-4 flex items-center justify-between">
        <Space wrap>
          <Select
            v-model:value="projectFilter"
            :options="projects"
            placeholder="All Projects"
            allow-clear
            show-search
            :filter-option="(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
            style="width: 200px"
            @change="handleSearch"
          />
          <Input
            v-model:value="searchText"
            placeholder="Search submittals..."
            style="width: 220px"
            @press-enter="handleSearch"
          >
            <template #prefix>
              <SearchOutlined />
            </template>
          </Input>
          <Button @click="handleSearch">Search</Button>
          <Select
            v-model:value="statusFilter"
            :options="statusOptions"
            placeholder="All Statuses"
            allow-clear
            style="width: 170px"
            @change="handleSearch"
          />
          <Select
            v-model:value="priorityFilter"
            :options="priorityOptions"
            placeholder="All Priorities"
            allow-clear
            style="width: 140px"
            @change="handleSearch"
          />
        </Space>
        <Space>
          <Button @click="fetchData">
            <template #icon><ReloadOutlined /></template>
            Refresh
          </Button>
          <Button type="primary" @click="handleCreate">
            <template #icon><PlusOutlined /></template>
            New Submittal
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
          <template v-if="column.key === 'status'">
            <Tag :color="statusColors[record.status] || 'default'">
              {{ statusLabels[record.status] || record.status }}
            </Tag>
          </template>
          <template v-else-if="column.key === 'priority'">
            <Tag :color="priorityColors[record.priority] || 'default'">
              {{ (record.priority || '').replace(/^\w/, c => c.toUpperCase()) }}
            </Tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="handleView(record)">
                <template #icon><EyeOutlined /></template>
              </Button>
              <Button type="link" size="small" @click="handleEdit(record)">
                <template #icon><EditOutlined /></template>
              </Button>
              <Popconfirm
                title="Delete this submittal?"
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
