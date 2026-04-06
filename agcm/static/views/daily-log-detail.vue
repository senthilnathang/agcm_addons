<script setup>
import { computed, onMounted, ref, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  AlertOutlined,
  ArrowLeftOutlined,
  CameraOutlined,
  ClockCircleOutlined,
  CloudOutlined,
  CopyOutlined,
  DeleteOutlined,
  EditOutlined,
  FilePdfOutlined,
  ExclamationCircleOutlined,
  EyeOutlined,
  PlusOutlined,
  SafetyOutlined,
  SearchOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons-vue';

import {
  getDailyLogApi,
  getManpowerApi, createManpowerApi, updateManpowerApi, deleteManpowerApi,
  getNotesApi, createNotesApi, updateNotesApi, deleteNotesApi,
  getInspectionsApi, createInspectionApi, updateInspectionApi, deleteInspectionApi,
  getAccidentsApi, createAccidentApi, updateAccidentApi, deleteAccidentApi,
  getVisitorsApi, createVisitorApi, updateVisitorApi, deleteVisitorApi,
  getSafetyViolationsApi, createSafetyViolationApi, updateSafetyViolationApi, deleteSafetyViolationApi,
  getDelaysApi, createDelayApi, updateDelayApi, deleteDelayApi,
  getDeficienciesApi, createDeficiencyApi, updateDeficiencyApi, deleteDeficiencyApi,
  getPhotosApi, uploadPhotoApi, deletePhotoApi,
  exportDailyLogHtmlUrl,
  fetchWeatherForecastApi, getWeatherForecastApi,
  getManualWeatherApi, createManualWeatherApi,
} from '#/api/agcm';

import { requestClient } from '#/api/request';
import { message } from 'ant-design-vue';

defineOptions({ name: 'AGCMDailyLogDetail' });

const route = useRoute();
const router = useRouter();
const logId = computed(() => route.params.id);

const loading = ref(false);
const log = ref(null);
const activeTab = ref('manpower');

// =============================================================================
// =============================================================================
// Weather data (forecast + manual)
// =============================================================================

const weatherForecasts = ref([]);
const manualWeather = ref([]);
const weatherFetching = ref(false);
const weatherManualModalVisible = ref(false);
const weatherManualSaving = ref(false);
const weatherManualForm = reactive({
  temperature: null,
  climate_type: 'clear',
  humidity: null,
  wind: null,
  precipitation: null,
  rain: false,
  rain_fall: null,
});

const weatherCodeIcons = {
  1: { icon: '☀️', label: 'Clear', color: '#faad14' },
  2: { icon: '☁️', label: 'Cloudy', color: '#8c8c8c' },
  3: { icon: '🌦️', label: 'Light Rain', color: '#1890ff' },
  4: { icon: '🌧️', label: 'Heavy Rain', color: '#0050b3' },
  5: { icon: '⛈️', label: 'Thunder', color: '#722ed1' },
};

async function fetchWeatherForecast() {
  if (!log.value) return;
  weatherFetching.value = true;
  try {
    const params = {
      project_id: log.value.project_id,
      log_date: log.value.date,
      dailylog_id: log.value.id,
    };
    const data = await fetchWeatherForecastApi(params);
    weatherForecasts.value = data.items || [];
  } catch (error) {
    console.error('Weather fetch failed:', error);
    message.error('Failed to fetch weather data. Check project coordinates.');
  } finally {
    weatherFetching.value = false;
  }
}

async function loadWeatherData() {
  if (!logId.value) return;
  try {
    const [forecastData, manualData] = await Promise.all([
      getWeatherForecastApi({ dailylog_id: logId.value }).catch(() => ({ items: [] })),
      getManualWeatherApi({ dailylog_id: logId.value }).catch(() => ({ items: [] })),
    ]);
    weatherForecasts.value = forecastData.items || [];
    manualWeather.value = manualData.items || [];
  } catch {}
}

function openWeatherManualModal() {
  Object.assign(weatherManualForm, {
    temperature: null, climate_type: 'clear', humidity: null,
    wind: null, precipitation: null, rain: false, rain_fall: null,
  });
  weatherManualModalVisible.value = true;
}

async function saveManualWeather() {
  weatherManualSaving.value = true;
  try {
    await createManualWeatherApi(logId.value, {
      ...weatherManualForm,
      date: log.value?.date,
      project_id: log.value?.project_id,
    });
    message.success('Weather observation added');
    weatherManualModalVisible.value = false;
    await loadWeatherData();
  } catch {
    message.error('Failed to save weather observation');
  } finally {
    weatherManualSaving.value = false;
  }
}

const climateOptions = [
  { value: 'clear', label: 'Clear / Sunny' },
  { value: 'cloudy', label: 'Cloudy' },
  { value: 'wet', label: 'Wet / Rainy' },
  { value: 'dry', label: 'Dry' },
];

// Lookup data — loaded once, used as dropdown options in modals
// =============================================================================

const lookups = reactive({
  inspectionTypes: [],
  accidentTypes: [],
  violationTypes: [],
  trades: [],
  users: [],
});

async function fetchLookups() {
  try {
    const [inspTypes, accTypes, violTypes, usersData] = await Promise.all([
      requestClient.get('/agcm/inspection-types').catch(() => []),
      requestClient.get('/agcm/accident-types').catch(() => []),
      requestClient.get('/agcm/violation-types').catch(() => []),
      requestClient.get('/users/', { params: { page_size: 200 } }).catch(() => ({ items: [] })),
    ]);
    lookups.inspectionTypes = (inspTypes.items || inspTypes || []).map(t => ({ value: t.id, label: t.name }));
    lookups.accidentTypes = (accTypes.items || accTypes || []).map(t => ({ value: t.id, label: t.name }));
    lookups.violationTypes = (violTypes.items || violTypes || []).map(t => ({ value: t.id, label: t.name }));
    lookups.users = (usersData.items || usersData || []).map(u => ({
      value: u.id,
      label: u.full_name || u.username || u.email,
    }));
  } catch (error) {
    console.error('Failed to fetch lookups:', error);
  }
}

// Child data
const manpower = ref([]);
const notes = ref([]);
const inspections = ref([]);
const accidents = ref([]);
const visitors = ref([]);
const safetyViolations = ref([]);
const delays = ref([]);
const deficiencies = ref([]);
const photos = ref([]);

// Modal state
const modalVisible = ref(false);
const modalTitle = ref('');
const modalSaving = ref(false);
const editingId = ref(null);
const editingEntity = ref(''); // which entity type is being edited

// Generic form data — each entity type uses its own fields
const formData = reactive({});

// =============================================================================
// ENTITY DEFINITIONS — config for each child type
// =============================================================================

const entityConfig = {
  manpower: {
    label: 'Manpower',
    dataRef: manpower,
    listApi: getManpowerApi,
    createApi: createManpowerApi,
    updateApi: updateManpowerApi,
    deleteApi: deleteManpowerApi,
    fields: [
      { key: 'name', label: 'Comments', type: 'text' },
      { key: 'location', label: 'Location', type: 'text' },
      { key: 'number_of_workers', label: 'Number of Workers', type: 'number', required: true },
      { key: 'number_of_hours', label: 'Hours per Worker', type: 'number', required: true },
      { key: 'partner_id', label: 'Contractor', type: 'select', optionsKey: 'users' },
    ],
    defaults: { name: '', location: '', number_of_workers: 0, number_of_hours: 0, partner_id: null },
    columns: [
      { title: 'Seq #', dataIndex: 'sequence_name', width: 90 },
      { title: 'Comments', dataIndex: 'name' },
      { title: 'Location', dataIndex: 'location', width: 140 },
      { title: 'Workers', dataIndex: 'number_of_workers', width: 80 },
      { title: 'Hours', dataIndex: 'number_of_hours', width: 80 },
      { title: 'Total Hrs', dataIndex: 'total_hours', width: 90 },
      { title: 'Actions', key: 'actions', width: 100, fixed: 'right' },
    ],
  },
  notes: {
    label: 'Observation',
    dataRef: notes,
    listApi: getNotesApi,
    createApi: createNotesApi,
    updateApi: updateNotesApi,
    deleteApi: deleteNotesApi,
    fields: [
      { key: 'name', label: 'Comments', type: 'text' },
      { key: 'issue', label: 'Issue', type: 'text' },
      { key: 'description', label: 'Description', type: 'textarea' },
      { key: 'note', label: 'Note', type: 'textarea' },
      { key: 'location', label: 'Location', type: 'text' },
    ],
    defaults: { name: '', issue: '', description: '', note: '', location: '' },
    columns: [
      { title: 'Seq #', dataIndex: 'sequence_name', width: 90 },
      { title: 'Comments', dataIndex: 'name' },
      { title: 'Issue', dataIndex: 'issue', width: 180 },
      { title: 'Location', dataIndex: 'location', width: 140 },
      { title: 'Actions', key: 'actions', width: 100, fixed: 'right' },
    ],
  },
  inspections: {
    label: 'Inspection',
    dataRef: inspections,
    listApi: getInspectionsApi,
    createApi: createInspectionApi,
    updateApi: updateInspectionApi,
    deleteApi: deleteInspectionApi,
    fields: [
      { key: 'name', label: 'Name', type: 'text' },
      { key: 'inspection_type_id', label: 'Inspection Type', type: 'select', optionsKey: 'inspectionTypes' },
      { key: 'result', label: 'Result', type: 'textarea', required: true },
    ],
    defaults: { name: '', inspection_type_id: null, result: '' },
    columns: [
      { title: 'Seq #', dataIndex: 'sequence_name', width: 90 },
      { title: 'Name', dataIndex: 'name' },
      { title: 'Result', dataIndex: 'result' },
      { title: 'Actions', key: 'actions', width: 100, fixed: 'right' },
    ],
  },
  accidents: {
    label: 'Accident',
    dataRef: accidents,
    listApi: getAccidentsApi,
    createApi: createAccidentApi,
    updateApi: updateAccidentApi,
    deleteApi: deleteAccidentApi,
    fields: [
      { key: 'name', label: 'Description', type: 'textarea', required: true },
      { key: 'accident_type_id', label: 'Accident Type', type: 'select', optionsKey: 'accidentTypes' },
      { key: 'location', label: 'Location', type: 'text' },
      { key: 'resolution', label: 'Resolution', type: 'textarea' },
      { key: 'incident_time', label: 'Incident Time', type: 'datetime' },
      { key: 'safety_measure_precautions', label: 'Safety Precautions Taken', type: 'checkbox' },
    ],
    defaults: { name: '', accident_type_id: null, location: '', resolution: '', incident_time: null, safety_measure_precautions: false },
    columns: [
      { title: 'Seq #', dataIndex: 'sequence_name', width: 90 },
      { title: 'Description', dataIndex: 'name', ellipsis: true },
      { title: 'Location', dataIndex: 'location', width: 140 },
      { title: 'Resolution', dataIndex: 'resolution', ellipsis: true },
      { title: 'Actions', key: 'actions', width: 100, fixed: 'right' },
    ],
  },
  visitors: {
    label: 'Visitor',
    dataRef: visitors,
    listApi: getVisitorsApi,
    createApi: createVisitorApi,
    updateApi: updateVisitorApi,
    deleteApi: deleteVisitorApi,
    fields: [
      { key: 'name', label: 'Visitor Name', type: 'text', required: true },
      { key: 'reason', label: 'Reason for Visit', type: 'textarea', required: true },
      { key: 'visit_entry_time', label: 'Entry Time', type: 'datetime', required: true },
      { key: 'visit_exit_time', label: 'Exit Time', type: 'datetime' },
      { key: 'comments', label: 'Comments', type: 'text' },
      { key: 'user_id', label: 'Person to Meet', type: 'select', optionsKey: 'users' },
    ],
    defaults: { name: '', reason: '', visit_entry_time: null, visit_exit_time: null, comments: '', user_id: null },
    columns: [
      { title: 'Seq #', dataIndex: 'sequence_name', width: 90 },
      { title: 'Visitor', dataIndex: 'name' },
      { title: 'Reason', dataIndex: 'reason', ellipsis: true },
      { title: 'Entry', dataIndex: 'visit_entry_time', width: 155 },
      { title: 'Exit', dataIndex: 'visit_exit_time', width: 155 },
      { title: 'Actions', key: 'actions', width: 100, fixed: 'right' },
    ],
  },
  safety: {
    label: 'Safety Observation',
    dataRef: safetyViolations,
    listApi: getSafetyViolationsApi,
    createApi: createSafetyViolationApi,
    updateApi: updateSafetyViolationApi,
    deleteApi: deleteSafetyViolationApi,
    fields: [
      { key: 'name', label: 'Description', type: 'text', required: true },
      { key: 'violation_notice', label: 'Violation Notice', type: 'textarea', required: true },
      { key: 'violation_type_id', label: 'Violation Type', type: 'select', optionsKey: 'violationTypes' },
      { key: 'partner_id', label: 'Notice To', type: 'select', optionsKey: 'users' },
    ],
    defaults: { name: '', violation_notice: '', violation_type_id: null, partner_id: null },
    columns: [
      { title: 'Seq #', dataIndex: 'sequence_name', width: 90 },
      { title: 'Description', dataIndex: 'name' },
      { title: 'Notice', dataIndex: 'violation_notice', ellipsis: true },
      { title: 'Actions', key: 'actions', width: 100, fixed: 'right' },
    ],
  },
  delays: {
    label: 'Delay',
    dataRef: delays,
    listApi: getDelaysApi,
    createApi: createDelayApi,
    updateApi: updateDelayApi,
    deleteApi: deleteDelayApi,
    fields: [
      { key: 'name', label: 'Name', type: 'text', required: true },
      { key: 'reason', label: 'Reason', type: 'textarea', required: true },
      { key: 'delay', label: 'Delay Details', type: 'textarea' },
      { key: 'reported_by', label: 'Reported By', type: 'text' },
      { key: 'partner_id', label: 'Contractor', type: 'select', optionsKey: 'users', required: true },
    ],
    defaults: { name: '', reason: '', delay: '', reported_by: '', partner_id: null },
    columns: [
      { title: 'Seq #', dataIndex: 'sequence_name', width: 90 },
      { title: 'Name', dataIndex: 'name' },
      { title: 'Reason', dataIndex: 'reason', ellipsis: true },
      { title: 'Reported By', dataIndex: 'reported_by', width: 140 },
      { title: 'Actions', key: 'actions', width: 100, fixed: 'right' },
    ],
  },
  deficiencies: {
    label: 'Deficiency',
    dataRef: deficiencies,
    listApi: getDeficienciesApi,
    createApi: createDeficiencyApi,
    updateApi: updateDeficiencyApi,
    deleteApi: deleteDeficiencyApi,
    fields: [
      { key: 'name', label: 'Name', type: 'text', required: true },
      { key: 'description', label: 'Description', type: 'textarea', required: true },
    ],
    defaults: { name: '', description: '' },
    columns: [
      { title: 'Seq #', dataIndex: 'sequence_name', width: 90 },
      { title: 'Name', dataIndex: 'name' },
      { title: 'Description', dataIndex: 'description' },
      { title: 'Actions', key: 'actions', width: 100, fixed: 'right' },
    ],
  },
  // Photos handled separately with file upload UI (not generic CRUD)
};

// =============================================================================
// Photo upload state
// =============================================================================

const photoUploadVisible = ref(false);
const photoUploading = ref(false);
const photoUploadForm = reactive({ name: '', location: '', album: '', files: [] });

function openPhotoUpload() {
  Object.assign(photoUploadForm, { name: '', location: '', album: '', files: [] });
  photoUploadVisible.value = true;
}

async function handlePhotoUpload() {
  if (!photoUploadForm.files || photoUploadForm.files.length === 0) {
    message.warning('Please select at least one photo');
    return;
  }
  photoUploading.value = true;
  try {
    for (const fileObj of photoUploadForm.files) {
      const file = fileObj.originFileObj || fileObj;
      await uploadPhotoApi(logId.value, file, {
        name: photoUploadForm.name || file.name,
        location: photoUploadForm.location || undefined,
        album: photoUploadForm.album || undefined,
      });
    }
    message.success(`${photoUploadForm.files.length} photo(s) uploaded`);
    photoUploadVisible.value = false;
    await loadPhotos();
    await fetchLog();
  } catch (error) {
    console.error('Upload failed:', error);
    message.error('Failed to upload photos');
  } finally {
    photoUploading.value = false;
  }
}

function handlePhotoFileChange(info) {
  photoUploadForm.files = info.fileList;
}

async function loadPhotos() {
  if (!logId.value) return;
  try {
    const data = await getPhotosApi({ dailylog_id: logId.value });
    photos.value = data.items || [];
  } catch {}
}

async function handleDeletePhoto(record) {
  try {
    await deletePhotoApi(record.id);
    message.success('Photo deleted');
    await loadPhotos();
    await fetchLog();
  } catch {
    message.error('Failed to delete photo');
  }
}

// =============================================================================
// Data fetching
// =============================================================================

async function fetchLog() {
  if (!logId.value) return;
  loading.value = true;
  try {
    log.value = await getDailyLogApi(logId.value);
    if (log.value?.sequence_name) {
      window.dispatchEvent(new CustomEvent('fastvue:set-record-name', { detail: { name: `Daily Log: ${log.value.sequence_name}` } }));
    }
  } catch (error) {
    console.error('Failed to load daily log:', error);
  } finally {
    loading.value = false;
  }
}

async function fetchTabData(tab) {
  const id = logId.value;
  if (!id) return;
  const cfg = entityConfig[tab];
  if (!cfg) return;
  try {
    const data = await cfg.listApi({ dailylog_id: id, page_size: 200 });
    cfg.dataRef.value = data.items || [];
  } catch (error) {
    console.error(`Failed to load ${tab}:`, error);
  }
}

function onTabChange(key) {
  activeTab.value = key;
  if (key === 'photos') {
    loadPhotos();
  } else {
    fetchTabData(key);
  }
}

// =============================================================================
// Modal CRUD operations
// =============================================================================

function openAdd(entityKey) {
  const cfg = entityConfig[entityKey];
  editingEntity.value = entityKey;
  editingId.value = null;
  modalTitle.value = `Add ${cfg.label}`;

  // Reset form with defaults
  Object.keys(formData).forEach(k => delete formData[k]);
  Object.assign(formData, { ...cfg.defaults });

  modalVisible.value = true;
}

function openEdit(entityKey, record) {
  const cfg = entityConfig[entityKey];
  editingEntity.value = entityKey;
  editingId.value = record.id;
  modalTitle.value = `Edit ${cfg.label}`;

  // Populate form from record
  Object.keys(formData).forEach(k => delete formData[k]);
  const populated = {};
  for (const field of cfg.fields) {
    populated[field.key] = record[field.key] ?? cfg.defaults[field.key];
  }
  Object.assign(formData, populated);

  modalVisible.value = true;
}

async function handleModalSave() {
  const cfg = entityConfig[editingEntity.value];

  // Validate required fields
  for (const field of cfg.fields) {
    if (field.required && (formData[field.key] === '' || formData[field.key] === null || formData[field.key] === undefined)) {
      message.warning(`${field.label} is required`);
      return;
    }
  }

  modalSaving.value = true;
  try {
    if (editingId.value) {
      // Update
      const updatePayload = {};
      for (const field of cfg.fields) {
        if (formData[field.key] !== undefined) {
          updatePayload[field.key] = formData[field.key];
        }
      }
      await cfg.updateApi(editingId.value, updatePayload);
      message.success(`${cfg.label} updated`);
    } else {
      // Create — include dailylog_id and project_id
      const createPayload = {
        dailylog_id: Number(logId.value),
        project_id: log.value?.project_id || null,
      };
      for (const field of cfg.fields) {
        createPayload[field.key] = formData[field.key];
      }
      await cfg.createApi(createPayload);
      message.success(`${cfg.label} added`);
    }
    modalVisible.value = false;
    await fetchTabData(editingEntity.value);
    await fetchLog(); // refresh counts
  } catch (error) {
    console.error('Save failed:', error);
    message.error(`Failed to save ${cfg.label}`);
  } finally {
    modalSaving.value = false;
  }
}

async function handleDelete(entityKey, record) {
  const cfg = entityConfig[entityKey];
  try {
    await cfg.deleteApi(record.id);
    message.success(`${cfg.label} deleted`);
    await fetchTabData(entityKey);
    await fetchLog();
  } catch (error) {
    console.error('Delete failed:', error);
    message.error(`Failed to delete ${cfg.label}`);
  }
}

function handleBack() {
  router.push('/agcm/daily-logs');
}

function handleCopy() {
  router.push(`/agcm/daily-logs/copy/${logId.value}`);
}

function handleExportPdf() {
  const url = exportDailyLogHtmlUrl(logId.value);
  window.open(url, '_blank');
}

// Current entity config (reactive)
const currentConfig = computed(() => entityConfig[editingEntity.value] || { fields: [] });

onMounted(async () => {
  await fetchLog();
  fetchLookups();
  loadWeatherData();
  fetchTabData('manpower');
});
</script>

<template>
  <div class="p-6">
<ASpin :spinning="loading">
      <!-- Teleport actions into ModuleView toolbar -->
      <Teleport to="#fv-toolbar-actions" v-if="log">
        <AButton size="small" type="primary" @click="handleExportPdf"><FilePdfOutlined /> Export PDF</AButton>
        <AButton size="small" @click="handleCopy"><CopyOutlined /> Copy Log</AButton>
      </Teleport>

      <template v-if="log">
        <!-- Title Card -->
        <ACard class="mb-4">
          <div class="flex items-start justify-between">
            <div>
              <h1 class="text-2xl font-bold mb-1">
                Daily Log: {{ log.sequence_name }}
              </h1>
              <p class="text-gray-500 mb-2">
                Date: <strong>{{ log.date }}</strong> | Project ID: {{ log.project_id }}
              </p>
              <ASpace wrap>
                <ATag v-if="log.copy_id" color="blue">Copied from #{{ log.copy_id }}</ATag>
              </ASpace>
            </div>
          </div>
        </ACard>

        <!-- Summary Stats -->
        <ARow :gutter="12" class="mb-4">
          <ACol :span="3"><ACard size="small"><AStatistic title="Manpower" :value="log.manpower_count || 0"><template #prefix><TeamOutlined /></template></AStatistic></ACard></ACol>
          <ACol :span="3"><ACard size="small"><AStatistic title="Notes" :value="log.notes_count || 0"><template #prefix><EyeOutlined /></template></AStatistic></ACard></ACol>
          <ACol :span="3"><ACard size="small"><AStatistic title="Inspections" :value="log.inspection_count || 0"><template #prefix><SearchOutlined /></template></AStatistic></ACard></ACol>
          <ACol :span="3"><ACard size="small"><AStatistic title="Accidents" :value="log.accident_count || 0"><template #prefix><AlertOutlined /></template></AStatistic></ACard></ACol>
          <ACol :span="3"><ACard size="small"><AStatistic title="Visitors" :value="log.visitor_count || 0"><template #prefix><UserOutlined /></template></AStatistic></ACard></ACol>
          <ACol :span="3"><ACard size="small"><AStatistic title="Safety" :value="log.safety_violation_count || 0"><template #prefix><SafetyOutlined /></template></AStatistic></ACard></ACol>
          <ACol :span="3"><ACard size="small"><AStatistic title="Delays" :value="log.delay_count || 0"><template #prefix><ClockCircleOutlined /></template></AStatistic></ACard></ACol>
          <ACol :span="3"><ACard size="small"><AStatistic title="Photos" :value="log.photo_count || 0"><template #prefix><CameraOutlined /></template></AStatistic></ACard></ACol>
        </ARow>

        <!-- ════════ WEATHER WIDGET ════════ -->
        <ACard class="mb-4">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-base font-semibold m-0">Weather Conditions</h3>
            <ASpace>
              <AButton size="small" :loading="weatherFetching" @click="fetchWeatherForecast">
                <template #icon><CloudOutlined /></template>
                Fetch Forecast
              </AButton>
              <AButton size="small" type="primary" @click="openWeatherManualModal">
                <template #icon><PlusOutlined /></template>
                Add Observation
              </AButton>
            </ASpace>
          </div>

          <!-- Forecast strip (6 time slots) -->
          <div v-if="weatherForecasts.length > 0" class="mb-4">
            <div class="text-xs text-gray-400 mb-2 font-medium">FORECAST (weather.gov)</div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
              <div
                v-for="f in weatherForecasts"
                :key="f.time_interval"
                style="flex: 1; min-width: 100px; max-width: 160px; background: #f5f7fa; border-radius: 8px; padding: 12px; text-align: center;"
              >
                <div style="font-size: 10px; color: #888; margin-bottom: 4px;">
                  {{ f.time_interval ? f.time_interval.split('T')[1] || f.time_interval : '' }}
                </div>
                <div style="font-size: 28px; line-height: 1;">
                  {{ (weatherCodeIcons[f.weather_code] || {}).icon || '🌡️' }}
                </div>
                <div style="font-size: 18px; font-weight: 600; margin: 4px 0;">
                  {{ f.temperature || 0 }}°F
                </div>
                <div style="font-size: 10px; color: #555;">
                  {{ f.weather_label || '' }}
                </div>
                <div style="display: flex; justify-content: space-around; margin-top: 6px; font-size: 9px; color: #888;">
                  <span title="Humidity">💧{{ f.humidity || 0 }}%</span>
                  <span title="Wind">💨{{ f.wind || 0 }}</span>
                </div>
              </div>
            </div>
          </div>
          <AEmpty v-else-if="!weatherFetching" description="No forecast data. Click 'Fetch Forecast' to load from weather.gov." style="padding: 12px 0;" />

          <!-- Manual weather observations table -->
          <div v-if="manualWeather.length > 0">
            <div class="text-xs text-gray-400 mb-2 font-medium">OBSERVED CONDITIONS (manual entry)</div>
            <ATable
              :data-source="manualWeather"
              :columns="[
                { title: 'Seq #', dataIndex: 'sequence_name', width: 100 },
                { title: 'Temp', dataIndex: 'temperature', width: 70 },
                { title: 'Weather', dataIndex: 'climate_type', width: 100 },
                { title: 'Humidity', dataIndex: 'humidity', width: 80 },
                { title: 'Wind', dataIndex: 'wind', width: 70 },
                { title: 'Precip', dataIndex: 'precipitation', width: 80 },
                { title: 'Rain', dataIndex: 'rain', width: 60 },
                { title: 'Rainfall (in)', dataIndex: 'rain_fall', width: 100 },
              ]"
              row-key="id"
              size="small"
              :pagination="false"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.dataIndex === 'rain'">
                  <ATag :color="record.rain ? 'blue' : 'default'">{{ record.rain ? 'Yes' : 'No' }}</ATag>
                </template>
                <template v-else-if="column.dataIndex === 'temperature'">
                  {{ record.temperature }}°{{ record.temperature_type || 'F' }}
                </template>
                <template v-else-if="column.dataIndex === 'climate_type'">
                  <ATag>{{ (record.climate_type || '').replace(/^\w/, c => c.toUpperCase()) }}</ATag>
                </template>
              </template>
            </ATable>
          </div>
        </ACard>

        <!-- Manual Weather Modal -->
        <AModal
          v-model:open="weatherManualModalVisible"
          title="Add Weather Observation"
          :confirm-loading="weatherManualSaving"
          width="520px"
          @ok="saveManualWeather"
        >
          <AForm layout="vertical" style="margin-top: 12px;">
            <ARow :gutter="16">
              <ACol :span="8">
                <AFormItem label="Temperature (°F)">
                  <AInputNumber v-model:value="weatherManualForm.temperature" style="width: 100%;" />
                </AFormItem>
              </ACol>
              <ACol :span="8">
                <AFormItem label="Weather">
                  <ASelect v-model:value="weatherManualForm.climate_type" :options="climateOptions" style="width: 100%;" />
                </AFormItem>
              </ACol>
              <ACol :span="8">
                <AFormItem label="Humidity (%)">
                  <AInputNumber v-model:value="weatherManualForm.humidity" :min="0" :max="100" style="width: 100%;" />
                </AFormItem>
              </ACol>
            </ARow>
            <ARow :gutter="16">
              <ACol :span="8">
                <AFormItem label="Wind (mph)">
                  <AInputNumber v-model:value="weatherManualForm.wind" :min="0" style="width: 100%;" />
                </AFormItem>
              </ACol>
              <ACol :span="8">
                <AFormItem label="Precipitation (in)">
                  <AInputNumber v-model:value="weatherManualForm.precipitation" :min="0" :step="0.1" style="width: 100%;" />
                </AFormItem>
              </ACol>
              <ACol :span="8">
                <AFormItem label="Rain">
                  <ACheckbox v-model:checked="weatherManualForm.rain">Rain</ACheckbox>
                </AFormItem>
              </ACol>
            </ARow>
            <ARow v-if="weatherManualForm.rain" :gutter="16">
              <ACol :span="8">
                <AFormItem label="Rainfall (inches)">
                  <AInputNumber v-model:value="weatherManualForm.rain_fall" :min="0" :step="0.1" style="width: 100%;" />
                </AFormItem>
              </ACol>
            </ARow>
          </AForm>
        </AModal>

        <!-- Tabbed Child Data with CRUD -->
        <ACard>
          <ATabs v-model:activeKey="activeTab" @change="onTabChange">
            <ATabPane v-for="(cfg, key) in entityConfig" :key="key" :tab="cfg.label + (cfg.label.endsWith('s') ? '' : 's')">
              <!-- Add button above each table -->
              <div class="mb-3 flex justify-end">
                <AButton type="primary" size="small" @click="openAdd(key)">
                  <template #icon><PlusOutlined /></template>
                  Add {{ cfg.label }}
                </AButton>
              </div>

              <ATable
                :columns="cfg.columns"
                :data-source="cfg.dataRef.value"
                row-key="id"
                size="small"
                :pagination="false"
                :scroll="{ x: 600 }"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'actions'">
                    <ASpace :size="4">
                      <AButton type="link" size="small" @click="openEdit(key, record)">
                        <template #icon><EditOutlined /></template>
                      </AButton>
                      <APopconfirm
                        :title="`Delete this ${cfg.label.toLowerCase()}?`"
                        ok-text="Yes"
                        cancel-text="No"
                        @confirm="handleDelete(key, record)"
                      >
                        <AButton type="link" size="small" danger>
                          <template #icon><DeleteOutlined /></template>
                        </AButton>
                      </APopconfirm>
                    </ASpace>
                  </template>
                </template>
                <template #emptyText>
                  <div class="py-6 text-center text-gray-400">
                    No {{ cfg.label.toLowerCase() }} entries yet.
                    <a class="ml-1" @click="openAdd(key)">Add one</a>
                  </div>
                </template>
              </ATable>
            </ATabPane>

            <!-- ═══ Photos Tab (custom upload UI) ═══ -->
            <ATabPane key="photos" tab="Photos">
              <div class="mb-3 flex justify-end">
                <AButton type="primary" size="small" @click="openPhotoUpload">
                  <template #icon><CameraOutlined /></template>
                  Upload Photos
                </AButton>
              </div>

              <!-- Photo grid -->
              <div v-if="photos.length > 0" style="display: flex; flex-wrap: wrap; gap: 12px;">
                <div
                  v-for="photo in photos"
                  :key="photo.id"
                  style="width: 200px; border: 1px solid #f0f0f0; border-radius: 8px; overflow: hidden; background: #fafafa;"
                >
                  <div style="height: 150px; display: flex; align-items: center; justify-content: center; background: #f5f5f5;">
                    <img
                      v-if="photo.file_url"
                      :src="photo.file_url"
                      :alt="photo.name"
                      style="max-width: 100%; max-height: 150px; object-fit: cover;"
                    />
                    <CameraOutlined v-else style="font-size: 40px; color: #d9d9d9;" />
                  </div>
                  <div style="padding: 8px;">
                    <div style="font-size: 12px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                      {{ photo.name }}
                    </div>
                    <div style="font-size: 10px; color: #888; margin-top: 2px;">
                      {{ photo.file_name || '' }}
                    </div>
                    <div v-if="photo.album" style="font-size: 10px; color: #888;">
                      Album: {{ photo.album }}
                    </div>
                    <div style="margin-top: 6px; text-align: right;">
                      <APopconfirm title="Delete this photo?" @confirm="handleDeletePhoto(photo)">
                        <AButton type="link" size="small" danger>
                          <template #icon><DeleteOutlined /></template>
                        </AButton>
                      </APopconfirm>
                    </div>
                  </div>
                </div>
              </div>
              <AEmpty v-else description="No photos yet. Click 'Upload Photos' to add." />
            </ATabPane>
          </ATabs>
        </ACard>

        <!-- Photo Upload Modal -->
        <AModal
          v-model:open="photoUploadVisible"
          title="Upload Photos"
          :confirm-loading="photoUploading"
          width="520px"
          @ok="handlePhotoUpload"
        >
          <AForm layout="vertical" style="margin-top: 12px;">
            <AFormItem label="Photos">
              <AUpload
                :before-upload="() => false"
                :multiple="true"
                accept="image/*"
                list-type="picture-card"
                @change="handlePhotoFileChange"
              >
                <div>
                  <PlusOutlined />
                  <div style="margin-top: 8px;">Select</div>
                </div>
              </AUpload>
            </AFormItem>
            <ARow :gutter="16">
              <ACol :span="8">
                <AFormItem label="Caption">
                  <AInput v-model:value="photoUploadForm.name" placeholder="Photo name" />
                </AFormItem>
              </ACol>
              <ACol :span="8">
                <AFormItem label="Location">
                  <AInput v-model:value="photoUploadForm.location" placeholder="e.g. Floor 3" />
                </AFormItem>
              </ACol>
              <ACol :span="8">
                <AFormItem label="Album">
                  <AInput v-model:value="photoUploadForm.album" placeholder="e.g. Exterior" />
                </AFormItem>
              </ACol>
            </ARow>
          </AForm>
        </AModal>

      </template>

      <AEmpty v-else-if="!loading" description="Daily log not found" />
    </ASpin>

    <!-- ======= Shared Add/Edit Modal ======= -->
    <AModal
      v-model:open="modalVisible"
      :title="modalTitle"
      :confirm-loading="modalSaving"
      width="640px"
      @ok="handleModalSave"
      @cancel="modalVisible = false"
    >
      <AForm layout="vertical" style="margin-top: 12px;">
        <template v-for="field in currentConfig.fields" :key="field.key">
          <!-- Text input -->
          <AFormItem v-if="field.type === 'text'" :label="field.label" :required="field.required">
            <AInput v-model:value="formData[field.key]" :placeholder="`Enter ${field.label.toLowerCase()}`" />
          </AFormItem>

          <!-- Textarea -->
          <AFormItem v-else-if="field.type === 'textarea'" :label="field.label" :required="field.required">
            <ATextarea v-model:value="formData[field.key]" :placeholder="`Enter ${field.label.toLowerCase()}`" :rows="3" />
          </AFormItem>

          <!-- Number -->
          <AFormItem v-else-if="field.type === 'number'" :label="field.label" :required="field.required">
            <AInputNumber v-model:value="formData[field.key]" :placeholder="field.label" style="width: 100%;" />
          </AFormItem>

          <!-- Select (lookup dropdown) -->
          <AFormItem v-else-if="field.type === 'select'" :label="field.label" :required="field.required">
            <ASelect
              v-model:value="formData[field.key]"
              :options="lookups[field.optionsKey] || []"
              :placeholder="`Select ${field.label.toLowerCase()}`"
              allow-clear
              show-search
              :filter-option="(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
              style="width: 100%;"
            />
          </AFormItem>

          <!-- Datetime -->
          <AFormItem v-else-if="field.type === 'datetime'" :label="field.label" :required="field.required">
            <ADatePicker
              v-model:value="formData[field.key]"
              show-time
              style="width: 100%;"
              value-format="YYYY-MM-DDTHH:mm:ss"
              :placeholder="`Select ${field.label.toLowerCase()}`"
            />
          </AFormItem>

          <!-- Checkbox -->
          <AFormItem v-else-if="field.type === 'checkbox'" :label="field.label">
            <ACheckbox v-model:checked="formData[field.key]">{{ field.label }}</ACheckbox>
          </AFormItem>
        </template>
      </AForm>
    </AModal>
  </div>
</template>
