<script setup>
import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Col,
  DatePicker,
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
  Textarea,
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

defineOptions({ name: 'AGCMChangeOrderForm' });

const route = useRoute();
const router = useRouter();
const BASE = '/agcm_change_order';

const coId = ref(route.query.id ? Number(route.query.id) : null);
const isEdit = ref(!!coId.value);
const saving = ref(false);
const projects = ref([]);

const form = ref({
  title: '',
  description: '',
  reason: '',
  cost_impact: 0,
  schedule_impact_days: 0,
  requested_date: null,
  project_id: route.query.project_id ? Number(route.query.project_id) : null,
  lines: [],
});

const lineColumns = [
  { title: 'Description', dataIndex: 'description', key: 'description' },
  { title: 'Qty', dataIndex: 'quantity', key: 'quantity', width: 100 },
  { title: 'Unit', dataIndex: 'unit', key: 'unit', width: 100 },
  { title: 'Unit Cost', dataIndex: 'unit_cost', key: 'unit_cost', width: 130 },
  { title: 'Total Cost', dataIndex: 'total_cost', key: 'total_cost', width: 130 },
  { title: '', key: 'actions', width: 60 },
];

function addLine() {
  form.value.lines.push({
    _key: Date.now(),
    description: '',
    quantity: 1,
    unit: '',
    unit_cost: 0,
    total_cost: 0,
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

async function fetchChangeOrder() {
  if (!coId.value) return;
  try {
    const data = await requestClient.get(`${BASE}/change-orders/${coId.value}`);
    form.value = {
      title: data.title || '',
      description: data.description || '',
      reason: data.reason || '',
      cost_impact: data.cost_impact || 0,
      schedule_impact_days: data.schedule_impact_days || 0,
      requested_date: data.requested_date || null,
      project_id: data.project_id,
      lines: (data.lines || []).map((l, i) => ({
        _key: l.id || Date.now() + i,
        description: l.description || '',
        quantity: l.quantity || 1,
        unit: l.unit || '',
        unit_cost: l.unit_cost || 0,
        total_cost: l.total_cost || 0,
      })),
    };
  } catch { message.error('Failed to load change order'); }
}

async function handleSave() {
  if (!form.value.title.trim()) { message.warning('Title is required'); return; }
  if (!form.value.project_id) { message.warning('Project is required'); return; }

  const payload = {
    ...form.value,
    lines: form.value.lines.map(({ _key, ...rest }) => rest),
  };

  saving.value = true;
  try {
    if (isEdit.value) {
      await requestClient.put(`${BASE}/change-orders/${coId.value}`, payload);
      message.success('Change order updated');
    } else {
      await requestClient.post(`${BASE}/change-orders`, payload);
      message.success('Change order created');
    }
    router.push('/agcm/change-orders');
  } catch { message.error('Failed to save change order'); }
  finally { saving.value = false; }
}

onMounted(async () => {
  await fetchProjects();
  if (isEdit.value) fetchChangeOrder();
});
</script>

<template>
  <Page :title="isEdit ? 'Edit Change Order' : 'New Change Order'">
    <Card>
      <Form layout="vertical">
        <Row :gutter="16">
          <Col :span="16">
            <FormItem label="Title" required>
              <Input v-model:value="form.title" placeholder="Enter change order title" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Project" required>
              <Select v-model:value="form.project_id" placeholder="Select project" show-search option-filter-prop="label" style="width: 100%">
                <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.name }}</SelectOption>
              </Select>
            </FormItem>
          </Col>
        </Row>

        <FormItem label="Description">
          <Textarea v-model:value="form.description" :rows="3" placeholder="Describe the change..." />
        </FormItem>

        <FormItem label="Reason">
          <Textarea v-model:value="form.reason" :rows="2" placeholder="Reason for change..." />
        </FormItem>

        <Row :gutter="16">
          <Col :span="6">
            <FormItem label="Cost Impact ($)">
              <InputNumber v-model:value="form.cost_impact" :min="0" :precision="2" style="width: 100%" />
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Schedule Impact (days)">
              <InputNumber v-model:value="form.schedule_impact_days" :min="0" style="width: 100%" />
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Requested Date">
              <DatePicker v-model:value="form.requested_date" style="width: 100%" value-format="YYYY-MM-DD" />
            </FormItem>
          </Col>
        </Row>

        <!-- Line Items -->
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
                <Input v-model:value="record.unit" placeholder="ea, lf..." size="small" />
              </template>
              <template v-else-if="column.key === 'unit_cost'">
                <InputNumber v-model:value="record.unit_cost" :min="0" :precision="2" size="small" style="width: 100%" @change="calcLineTotal(record)" />
              </template>
              <template v-else-if="column.key === 'total_cost'">
                <InputNumber v-model:value="record.total_cost" :min="0" :precision="2" size="small" style="width: 100%" />
              </template>
              <template v-else-if="column.key === 'actions'">
                <Button type="link" size="small" danger @click="removeLine(index)"><DeleteOutlined /></Button>
              </template>
            </template>
          </Table>
        </div>

        <div class="flex justify-end gap-2 mt-4">
          <Button @click="router.push('/agcm/change-orders')"><ArrowLeftOutlined /> Back</Button>
          <Button type="primary" :loading="saving" @click="handleSave"><SaveOutlined /> {{ isEdit ? 'Update' : 'Create' }}</Button>
        </div>
      </Form>
    </Card>
  </Page>
</template>
