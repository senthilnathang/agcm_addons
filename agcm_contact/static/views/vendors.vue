<script setup>
import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Col,
  Form,
  FormItem,
  Input,
  message,
  Modal,
  Row,
  Select,
  SelectOption,
  Space,
  Table,
  Tag,
  Textarea,
} from 'ant-design-vue';
import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  SearchOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMVendors' });

const BASE = '/agcm_contact';
const loading = ref(false);
const vendors = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const searchText = ref('');
const filterType = ref(null);

const modalVisible = ref(false);
const editingId = ref(null);
const form = ref({
  name: '', vendor_type: 'vendor', code: '',
  contact_name: '', email: '', phone: '',
  address_line1: '', city: '', state: '', zip_code: '', country: '',
  tax_id: '', payment_terms: '', website: '', trade: '', notes: '',
});

const typeColors = {
  vendor: 'blue', client: 'green', subcontractor: 'orange',
  supplier: 'purple', architect: 'cyan', engineer: 'geekblue',
  consultant: 'magenta', other: 'default',
};

const typeOptions = [
  { value: 'vendor', label: 'Vendor' },
  { value: 'client', label: 'Client' },
  { value: 'subcontractor', label: 'Subcontractor' },
  { value: 'supplier', label: 'Supplier' },
  { value: 'architect', label: 'Architect' },
  { value: 'engineer', label: 'Engineer' },
  { value: 'consultant', label: 'Consultant' },
  { value: 'other', label: 'Other' },
];

const columns = [
  { title: 'Name', dataIndex: 'name', key: 'name', ellipsis: true },
  { title: 'Type', dataIndex: 'vendor_type', key: 'vendor_type', width: 130 },
  { title: 'Contact', dataIndex: 'contact_name', key: 'contact_name', ellipsis: true },
  { title: 'Email', dataIndex: 'email', key: 'email', ellipsis: true },
  { title: 'Phone', dataIndex: 'phone', key: 'phone', width: 140 },
  { title: 'Trade', dataIndex: 'trade', key: 'trade', width: 140 },
  { title: 'City', dataIndex: 'city', key: 'city', width: 130 },
  { title: 'Actions', key: 'actions', width: 100, fixed: 'right' },
];

async function fetchVendors() {
  loading.value = true;
  try {
    const params = { page: page.value, page_size: pageSize.value };
    if (searchText.value) params.search = searchText.value;
    if (filterType.value) params.vendor_type = filterType.value;
    const data = await requestClient.get(`${BASE}/vendors`, { params });
    vendors.value = data.items || [];
    total.value = data.total || 0;
  } catch { message.error('Failed to load vendors'); }
  finally { loading.value = false; }
}

function openCreate() {
  editingId.value = null;
  form.value = {
    name: '', vendor_type: 'vendor', code: '',
    contact_name: '', email: '', phone: '',
    address_line1: '', city: '', state: '', zip_code: '', country: '',
    tax_id: '', payment_terms: '', website: '', trade: '', notes: '',
  };
  modalVisible.value = true;
}

function openEdit(record) {
  editingId.value = record.id;
  form.value = { ...record };
  modalVisible.value = true;
}

async function handleSave() {
  if (!form.value.name?.trim()) { message.warning('Name is required'); return; }
  try {
    if (editingId.value) {
      await requestClient.put(`${BASE}/vendors/${editingId.value}`, form.value);
      message.success('Vendor updated');
    } else {
      await requestClient.post(`${BASE}/vendors`, form.value);
      message.success('Vendor created');
    }
    modalVisible.value = false;
    fetchVendors();
  } catch { message.error('Failed to save vendor'); }
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/vendors/${record.id}`);
    message.success('Vendor deleted');
    fetchVendors();
  } catch { message.error('Failed to delete vendor'); }
}

function handlePageChange(p) { page.value = p; fetchVendors(); }

onMounted(fetchVendors);
</script>

<template>
  <Page title="Vendors & Contacts" description="Manage vendors, clients, subcontractors, and suppliers">
    <Card>
      <div class="flex items-center justify-between mb-4">
        <Space>
          <AInput
            v-model:value="searchText"
            placeholder="Search vendors..."
            style="width: 250px;"
            @pressEnter="fetchVendors"
          >
            <template #prefix><SearchOutlined /></template>
          </AInput>
          <ASelect v-model:value="filterType" placeholder="All Types" allowClear style="width: 160px;" @change="fetchVendors">
            <ASelectOption v-for="opt in typeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</ASelectOption>
          </ASelect>
          <Button @click="fetchVendors">Search</Button>
        </Space>
        <Button type="primary" @click="openCreate">
          <template #icon><PlusOutlined /></template>
          New Vendor
        </Button>
      </div>

      <Table
        :columns="columns"
        :dataSource="vendors"
        :loading="loading"
        :pagination="{ current: page, pageSize, total, onChange: handlePageChange }"
        row-key="id"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'vendor_type'">
            <Tag :color="typeColors[record.vendor_type] || 'default'">
              {{ (record.vendor_type || '').replace(/^\w/, c => c.toUpperCase()) }}
            </Tag>
          </template>
          <template v-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="openEdit(record)"><EditOutlined /></Button>
              <Button type="link" size="small" danger @click="handleDelete(record)"><DeleteOutlined /></Button>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <Modal
      v-model:open="modalVisible"
      :title="editingId ? 'Edit Vendor' : 'New Vendor'"
      :width="720"
      @ok="handleSave"
    >
      <Form layout="vertical" style="margin-top: 16px;">
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Name" required>
              <AInput v-model:value="form.name" placeholder="Company name" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Type">
              <ASelect v-model:value="form.vendor_type">
                <ASelectOption v-for="opt in typeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</ASelectOption>
              </ASelect>
            </FormItem>
          </Col>
          <Col :span="4">
            <FormItem label="Code">
              <AInput v-model:value="form.code" placeholder="V-001" />
            </FormItem>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="8"><FormItem label="Contact Name"><AInput v-model:value="form.contact_name" /></FormItem></Col>
          <Col :span="8"><FormItem label="Email"><AInput v-model:value="form.email" /></FormItem></Col>
          <Col :span="8"><FormItem label="Phone"><AInput v-model:value="form.phone" /></FormItem></Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12"><FormItem label="Address"><AInput v-model:value="form.address_line1" /></FormItem></Col>
          <Col :span="6"><FormItem label="City"><AInput v-model:value="form.city" /></FormItem></Col>
          <Col :span="3"><FormItem label="State"><AInput v-model:value="form.state" /></FormItem></Col>
          <Col :span="3"><FormItem label="ZIP"><AInput v-model:value="form.zip_code" /></FormItem></Col>
        </Row>
        <Row :gutter="16">
          <Col :span="6"><FormItem label="Trade"><AInput v-model:value="form.trade" placeholder="e.g. Electrical" /></FormItem></Col>
          <Col :span="6"><FormItem label="Tax ID"><AInput v-model:value="form.tax_id" /></FormItem></Col>
          <Col :span="6"><FormItem label="Payment Terms"><AInput v-model:value="form.payment_terms" placeholder="Net 30" /></FormItem></Col>
          <Col :span="6"><FormItem label="Website"><AInput v-model:value="form.website" /></FormItem></Col>
        </Row>
        <FormItem label="Notes">
          <ATextarea v-model:value="form.notes" :rows="3" />
        </FormItem>
      </Form>
    </Modal>
  </Page>
</template>
