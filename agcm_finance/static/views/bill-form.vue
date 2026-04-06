<script setup>
import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Col,
  DatePicker,
  Descriptions,
  DescriptionsItem,
  Form,
  FormItem,
  Input,
  InputNumber,
  message,
  Modal,
  Row,
  Select,
  SelectOption,
} from 'ant-design-vue';
import {
  ArrowLeftOutlined,
  DollarOutlined,
  SaveOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';
import { useRoute, useRouter } from 'vue-router';

defineOptions({ name: 'AGCMBillForm' });

const route = useRoute();
const router = useRouter();
const BASE = '/agcm_finance';

const billId = ref(route.query.id ? Number(route.query.id) : null);
const isEdit = ref(!!billId.value);
const saving = ref(false);
const projects = ref([]);
const paymentModalVisible = ref(false);
const paymentAmount = ref(0);
const existingBill = ref(null);

const form = ref({
  bill_number: '',
  vendor_name: '',
  amount: 0,
  tax_amount: 0,
  total_amount: 0,
  issue_date: null,
  due_date: null,
  project_id: route.query.project_id ? Number(route.query.project_id) : null,
});

function recalcTotal() {
  form.value.total_amount = Number(((form.value.amount || 0) + (form.value.tax_amount || 0)).toFixed(2));
}

function formatCurrency(val) {
  if (val == null) return '$0.00';
  return `$${Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = data.items || data.results || [];
  } catch {}
}

async function fetchBill() {
  if (!billId.value) return;
  try {
    const data = await requestClient.get(`${BASE}/bills/${billId.value}`);
    existingBill.value = data;
    form.value = {
      bill_number: data.bill_number || '',
      vendor_name: data.vendor_name || '',
      amount: data.amount || 0,
      tax_amount: data.tax_amount || 0,
      total_amount: data.total_amount || 0,
      issue_date: data.issue_date || null,
      due_date: data.due_date || null,
      project_id: data.project_id,
    };
  } catch { message.error('Failed to load bill'); }
}

async function handleSave() {
  if (!form.value.vendor_name.trim()) { message.warning('Vendor name is required'); return; }
  if (!form.value.project_id) { message.warning('Project is required'); return; }

  saving.value = true;
  try {
    if (isEdit.value) {
      await requestClient.put(`${BASE}/bills/${billId.value}`, form.value);
      message.success('Bill updated');
    } else {
      await requestClient.post(`${BASE}/bills`, form.value);
      message.success('Bill created');
    }
    router.push('/agcm/finance/bills');
  } catch { message.error('Failed to save bill'); }
  finally { saving.value = false; }
}

async function handleRecordPayment() {
  if (!paymentAmount.value || paymentAmount.value <= 0) { message.warning('Enter a valid amount'); return; }
  try {
    await requestClient.post(`${BASE}/bills/${billId.value}/record-payment`, { amount: paymentAmount.value });
    message.success('Payment recorded');
    paymentModalVisible.value = false;
    paymentAmount.value = 0;
    fetchBill();
  } catch { message.error('Failed to record payment'); }
}

onMounted(async () => {
  await fetchProjects();
  if (isEdit.value) fetchBill();
});
</script>

<template>
  <Page :title="isEdit ? 'Edit Bill' : 'New Bill'">
    <Card>
      <div v-if="isEdit && existingBill" class="mb-4">
        <Descriptions bordered size="small" :column="4">
          <DescriptionsItem label="Sequence">{{ existingBill.sequence_name }}</DescriptionsItem>
          <DescriptionsItem label="Status">{{ existingBill.status }}</DescriptionsItem>
          <DescriptionsItem label="Paid">{{ formatCurrency(existingBill.paid_amount) }}</DescriptionsItem>
          <DescriptionsItem label="Remaining">
            <span :style="{ fontWeight: 'bold', color: ((existingBill.total_amount || 0) - (existingBill.paid_amount || 0)) > 0 ? '#cf1322' : '#3f8600' }">
              {{ formatCurrency((existingBill.total_amount || 0) - (existingBill.paid_amount || 0)) }}
            </span>
          </DescriptionsItem>
        </Descriptions>
      </div>

      <Form layout="vertical">
        <Row :gutter="16">
          <Col :span="8">
            <FormItem label="Vendor Name" required>
              <Input v-model:value="form.vendor_name" placeholder="Vendor name" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Bill Number">
              <Input v-model:value="form.bill_number" placeholder="Optional bill #" />
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

        <Row :gutter="16">
          <Col :span="6">
            <FormItem label="Amount ($)">
              <InputNumber v-model:value="form.amount" :min="0" :precision="2" style="width: 100%" @change="recalcTotal" />
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Tax ($)">
              <InputNumber v-model:value="form.tax_amount" :min="0" :precision="2" style="width: 100%" @change="recalcTotal" />
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Total ($)">
              <InputNumber v-model:value="form.total_amount" :min="0" :precision="2" style="width: 100%" />
            </FormItem>
          </Col>
        </Row>

        <Row :gutter="16">
          <Col :span="6">
            <FormItem label="Issue Date">
              <DatePicker v-model:value="form.issue_date" style="width: 100%" value-format="YYYY-MM-DD" />
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Due Date">
              <DatePicker v-model:value="form.due_date" style="width: 100%" value-format="YYYY-MM-DD" />
            </FormItem>
          </Col>
        </Row>

        <div class="flex justify-end gap-2 mt-4">
          <Button @click="router.push('/agcm/finance/bills')"><ArrowLeftOutlined /> Back</Button>
          <Button v-if="isEdit && existingBill && existingBill.status !== 'paid'" @click="paymentModalVisible = true">
            <template #icon><DollarOutlined /></template>Record Payment
          </Button>
          <Button type="primary" :loading="saving" @click="handleSave"><SaveOutlined /> {{ isEdit ? 'Update' : 'Create' }}</Button>
        </div>
      </Form>
    </Card>

    <Modal
      v-model:open="paymentModalVisible"
      title="Record Payment"
      @ok="handleRecordPayment"
      ok-text="Record"
    >
      <Form layout="vertical">
        <FormItem label="Payment Amount ($)">
          <InputNumber v-model:value="paymentAmount" :min="0.01" :precision="2" style="width: 100%" />
        </FormItem>
      </Form>
    </Modal>
  </Page>
</template>
