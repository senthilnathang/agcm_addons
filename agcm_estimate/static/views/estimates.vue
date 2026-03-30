<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { requestClient } from '#/api/request';
import { message } from 'ant-design-vue';
import {
  DeleteOutlined,
  EyeOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
} from '@ant-design/icons-vue';

defineOptions({ name: 'AGCMEstimates' });

const BASE = '/agcm_estimate';
const router = useRouter();

const loading = ref(false);
const items = ref([]);
const projects = ref([]);
const projectFilter = ref(null);
const statusFilter = ref(null);
const typeFilter = ref(null);

const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  pageSizeOptions: ['10', '20', '50', '100'],
  showTotal: (total) => `Total ${total} estimates`,
});

const statusOptions = [
  { value: 'draft', label: 'Draft' },
  { value: 'in_review', label: 'In Review' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'superseded', label: 'Superseded' },
];

const typeOptions = [
  { value: 'preliminary', label: 'Preliminary' },
  { value: 'schematic', label: 'Schematic' },
  { value: 'detailed', label: 'Detailed' },
  { value: 'change_order', label: 'Change Order' },
];

const statusColors = {
  draft: 'default',
  in_review: 'processing',
  approved: 'success',
  rejected: 'error',
  superseded: 'warning',
};

const typeColors = {
  preliminary: 'blue',
  schematic: 'cyan',
  detailed: 'green',
  change_order: 'orange',
};

function fmtCurrency(val) {
  if (val == null) return '$0.00';
  return Number(val).toLocaleString('en-US', { style: 'currency', currency: 'USD' });
}

function fmtLabel(str) {
  if (!str) return '';
  return str.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

const columns = computed(() => [
  { title: 'Seq #', dataIndex: 'sequence_name', key: 'sequence_name', width: 120 },
  { title: 'Name', dataIndex: 'name', key: 'name', ellipsis: true },
  { title: 'Version', dataIndex: 'version', key: 'version', width: 90, align: 'center' },
  { title: 'Type', key: 'estimate_type', width: 130 },
  { title: 'Status', key: 'status', width: 120 },
  { title: 'Grand Total', key: 'grand_total', width: 150, align: 'right' },
  { title: 'Created', dataIndex: 'created_at', key: 'created_at', width: 120 },
  { title: 'Actions', key: 'actions', width: 100, fixed: 'right' },
]);

async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = (data.items || []).map((p) => ({
      value: p.id,
      label: `${p.sequence_name || ''} - ${p.name}`,
    }));
  } catch { /* ignore */ }
}

async function fetchData() {
  loading.value = true;
  try {
    const params = {
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
      project_id: projectFilter.value || undefined,
      status: statusFilter.value || undefined,
      estimate_type: typeFilter.value || undefined,
    };
    const res = await requestClient.get(`${BASE}/estimates`, { params });
    items.value = res.items || [];
    pagination.value.total = res.total || 0;
  } catch (err) {
    console.error('Failed to fetch estimates:', err);
    message.error('Failed to load estimates');
  } finally {
    loading.value = false;
  }
}

function onTableChange(pag) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

function handleFilterChange() {
  pagination.value.current = 1;
  fetchData();
}

function handleRowClick(record) {
  router.push(`/agcm-estimate/estimates/detail/${record.id}`);
}

function handleCreate() {
  router.push('/agcm-estimate/estimates/detail/new');
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/estimates/${record.id}`);
    message.success('Estimate deleted');
    fetchData();
  } catch {
    message.error('Failed to delete estimate');
  }
}

onMounted(() => {
  fetchProjects();
  fetchData();
});
</script>

<template>
  <Page title="Estimates" description="Construction cost estimates">
    <ACard>
      <div class="mb-4 flex items-center justify-between">
        <ASpace>
          <ASelect
            v-model:value="projectFilter"
            :options="projects"
            placeholder="All Projects"
            allow-clear
            show-search
            :filter-option="(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
            style="width: 280px"
            @change="handleFilterChange"
          />
          <ASelect
            v-model:value="statusFilter"
            :options="statusOptions"
            placeholder="All Statuses"
            allow-clear
            style="width: 150px"
            @change="handleFilterChange"
          />
          <ASelect
            v-model:value="typeFilter"
            :options="typeOptions"
            placeholder="All Types"
            allow-clear
            style="width: 150px"
            @change="handleFilterChange"
          />
        </ASpace>
        <ASpace>
          <AButton @click="fetchData">
            <template #icon><ReloadOutlined /></template>
            Refresh
          </AButton>
          <AButton type="primary" @click="handleCreate">
            <template #icon><PlusOutlined /></template>
            New Estimate
          </AButton>
        </ASpace>
      </div>

      <ATable
        :columns="columns"
        :data-source="items"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        size="middle"
        :custom-row="(record) => ({ onClick: () => handleRowClick(record) })"
        @change="onTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'estimate_type'">
            <ATag :color="typeColors[record.estimate_type] || 'default'">
              {{ fmtLabel(record.estimate_type) }}
            </ATag>
          </template>
          <template v-else-if="column.key === 'status'">
            <ABadge
              :status="statusColors[record.status] || 'default'"
              :text="fmtLabel(record.status)"
            />
          </template>
          <template v-else-if="column.key === 'grand_total'">
            {{ fmtCurrency(record.grand_total) }}
          </template>
          <template v-else-if="column.key === 'created_at'">
            {{ record.created_at ? new Date(record.created_at).toLocaleDateString() : '-' }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <ASpace>
              <AButton type="link" size="small" @click.stop="handleRowClick(record)">
                <template #icon><EyeOutlined /></template>
              </AButton>
              <APopconfirm
                title="Delete this estimate?"
                ok-text="Yes"
                cancel-text="No"
                @confirm="handleDelete(record)"
              >
                <AButton type="link" size="small" danger @click.stop>
                  <template #icon><DeleteOutlined /></template>
                </AButton>
              </APopconfirm>
            </ASpace>
          </template>
        </template>
      </ATable>
    </ACard>
  </Page>
</template>
