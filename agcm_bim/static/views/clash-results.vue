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
  Divider,
  Drawer,
  Empty,
  Input,
  message,
  Row,
  Select,
  SelectOption,
  Space,
  Spin,
  Statistic,
  Table,
  Tag,
  Textarea,
  Tooltip,
} from 'ant-design-vue';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  EyeOutlined,
  ReloadOutlined,
  StopOutlined,
  UserAddOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';
import { useRoute, useRouter } from 'vue-router';

defineOptions({ name: 'AGCMClashResults' });

const route = useRoute();
const router = useRouter();
const BASE = '/agcm_bim';

const loading = ref(true);
const test = ref(null);
const results = ref([]);
const resultsTotal = ref(0);
const resultsPage = ref(1);
const resultsPageSize = ref(50);
const filterStatus = ref(null);
const filterSeverity = ref(null);

// Detail drawer
const showDetail = ref(false);
const selectedResult = ref(null);
const resolutionNotes = ref('');

const statusOptions = [
  { value: 'new', label: 'New' },
  { value: 'active', label: 'Active' },
  { value: 'reviewed', label: 'Reviewed' },
  { value: 'approved', label: 'Approved' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'ignored', label: 'Ignored' },
];

const severityOptions = [
  { value: 'critical', label: 'Critical' },
  { value: 'major', label: 'Major' },
  { value: 'minor', label: 'Minor' },
  { value: 'info', label: 'Info' },
];

const statusColors = {
  new: 'default', active: 'processing', reviewed: 'warning',
  approved: 'success', resolved: 'success', ignored: 'default',
};

const severityColors = { critical: 'red', major: 'orange', minor: 'gold', info: 'blue' };

const testStatusColors = { pending: 'default', running: 'processing', completed: 'success', failed: 'error' };

const columns = [
  { title: 'Seq', dataIndex: 'sequence_name', key: 'sequence_name', width: 100 },
  { title: 'Element A', key: 'element_a', width: 200 },
  { title: 'Element B', key: 'element_b', width: 200 },
  { title: 'Severity', dataIndex: 'severity', key: 'severity', width: 100 },
  { title: 'Status', dataIndex: 'status', key: 'status', width: 110 },
  { title: 'Distance', dataIndex: 'distance', key: 'distance', width: 100 },
  { title: 'Assigned', dataIndex: 'assigned_to', key: 'assigned_to', width: 90 },
  { title: 'Actions', key: 'actions', width: 140 },
];

async function fetchTest() {
  const testId = route.query.test_id;
  if (!testId) { router.push('/agcm/bim/clash-tests'); return; }
  loading.value = true;
  try {
    test.value = await requestClient.get(`${BASE}/clash-tests/${testId}`);
  } catch {
    message.error('Failed to load clash test');
    router.push('/agcm/bim/clash-tests');
  } finally { loading.value = false; }
}

async function fetchResults() {
  const testId = route.query.test_id;
  if (!testId) return;
  loading.value = true;
  try {
    const params = { page: resultsPage.value, page_size: resultsPageSize.value };
    if (filterStatus.value) params.status = filterStatus.value;
    if (filterSeverity.value) params.severity = filterSeverity.value;

    const data = await requestClient.get(`${BASE}/clash-tests/${testId}/results`, { params });
    results.value = data.items || [];
    resultsTotal.value = data.total || 0;
  } catch { message.error('Failed to load results'); }
  finally { loading.value = false; }
}

function openDetail(record) {
  selectedResult.value = record;
  resolutionNotes.value = record.resolution_notes || '';
  showDetail.value = true;
}

async function resolveClash() {
  if (!selectedResult.value) return;
  try {
    await requestClient.post(`${BASE}/clash-results/${selectedResult.value.id}/resolve`, {
      resolution_notes: resolutionNotes.value,
    });
    message.success('Clash resolved');
    showDetail.value = false;
    fetchResults();
    fetchTest();
  } catch { message.error('Failed to resolve clash'); }
}

async function ignoreClash(resultId) {
  try {
    await requestClient.post(`${BASE}/clash-results/${resultId || selectedResult.value?.id}/ignore`);
    message.success('Clash ignored');
    showDetail.value = false;
    fetchResults();
  } catch { message.error('Failed to ignore clash'); }
}

async function updateStatus(resultId, newStatus) {
  try {
    await requestClient.put(`${BASE}/clash-results/${resultId}`, { status: newStatus });
    message.success('Status updated');
    fetchResults();
  } catch { message.error('Failed to update status'); }
}

function parsePoint(json) {
  try {
    const p = JSON.parse(json);
    return `(${p.x}, ${p.y}, ${p.z})`;
  } catch { return '-'; }
}

onMounted(async () => {
  await fetchTest();
  fetchResults();
});
</script>

<template>
  <Page title="Clash Results" description="Review, assign, and resolve individual clashes">
    <Spin :spinning="loading && !test">
      <div v-if="test">
        <!-- Test Summary -->
        <Card class="mb-4">
          <Row :gutter="24" align="middle">
            <Col :span="12">
              <div class="flex items-center gap-3 mb-2">
                <Tag color="blue">{{ test.sequence_name }}</Tag>
                <h3 style="margin: 0">{{ test.name }}</h3>
                <Badge :status="testStatusColors[test.status]" :text="test.status" />
              </div>
              <Descriptions :column="2" size="small">
                <DescriptionsItem label="Test Type"><Tag>{{ test.test_type }}</Tag></DescriptionsItem>
                <DescriptionsItem label="Tolerance">{{ test.tolerance }}m</DescriptionsItem>
                <DescriptionsItem label="Model A">{{ test.model_a_name || '-' }}</DescriptionsItem>
                <DescriptionsItem label="Model B">{{ test.model_b_name || '(same model)' }}</DescriptionsItem>
                <DescriptionsItem label="Duration">{{ test.duration_seconds ? test.duration_seconds.toFixed(1) + 's' : '-' }}</DescriptionsItem>
                <DescriptionsItem label="Run Date">{{ test.run_date ? new Date(test.run_date).toLocaleString() : '-' }}</DescriptionsItem>
              </Descriptions>
            </Col>
            <Col :span="12">
              <Row :gutter="16">
                <Col :span="6"><Statistic title="Total" :value="test.total_clashes" /></Col>
                <Col :span="6"><Statistic title="Critical" :value="test.critical_count" :value-style="{ color: '#f5222d' }" /></Col>
                <Col :span="6"><Statistic title="Major" :value="test.major_count" :value-style="{ color: '#fa8c16' }" /></Col>
                <Col :span="6"><Statistic title="Minor" :value="test.minor_count" :value-style="{ color: '#faad14' }" /></Col>
              </Row>
            </Col>
          </Row>
        </Card>

        <!-- Results Table -->
        <Card>
          <div class="mb-4 flex flex-wrap items-center gap-3">
            <Select v-model:value="filterSeverity" placeholder="Severity" style="width: 130px" allow-clear @change="fetchResults">
              <SelectOption v-for="s in severityOptions" :key="s.value" :value="s.value">{{ s.label }}</SelectOption>
            </Select>
            <Select v-model:value="filterStatus" placeholder="Status" style="width: 130px" allow-clear @change="fetchResults">
              <SelectOption v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</SelectOption>
            </Select>
            <div class="flex-1" />
            <Button @click="fetchResults"><template #icon><ReloadOutlined /></template>Refresh</Button>
            <Button @click="router.push('/agcm/bim/clash-tests')">Back to Tests</Button>
          </div>

          <Table
            :columns="columns"
            :data-source="results"
            :loading="loading"
            row-key="id"
            size="middle"
            :pagination="{ current: resultsPage, pageSize: resultsPageSize, total: resultsTotal, showSizeChanger: true, showTotal: (t) => `${t} clashes` }"
            @change="(p) => { resultsPage = p.current; resultsPageSize = p.pageSize; fetchResults(); }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'element_a'">
                <div>
                  <Tag size="small">{{ record.element_a_type || '?' }}</Tag>
                  <span class="ml-1">{{ record.element_a_name || record.element_a_id || '-' }}</span>
                </div>
              </template>
              <template v-else-if="column.key === 'element_b'">
                <div>
                  <Tag size="small">{{ record.element_b_type || '?' }}</Tag>
                  <span class="ml-1">{{ record.element_b_name || record.element_b_id || '-' }}</span>
                </div>
              </template>
              <template v-else-if="column.key === 'severity'">
                <Tag :color="severityColors[record.severity]">{{ record.severity }}</Tag>
              </template>
              <template v-else-if="column.key === 'status'">
                <Badge :status="statusColors[record.status] || 'default'" :text="(record.status || '').replace(/_/g, ' ')" />
              </template>
              <template v-else-if="column.key === 'distance'">
                {{ record.distance != null ? record.distance.toFixed(3) + 'm' : '-' }}
              </template>
              <template v-else-if="column.key === 'assigned_to'">
                <Tag v-if="record.assigned_to" color="blue">#{{ record.assigned_to }}</Tag>
                <span v-else>-</span>
              </template>
              <template v-else-if="column.key === 'actions'">
                <Space>
                  <Tooltip title="Details">
                    <Button type="link" size="small" @click="openDetail(record)"><EyeOutlined /></Button>
                  </Tooltip>
                  <Tooltip title="Resolve">
                    <Button type="link" size="small" @click="openDetail(record)" :disabled="record.status === 'resolved'"><CheckCircleOutlined /></Button>
                  </Tooltip>
                  <Tooltip title="Ignore">
                    <Button type="link" size="small" @click="ignoreClash(record.id)" :disabled="record.status === 'ignored'"><StopOutlined /></Button>
                  </Tooltip>
                </Space>
              </template>
            </template>
          </Table>
        </Card>
      </div>
      <Empty v-else-if="!loading" description="Clash test not found" />
    </Spin>

    <!-- Detail Drawer -->
    <Drawer v-model:open="showDetail" title="Clash Detail" width="560">
      <div v-if="selectedResult">
        <Descriptions :column="1" bordered size="small">
          <DescriptionsItem label="Sequence">{{ selectedResult.sequence_name }}</DescriptionsItem>
          <DescriptionsItem label="Severity"><Tag :color="severityColors[selectedResult.severity]">{{ selectedResult.severity }}</Tag></DescriptionsItem>
          <DescriptionsItem label="Status"><Badge :status="statusColors[selectedResult.status]" :text="selectedResult.status" /></DescriptionsItem>
          <DescriptionsItem label="Element A">
            <Tag>{{ selectedResult.element_a_type }}</Tag> {{ selectedResult.element_a_name || selectedResult.element_a_id }}
          </DescriptionsItem>
          <DescriptionsItem label="Element B">
            <Tag>{{ selectedResult.element_b_type }}</Tag> {{ selectedResult.element_b_name || selectedResult.element_b_id }}
          </DescriptionsItem>
          <DescriptionsItem label="Clash Point">{{ selectedResult.clash_point ? parsePoint(selectedResult.clash_point) : '-' }}</DescriptionsItem>
          <DescriptionsItem label="Distance">{{ selectedResult.distance != null ? selectedResult.distance.toFixed(4) + 'm' : '-' }}</DescriptionsItem>
          <DescriptionsItem label="Description">{{ selectedResult.description || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Assigned To">{{ selectedResult.assigned_to ? `User #${selectedResult.assigned_to}` : 'Unassigned' }}</DescriptionsItem>
          <DescriptionsItem label="Notes">{{ selectedResult.notes || '-' }}</DescriptionsItem>
        </Descriptions>

        <Divider />

        <div v-if="selectedResult.status !== 'resolved' && selectedResult.status !== 'ignored'">
          <h4>Resolution</h4>
          <Textarea v-model:value="resolutionNotes" placeholder="Describe how this clash was resolved..." :rows="3" class="mb-3" />
          <Space>
            <Button type="primary" @click="resolveClash"><CheckCircleOutlined /> Resolve</Button>
            <Button @click="ignoreClash()"><StopOutlined /> Ignore</Button>
          </Space>
        </div>

        <div v-else>
          <Tag v-if="selectedResult.status === 'resolved'" color="green">Resolved</Tag>
          <Tag v-else color="default">Ignored</Tag>
          <p v-if="selectedResult.resolution_notes" class="mt-2">{{ selectedResult.resolution_notes }}</p>
          <p v-if="selectedResult.resolved_date" class="text-gray-400 mt-1">Resolved: {{ selectedResult.resolved_date }}</p>
        </div>
      </div>
    </Drawer>
  </Page>
</template>
