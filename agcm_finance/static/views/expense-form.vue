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
  InputNumber,
  message,
  Row,
  Select,
  SelectOption,
  Space,
  Table,
} from 'ant-design-vue';
import {
  ArrowLeftOutlined,
  DeleteOutlined,
  PlusOutlined,
  SaveOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';
import { useRoute, useRouter } from 'vue-router';
import { RecordPager } from '#/components/common'

defineOptions({ name: 'AGCMExpenseForm' });

const route = useRoute();
const router = useRouter();
const BASE = '/agcm_finance';

const expId = ref(route.query.id ? Number(route.query.id) : null);
const isEdit = ref(!!expId.value);
const saving = ref(false);
const projects = ref([]);
const costCodes = ref([]);

const form = ref({
  description: '',
  vendor: '',
  project_id: route.query.project_id ? Number(route.query.project_id) : null,
  lines: [],
});

const lineColumns = [
  { title: 'Description', dataIndex: 'description', key: 'description' },
  { title: 'Qty', dataIndex: 'quantity', key: 'quantity', width: 90 },
  { title: 'Unit', dataIndex: 'unit', key: 'unit', width: 90 },
  { title: 'Unit Cost', dataIndex: 'unit_cost', key: 'unit_cost', width: 120 },
  { title: 'Total Cost', dataIndex: 'total_cost', key: 'total_cost', width: 120 },
  { title: 'Cost Code', dataIndex: 'cost_code_id', key: 'cost_code_id', width: 160 },
  { title: 'Category', dataIndex: 'category', key: 'category', width: 120 },
  { title: '', key: 'actions', width: 50 },
];

function addLine() {
  form.value.lines.push({
    _key: Date.now(),
    description: '',
    quantity: 1,
    unit: '',
    unit_cost: 0,
    total_cost: 0,
    cost_code_id: null,
    category: '',
  });
}

function removeLine(index) {
  form.value.lines.splice(index, 1);
}

function calcLineTotal(line) {
  line.total_cost = Number(((line.quantity || 0) * (line.unit_cost || 0)).toFixed(2));
}

async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = data.items || data.results || [];
  } catch {}
}

async function fetchCostCodes() {
  if (!form.value.project_id) { costCodes.value = []; return; }
  try {
    const data = await requestClient.get(`${BASE}/cost-codes`, { params: { project_id: form.value.project_id } });
    costCodes.value = data || [];
  } catch { costCodes.value = []; }
}

async function fetchExpense() {
  if (!expId.value) return;
  try {
    const data = await requestClient.get(`${BASE}/expenses/${expId.value}`);
    form.value = {
      description: data.description || '',
      vendor: data.vendor || '',
      project_id: data.project_id,
      lines: (data.lines || []).map((l, i) => ({
        _key: l.id || Date.now() + i,
        description: l.description || '',
        quantity: l.quantity || 1,
        unit: l.unit || '',
        unit_cost: l.unit_cost || 0,
        total_cost: l.total_cost || 0,
        cost_code_id: l.cost_code_id,
        category: l.category || '',
      })),
    };
    fetchCostCodes();
  } catch { message.error('Failed to load expense'); }
}

async function handleSave() {
  if (!form.value.description.trim()) { message.warning('Description is required'); return; }
  if (!form.value.project_id) { message.warning('Project is required'); return; }

  const payload = {
    ...form.value,
    lines: form.value.lines.map(({ _key, ...rest }) => rest),
  };

  saving.value = true;
  try {
    if (isEdit.value) {
      await requestClient.put(`${BASE}/expenses/${expId.value}`, payload);
      message.success('Expense updated');
    } else {
      await requestClient.post(`${BASE}/expenses`, payload);
      message.success('Expense created');
    }
    router.push('/agcm/finance/expenses');
  } catch { message.error('Failed to save expense'); }
  finally { saving.value = false; }
}

onMounted(async () => {
  await fetchProjects();
  if (isEdit.value) {
    fetchExpense();
  } else {
    fetchCostCodes();
  }
});
</script>

<template>
  <Page :title="isEdit ? 'Edit Expense' : 'New Expense'">
    <Card>
      <Form layout="vertical">
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Description" required>
              <Input v-model:value="form.description" placeholder="Expense description" />
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Vendor">
              <Input v-model:value="form.vendor" placeholder="Vendor name" />
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Project" required>
              <Select v-model:value="form.project_id" placeholder="Select project" show-search option-filter-prop="label" style="width: 100%" @change="fetchCostCodes">
                <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.name }}</SelectOption>
              </Select>
            </FormItem>
          </Col>
        </Row>

        <div class="mt-4">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-base font-medium">Line Items</h3>
            <Button size="small" @click="addLine"><PlusOutlined /> Add Line</Button>
          </div>

          <Table
            :columns="lineColumns"
            :data-source="form.lines"
            :row-key="(r, i) => r._key || i"
            :pagination="false"
            size="small"
            bordered
          >
            <template #bodyCell="{ column, record, index }">
              <template v-if="column.key === 'description'">
                <Input v-model:value="record.description" placeholder="Description" size="small" />
              </template>
              <template v-else-if="column.key === 'quantity'">
                <InputNumber v-model:value="record.quantity" :min="0" size="small" style="width: 100%" @change="calcLineTotal(record)" />
              </template>
              <template v-else-if="column.key === 'unit'">
                <Input v-model:value="record.unit" placeholder="ea" size="small" />
              </template>
              <template v-else-if="column.key === 'unit_cost'">
                <InputNumber v-model:value="record.unit_cost" :min="0" :precision="2" size="small" style="width: 100%" @change="calcLineTotal(record)" />
              </template>
              <template v-else-if="column.key === 'total_cost'">
                <InputNumber v-model:value="record.total_cost" :min="0" :precision="2" size="small" style="width: 100%" />
              </template>
              <template v-else-if="column.key === 'cost_code_id'">
                <Select v-model:value="record.cost_code_id" placeholder="Code" size="small" allow-clear style="width: 100%">
                  <SelectOption v-for="c in costCodes" :key="c.id" :value="c.id">{{ c.code }}</SelectOption>
                </Select>
              </template>
              <template v-else-if="column.key === 'category'">
                <Input v-model:value="record.category" placeholder="Cat." size="small" />
              </template>
              <template v-else-if="column.key === 'actions'">
                <Button type="link" size="small" danger @click="removeLine(index)"><DeleteOutlined /></Button>
              </template>
            </template>
          </Table>
        </div>

        <div class="flex justify-end gap-2 mt-4">
          <Button @click="router.push('/agcm/finance/expenses')"><ArrowLeftOutlined /> Back</Button>
          <Button type="primary" :loading="saving" @click="handleSave"><SaveOutlined /> {{ isEdit ? 'Update' : 'Create' }}</Button>
        </div>
      </Form>
    </Card>
  </Page>
</template>
