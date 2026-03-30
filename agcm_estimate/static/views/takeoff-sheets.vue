<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { requestClient } from '#/api/request';
import { message } from 'ant-design-vue';
import {
  DeleteOutlined,
  EditOutlined,
  LinkOutlined,
  PlusOutlined,
  ReloadOutlined,
  UploadOutlined,
} from '@ant-design/icons-vue';

defineOptions({ name: 'AGCMTakeoffSheets' });

const BASE = '/agcm_estimate';

const loading = ref(false);
const sheets = ref([]);
const projects = ref([]);
const projectFilter = ref(null);
const expandedRowKeys = ref([]);

// Sheet drawer
const drawerVisible = ref(false);
const drawerTitle = ref('New Takeoff Sheet');
const drawerSaving = ref(false);
const editingSheetId = ref(null);
const sheetForm = reactive({
  project_id: null,
  name: '',
  description: '',
  scale_factor: 1,
  scale_unit: 'ft',
  plan_file: '',
  revision: '',
});

// Measurement form
const measurementForm = reactive({
  sheet_id: null,
  label: '',
  measurement_type: 'linear',
  value: 0,
  unit: 'ft',
  notes: '',
});
const measurementSaving = ref(false);

// Link modal
const linkModalVisible = ref(false);
const linkingMeasurementId = ref(null);
const estimateLines = ref([]);
const selectedLineId = ref(null);
const linkSaving = ref(false);

const measurementTypes = [
  { value: 'linear', label: 'Linear' },
  { value: 'area', label: 'Area' },
  { value: 'count', label: 'Count' },
];

const scaleUnits = [
  { value: 'ft', label: 'Feet' },
  { value: 'in', label: 'Inches' },
  { value: 'm', label: 'Meters' },
  { value: 'cm', label: 'Centimeters' },
];

const columns = computed(() => [
  { title: 'Name', dataIndex: 'name', key: 'name', ellipsis: true },
  { title: 'Plan File', dataIndex: 'plan_file', key: 'plan_file', width: 180, ellipsis: true },
  { title: 'Scale', key: 'scale', width: 120 },
  { title: 'Revision', dataIndex: 'revision', key: 'revision', width: 100 },
  { title: 'Measurements', key: 'measurement_count', width: 130, align: 'center' },
  { title: 'Actions', key: 'actions', width: 120, fixed: 'right' },
]);

const measurementColumns = [
  { title: 'Label', dataIndex: 'label', key: 'label' },
  { title: 'Type', key: 'measurement_type', width: 100 },
  { title: 'Value', key: 'value', width: 100, align: 'right' },
  { title: 'Unit', dataIndex: 'unit', key: 'unit', width: 80 },
  { title: 'Linked Line', key: 'linked_line', width: 180 },
  { title: 'Actions', key: 'actions', width: 130 },
];

async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = (data.items || []).map(p => ({
      value: p.id, label: `${p.sequence_name || ''} - ${p.name}`,
    }));
  } catch { /* ignore */ }
}

async function fetchData() {
  loading.value = true;
  try {
    const params = {
      project_id: projectFilter.value || undefined,
      page_size: 200,
    };
    const res = await requestClient.get(`${BASE}/takeoff-sheets`, { params });
    sheets.value = res.items || res || [];
  } catch {
    message.error('Failed to load takeoff sheets');
  } finally {
    loading.value = false;
  }
}

function handleFilterChange() {
  fetchData();
}

async function handleExpand(expanded, record) {
  if (expanded) {
    expandedRowKeys.value = [record.id];
    try {
      const res = await requestClient.get(`${BASE}/measurements`, { params: { sheet_id: record.id, page_size: 200 } });
      record._measurements = res.items || res || [];
    } catch {
      record._measurements = [];
    }
  } else {
    expandedRowKeys.value = [];
  }
}

function openNewSheet() {
  editingSheetId.value = null;
  drawerTitle.value = 'New Takeoff Sheet';
  Object.assign(sheetForm, {
    project_id: projectFilter.value, name: '', description: '',
    scale_factor: 1, scale_unit: 'ft', plan_file: '', revision: '',
  });
  drawerVisible.value = true;
}

function openEditSheet(record) {
  editingSheetId.value = record.id;
  drawerTitle.value = 'Edit Takeoff Sheet';
  Object.assign(sheetForm, {
    project_id: record.project_id,
    name: record.name,
    description: record.description || '',
    scale_factor: record.scale_factor || 1,
    scale_unit: record.scale_unit || 'ft',
    plan_file: record.plan_file || '',
    revision: record.revision || '',
  });
  drawerVisible.value = true;
}

async function saveSheet() {
  if (!sheetForm.name) { message.warning('Name is required'); return; }
  if (!sheetForm.project_id) { message.warning('Project is required'); return; }
  drawerSaving.value = true;
  try {
    if (editingSheetId.value) {
      await requestClient.put(`${BASE}/takeoff-sheets/${editingSheetId.value}`, { ...sheetForm });
      message.success('Sheet updated');
    } else {
      await requestClient.post(`${BASE}/takeoff-sheets`, { ...sheetForm });
      message.success('Sheet created');
    }
    drawerVisible.value = false;
    fetchData();
  } catch {
    message.error('Failed to save sheet');
  } finally {
    drawerSaving.value = false;
  }
}

async function handleDeleteSheet(record) {
  try {
    await requestClient.delete(`${BASE}/takeoff-sheets/${record.id}`);
    message.success('Sheet deleted');
    fetchData();
  } catch {
    message.error('Failed to delete sheet');
  }
}

async function addMeasurement(sheet) {
  if (!measurementForm.label) { message.warning('Label is required'); return; }
  measurementSaving.value = true;
  try {
    await requestClient.post(`${BASE}/measurements`, {
      sheet_id: sheet.id,
      label: measurementForm.label,
      measurement_type: measurementForm.measurement_type,
      value: measurementForm.value,
      unit: measurementForm.unit,
      notes: measurementForm.notes,
    });
    message.success('Measurement added');
    Object.assign(measurementForm, { label: '', measurement_type: 'linear', value: 0, unit: 'ft', notes: '' });
    // Refresh measurements
    const res = await requestClient.get(`${BASE}/measurements`, { params: { sheet_id: sheet.id, page_size: 200 } });
    sheet._measurements = res.items || res || [];
  } catch {
    message.error('Failed to add measurement');
  } finally {
    measurementSaving.value = false;
  }
}

async function deleteMeasurement(sheet, meas) {
  try {
    await requestClient.delete(`${BASE}/measurements/${meas.id}`);
    message.success('Measurement deleted');
    sheet._measurements = (sheet._measurements || []).filter(m => m.id !== meas.id);
  } catch {
    message.error('Failed to delete measurement');
  }
}

async function openLinkModal(meas) {
  linkingMeasurementId.value = meas.id;
  selectedLineId.value = meas.estimate_line_item_id || null;
  try {
    const res = await requestClient.get(`${BASE}/estimate-line-items`, { params: { page_size: 200 } });
    estimateLines.value = (res.items || res || []).map(l => ({
      value: l.id, label: `${l.name} (${l.total_cost ? fmtCurrency(l.total_cost) : '-'})`,
    }));
  } catch {
    estimateLines.value = [];
  }
  linkModalVisible.value = true;
}

function fmtCurrency(val) {
  if (val == null) return '$0.00';
  return Number(val).toLocaleString('en-US', { style: 'currency', currency: 'USD' });
}

async function handleLink() {
  if (!selectedLineId.value) { message.warning('Select a line item'); return; }
  linkSaving.value = true;
  try {
    await requestClient.post(`${BASE}/measurements/${linkingMeasurementId.value}/link-to-line`, {
      estimate_line_item_id: selectedLineId.value,
    });
    message.success('Measurement linked');
    linkModalVisible.value = false;
    // Refresh expanded sheet
    if (expandedRowKeys.value.length) {
      const sheet = sheets.value.find(s => s.id === expandedRowKeys.value[0]);
      if (sheet) {
        const res = await requestClient.get(`${BASE}/measurements`, { params: { sheet_id: sheet.id, page_size: 200 } });
        sheet._measurements = res.items || res || [];
      }
    }
  } catch {
    message.error('Failed to link measurement');
  } finally {
    linkSaving.value = false;
  }
}

onMounted(() => {
  fetchProjects();
  fetchData();
});
</script>

<template>
  <Page title="Takeoff Sheets" description="Plan takeoff and measurements">
    <ACard>
      <div class="mb-4 flex items-center justify-between">
        <ASpace>
          <ASelect
            v-model:value="projectFilter"
            :options="projects"
            placeholder="All Projects"
            allow-clear
            show-search
            :filter-option="(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
            style="width: 280px"
            @change="handleFilterChange"
          />
        </ASpace>
        <ASpace>
          <AButton @click="fetchData">
            <template #icon><ReloadOutlined /></template>
            Refresh
          </AButton>
          <AButton type="primary" @click="openNewSheet">
            <template #icon><PlusOutlined /></template>
            New Sheet
          </AButton>
        </ASpace>
      </div>

      <ATable
        :columns="columns"
        :data-source="sheets"
        :loading="loading"
        :expanded-row-keys="expandedRowKeys"
        row-key="id"
        size="middle"
        @expand="handleExpand"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'scale'">
            {{ record.scale_factor || 1 }} {{ record.scale_unit || '' }}
          </template>
          <template v-else-if="column.key === 'measurement_count'">
            <ATag color="blue">{{ record.measurement_count || (record._measurements || []).length || 0 }}</ATag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <ASpace>
              <AButton type="link" size="small" @click="openEditSheet(record)">
                <template #icon><EditOutlined /></template>
              </AButton>
              <APopconfirm title="Delete this sheet?" ok-text="Yes" cancel-text="No" @confirm="handleDeleteSheet(record)">
                <AButton type="link" size="small" danger>
                  <template #icon><DeleteOutlined /></template>
                </AButton>
              </APopconfirm>
            </ASpace>
          </template>
        </template>

        <template #expandedRowRender="{ record: sheet }">
          <div style="padding: 8px 0">
            <ATable
              :columns="measurementColumns"
              :data-source="sheet._measurements || []"
              row-key="id"
              size="small"
              :pagination="false"
            >
              <template #bodyCell="{ column, record: meas }">
                <template v-if="column.key === 'measurement_type'">
                  <ATag :color="meas.measurement_type === 'linear' ? 'blue' : meas.measurement_type === 'area' ? 'green' : 'orange'">
                    {{ (meas.measurement_type || '').replace(/^\w/, c => c.toUpperCase()) }}
                  </ATag>
                </template>
                <template v-else-if="column.key === 'value'">
                  {{ Number(meas.value || 0).toFixed(2) }}
                </template>
                <template v-else-if="column.key === 'linked_line'">
                  <ATag v-if="meas.estimate_line_item_id" color="green">
                    Linked #{{ meas.estimate_line_item_id }}
                  </ATag>
                  <span v-else style="color: #bbb">Not linked</span>
                </template>
                <template v-else-if="column.key === 'actions'">
                  <ASpace>
                    <AButton type="link" size="small" @click="openLinkModal(meas)">
                      <template #icon><LinkOutlined /></template>
                    </AButton>
                    <APopconfirm title="Delete?" @confirm="deleteMeasurement(sheet, meas)">
                      <AButton type="link" size="small" danger>
                        <template #icon><DeleteOutlined /></template>
                      </AButton>
                    </APopconfirm>
                  </ASpace>
                </template>
              </template>
            </ATable>

            <!-- Inline add measurement form -->
            <div style="margin-top: 12px; display: flex; gap: 8px; align-items: flex-end; flex-wrap: wrap">
              <AInput v-model:value="measurementForm.label" placeholder="Label" size="small" style="width: 160px" />
              <ASelect v-model:value="measurementForm.measurement_type" :options="measurementTypes" size="small" style="width: 100px" />
              <AInputNumber v-model:value="measurementForm.value" :min="0" :precision="2" placeholder="Value" size="small" style="width: 100px" />
              <AInput v-model:value="measurementForm.unit" placeholder="Unit" size="small" style="width: 70px" />
              <AButton type="primary" size="small" :loading="measurementSaving" @click="addMeasurement(sheet)">
                <template #icon><PlusOutlined /></template>
                Add
              </AButton>
            </div>
          </div>
        </template>
      </ATable>
    </ACard>

    <!-- Sheet Drawer -->
    <ADrawer
      :open="drawerVisible"
      :title="drawerTitle"
      :width="520"
      @close="drawerVisible = false"
    >
      <AForm layout="vertical">
        <AFormItem label="Project" required>
          <ASelect
            v-model:value="sheetForm.project_id"
            :options="projects"
            placeholder="Select project"
            show-search
            :filter-option="(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
          />
        </AFormItem>
        <AFormItem label="Name" required>
          <AInput v-model:value="sheetForm.name" />
        </AFormItem>
        <AFormItem label="Description">
          <ATextarea v-model:value="sheetForm.description" :rows="2" />
        </AFormItem>
        <AFormItem label="Plan File">
          <AInput v-model:value="sheetForm.plan_file" placeholder="File path or URL" />
        </AFormItem>
        <div style="display: flex; gap: 16px">
          <AFormItem label="Scale Factor" style="flex: 1">
            <AInputNumber v-model:value="sheetForm.scale_factor" :min="0" :precision="2" style="width: 100%" />
          </AFormItem>
          <AFormItem label="Scale Unit" style="flex: 1">
            <ASelect v-model:value="sheetForm.scale_unit" :options="scaleUnits" />
          </AFormItem>
        </div>
        <AFormItem label="Revision">
          <AInput v-model:value="sheetForm.revision" />
        </AFormItem>
      </AForm>
      <template #footer>
        <ASpace>
          <AButton @click="drawerVisible = false">Cancel</AButton>
          <AButton type="primary" :loading="drawerSaving" @click="saveSheet">Save</AButton>
        </ASpace>
      </template>
    </ADrawer>

    <!-- Link to Estimate Line Modal -->
    <AModal
      v-model:open="linkModalVisible"
      title="Link to Estimate Line Item"
      :confirm-loading="linkSaving"
      ok-text="Link"
      @ok="handleLink"
    >
      <ASelect
        v-model:value="selectedLineId"
        :options="estimateLines"
        placeholder="Select estimate line item"
        show-search
        :filter-option="(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
        style="width: 100%"
      />
    </AModal>
  </Page>
</template>
