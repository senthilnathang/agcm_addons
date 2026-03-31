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
  Input,
  InputNumber,
  message,
  Popconfirm,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Textarea,
} from 'ant-design-vue';
import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
} from '@ant-design/icons-vue';

import {
  createEquipmentApi,
  deleteEquipmentApi,
  getEquipmentListApi,
  updateEquipmentApi,
} from '#/api/agcm_resource';
import { getProjectsApi } from '#/api/agcm';

defineOptions({ name: 'AGCMEquipment' });

const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  pageSizeOptions: ['10', '20', '50', '100'],
  showTotal: (total: number) => `Total ${total} equipment`,
});

const loading = ref(false);
const items = ref<any[]>([]);
const searchText = ref('');
const statusFilter = ref<string | null>(null);
const typeFilter = ref<string | null>(null);
const projects = ref<any[]>([]);

const drawerVisible = ref(false);
const drawerTitle = ref('New Equipment');
const editingId = ref<number | null>(null);
const saving = ref(false);

const form = reactive({
  name: '',
  description: '',
  equipment_type: '',
  make: '',
  model: '',
  year: null as number | null,
  serial_number: '',
  license_plate: '',
  status: 'available',
  ownership_type: 'owned',
  daily_rate: 0,
  hourly_rate: 0,
  current_project_id: null as number | null,
  current_location: '',
  last_maintenance_date: null as string | null,
  next_maintenance_date: null as string | null,
  notes: '',
});

const statusOptions = [
  { value: 'available', label: 'Available' },
  { value: 'in_use', label: 'In Use' },
  { value: 'maintenance', label: 'Maintenance' },
  { value: 'retired', label: 'Retired' },
];

const ownershipOptions = [
  { value: 'owned', label: 'Owned' },
  { value: 'rented', label: 'Rented' },
  { value: 'leased', label: 'Leased' },
];

const statusColors: Record<string, string> = {
  available: 'green',
  in_use: 'blue',
  maintenance: 'orange',
  retired: 'default',
};

const columns = computed(() => [
  { title: 'Seq #', dataIndex: 'sequence_name', key: 'sequence_name', width: 120 },
  { title: 'Name', dataIndex: 'name', key: 'name', sorter: true },
  { title: 'Type', dataIndex: 'equipment_type', key: 'equipment_type', width: 130 },
  { title: 'Make', dataIndex: 'make', key: 'make', width: 110 },
  { title: 'Status', key: 'status', width: 120 },
  { title: 'Ownership', key: 'ownership_type', width: 110 },
  { title: 'Daily Rate', dataIndex: 'daily_rate', key: 'daily_rate', width: 110 },
  { title: 'Location', dataIndex: 'current_location', key: 'current_location', width: 150 },
  { title: 'Actions', key: 'actions', width: 120, fixed: 'right' as const },
]);

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
      search: searchText.value || undefined,
      status: statusFilter.value || undefined,
      equipment_type: typeFilter.value || undefined,
    };
    const response = await getEquipmentListApi(params);
    items.value = response.items || [];
    pagination.value.total = response.total || 0;
  } catch (error) {
    console.error('Failed to fetch equipment:', error);
    message.error('Failed to load equipment');
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
    name: '',
    description: '',
    equipment_type: '',
    make: '',
    model: '',
    year: null,
    serial_number: '',
    license_plate: '',
    status: 'available',
    ownership_type: 'owned',
    daily_rate: 0,
    hourly_rate: 0,
    current_project_id: null,
    current_location: '',
    last_maintenance_date: null,
    next_maintenance_date: null,
    notes: '',
  });
}

function handleCreate() {
  editingId.value = null;
  drawerTitle.value = 'New Equipment';
  resetForm();
  drawerVisible.value = true;
}

function handleEdit(record: any) {
  editingId.value = record.id;
  drawerTitle.value = 'Edit Equipment';
  Object.assign(form, {
    name: record.name || '',
    description: record.description || '',
    equipment_type: record.equipment_type || '',
    make: record.make || '',
    model: record.model || '',
    year: record.year || null,
    serial_number: record.serial_number || '',
    license_plate: record.license_plate || '',
    status: record.status || 'available',
    ownership_type: record.ownership_type || 'owned',
    daily_rate: record.daily_rate || 0,
    hourly_rate: record.hourly_rate || 0,
    current_project_id: record.current_project_id || null,
    current_location: record.current_location || '',
    last_maintenance_date: record.last_maintenance_date || null,
    next_maintenance_date: record.next_maintenance_date || null,
    notes: record.notes || '',
  });
  drawerVisible.value = true;
}

async function handleSave() {
  if (!form.name || !form.equipment_type) {
    message.warning('Name and equipment type are required');
    return;
  }
  saving.value = true;
  try {
    const payload = { ...form };
    if (editingId.value) {
      await updateEquipmentApi(editingId.value, payload);
      message.success('Equipment updated successfully');
    } else {
      await createEquipmentApi(payload);
      message.success('Equipment created successfully');
    }
    drawerVisible.value = false;
    fetchData();
  } catch (error) {
    console.error('Failed to save equipment:', error);
    message.error('Failed to save equipment');
  } finally {
    saving.value = false;
  }
}

async function handleDelete(record: any) {
  try {
    await deleteEquipmentApi(record.id);
    message.success('Equipment deleted successfully');
    fetchData();
  } catch (error) {
    console.error('Failed to delete:', error);
    message.error('Failed to delete equipment');
  }
}

function formatStatus(val: string) {
  if (!val) return '-';
  return val.replace(/_/g, ' ').replace(/^\w/, (c: string) => c.toUpperCase());
}

onMounted(() => {
  fetchData();
  loadProjects();
});
</script>

<template>
  <Page title="Equipment" description="Manage construction equipment register">
    <Card>
      <!-- Toolbar -->
      <div class="mb-4 flex items-center justify-between">
        <Space>
          <Input
            v-model:value="searchText"
            placeholder="Search equipment..."
            style="width: 240px"
            @press-enter="handleSearch"
          >
            <template #prefix>
              <SearchOutlined />
            </template>
          </Input>
          <Select
            v-model:value="statusFilter"
            :options="statusOptions"
            placeholder="All Statuses"
            allow-clear
            style="width: 140px"
            @change="handleSearch"
          />
          <Input
            v-model:value="typeFilter"
            placeholder="Filter by type"
            style="width: 160px"
            allow-clear
            @press-enter="handleSearch"
          />
          <Button @click="handleSearch">Search</Button>
        </Space>
        <Space>
          <Button @click="fetchData">
            <template #icon><ReloadOutlined /></template>
            Refresh
          </Button>
          <Button type="primary" @click="handleCreate">
            <template #icon><PlusOutlined /></template>
            New Equipment
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
        :scroll="{ x: 1100 }"
        @change="onTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <Tag :color="statusColors[record.status] || 'default'">
              {{ formatStatus(record.status) }}
            </Tag>
          </template>
          <template v-else-if="column.key === 'ownership_type'">
            <Tag color="blue">{{ (record.ownership_type || 'owned').replace(/^\w/, (c: string) => c.toUpperCase()) }}</Tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="handleEdit(record)">
                <template #icon><EditOutlined /></template>
              </Button>
              <Popconfirm
                title="Delete this equipment?"
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
      width="560"
      :body-style="{ paddingBottom: '80px' }"
    >
      <Form layout="vertical">
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Name" required>
              <Input v-model:value="form.name" placeholder="Equipment name" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Type" required>
              <Input v-model:value="form.equipment_type" placeholder="e.g. Excavator, Crane" />
            </FormItem>
          </Col>
        </Row>
        <FormItem label="Description">
          <Textarea v-model:value="form.description" :rows="2" placeholder="Description" />
        </FormItem>
        <Row :gutter="16">
          <Col :span="8">
            <FormItem label="Make">
              <Input v-model:value="form.make" placeholder="Manufacturer" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Model">
              <Input v-model:value="form.model" placeholder="Model" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Year">
              <InputNumber v-model:value="form.year" :min="1900" :max="2100" style="width: 100%" />
            </FormItem>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Serial Number">
              <Input v-model:value="form.serial_number" placeholder="Serial #" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="License Plate">
              <Input v-model:value="form.license_plate" placeholder="Plate #" />
            </FormItem>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Status">
              <Select v-model:value="form.status" :options="statusOptions" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Ownership">
              <Select v-model:value="form.ownership_type" :options="ownershipOptions" />
            </FormItem>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Daily Rate ($)">
              <InputNumber v-model:value="form.daily_rate" :min="0" :max="99999.99" :precision="2" style="width: 100%" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Hourly Rate ($)">
              <InputNumber v-model:value="form.hourly_rate" :min="0" :max="99999.99" :precision="2" style="width: 100%" />
            </FormItem>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Current Project">
              <Select v-model:value="form.current_project_id" :options="projects" allow-clear placeholder="Select project" show-search :filter-option="(input: string, option: any) => (option?.label || '').toLowerCase().includes(input.toLowerCase())" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Current Location">
              <Input v-model:value="form.current_location" placeholder="Location" />
            </FormItem>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Last Maintenance">
              <DatePicker v-model:value="form.last_maintenance_date" style="width: 100%" value-format="YYYY-MM-DD" />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Next Maintenance">
              <DatePicker v-model:value="form.next_maintenance_date" style="width: 100%" value-format="YYYY-MM-DD" />
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
