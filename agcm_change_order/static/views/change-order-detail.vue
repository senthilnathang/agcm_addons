<script setup>
import { computed, onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Badge,
  Button,
  Card,
  Col,
  Descriptions,
  DescriptionsItem,
  message,
  Row,
  Space,
  Statistic,
  Table,
  Tag,
  Tabs,
} from 'ant-design-vue';
import {
  ArrowLeftOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  EditOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';
import { useRoute, useRouter } from 'vue-router';
import { RecordPager } from '#/components/common'

defineOptions({ name: 'AGCMChangeOrderDetail' });

const route = useRoute();
const router = useRouter();
const BASE = '/agcm_change_order';

const coId = ref(Number(route.query.id));
const co = ref(null);
const loading = ref(false);
const activeTab = ref('details');

function getAccessToken() {
  try {
    return localStorage?.getItem('accessToken') || '';
  } catch {
    return '';
  }
}

const statusColors = {
  draft: 'default',
  pending: 'processing',
  approved: 'success',
  rejected: 'error',
  void: 'default',
};

const lineColumns = [
  { title: '#', key: 'index', width: 50 },
  { title: 'Description', dataIndex: 'description', key: 'description' },
  { title: 'Qty', dataIndex: 'quantity', key: 'quantity', width: 80 },
  { title: 'Unit', dataIndex: 'unit', key: 'unit', width: 80 },
  { title: 'Unit Cost', dataIndex: 'unit_cost', key: 'unit_cost', width: 120 },
  { title: 'Total Cost', dataIndex: 'total_cost', key: 'total_cost', width: 120 },
];

const lineTotalCost = computed(() => {
  if (!co.value || !co.value.lines) return 0;
  return co.value.lines.reduce((sum, l) => sum + (l.total_cost || 0), 0);
});

async function fetchChangeOrder() {
  loading.value = true;
  try {
    co.value = await requestClient.get(`${BASE}/change-orders/${coId.value}`);
  } catch { message.error('Failed to load change order'); }
  finally { loading.value = false; }
}

async function handleApprove() {
  try {
    await requestClient.post(`${BASE}/change-orders/${coId.value}/approve`);
    message.success('Change order approved');
    fetchChangeOrder();
  } catch { message.error('Failed to approve change order'); }
}

async function handleReject() {
  try {
    await requestClient.post(`${BASE}/change-orders/${coId.value}/reject`);
    message.success('Change order rejected');
    fetchChangeOrder();
  } catch { message.error('Failed to reject change order'); }
}

function formatCurrency(val) {
  if (val == null) return '$0.00';
  return `$${Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatDate(d) {
  if (!d) return '-';
  return new Date(d).toLocaleDateString();
}

onMounted(fetchChangeOrder);
</script>

<template>
  <Page title="Change Order Detail">
    <template v-if="co">
      <Card>
        <div class="flex items-start justify-between mb-4">
          <div>
            <h2 class="text-xl font-semibold mb-1">{{ co.sequence_name }} — {{ co.title }}</h2>
            <Space>
              <Badge :status="statusColors[co.status] || 'default'" :text="(co.status || '').replace(/_/g, ' ')" />
            </Space>
          </div>
          <Space>
            <Button @click="router.push('/agcm/change-orders')"><ArrowLeftOutlined /> Back</Button>
            <Button @click="router.push({ path: '/agcm/change-orders/form', query: { id: co.id } })"><EditOutlined /> Edit</Button>
            <Button
              v-if="co.status === 'draft' || co.status === 'pending'"
              type="primary"
              @click="handleApprove"
            >
              <CheckCircleOutlined /> Approve
            </Button>
            <Button
              v-if="co.status === 'draft' || co.status === 'pending'"
              danger
              @click="handleReject"
            >
              <CloseCircleOutlined /> Reject
            </Button>
          </Space>
        </div>

        <Descriptions bordered size="small" :column="3">
          <DescriptionsItem label="Requested Date">{{ formatDate(co.requested_date) }}</DescriptionsItem>
          <DescriptionsItem label="Approved Date">{{ formatDate(co.approved_date) }}</DescriptionsItem>
          <DescriptionsItem label="Status">
            <Badge :status="statusColors[co.status] || 'default'" :text="(co.status || '').replace(/_/g, ' ')" />
          </DescriptionsItem>
          <DescriptionsItem label="Cost Impact">{{ formatCurrency(co.cost_impact) }}</DescriptionsItem>
          <DescriptionsItem label="Schedule Impact">{{ co.schedule_impact_days || 0 }} days</DescriptionsItem>
          <DescriptionsItem label="Created">{{ formatDate(co.created_at) }}</DescriptionsItem>
        </Descriptions>

        <div v-if="co.description" class="mt-4 p-4 bg-gray-50 rounded">
          <h4 class="font-medium mb-2">Description</h4>
          <p style="white-space: pre-wrap;">{{ co.description }}</p>
        </div>

        <div v-if="co.reason" class="mt-4 p-4 bg-gray-50 rounded">
          <h4 class="font-medium mb-2">Reason</h4>
          <p style="white-space: pre-wrap;">{{ co.reason }}</p>
        </div>
      </Card>

      <!-- Tabs for Details and Activity -->
      <Card class="mt-4">
        <Tabs v-model:activeKey="activeTab">
          <Tabs.TabPane key="details" tab="Line Items">
            <Table
              :columns="lineColumns"
              :data-source="co.lines || []"
              row-key="id"
              size="small"
              :pagination="false"
              bordered
            >
              <template #bodyCell="{ column, record, index }">
                <template v-if="column.key === 'index'">{{ index + 1 }}</template>
                <template v-else-if="column.key === 'unit_cost'">{{ formatCurrency(record.unit_cost) }}</template>
                <template v-else-if="column.key === 'total_cost'">{{ formatCurrency(record.total_cost) }}</template>
              </template>
            </Table>

            <div class="flex justify-end mt-4">
              <Statistic title="Total Line Cost" :value="formatCurrency(lineTotalCost)" style="text-align: right;" />
            </div>
          </Tabs.TabPane>
          <Tabs.TabPane key="activity" tab="Activity">
            <ActivityThread
              :model-name="'agcm_change_orders'"
              :record-id="coId"
              :access-token="getAccessToken()"
              :api-base="'/api/v1'"
              :show-messages="true"
              :show-activities="true"
            />
          </Tabs.TabPane>
        </Tabs>
      </Card>
    </template>
  </Page>
</template>
