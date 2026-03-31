<script lang="ts" setup>
import { computed, onMounted, reactive, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Col,
  DatePicker,
  Drawer,
  Form,
  FormItem,
  InputNumber,
  message,
  Popconfirm,
  Row,
  Select,
  Space,
  Table,
  Textarea,
} from 'ant-design-vue';
import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';

import {
  createEquipmentAssignmentApi,
  deleteEquipmentAssignmentApi,
  getEquipmentAssignmentsApi,
  getEquipmentListApi,
  updateEquipmentAssignmentApi,
} from '#/api/agcm_resource';
import { getProjectsApi } from '#/api/agcm';

defineOptions({ name: 'AGCMEquipmentAssignments' });

const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  pageSizeOptions: ['10', '20', '50', '100'],
  showTotal: (total: number) => `Total ${total} assignments`,
});

const loading = ref(false);
const items = ref<any[]>([]);
const equipmentFilter = ref<number | null>(null);
const projectFilter = ref<number | null>(null);

const equipmentList = ref<any[]>([]);
const projects = ref<any[]>([]);

const drawerVisible = ref(false);
const drawerTitle = ref('New Assignment');
const editingId = ref<number | null>(null);
const saving = ref(false);

const form = reactive({
  equipment_id: null as number | null,
  project_id: null as number | null,
  assigned_date: null as string | null,
  return_date: null as string | null,
  daily_rate: 0,
  total_days: 0,
  total_cost: 0,
  notes: '',
});

const columns = computed(() => [
  { title: 'Equipment', dataIndex: 'equipment_name', key: 'equipment_name', width: 200 },
  { title: 'Project', dataIndex: 'project_name', key: 'project_name', width: 200 },
  { title: 'Assigned Date', dataIndex: 'assigned_date', key: 'assigned_date', width: 130 },
  { title: 'Return Date', dataIndex: 'return_date', key: 'return_date', width: 130 },
  { title: 'Daily Rate', key: 'daily_rate', width: 110 },
  { title: 'Total Days', dataIndex: 'total_days', key: 'total_days', width: 100 },
  { title: 'Total Cost', key: 'total_cost', width: 120 },
  { title: 'Actions', key: 'actions', width: 120, fixed: 'right' as const },
]);

async function loadEquipment() {
  try {
    const res = await getEquipmentListApi({ page_size: 200 });
    equipmentList.value = (res.items || []).map((e: any) => ({ value: e.id, label: `${e.sequence_name || ''} - ${e.name}` }));
  } catch (e) {
    console.error('Failed to load equipment:', e);
  }
}

async function loadProjects() {
  try {
    const res = await getProjectsApi({ page_size: 200 });
    projects.value = (res.items || []).map((p: any) => ({ value: p.id, label: p.name }));
  } catch (e) {
    console.error('Failed to load projects:', e);
  }
}

async function fetchData() {
  loading.value = true;
  try {
    const params: any = {
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
      equipment_id: equipmentFilter.value || undefined,
      project_id: projectFilter.value || undefined,
    };
    const response = await getEquipmentAssignmentsApi(params);
    items.value = response.items || [];
    pagination.value.total = response.total || 0;
  } catch (error) {
    console.error('Failed to fetch assignments:', error);
    message.error('Failed to load assignments');
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

function resetForm() {
  Object.assign(form, {
    equipment_id: null,
    project_id: null,
    assigned_date: null,
    return_date: null,
    daily_rate: 0,
    total_days: 0,
    total_cost: 0,
    notes: '',
  });
}

function handleCreate() {
  editingId.value = null;
  drawerTitle.value = 'New Assignment';
  resetForm();
  drawerVisible.value = true;
}

function handleEdit(record: any) {
  editingId.value = record.id;
  drawerTitle.value = 'Edit Assignment';
  Object.assign(form, {
    equipment_id: record.equipment_id,
    project_id: record.project_id,
    assigned_date: record.assigned_date || null,
    return_date: record.return_date || null,
    daily_rate: record.daily_rate || 0,
    total_days: record.total_days || 0,
    total_cost: record.total_cost || 0,
    notes: record.notes || '',
  });
  drawerVisible.value = true;
}

function recalcCost() {
  form.total_cost = form.daily_rate * form.total_days;
}

async function handleSave() {
  if (!form.equipment_id || !form.project_id || !form.assigned_date) {
    message.warning('Equipment, project, and assigned date are required');
    return;
  }
  saving.value = true;
  try {
    const payload = { ...form };
    if (editingId.value) {
      await updateEquipmentAssignmentApi(editingId.value, payload);
      message.success('Assignment updated successfully');
    } else {
      await createEquipmentAssignmentApi(payload);
      message.success('Assignment created successfully');
    }
    drawerVisible.value = false;
    fetchData();
  } catch (error) {
    console.error('Failed to save assignment:', error);
    message.error('Failed to save assignment');
  } finally {
    saving.value = false;
  }
}

async function handleDelete(record: any) {
  try {
    await deleteEquipmentAssignmentApi(record.id);
    message.success('Assignment deleted successfully');
    fetchData();
  } catch (error) {
    console.error('Failed to delete:', error);
    message.error('Failed to delete assignment');
  }
}

function formatCurrency(val: number) {
  return `$${(val || 0).toFixed(2)}`;
}

onMounted(() => {
  fetchData();
  loadEquipment();
  loadProjects();
});
</script>

<template>
  <Page title="Equipment Assignments" description="Track equipment allocation to projects">
    <Card>
      <!-- Toolbar -->
      <div class="mb-4 flex items-center justify-between">
        <Space>
          <Select
            v-model:value="equipmentFilter"
            :options="equipmentList"
            placeholder="All Equipment"
            allow-clear
            show-search
            :filter-option="(input: string, option: any) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
            style="width: 220px"
            @change="handleSearch"
          />
          <Select
            v-model:value="projectFilter"
            :options="projects"
            placeholder="All Projects"
            allow-clear
            show-search
            :filter-option="(input: string, option: any) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
            style="width: 200px"
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
            New Assignment
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
        :scroll="{ x: 1000 }"
        @change="onTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'daily_rate'">
            {{ formatCurrency(record.daily_rate) }}
          </template>
          <template v-else-if="column.key === 'total_cost'">
            {{ formatCurrency(record.total_cost) }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="handleEdit(record)">
                <template #icon><EditOutlined /></template>
              </Button>
              <Popconfirm
                title="Delete this assignment?"
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

    <!-- Drawer for create/edit -->
    <Drawer
      v-model:open="drawerVisible"
      :title="drawerTitle"
      width="480"
      :body-style="{ paddingBottom: '80px' }"
    >
      <Form layout="vertical">
        <FormItem label="Equipment" required>
          <Select
            v-model:value="form.equipment_id"
            :options="equipmentList"
            placeholder="Select equipment"
            show-search
            :filter-option="(input: string, option: any) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
          />
        </FormItem>
        <FormItem label="Project" required>
          <Select
            v-model:value="form.project_id"
            :options="projects"
            placeholder="Select project"
            show-search
            :filter-option="(input: string, option: any) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
          />
        </FormItem>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Assigned Date" required>
              <DatePicker v-model:value="form.assigned_date" style="width: 100%" value-format="YYYY-MM-DD" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Return Date">
              <DatePicker v-model:value="form.return_date" style="width: 100%" value-format="YYYY-MM-DD" />
            </FormItem>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="8">
            <FormItem label="Daily Rate ($)">
              <InputNumber v-model:value="form.daily_rate" :min="0" :max="99999.99" :precision="2" style="width: 100%" @change="recalcCost" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Total Days">
              <InputNumber v-model:value="form.total_days" :min="0" :max="9999" style="width: 100%" @change="recalcCost" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Total Cost ($)">
              <InputNumber v-model:value="form.total_cost" :min="0" :max="9999999.99" :precision="2" style="width: 100%" />
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Notes">
          <Textarea v-model:value="form.notes" :rows="3" placeholder="Additional notes" />
        </FormItem>
      </Form>
      <div class="drawer-footer">
        <Space>
          <Button @click="drawerVisible = false">Cancel</Button>
          <Button type="primary" :loading="saving" @click="handleSave">
            {{ editingId ? 'Update' : 'Create' }}
          </Button>
        </Space>
      </div>
    </Drawer>
  </Page>
</template>
