<script setup>
import { computed, onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import { requestClient } from '#/api/request';
import { useRoute, useRouter } from 'vue-router';
import { useUserStore } from '#/store/user';

defineOptions({ name: 'AGCMBIMModelDetail' });

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const BASE = '/agcm_bim';

const loading = ref(true);
const model = ref(null);
const viewpoints = ref([]);
const summary = ref(null);
const versions = ref([]);
const metadata = ref(null);
const activeTab = ref('info');
const modelId = computed(() => route.query.id);

// Element search
const elementSearch = ref({ ifc_type: '', name: '', level: '' });
const elements = ref([]);
const elementsTotal = ref(0);
const elementsPage = ref(1);
const elementsLoading = ref(false);

const statusColors = { uploading: 'processing', processing: 'warning', ready: 'success', failed: 'error', archived: 'default' };
const disciplineColors = { architectural: 'blue', structural: 'red', mep: 'green', civil: 'orange', composite: 'purple' };

function formatSize(bytes) {
  if (!bytes) return '-';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
}

function formatDate(dt) {
  if (!dt) return '-';
  return new Date(dt).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

async function fetchModel() {
  const id = route.query.id;
  if (!id) { router.push('/agcm/bim/models'); return; }
  loading.value = true;
  try {
    model.value = await requestClient.get(`${BASE}/models/${id}`);
    // Viewpoints
    try { const vp = await requestClient.get(`${BASE}/viewpoints`, { params: { model_id: id } }); viewpoints.value = vp.items || vp || []; } catch {}
    // Summary
    try { summary.value = await requestClient.get(`${BASE}/models/${id}/summary`); } catch { summary.value = null; }
    // Metadata
    try { metadata.value = await requestClient.get(`${BASE}/models/${id}/metadata`); } catch { metadata.value = null; }
    // Versions
    try { versions.value = await requestClient.get(`${BASE}/models/${id}/versions`); } catch { versions.value = []; }
  } catch {
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
    const data = await requestClient.get(`${BASE}/models/${route.query.id}/elements`, { params });
    elements.value = data.items || [];
    elementsTotal.value = data.total || 0;
  } catch {} finally { elementsLoading.value = false; }
}

async function deleteViewpoint(vpId) {
  try { await requestClient.delete(`${BASE}/viewpoints/${vpId}`); fetchModel(); } catch {}
}

const summaryTypes = computed(() => {
  const src = summary.value?.by_type || summary.value?.types || {};
  return Object.entries(src).sort((a, b) => b[1] - a[1]).map(([type, count]) => ({ type, count }));
});

const summaryLevels = computed(() => {
  const src = summary.value?.by_level || summary.value?.levels || {};
  return Object.entries(src).sort((a, b) => b[1] - a[1]).map(([level, count]) => ({ level, count }));
});

const summaryMaterials = computed(() => {
  const src = summary.value?.by_material || {};
  return Object.entries(src).sort((a, b) => b[1] - a[1]).map(([material, count]) => ({ material, count }));
});

function formatMetaValue(val) {
  if (val === null || val === undefined) return '-';
  if (typeof val === 'object') return JSON.stringify(val);
  return String(val);
}

onMounted(fetchModel);
</script>

<template>
  <Page title="BIM Model Detail" description="Model metadata, elements, viewpoints, and version history">
    <ASpin :spinning="loading">
      <div v-if="model">
        <!-- Header Card -->
        <ACard class="mb-4">
          <ARow :gutter="24">
            <ACol :span="18">
              <div class="flex items-center gap-3 mb-2">
                <ATag color="blue">{{ model.sequence_name }}</ATag>
                <h3 style="margin:0; font-size:18px; font-weight:600;">{{ model.name }}</h3>
                <ABadge :status="statusColors[model.status] || 'default'" :text="model.status" />
              </div>
              <p v-if="model.description" style="color:#888; margin:4px 0 12px;">{{ model.description }}</p>

              <ADescriptions :column="3" size="small" bordered>
                <ADescriptionsItem label="Discipline">
                  <ATag v-if="model.discipline" :color="disciplineColors[model.discipline]">{{ model.discipline }}</ATag>
                  <span v-else>-</span>
                </ADescriptionsItem>
                <ADescriptionsItem label="Format"><ATag>{{ (model.file_format || '').toUpperCase() }}</ATag></ADescriptionsItem>
                <ADescriptionsItem label="File Name">{{ model.file_name || '-' }}</ADescriptionsItem>
                <ADescriptionsItem label="File Size">{{ formatSize(model.file_size) }}</ADescriptionsItem>
                <ADescriptionsItem label="XKT Size">{{ formatSize(model.file_size_xkt) }}</ADescriptionsItem>
                <ADescriptionsItem label="Elements">{{ (model.element_count || 0).toLocaleString() }}</ADescriptionsItem>
                <ADescriptionsItem label="Version">v{{ model.version }} <ATag v-if="model.is_current" color="green" size="small">current</ATag></ADescriptionsItem>
                <ADescriptionsItem label="Created">{{ formatDate(model.created_at) }}</ADescriptionsItem>
                <ADescriptionsItem label="Updated">{{ formatDate(model.updated_at) }}</ADescriptionsItem>
              </ADescriptions>

              <!-- Federation Transforms -->
              <template v-if="model.position_x || model.rotation_x || model.scale_factor !== 1">
                <h4 style="margin:12px 0 6px; font-size:12px; font-weight:600; color:#555;">Federation Transforms</h4>
                <ADescriptions :column="3" size="small" bordered>
                  <ADescriptionsItem label="Position">{{ model.position_x }}, {{ model.position_y }}, {{ model.position_z }}</ADescriptionsItem>
                  <ADescriptionsItem label="Rotation">{{ model.rotation_x }}, {{ model.rotation_y }}, {{ model.rotation_z }}</ADescriptionsItem>
                  <ADescriptionsItem label="Scale">{{ model.scale_factor }}</ADescriptionsItem>
                </ADescriptions>
              </template>
            </ACol>

            <ACol :span="6">
              <div class="flex flex-col gap-2">
                <AButton type="primary" block @click="router.push({ path: '/agcm/bim/viewer', query: { id: model.id } })">Open 3D Viewer</AButton>
                <AButton block @click="router.push('/agcm/bim/models')">Back to Models</AButton>
              </div>
            </ACol>
          </ARow>
        </ACard>

        <!-- Tabs -->
        <ACard>
          <ATabs v-model:activeKey="activeTab">

            <!-- Info Tab -->
            <ATabPane key="info" tab="Model Info">
              <ARow :gutter="16" class="mb-4">
                <ACol :span="6"><AStatistic title="Total Elements" :value="model.element_count || 0" /></ACol>
                <ACol :span="6"><AStatistic title="IFC Types" :value="summaryTypes.length" /></ACol>
                <ACol :span="6"><AStatistic title="Levels" :value="summaryLevels.length" /></ACol>
                <ACol :span="6"><AStatistic title="Materials" :value="summaryMaterials.length" /></ACol>
              </ARow>
              <ADivider />
              <ARow :gutter="24">
                <ACol :span="8">
                  <h4 style="font-weight:600; margin-bottom:8px;">Element Types</h4>
                  <ATable :data-source="summaryTypes" :pagination="false" size="small" row-key="type">
                    <ATableColumn title="IFC Type" dataIndex="type" key="type" />
                    <ATableColumn title="Count" dataIndex="count" key="count" width="80" />
                  </ATable>
                </ACol>
                <ACol :span="8">
                  <h4 style="font-weight:600; margin-bottom:8px;">Levels / Storeys</h4>
                  <ATable :data-source="summaryLevels" :pagination="false" size="small" row-key="level">
                    <ATableColumn title="Level" dataIndex="level" key="level" />
                    <ATableColumn title="Elements" dataIndex="count" key="count" width="80" />
                  </ATable>
                </ACol>
                <ACol :span="8">
                  <h4 style="font-weight:600; margin-bottom:8px;">Materials</h4>
                  <ATable :data-source="summaryMaterials" :pagination="false" size="small" row-key="material">
                    <ATableColumn title="Material" dataIndex="material" key="material" />
                    <ATableColumn title="Count" dataIndex="count" key="count" width="80" />
                  </ATable>
                </ACol>
              </ARow>
            </ATabPane>

            <!-- Metadata Tab -->
            <ATabPane key="metadata" tab="File Metadata">
              <template v-if="metadata">
                <ADescriptions bordered size="small" :column="2">
                  <template v-for="(val, key) in metadata" :key="key">
                    <ADescriptionsItem v-if="typeof val !== 'object'" :label="key">{{ formatMetaValue(val) }}</ADescriptionsItem>
                  </template>
                </ADescriptions>
                <template v-for="(val, key) in metadata" :key="'nested-'+key">
                  <template v-if="typeof val === 'object' && val !== null">
                    <h4 style="margin:16px 0 8px; font-size:13px; font-weight:600; color:#555;">{{ key }}</h4>
                    <ADescriptions bordered size="small" :column="2">
                      <ADescriptionsItem v-for="(v2, k2) in val" :key="k2" :label="k2">{{ formatMetaValue(v2) }}</ADescriptionsItem>
                    </ADescriptions>
                  </template>
                </template>
              </template>
              <AEmpty v-else description="No metadata available" />
            </ATabPane>

            <!-- Viewpoints Tab -->
            <ATabPane key="viewpoints" tab="Viewpoints">
              <p class="mb-3" style="color:#888;">{{ viewpoints.length }} viewpoint(s) saved</p>
              <AList v-if="viewpoints.length" :data-source="viewpoints" size="small">
                <template #renderItem="{ item }">
                  <AListItem>
                    <AListItemMeta :title="item.name" :description="item.description || formatDate(item.created_at)" />
                    <template #actions>
                      <ATag v-if="item.entity_type" color="blue">{{ item.entity_type }}</ATag>
                      <AButton type="link" size="small" danger @click="deleteViewpoint(item.id)">Delete</AButton>
                    </template>
                  </AListItem>
                </template>
              </AList>
              <AEmpty v-else description="No viewpoints saved" />
            </ATabPane>

            <!-- Elements Tab -->
            <ATabPane key="elements" tab="Elements">
              <div class="mb-3 flex flex-wrap items-center gap-3">
                <AInput v-model:value="elementSearch.ifc_type" placeholder="IFC Type" style="width:160px" allow-clear />
                <AInput v-model:value="elementSearch.name" placeholder="Name" style="width:160px" allow-clear />
                <AInput v-model:value="elementSearch.level" placeholder="Level" style="width:140px" allow-clear />
                <AButton @click="fetchElements">Search</AButton>
              </div>
              <ATable
                :data-source="elements" :loading="elementsLoading" row-key="id" size="small"
                :pagination="{ current: elementsPage, pageSize: 50, total: elementsTotal, showTotal: t => `${t} elements` }"
                @change="p => { elementsPage = p.current; fetchElements(); }"
              >
                <ATableColumn title="GlobalId" dataIndex="global_id" key="global_id" width="180" :ellipsis="true" />
                <ATableColumn title="Type" dataIndex="ifc_type" key="ifc_type" width="140" />
                <ATableColumn title="Name" dataIndex="name" key="name" />
                <ATableColumn title="Level" dataIndex="level" key="level" width="120" />
                <ATableColumn title="Material" dataIndex="material" key="material" width="140" />
                <ATableColumn title="Discipline" dataIndex="discipline" key="discipline" width="110" />
              </ATable>
            </ATabPane>

            <!-- Versions Tab -->
            <ATabPane key="versions" tab="Versions">
              <ATable :data-source="versions" row-key="id" size="small" :pagination="false">
                <ATableColumn title="Version" key="version" width="100">
                  <template #default="{ record }">v{{ record.version }} <ATag v-if="record.is_current" color="green" size="small">current</ATag></template>
                </ATableColumn>
                <ATableColumn title="Name" dataIndex="name" key="name" />
                <ATableColumn title="Status" key="status" width="100">
                  <template #default="{ record }"><ABadge :status="statusColors[record.status]" :text="record.status" /></template>
                </ATableColumn>
                <ATableColumn title="Created" key="created_at" width="160">
                  <template #default="{ record }">{{ formatDate(record.created_at) }}</template>
                </ATableColumn>
                <ATableColumn title="" key="actions" width="80">
                  <template #default="{ record }">
                    <AButton type="link" size="small" @click="router.push({ path: '/agcm/bim/viewer', query: { id: record.id } })">View 3D</AButton>
                  </template>
                </ATableColumn>
              </ATable>
            </ATabPane>

            <!-- Activity Tab -->
            <ATabPane key="activity" tab="Activity">
              <ActivityThread
                :model-name="'agcm_bim_models'"
                :record-id="modelId"
                :access-token="userStore.accessToken"
                :api-base="'/api/v1'"
                :show-messages="true"
                :show-activities="true"
              />
            </ATabPane>
          </ATabs>
        </ACard>
      </div>
      <AEmpty v-else-if="!loading" description="Model not found" />
    </ASpin>
  </Page>
</template>
