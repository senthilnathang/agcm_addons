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
  EyeOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
} from '@ant-design/icons-vue';

import { deleteProjectApi, getProjectsApi } from '#/api/agcm';

defineOptions({ name: 'AGCMProjects' });

const router = useRouter();

const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  pageSizeOptions: ['10', '20', '50', '100'],
  showTotal: (total: number) => `Total ${total} projects`,
});

const loading = ref(false);
const items = ref<any[]>([]);
const searchText = ref('');
const statusFilter = ref<string | null>(null);

const statusOptions = [
  { value: 'new', label: 'New' },
  { value: 'inprogress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
];

const statusColors: Record<string, string> = {
  new: 'blue',
  inprogress: 'orange',
  completed: 'green',
};

const columns = computed(() => [
  { title: 'Seq #', dataIndex: 'sequence_name', key: 'sequence_name', width: 120 },
  { title: 'Project Name', dataIndex: 'name', key: 'name', sorter: true },
  { title: 'Project #', dataIndex: 'ref_number', key: 'ref_number', width: 130 },
  { title: 'Status', key: 'status', width: 120 },
  { title: 'Start Date', dataIndex: 'start_date', key: 'start_date', width: 120 },
  { title: 'End Date', dataIndex: 'end_date', key: 'end_date', width: 120 },
  { title: 'City', dataIndex: 'city', key: 'city', width: 130 },
  { title: 'Office', key: 'agcm_office', width: 100 },
  { title: 'Actions', key: 'actions', width: 150, fixed: 'right' as const },
]);

async function fetchData() {
  loading.value = true;
  try {
    const params: any = {
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
      search: searchText.value || undefined,
      status: statusFilter.value || undefined,
    };
    const response = await getProjectsApi(params);
    items.value = response.items || [];
    pagination.value.total = response.total || 0;
  } catch (error) {
    console.error('Failed to fetch projects:', error);
    message.error('Failed to load projects');
  } finally {
    loading.value = false;
  }
}

function onTableChange(pag: any) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

function handleSearch() {
  pagination.value.current = 1;
  fetchData();
}

function handleCreate() {
  router.push('/agcm/projects/form');
}

function handleEdit(record: any) {
  router.push(`/agcm/projects/form/${record.id}`);
}

function handleView(record: any) {
  router.push(`/agcm/projects/detail/${record.id}`);
}

async function handleDelete(record: any) {
  try {
    await deleteProjectApi(record.id);
    message.success('Project deleted successfully');
    fetchData();
  } catch (error) {
    console.error('Failed to delete:', error);
    message.error('Failed to delete project');
  }
}

onMounted(fetchData);
</script>

<template>
  <Page title="Projects" description="Manage construction projects">
    <Card>
      <!-- Toolbar -->
      <div class="mb-4 flex items-center justify-between">
        <Space>
          <Input
            v-model:value="searchText"
            placeholder="Search projects..."
            style="width: 280px"
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
            style="width: 150px"
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
            New Project
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
              {{ record.status === 'inprogress' ? 'In Progress' : (record.status || '').replace(/^\w/, (c: string) => c.toUpperCase()) }}
            </Tag>
          </template>
          <template v-else-if="column.key === 'agcm_office'">
            <Tag v-if="record.agcm_office" color="purple">
              {{ (record.agcm_office || '').replace(/^\w/, (c: string) => c.toUpperCase()) }}
            </Tag>
            <span v-else>-</span>
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
                title="Delete this project?"
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
