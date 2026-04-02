<script setup>
import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Badge,
  Button,
  Card,
  Col,
  Descriptions,
  DescriptionsItem,
  Divider,
  Input,
  List,
  ListItem,
  ListItemMeta,
  message,
  Row,
  Space,
  Switch,
  Tabs,
  Tag,
  Textarea,
  Timeline,
  TimelineItem,
  Typography,
  TypographyText,
} from 'ant-design-vue';
import {
  ArrowLeftOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  EditOutlined,
  LockOutlined,
  MessageOutlined,
  SendOutlined,
  UnlockOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';
import { useRoute, useRouter } from 'vue-router';
import { useUserStore } from '#/store/user';

defineOptions({ name: 'AGCMRFIDetail' });

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const BASE = '/agcm_rfi';

const rfiId = ref(Number(route.query.id));
const rfi = ref(null);
const loading = ref(false);
const activeTab = ref('responses');

// Response form
const newResponseContent = ref('');
const isOfficialResponse = ref(false);
const sendingResponse = ref(false);

const statusColors = { draft: 'default', open: 'processing', in_progress: 'warning', answered: 'success', closed: 'default' };
const priorityColors = { low: 'green', medium: 'orange', high: 'red' };

async function fetchRFI() {
  loading.value = true;
  try {
    rfi.value = await requestClient.get(`${BASE}/rfis/${rfiId.value}`);
  } catch { message.error('Failed to load RFI'); }
  finally { loading.value = false; }
}

async function handleClose() {
  try {
    await requestClient.post(`${BASE}/rfis/${rfiId.value}/close`);
    message.success('RFI closed');
    fetchRFI();
  } catch { message.error('Failed to close RFI'); }
}

async function handleReopen() {
  try {
    await requestClient.post(`${BASE}/rfis/${rfiId.value}/reopen`);
    message.success('RFI reopened');
    fetchRFI();
  } catch { message.error('Failed to reopen RFI'); }
}

async function handleSendResponse() {
  if (!newResponseContent.value.trim()) { message.warning('Response content required'); return; }
  sendingResponse.value = true;
  try {
    await requestClient.post(`${BASE}/rfis/${rfiId.value}/responses`, {
      content: newResponseContent.value,
      is_official_response: isOfficialResponse.value,
    });
    message.success('Response added');
    newResponseContent.value = '';
    isOfficialResponse.value = false;
    fetchRFI();
  } catch { message.error('Failed to add response'); }
  finally { sendingResponse.value = false; }
}

function formatDate(d) {
  if (!d) return '-';
  return new Date(d).toLocaleDateString();
}

onMounted(fetchRFI);
</script>

<template>
  <Page title="RFI Detail">
    <template v-if="rfi">
      <Card>
        <div class="flex items-start justify-between mb-4">
          <div>
            <h2 class="text-xl font-semibold mb-1">{{ rfi.sequence_name }} — {{ rfi.subject }}</h2>
            <Space>
              <Badge :status="statusColors[rfi.status] || 'default'" :text="(rfi.status || '').replace(/_/g, ' ')" />
              <Tag :color="priorityColors[rfi.priority]">{{ rfi.priority }} priority</Tag>
              <span v-for="l in (rfi.labels || [])" :key="l.id">
                <Tag :color="l.color">{{ l.name }}</Tag>
              </span>
            </Space>
          </div>
          <Space>
            <Button @click="router.push('/agcm/rfi')"><ArrowLeftOutlined /> Back</Button>
            <Button @click="router.push({ path: '/agcm/rfi/form', query: { id: rfi.id } })"><EditOutlined /> Edit</Button>
            <Button v-if="rfi.status !== 'closed'" type="primary" danger @click="handleClose"><LockOutlined /> Close</Button>
            <Button v-else type="primary" @click="handleReopen"><UnlockOutlined /> Reopen</Button>
          </Space>
        </div>

        <Descriptions bordered size="small" :column="3">
          <DescriptionsItem label="Due Date">{{ formatDate(rfi.due_date) }}</DescriptionsItem>
          <DescriptionsItem label="Schedule Impact">{{ rfi.schedule_impact_days || 0 }} days</DescriptionsItem>
          <DescriptionsItem label="Cost Impact">${{ Number(rfi.cost_impact || 0).toLocaleString() }}</DescriptionsItem>
          <DescriptionsItem label="Created">{{ formatDate(rfi.created_at) }}</DescriptionsItem>
          <DescriptionsItem label="Closed">{{ formatDate(rfi.closed_date) }}</DescriptionsItem>
          <DescriptionsItem label="Responses">{{ rfi.response_count || 0 }}</DescriptionsItem>
        </Descriptions>

        <div v-if="rfi.question" class="mt-4 p-4 bg-gray-50 rounded">
          <h4 class="font-medium mb-2">Question</h4>
          <p style="white-space: pre-wrap;">{{ rfi.question }}</p>
        </div>
      </Card>

      <!-- Responses & Activity Tabs -->
      <Card class="mt-4">
        <Tabs v-model:activeKey="activeTab">
          <Tabs.TabPane key="responses" tab="Responses">
            <div v-if="rfi.responses && rfi.responses.length">
              <div v-for="resp in rfi.responses" :key="resp.id" class="mb-4 p-3 border rounded" :class="resp.is_official_response ? 'border-green-300 bg-green-50' : 'border-gray-200'">
                <div class="flex items-center justify-between mb-2">
                  <Space>
                    <Tag v-if="resp.is_official_response" color="green"><CheckCircleOutlined /> Official Response</Tag>
                    <span class="text-gray-500 text-xs">User #{{ resp.responded_by }}</span>
                  </Space>
                  <span class="text-gray-400 text-xs">{{ formatDate(resp.created_at) }}</span>
                </div>
                <p style="white-space: pre-wrap;">{{ resp.content }}</p>
              </div>
            </div>
            <div v-else class="text-gray-400 text-center py-4">No responses yet</div>

            <Divider />

            <div v-if="rfi.status !== 'closed'">
              <h4 class="font-medium mb-2"><MessageOutlined /> Add Response</h4>
              <Textarea v-model:value="newResponseContent" :rows="3" placeholder="Type your response..." />
              <div class="flex items-center justify-between mt-2">
                <Space>
                  <Switch v-model:checked="isOfficialResponse" />
                  <span>Mark as official response</span>
                </Space>
                <Button type="primary" :loading="sendingResponse" @click="handleSendResponse"><SendOutlined /> Send</Button>
              </div>
            </div>
          </Tabs.TabPane>
          <Tabs.TabPane key="activity" tab="Activity">
            <ActivityThread
              :model-name="'agcm_rfis'"
              :record-id="rfiId"
              :access-token="userStore.accessToken"
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
