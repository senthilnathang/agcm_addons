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
  Empty,
  Input,
  List,
  ListItem,
  ListItemMeta,
  message,
  Modal,
  Row,
  Space,
  Spin,
  Statistic,
  Table,
  Tabs,
  TabPane,
  Tag,
  Tooltip,
  Typography,
  TypographyText,
  TypographyTitle,
} from 'ant-design-vue';
import {
  AimOutlined,
  AppstoreOutlined,
  CameraOutlined,
  DeleteOutlined,
  EnvironmentOutlined,
  EyeOutlined,
  FileOutlined,
  HistoryOutlined,
  InfoCircleOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';
import { useRoute, useRouter } from 'vue-router';

defineOptions({ name: 'AGCMBIMViewer' });

const route = useRoute();
const router = useRouter();
const BASE = '/agcm_bim';

const loading = ref(true);
const model = ref(null);
const viewpoints = ref([]);
const summary = ref(null);
const activeTab = ref('info');

// Viewpoint create
const showCreateVP = ref(false);
const vpForm = ref({ name: '', description: '' });

// Element search
const elementSearch = ref({ ifc_type: '', name: '', level: '' });
const elements = ref([]);
const elementsTotal = ref(0);
const elementsPage = ref(1);
const elementsLoading = ref(false);

const statusColors = {
  uploading: 'processing',
  processing: 'warning',
  ready: 'success',
  failed: 'error',
  archived: 'default',
};

function formatSize(bytes) {
  if (!bytes) return '-';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
}

async function fetchModel() {
  const id = route.query.id;
  if (!id) { router.push('/agcm/bim/models'); return; }
  loading.value = true;
  try {
    model.value = await requestClient.get(`${BASE}/models/${id}`);
    // Fetch viewpoints
    const vpData = await requestClient.get(`${BASE}/viewpoints`, { params: { model_id: id } });
    viewpoints.value = vpData.items || [];
    // Fetch summary
    try {
      summary.value = await requestClient.get(`${BASE}/models/${id}/summary`);
    } catch { summary.value = null; }
  } catch {
    message.error('Failed to load model');
    router.push('/agcm/bim/models');
  } finally { loading.value = false; }
}

async function fetchElements() {
  const id = route.query.id;
  if (!id) return;
  elementsLoading.value = true;
  try {
    const params = { page: elementsPage.value, page_size: 50 };
    if (elementSearch.value.ifc_type) params.ifc_type = elementSearch.value.ifc_type;
    if (elementSearch.value.name) params.name = elementSearch.value.name;
    if (elementSearch.value.level) params.level = elementSearch.value.level;

    const data = await requestClient.get(`${BASE}/models/${id}/elements`, { params });
    elements.value = data.items || [];
    elementsTotal.value = data.total || 0;
  } catch { message.error('Failed to search elements'); }
  finally { elementsLoading.value = false; }
}

async function createViewpoint() {
  if (!vpForm.value.name) { message.warning('Name is required'); return; }
  try {
    await requestClient.post(`${BASE}/viewpoints`, {
      model_id: parseInt(route.query.id),
      name: vpForm.value.name,
      description: vpForm.value.description,
      camera_position: JSON.stringify({ x: 0, y: 0, z: 10, rx: 0, ry: 0, rz: 0, fov: 60 }),
      camera_target: JSON.stringify({ x: 0, y: 0, z: 0 }),
    });
    message.success('Viewpoint saved');
    showCreateVP.value = false;
    vpForm.value = { name: '', description: '' };
    fetchModel();
  } catch { message.error('Failed to save viewpoint'); }
}

async function deleteViewpoint(vpId) {
  try {
    await requestClient.delete(`${BASE}/viewpoints/${vpId}`);
    message.success('Viewpoint deleted');
    fetchModel();
  } catch { message.error('Failed to delete viewpoint'); }
}

const summaryTypes = computed(() => {
  if (!summary.value?.types) return [];
  return Object.entries(summary.value.types)
    .sort((a, b) => b[1] - a[1])
    .map(([type, count]) => ({ type, count }));
});

const summaryLevels = computed(() => {
  if (!summary.value?.levels) return [];
  return Object.entries(summary.value.levels)
    .sort((a, b) => b[1] - a[1])
    .map(([level, count]) => ({ level, count }));
});

onMounted(() => {
  fetchModel();
});
</script>

<template>
  <Page title="BIM Model Viewer" description="View model details, viewpoints, and element data">
    <Spin :spinning="loading">
      <div v-if="model">
        <!-- Header -->
        <Card class="mb-4">
          <Row :gutter="24">
            <Col :span="16">
              <div class="flex items-center gap-3 mb-2">
                <Tag color="blue">{{ model.sequence_name }}</Tag>
                <TypographyTitle :level="4" style="margin: 0">{{ model.name }}</TypographyTitle>
                <Badge :status="statusColors[model.status] || 'default'" :text="model.status" />
              </div>
              <TypographyText v-if="model.description" type="secondary">{{ model.description }}</TypographyText>
              <Descriptions :column="3" size="small" class="mt-3">
                <DescriptionsItem label="Discipline">
                  <Tag v-if="model.discipline" :color="{ architectural: 'blue', structural: 'red', mep: 'green', civil: 'orange', composite: 'purple' }[model.discipline]">{{ model.discipline }}</Tag>
                  <span v-else>-</span>
                </DescriptionsItem>
                <DescriptionsItem label="Format">{{ model.file_format ? model.file_format.toUpperCase() : '-' }}</DescriptionsItem>
                <DescriptionsItem label="File">{{ model.file_name || '-' }} ({{ formatSize(model.file_size) }})</DescriptionsItem>
                <DescriptionsItem label="Version">v{{ model.version }}{{ model.is_current ? ' (current)' : '' }}</DescriptionsItem>
                <DescriptionsItem label="Elements">{{ model.element_count.toLocaleString() }}</DescriptionsItem>
                <DescriptionsItem label="Viewpoints">{{ model.viewpoint_count || 0 }}</DescriptionsItem>
              </Descriptions>
            </Col>
            <Col :span="8">
              <!-- 3D Viewer Placeholder -->
              <div class="bim-viewer-placeholder">
                <div class="flex flex-col items-center justify-center h-full text-gray-400">
                  <AppstoreOutlined style="font-size: 48px" />
                  <p class="mt-2">3D Viewer</p>
                  <p class="text-xs">Integrate xeokit SDK for IFC viewing</p>
                </div>
              </div>
            </Col>
          </Row>
        </Card>

        <!-- Tabs -->
        <Card>
          <Tabs v-model:activeKey="activeTab">
            <!-- Info Tab -->
            <TabPane key="info" tab="Model Info">
              <Row :gutter="16">
                <Col :span="8">
                  <Statistic title="Total Elements" :value="model.element_count" />
                </Col>
                <Col :span="8">
                  <Statistic title="IFC Types" :value="summaryTypes.length" />
                </Col>
                <Col :span="8">
                  <Statistic title="Levels" :value="summaryLevels.length" />
                </Col>
              </Row>
              <Divider />
              <Row :gutter="24">
                <Col :span="12">
                  <h4>Element Types</h4>
                  <Table :data-source="summaryTypes" :pagination="false" size="small" row-key="type">
                    <Table.Column title="IFC Type" dataIndex="type" key="type" />
                    <Table.Column title="Count" dataIndex="count" key="count" width="100" />
                  </Table>
                </Col>
                <Col :span="12">
                  <h4>Levels</h4>
                  <Table :data-source="summaryLevels" :pagination="false" size="small" row-key="level">
                    <Table.Column title="Level" dataIndex="level" key="level" />
                    <Table.Column title="Elements" dataIndex="count" key="count" width="100" />
                  </Table>
                </Col>
              </Row>
            </TabPane>

            <!-- Viewpoints Tab -->
            <TabPane key="viewpoints" tab="Viewpoints">
              <div class="mb-3 flex justify-between items-center">
                <span>{{ viewpoints.length }} viewpoint(s)</span>
                <Button type="primary" size="small" @click="showCreateVP = true"><template #icon><PlusOutlined /></template>Save Viewpoint</Button>
              </div>
              <List v-if="viewpoints.length > 0" :data-source="viewpoints" size="small">
                <template #renderItem="{ item }">
                  <ListItem>
                    <ListItemMeta :title="item.name" :description="item.description || 'No description'">
                      <template #avatar>
                        <CameraOutlined style="font-size: 20px; color: #1890ff" />
                      </template>
                    </ListItemMeta>
                    <template #actions>
                      <Tooltip v-if="item.entity_type" :title="`Linked to ${item.entity_type} #${item.entity_id}`">
                        <Tag color="blue">{{ item.entity_type }}</Tag>
                      </Tooltip>
                      <Button type="link" size="small" danger @click="deleteViewpoint(item.id)"><DeleteOutlined /></Button>
                    </template>
                  </ListItem>
                </template>
              </List>
              <Empty v-else description="No viewpoints saved yet" />
            </TabPane>

            <!-- Elements Tab -->
            <TabPane key="elements" tab="Elements">
              <div class="mb-3 flex flex-wrap items-center gap-3">
                <Input v-model:value="elementSearch.ifc_type" placeholder="IFC Type (e.g. IfcWall)" style="width: 180px" allow-clear />
                <Input v-model:value="elementSearch.name" placeholder="Name" style="width: 180px" allow-clear />
                <Input v-model:value="elementSearch.level" placeholder="Level" style="width: 140px" allow-clear />
                <Button @click="fetchElements"><template #icon><SearchOutlined /></template>Search</Button>
              </div>
              <Table
                :data-source="elements"
                :loading="elementsLoading"
                row-key="id"
                size="small"
                :pagination="{ current: elementsPage, pageSize: 50, total: elementsTotal, showTotal: (t) => `${t} elements` }"
                @change="(p) => { elementsPage = p.current; fetchElements(); }"
              >
                <Table.Column title="GlobalId" dataIndex="global_id" key="global_id" width="200" />
                <Table.Column title="Type" dataIndex="ifc_type" key="ifc_type" width="140" />
                <Table.Column title="Name" dataIndex="name" key="name" />
                <Table.Column title="Level" dataIndex="level" key="level" width="120" />
                <Table.Column title="Material" dataIndex="material" key="material" width="150" />
              </Table>
            </TabPane>

            <!-- Version History Tab -->
            <TabPane key="versions" tab="Versions">
              <Table :data-source="model.version_history || []" row-key="id" size="small" :pagination="false">
                <Table.Column title="Version" dataIndex="version" key="version" width="100">
                  <template #default="{ record }">
                    v{{ record.version }}
                    <Tag v-if="record.is_current" color="green" size="small">current</Tag>
                  </template>
                </Table.Column>
                <Table.Column title="Name" dataIndex="name" key="name" />
                <Table.Column title="Created" dataIndex="created_at" key="created_at" width="160">
                  <template #default="{ record }">
                    {{ record.created_at ? new Date(record.created_at).toLocaleDateString() : '-' }}
                  </template>
                </Table.Column>
                <Table.Column title="" key="actions" width="80">
                  <template #default="{ record }">
                    <Button type="link" size="small" @click="router.push({ path: '/agcm/bim/viewer', query: { id: record.id } })">
                      <EyeOutlined />
                    </Button>
                  </template>
                </Table.Column>
              </Table>
            </TabPane>
          </Tabs>
        </Card>
      </div>
      <Empty v-else-if="!loading" description="Model not found" />
    </Spin>

    <!-- Create Viewpoint Modal -->
    <Modal v-model:open="showCreateVP" title="Save Viewpoint" @ok="createViewpoint" ok-text="Save">
      <div class="flex flex-col gap-3 py-2">
        <div>
          <label class="mb-1 block text-sm font-medium">Name *</label>
          <Input v-model:value="vpForm.name" placeholder="e.g. Level 2 MEP Overview" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">Description</label>
          <Input v-model:value="vpForm.description" placeholder="Optional" />
        </div>
      </div>
    </Modal>
  </Page>
</template>
