<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { requestClient } from '#/api/request';
import { message, Tabs } from 'ant-design-vue';
import {
  ArrowLeftOutlined,
  CalculatorOutlined,
  CheckOutlined,
  CopyOutlined,
  DeleteOutlined,
  DollarOutlined,
  EditOutlined,
  FileTextOutlined,
  PlusOutlined,
  SendOutlined,
} from '@ant-design/icons-vue';

defineOptions({ name: 'AGCMEstimateDetail' });

const BASE = '/agcm_estimate';
const route = useRoute();
const router = useRouter();

const estimateId = computed(() => route.query.id);
const isNew = computed(() => estimateId.value === 'new');

function getAccessToken() {
  try {
    return localStorage?.getItem('accessToken') || '';
  } catch {
    return '';
  }
}

const loading = ref(false);
const saving = ref(false);
const estimate = ref(null);
const groups = ref([]);
const markups = ref([]);
const activeGroupKeys = ref([]);
const activeTab = ref('groups');

// ---- Formatters ----
function fmtCurrency(val) {
  if (val == null) return '$0.00';
  return Number(val).toLocaleString('en-US', { style: 'currency', currency: 'USD' });
}
function fmtPct(val) {
  if (val == null) return '0.0%';
  return `${Number(val).toFixed(1)}%`;
}
function fmtLabel(str) {
  if (!str) return '';
  return str.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

const statusColors = {
  draft: 'default', in_review: 'processing', approved: 'success',
  rejected: 'error', superseded: 'warning',
};
const typeColors = {
  material: 'blue', labor: 'green', equipment: 'orange',
  subcontractor: 'purple', fee: 'red', other: 'default',
};
const lineTypeOptions = [
  { value: 'material', label: 'Material' },
  { value: 'labor', label: 'Labor' },
  { value: 'equipment', label: 'Equipment' },
  { value: 'subcontractor', label: 'Subcontractor' },
  { value: 'fee', label: 'Fee' },
  { value: 'other', label: 'Other' },
];
const markupTypeOptions = [
  { value: 'percentage', label: 'Percentage (%)' },
  { value: 'lump_sum', label: 'Lump Sum ($)' },
];

// ---- Projects (for new estimate) ----
const projects = ref([]);
const newForm = reactive({
  project_id: null,
  name: '',
  estimate_type: 'detailed',
  description: '',
});
const estimateTypeOptions = [
  { value: 'preliminary', label: 'Preliminary' },
  { value: 'schematic', label: 'Schematic' },
  { value: 'detailed', label: 'Detailed' },
  { value: 'change_order', label: 'Change Order' },
];

// ---- Inline editing ----
const editingCell = ref(null); // { lineId, field }
const editingValue = ref(null);

// ---- New line item form per group ----
const newLineVisible = ref(null); // group id
const newLine = reactive({
  name: '', item_type: 'material', quantity: 1, unit: '', unit_cost: 0,
  markup_pct: 0, taxable: false, cost_code: '', description: '',
});

// ---- New group form ----
const newGroupVisible = ref(false);
const newGroupName = ref('');

// ---- Catalog modal ----
const catalogModalVisible = ref(false);
const catalogGroupId = ref(null);
const catalogItems = ref([]);
const catalogLoading = ref(false);

// ---- Assembly modal ----
const assemblyModalVisible = ref(false);
const assemblyGroupId = ref(null);
const assemblies = ref([]);
const assemblyLoading = ref(false);
const assemblyQuantity = ref(1);

// ---- New markup form ----
const newMarkupVisible = ref(false);
const newMarkup = reactive({
  name: '', markup_type: 'percentage', value: 0, before_tax: true, compounding: false,
});

// ---- Line item columns ----
const lineColumns = [
  { title: 'Name', dataIndex: 'name', key: 'name', ellipsis: true },
  { title: 'Type', key: 'item_type', width: 110 },
  { title: 'Qty', key: 'quantity', width: 80, align: 'right' },
  { title: 'Unit', dataIndex: 'unit', key: 'unit', width: 70 },
  { title: 'Unit Cost', key: 'unit_cost', width: 110, align: 'right' },
  { title: 'Markup%', key: 'markup_pct', width: 90, align: 'right' },
  { title: 'Unit Price', key: 'unit_price', width: 110, align: 'right' },
  { title: 'Total Cost', key: 'total_cost', width: 120, align: 'right' },
  { title: 'Total Price', key: 'total_price', width: 120, align: 'right' },
  { title: 'Tax', key: 'taxable', width: 60, align: 'center' },
  { title: 'Cost Code', dataIndex: 'cost_code', key: 'cost_code', width: 100 },
  { title: '', key: 'actions', width: 80, fixed: 'right' },
];

const markupColumns = [
  { title: 'Name', dataIndex: 'name', key: 'name', ellipsis: true },
  { title: 'Type', key: 'markup_type', width: 130 },
  { title: 'Value', key: 'value', width: 110, align: 'right' },
  { title: 'Before Tax?', key: 'before_tax', width: 100, align: 'center' },
  { title: 'Compounding?', key: 'compounding', width: 110, align: 'center' },
  { title: 'Amount', key: 'calculated_amount', width: 130, align: 'right' },
  { title: '', key: 'actions', width: 80, fixed: 'right' },
];

// ---- Load ----
async function fetchEstimate() {
  if (isNew.value) {
    try {
      const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
      projects.value = (data.items || []).map(p => ({
        value: p.id, label: `${p.sequence_name || ''} - ${p.name}`,
      }));
    } catch { /* ignore */ }
    return;
  }
  loading.value = true;
  try {
    const data = await requestClient.get(`${BASE}/estimates/${estimateId.value}`);
    estimate.value = data;
    groups.value = (data.groups || []).map(g => ({
      ...g,
      line_items: g.line_items || [],
    }));
    markups.value = data.markups || [];
    activeGroupKeys.value = groups.value.map(g => g.id);
  } catch {
    message.error('Failed to load estimate');
  } finally {
    loading.value = false;
  }
}

async function handleCreateEstimate() {
  if (!newForm.project_id || !newForm.name) {
    message.warning('Project and name are required');
    return;
  }
  saving.value = true;
  try {
    const res = await requestClient.post(`${BASE}/estimates`, { ...newForm });
    message.success('Estimate created');
    router.replace({ path: '/agcm/estimate/estimates/detail', query: { id: res.id } });
  } catch {
    message.error('Failed to create estimate');
  } finally {
    saving.value = false;
  }
}

// ---- Header actions ----
async function handleRecalculate() {
  try {
    await requestClient.post(`${BASE}/estimates/${estimateId.value}/recalculate`);
    message.success('Recalculated');
    fetchEstimate();
  } catch { message.error('Recalculation failed'); }
}

async function handleCreateVersion() {
  try {
    const res = await requestClient.post(`${BASE}/estimates/${estimateId.value}/create-version`);
    message.success('New version created');
    router.push({ path: '/agcm/estimate/estimates/detail', query: { id: res.id } });
  } catch { message.error('Failed to create version'); }
}

async function handleSendToBudget() {
  try {
    await requestClient.post(`${BASE}/estimates/${estimateId.value}/send-to-budget`);
    message.success('Sent to budget');
    fetchEstimate();
  } catch { message.error('Failed to send to budget'); }
}

async function handleApprove() {
  try {
    await requestClient.post(`${BASE}/estimates/${estimateId.value}/approve`);
    message.success('Estimate approved');
    fetchEstimate();
  } catch { message.error('Failed to approve'); }
}

async function handleGenerateProposal() {
  router.push({ path: '/agcm/estimate/proposals', query: { from_estimate: estimateId.value } });
}

// ---- Inline name editing ----
const editingName = ref(false);
const editNameValue = ref('');

function startEditName() {
  editNameValue.value = estimate.value?.name || '';
  editingName.value = true;
}

async function saveName() {
  if (!editNameValue.value) return;
  try {
    await requestClient.put(`${BASE}/estimates/${estimateId.value}`, { name: editNameValue.value });
    estimate.value.name = editNameValue.value;
    editingName.value = false;
  } catch { message.error('Failed to update name'); }
}

// ---- Notes ----
const editingNotes = ref(false);
const notesValue = ref('');

function startEditNotes() {
  notesValue.value = estimate.value?.notes || '';
  editingNotes.value = true;
}

async function saveNotes() {
  try {
    await requestClient.put(`${BASE}/estimates/${estimateId.value}`, { notes: notesValue.value });
    estimate.value.notes = notesValue.value;
    editingNotes.value = false;
    message.success('Notes saved');
  } catch { message.error('Failed to save notes'); }
}

// ---- Groups ----
async function addGroup() {
  if (!newGroupName.value) { message.warning('Group name is required'); return; }
  try {
    const res = await requestClient.post(`${BASE}/estimate-groups`, {
      estimate_id: estimateId.value,
      name: newGroupName.value,
    });
    groups.value.push({ ...res, line_items: [] });
    activeGroupKeys.value.push(res.id);
    newGroupName.value = '';
    newGroupVisible.value = false;
    message.success('Group added');
  } catch { message.error('Failed to add group'); }
}

async function deleteGroup(groupId) {
  try {
    await requestClient.delete(`${BASE}/estimate-groups/${groupId}`);
    groups.value = groups.value.filter(g => g.id !== groupId);
    message.success('Group deleted');
  } catch { message.error('Failed to delete group'); }
}

async function updateGroupName(group) {
  try {
    await requestClient.put(`${BASE}/estimate-groups/${group.id}`, { name: group.name });
  } catch { message.error('Failed to update group'); }
}

// ---- Line items: inline edit ----
function startInlineEdit(lineId, field, currentVal) {
  editingCell.value = { lineId, field };
  editingValue.value = currentVal;
}

function calcLine(line) {
  const uc = Number(line.unit_cost) || 0;
  const mp = Number(line.markup_pct) || 0;
  const qty = Number(line.quantity) || 0;
  line.unit_price = uc * (1 + mp / 100);
  line.total_cost = qty * uc;
  line.total_price = qty * line.unit_price;
}

async function saveInlineEdit(line) {
  if (!editingCell.value) return;
  const field = editingCell.value.field;
  line[field] = Number(editingValue.value) || 0;
  calcLine(line);
  editingCell.value = null;
  try {
    await requestClient.put(`${BASE}/estimate-line-items/${line.id}`, {
      [field]: line[field],
      unit_price: line.unit_price,
      total_cost: line.total_cost,
      total_price: line.total_price,
    });
  } catch { message.error('Failed to update line item'); }
}

function cancelInlineEdit() {
  editingCell.value = null;
}

function isEditing(lineId, field) {
  return editingCell.value && editingCell.value.lineId === lineId && editingCell.value.field === field;
}

// ---- Add line item ----
function openNewLine(groupId) {
  newLineVisible.value = groupId;
  Object.assign(newLine, {
    name: '', item_type: 'material', quantity: 1, unit: '', unit_cost: 0,
    markup_pct: 0, taxable: false, cost_code: '', description: '',
  });
}

async function saveNewLine(group) {
  if (!newLine.name) { message.warning('Name is required'); return; }
  const unitPrice = (newLine.unit_cost || 0) * (1 + (newLine.markup_pct || 0) / 100);
  const totalCost = (newLine.quantity || 0) * (newLine.unit_cost || 0);
  const totalPrice = (newLine.quantity || 0) * unitPrice;
  try {
    const res = await requestClient.post(`${BASE}/estimate-line-items`, {
      group_id: group.id,
      estimate_id: estimateId.value,
      ...newLine,
      unit_price: unitPrice,
      total_cost: totalCost,
      total_price: totalPrice,
    });
    group.line_items.push(res);
    newLineVisible.value = null;
    message.success('Line item added');
  } catch { message.error('Failed to add line item'); }
}

async function deleteLineItem(group, lineId) {
  try {
    await requestClient.delete(`${BASE}/estimate-line-items/${lineId}`);
    group.line_items = group.line_items.filter(l => l.id !== lineId);
    message.success('Line item deleted');
  } catch { message.error('Failed to delete line item'); }
}

async function toggleTaxable(line) {
  line.taxable = !line.taxable;
  try {
    await requestClient.put(`${BASE}/estimate-line-items/${line.id}`, { taxable: line.taxable });
  } catch { message.error('Failed to update'); }
}

// ---- Catalog picker ----
async function openCatalogModal(groupId) {
  catalogGroupId.value = groupId;
  catalogLoading.value = true;
  catalogModalVisible.value = true;
  try {
    const res = await requestClient.get(`${BASE}/cost-items`, { params: { page_size: 200, active: true } });
    catalogItems.value = res.items || res || [];
  } catch { catalogItems.value = []; }
  finally { catalogLoading.value = false; }
}

async function addCatalogItem(ci) {
  const group = groups.value.find(g => g.id === catalogGroupId.value);
  if (!group) return;
  const unitPrice = (ci.unit_cost || 0) * 1; // no markup by default from catalog
  try {
    const res = await requestClient.post(`${BASE}/estimate-line-items`, {
      group_id: group.id,
      estimate_id: estimateId.value,
      name: ci.name,
      item_type: ci.item_type,
      quantity: 1,
      unit: ci.unit || '',
      unit_cost: ci.unit_cost || 0,
      markup_pct: 0,
      unit_price: ci.unit_cost || 0,
      total_cost: ci.unit_cost || 0,
      total_price: ci.unit_cost || 0,
      taxable: ci.taxable || false,
      cost_code: ci.cost_code || '',
      cost_item_id: ci.id,
    });
    group.line_items.push(res);
    message.success(`Added "${ci.name}"`);
  } catch { message.error('Failed to add item'); }
  catalogModalVisible.value = false;
}

// ---- Assembly picker ----
async function openAssemblyModal(groupId) {
  assemblyGroupId.value = groupId;
  assemblyLoading.value = true;
  assemblyModalVisible.value = true;
  assemblyQuantity.value = 1;
  try {
    const res = await requestClient.get(`${BASE}/assemblies`, { params: { page_size: 200, active: true } });
    assemblies.value = res.items || res || [];
  } catch { assemblies.value = []; }
  finally { assemblyLoading.value = false; }
}

async function addAssembly(assembly) {
  try {
    await requestClient.post(`${BASE}/estimates/${estimateId.value}/add-assembly`, {
      group_id: assemblyGroupId.value,
      assembly_id: assembly.id,
      quantity_multiplier: assemblyQuantity.value,
    });
    message.success(`Assembly "${assembly.name}" added`);
    assemblyModalVisible.value = false;
    fetchEstimate(); // reload all to get expanded lines
  } catch { message.error('Failed to add assembly'); }
}

// ---- Markups ----
async function addMarkup() {
  if (!newMarkup.name) { message.warning('Name is required'); return; }
  try {
    const res = await requestClient.post(`${BASE}/estimate-markups`, {
      estimate_id: estimateId.value,
      ...newMarkup,
    });
    markups.value.push(res);
    newMarkupVisible.value = false;
    Object.assign(newMarkup, { name: '', markup_type: 'percentage', value: 0, before_tax: true, compounding: false });
    message.success('Markup added');
  } catch { message.error('Failed to add markup'); }
}

async function deleteMarkup(id) {
  try {
    await requestClient.delete(`${BASE}/estimate-markups/${id}`);
    markups.value = markups.value.filter(m => m.id !== id);
    message.success('Markup deleted');
  } catch { message.error('Failed to delete markup'); }
}

async function saveMarkupField(markup, field, val) {
  markup[field] = val;
  try {
    await requestClient.put(`${BASE}/estimate-markups/${markup.id}`, { [field]: val });
  } catch { message.error('Failed to update markup'); }
}

// ---- Group subtotal ----
function groupSubtotal(group) {
  return (group.line_items || []).reduce((s, l) => s + (Number(l.total_price) || 0), 0);
}

onMounted(fetchEstimate);
</script>

<template>
  <Page>
    <!-- New Estimate Form -->
    <template v-if="isNew">
      <ACard title="Create New Estimate">
        <AForm layout="vertical" style="max-width: 600px">
          <AFormItem label="Project" required>
            <ASelect
              v-model:value="newForm.project_id"
              :options="projects"
              placeholder="Select project"
              show-search
              :filter-option="(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
            />
          </AFormItem>
          <AFormItem label="Estimate Name" required>
            <AInput v-model:value="newForm.name" placeholder="e.g. Phase 1 - Detailed Estimate" />
          </AFormItem>
          <AFormItem label="Type">
            <ASelect v-model:value="newForm.estimate_type" :options="estimateTypeOptions" />
          </AFormItem>
          <AFormItem label="Description">
            <ATextarea v-model:value="newForm.description" :rows="3" />
          </AFormItem>
          <ASpace>
            <AButton @click="router.back()">Cancel</AButton>
            <AButton type="primary" :loading="saving" @click="handleCreateEstimate">Create Estimate</AButton>
          </ASpace>
        </AForm>
      </ACard>
    </template>

    <!-- Estimate Detail -->
    <template v-else>
      <ASpin :spinning="loading">
        <!-- Header -->
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px">
          <ASpace align="center">
            <AButton @click="router.push('/agcm/estimate/estimates')">
              <template #icon><ArrowLeftOutlined /></template>
            </AButton>
            <template v-if="editingName">
              <AInput
                v-model:value="editNameValue"
                style="width: 320px; font-size: 20px; font-weight: 600"
                @press-enter="saveName"
                @blur="saveName"
              />
            </template>
            <template v-else>
              <h2 style="margin: 0; cursor: pointer" @click="startEditName">
                {{ estimate?.name || 'Estimate' }}
                <EditOutlined style="font-size: 14px; color: #999; margin-left: 8px" />
              </h2>
            </template>
            <ATag v-if="estimate?.version">v{{ estimate.version }}</ATag>
            <ABadge
              v-if="estimate?.status"
              :status="statusColors[estimate.status] || 'default'"
              :text="fmtLabel(estimate.status)"
            />
          </ASpace>
          <ASpace>
            <AButton @click="handleRecalculate">
              <template #icon><CalculatorOutlined /></template>
              Recalculate
            </AButton>
            <AButton @click="handleCreateVersion">
              <template #icon><CopyOutlined /></template>
              Create Version
            </AButton>
            <AButton @click="handleSendToBudget">
              <template #icon><SendOutlined /></template>
              Send to Budget
            </AButton>
            <AButton @click="handleGenerateProposal">
              <template #icon><FileTextOutlined /></template>
              Generate Proposal
            </AButton>
            <AButton type="primary" @click="handleApprove">
              <template #icon><CheckOutlined /></template>
              Approve
            </AButton>
          </ASpace>
        </div>

        <!-- Summary Cards -->
        <div class="estimate-summary-cards">
          <ACard size="small">
            <AStatistic title="Direct Cost" :value="estimate?.subtotal || 0" :precision="2" prefix="$" />
          </ACard>
          <ACard size="small">
            <AStatistic title="Markup" :value="estimate?.markup_total || 0" :precision="2" prefix="$" />
          </ACard>
          <ACard size="small">
            <AStatistic title="Tax" :value="estimate?.tax_total || 0" :precision="2" prefix="$" />
          </ACard>
          <ACard size="small">
            <AStatistic title="Grand Total" :value="estimate?.grand_total || 0" :precision="2" prefix="$" value-style="color: #52c41a; font-weight: 700" />
          </ACard>
        </div>

        <!-- Groups & Line Items -->
        <ACard title="Groups & Line Items" style="margin-bottom: 16px">
          <template #extra>
            <ASpace>
              <AButton size="small" @click="newGroupVisible = true">
                <template #icon><PlusOutlined /></template>
                Add Group
              </AButton>
            </ASpace>
          </template>

          <!-- New group inline -->
          <div v-if="newGroupVisible" style="margin-bottom: 12px; display: flex; gap: 8px">
            <AInput v-model:value="newGroupName" placeholder="Group name" style="width: 300px" @press-enter="addGroup" />
            <AButton type="primary" size="small" @click="addGroup">Add</AButton>
            <AButton size="small" @click="newGroupVisible = false">Cancel</AButton>
          </div>

          <ACollapse v-model:activeKey="activeGroupKeys">
            <ACollapsePanel v-for="group in groups" :key="group.id">
              <template #header>
                <div class="group-header" @click.stop>
                  <div class="group-header-left">
                    <strong>{{ group.name }}</strong>
                    <span class="group-subtotal">{{ fmtCurrency(groupSubtotal(group)) }}</span>
                  </div>
                  <ASpace>
                    <AButton type="link" size="small" @click.stop="openCatalogModal(group.id)">+ Catalog</AButton>
                    <AButton type="link" size="small" @click.stop="openAssemblyModal(group.id)">+ Assembly</AButton>
                    <APopconfirm title="Delete this group and all its items?" @confirm="deleteGroup(group.id)">
                      <AButton type="link" size="small" danger @click.stop>
                        <template #icon><DeleteOutlined /></template>
                      </AButton>
                    </APopconfirm>
                  </ASpace>
                </div>
              </template>

              <ATable
                :columns="lineColumns"
                :data-source="group.line_items"
                row-key="id"
                size="small"
                :pagination="false"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'item_type'">
                    <ATag :color="typeColors[record.item_type] || 'default'" size="small">
                      {{ (record.item_type || '').replace(/^\w/, c => c.toUpperCase()) }}
                    </ATag>
                  </template>

                  <!-- Inline editable: quantity -->
                  <template v-else-if="column.key === 'quantity'">
                    <template v-if="isEditing(record.id, 'quantity')">
                      <AInputNumber
                        v-model:value="editingValue"
                        size="small"
                        :min="0"
                        style="width: 70px"
                        @press-enter="saveInlineEdit(record)"
                        @blur="saveInlineEdit(record)"
                        autofocus
                      />
                    </template>
                    <span v-else class="inline-edit-cell" @click="startInlineEdit(record.id, 'quantity', record.quantity)">
                      {{ record.quantity }}
                    </span>
                  </template>

                  <!-- Inline editable: unit_cost -->
                  <template v-else-if="column.key === 'unit_cost'">
                    <template v-if="isEditing(record.id, 'unit_cost')">
                      <AInputNumber
                        v-model:value="editingValue"
                        size="small"
                        :min="0"
                        :precision="2"
                        style="width: 100px"
                        @press-enter="saveInlineEdit(record)"
                        @blur="saveInlineEdit(record)"
                        autofocus
                      />
                    </template>
                    <span v-else class="inline-edit-cell" @click="startInlineEdit(record.id, 'unit_cost', record.unit_cost)">
                      {{ fmtCurrency(record.unit_cost) }}
                    </span>
                  </template>

                  <!-- Inline editable: markup_pct -->
                  <template v-else-if="column.key === 'markup_pct'">
                    <template v-if="isEditing(record.id, 'markup_pct')">
                      <AInputNumber
                        v-model:value="editingValue"
                        size="small"
                        :min="0"
                        :precision="1"
                        style="width: 80px"
                        @press-enter="saveInlineEdit(record)"
                        @blur="saveInlineEdit(record)"
                        autofocus
                      />
                    </template>
                    <span v-else class="inline-edit-cell" @click="startInlineEdit(record.id, 'markup_pct', record.markup_pct)">
                      {{ fmtPct(record.markup_pct) }}
                    </span>
                  </template>

                  <template v-else-if="column.key === 'unit_price'">
                    {{ fmtCurrency(record.unit_price) }}
                  </template>
                  <template v-else-if="column.key === 'total_cost'">
                    {{ fmtCurrency(record.total_cost) }}
                  </template>
                  <template v-else-if="column.key === 'total_price'">
                    <strong>{{ fmtCurrency(record.total_price) }}</strong>
                  </template>
                  <template v-else-if="column.key === 'taxable'">
                    <ACheckbox :checked="record.taxable" @change="toggleTaxable(record)" />
                  </template>
                  <template v-else-if="column.key === 'actions'">
                    <APopconfirm title="Delete?" @confirm="deleteLineItem(group, record.id)">
                      <AButton type="link" size="small" danger>
                        <template #icon><DeleteOutlined /></template>
                      </AButton>
                    </APopconfirm>
                  </template>
                </template>
              </ATable>

              <!-- Add line item inline form -->
              <div v-if="newLineVisible === group.id" style="margin-top: 12px; border: 1px dashed #d9d9d9; padding: 12px; border-radius: 4px">
                <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: flex-end">
                  <div>
                    <small>Name</small>
                    <AInput v-model:value="newLine.name" size="small" style="width: 160px" />
                  </div>
                  <div>
                    <small>Type</small>
                    <ASelect v-model:value="newLine.item_type" :options="lineTypeOptions" size="small" style="width: 120px" />
                  </div>
                  <div>
                    <small>Qty</small>
                    <AInputNumber v-model:value="newLine.quantity" :min="0" size="small" style="width: 70px" />
                  </div>
                  <div>
                    <small>Unit</small>
                    <AInput v-model:value="newLine.unit" size="small" style="width: 60px" />
                  </div>
                  <div>
                    <small>Unit Cost</small>
                    <AInputNumber v-model:value="newLine.unit_cost" :min="0" :precision="2" size="small" style="width: 100px" />
                  </div>
                  <div>
                    <small>Markup%</small>
                    <AInputNumber v-model:value="newLine.markup_pct" :min="0" :precision="1" size="small" style="width: 80px" />
                  </div>
                  <div>
                    <small>Cost Code</small>
                    <AInput v-model:value="newLine.cost_code" size="small" style="width: 90px" />
                  </div>
                  <ACheckbox v-model:checked="newLine.taxable">Taxable</ACheckbox>
                </div>
                <ASpace style="margin-top: 8px">
                  <AButton type="primary" size="small" @click="saveNewLine(group)">Add</AButton>
                  <AButton size="small" @click="newLineVisible = null">Cancel</AButton>
                </ASpace>
              </div>
              <AButton
                v-else
                type="dashed"
                block
                size="small"
                style="margin-top: 8px"
                @click="openNewLine(group.id)"
              >
                <template #icon><PlusOutlined /></template>
                Add Line Item
              </AButton>
            </ACollapsePanel>
          </ACollapse>

          <AEmpty v-if="!groups.length" description="No groups yet. Add a group to start estimating." />
        </ACard>

        <!-- Markups Section -->
        <ACard title="Markups" style="margin-bottom: 16px">
          <template #extra>
            <AButton size="small" @click="newMarkupVisible = true">
              <template #icon><PlusOutlined /></template>
              Add Markup
            </AButton>
          </template>

          <!-- New markup form -->
          <div v-if="newMarkupVisible" style="margin-bottom: 12px; display: flex; gap: 8px; align-items: flex-end; flex-wrap: wrap">
            <div>
              <small>Name</small>
              <AInput v-model:value="newMarkup.name" size="small" style="width: 180px" />
            </div>
            <div>
              <small>Type</small>
              <ASelect v-model:value="newMarkup.markup_type" :options="markupTypeOptions" size="small" style="width: 140px" />
            </div>
            <div>
              <small>Value</small>
              <AInputNumber v-model:value="newMarkup.value" :min="0" :precision="2" size="small" style="width: 100px" />
            </div>
            <ACheckbox v-model:checked="newMarkup.before_tax">Before Tax</ACheckbox>
            <ACheckbox v-model:checked="newMarkup.compounding">Compounding</ACheckbox>
            <AButton type="primary" size="small" @click="addMarkup">Add</AButton>
            <AButton size="small" @click="newMarkupVisible = false">Cancel</AButton>
          </div>

          <ATable
            :columns="markupColumns"
            :data-source="markups"
            row-key="id"
            size="small"
            :pagination="false"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'markup_type'">
                <ATag :color="record.markup_type === 'percentage' ? 'blue' : 'green'">
                  {{ record.markup_type === 'percentage' ? 'Percentage' : 'Lump Sum' }}
                </ATag>
              </template>
              <template v-else-if="column.key === 'value'">
                {{ record.markup_type === 'percentage' ? fmtPct(record.value) : fmtCurrency(record.value) }}
              </template>
              <template v-else-if="column.key === 'before_tax'">
                <ACheckbox :checked="record.before_tax" @change="saveMarkupField(record, 'before_tax', !record.before_tax)" />
              </template>
              <template v-else-if="column.key === 'compounding'">
                <ACheckbox :checked="record.compounding" @change="saveMarkupField(record, 'compounding', !record.compounding)" />
              </template>
              <template v-else-if="column.key === 'calculated_amount'">
                <strong>{{ fmtCurrency(record.calculated_amount) }}</strong>
              </template>
              <template v-else-if="column.key === 'actions'">
                <APopconfirm title="Delete this markup?" @confirm="deleteMarkup(record.id)">
                  <AButton type="link" size="small" danger>
                    <template #icon><DeleteOutlined /></template>
                  </AButton>
                </APopconfirm>
              </template>
            </template>
          </ATable>
          <AEmpty v-if="!markups.length" description="No markups applied." />
        </ACard>

        <!-- Notes Section -->
        <ACard title="Notes" class="notes-section">
          <template v-if="editingNotes">
            <ATextarea v-model:value="notesValue" :rows="4" />
            <ASpace style="margin-top: 8px">
              <AButton type="primary" size="small" @click="saveNotes">Save</AButton>
              <AButton size="small" @click="editingNotes = false">Cancel</AButton>
            </ASpace>
          </template>
          <template v-else>
            <p style="white-space: pre-wrap; color: #666; min-height: 40px; cursor: pointer" @click="startEditNotes">
              {{ estimate?.notes || 'Click to add notes...' }}
            </p>
          </template>
        </ACard>

        <!-- Activity Section -->
        <ACard title="Activity" class="mt-4">
          <ActivityThread
            :model-name="'agcm_estimates'"
            :record-id="estimateId"
            :access-token="getAccessToken()"
            :api-base="'/api/v1'"
            :show-messages="true"
            :show-activities="true"
          />
        </ACard>
      </ASpin>
    </template>

    <!-- Catalog Picker Modal -->
    <AModal
      v-model:open="catalogModalVisible"
      title="Add from Cost Catalog"
      :footer="null"
      :width="650"
    >
      <ASpin :spinning="catalogLoading">
        <ATable
          :data-source="catalogItems"
          row-key="id"
          size="small"
          :pagination="{ pageSize: 10 }"
          :columns="[
            { title: 'Name', dataIndex: 'name', key: 'name' },
            { title: 'Type', dataIndex: 'item_type', key: 'item_type', width: 110 },
            { title: 'Unit', dataIndex: 'unit', key: 'unit', width: 70 },
            { title: 'Unit Cost', key: 'uc', width: 110 },
            { title: '', key: 'add', width: 70 },
          ]"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'uc'">{{ fmtCurrency(record.unit_cost) }}</template>
            <template v-else-if="column.key === 'add'">
              <AButton type="link" size="small" @click="addCatalogItem(record)">Add</AButton>
            </template>
          </template>
        </ATable>
      </ASpin>
    </AModal>

    <!-- Assembly Picker Modal -->
    <AModal
      v-model:open="assemblyModalVisible"
      title="Add Assembly"
      :footer="null"
      :width="600"
    >
      <div style="margin-bottom: 12px">
        <label>Quantity Multiplier: </label>
        <AInputNumber v-model:value="assemblyQuantity" :min="1" :precision="0" style="width: 100px" />
      </div>
      <ASpin :spinning="assemblyLoading">
        <ATable
          :data-source="assemblies"
          row-key="id"
          size="small"
          :pagination="{ pageSize: 10 }"
          :columns="[
            { title: 'Name', dataIndex: 'name', key: 'name' },
            { title: 'Category', dataIndex: 'category', key: 'category', width: 130 },
            { title: 'Items', dataIndex: 'item_count', key: 'item_count', width: 70 },
            { title: '', key: 'add', width: 70 },
          ]"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'add'">
              <AButton type="link" size="small" @click="addAssembly(record)">Add</AButton>
            </template>
          </template>
        </ATable>
      </ASpin>
    </AModal>
  </Page>
</template>
