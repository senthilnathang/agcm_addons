<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { requestClient } from '#/api/request';
import { message } from 'ant-design-vue';
import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';

defineOptions({ name: 'AGCMAssemblies' });

const BASE = '/agcm_estimate';

const loading = ref(false);
const items = ref([]);
const expandedRowKeys = ref([]);

const drawerVisible = ref(false);
const drawerTitle = ref('New Assembly');
const drawerSaving = ref(false);
const editingId = ref(null);
const form = reactive({
  name: '',
  category: '',
  description: '',
  active: true,
});
const assemblyItems = ref([]);
const newItem = reactive({
  name: '', item_type: 'material', quantity: 1, unit: '', unit_cost: 0, waste_factor: 0,
});

const catalogItems = ref([]);
const catalogModalVisible = ref(false);

const typeOptions = [
  { value: 'material', label: 'Material' },
  { value: 'labor', label: 'Labor' },
  { value: 'equipment', label: 'Equipment' },
  { value: 'subcontractor', label: 'Subcontractor' },
  { value: 'fee', label: 'Fee' },
  { value: 'other', label: 'Other' },
];

const typeColors = {
  material: 'blue', labor: 'green', equipment: 'orange',
  subcontractor: 'purple', fee: 'red', other: 'default',
};

function fmtCurrency(val) {
  if (val == null) return '$0.00';
  return Number(val).toLocaleString('en-US', { style: 'currency', currency: 'USD' });
}

function calcTotalCost(items) {
  return (items || []).reduce((sum, i) => sum + (i.quantity || 0) * (i.unit_cost || 0) * (1 + (i.waste_factor || 0) / 100), 0);
}

const columns = computed(() => [
  { title: 'Name', dataIndex: 'name', key: 'name', ellipsis: true },
  { title: 'Category', dataIndex: 'category', key: 'category', width: 150 },
  { title: 'Items', key: 'item_count', width: 90, align: 'center' },
  { title: 'Total Cost', key: 'total_cost', width: 140, align: 'right' },
  { title: 'Active', key: 'active', width: 80, align: 'center' },
  { title: 'Actions', key: 'actions', width: 120, fixed: 'right' },
]);

const expandColumns = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Type', key: 'item_type', width: 120 },
  { title: 'Qty', dataIndex: 'quantity', key: 'quantity', width: 80, align: 'right' },
  { title: 'Unit', dataIndex: 'unit', key: 'unit', width: 80 },
  { title: 'Unit Cost', key: 'unit_cost', width: 120, align: 'right' },
  { title: 'Waste %', key: 'waste_factor', width: 100, align: 'right' },
  { title: 'Line Total', key: 'line_total', width: 120, align: 'right' },
];

const drawerItemColumns = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Type', key: 'item_type', width: 110 },
  { title: 'Qty', dataIndex: 'quantity', key: 'quantity', width: 70, align: 'right' },
  { title: 'Unit', dataIndex: 'unit', key: 'unit', width: 70 },
  { title: 'Unit Cost', key: 'unit_cost', width: 100, align: 'right' },
  { title: 'Waste %', key: 'waste_factor', width: 90, align: 'right' },
  { title: '', key: 'remove', width: 50 },
];

async function fetchData() {
  loading.value = true;
  try {
    const res = await requestClient.get(`${BASE}/assemblies`, { params: { page_size: 200 } });
    items.value = res.items || res || [];
  } catch {
    message.error('Failed to load assemblies');
  } finally {
    loading.value = false;
  }
}

async function handleExpand(expanded, record) {
  if (expanded) {
    expandedRowKeys.value = [record.id];
    try {
      const detail = await requestClient.get(`${BASE}/assemblies/${record.id}`);
      record._items = detail.items || [];
    } catch {
      record._items = [];
    }
  } else {
    expandedRowKeys.value = [];
  }
}

function openNew() {
  editingId.value = null;
  drawerTitle.value = 'New Assembly';
  Object.assign(form, { name: '', category: '', description: '', active: true });
  assemblyItems.value = [];
  drawerVisible.value = true;
}

async function openEdit(record) {
  editingId.value = record.id;
  drawerTitle.value = 'Edit Assembly';
  Object.assign(form, {
    name: record.name,
    category: record.category || '',
    description: record.description || '',
    active: record.active !== false,
  });
  try {
    const detail = await requestClient.get(`${BASE}/assemblies/${record.id}`);
    assemblyItems.value = (detail.items || []).map(i => ({ ...i, _key: i.id || Math.random() }));
  } catch {
    assemblyItems.value = [];
  }
  drawerVisible.value = true;
}

function addBlankItem() {
  assemblyItems.value.push({
    _key: Math.random(),
    _new: true,
    name: newItem.name || 'New Item',
    item_type: newItem.item_type,
    quantity: newItem.quantity,
    unit: newItem.unit,
    unit_cost: newItem.unit_cost,
    waste_factor: newItem.waste_factor,
  });
  Object.assign(newItem, { name: '', item_type: 'material', quantity: 1, unit: '', unit_cost: 0, waste_factor: 0 });
}

function removeDrawerItem(index) {
  assemblyItems.value.splice(index, 1);
}

async function openCatalogPicker() {
  try {
    const res = await requestClient.get(`${BASE}/cost-items`, { params: { page_size: 200, active: true } });
    catalogItems.value = res.items || res || [];
  } catch {
    catalogItems.value = [];
  }
  catalogModalVisible.value = true;
}

function addFromCatalog(ci) {
  assemblyItems.value.push({
    _key: Math.random(),
    _new: true,
    name: ci.name,
    item_type: ci.item_type,
    quantity: 1,
    unit: ci.unit || '',
    unit_cost: ci.unit_cost || 0,
    waste_factor: 0,
    cost_item_id: ci.id,
  });
  catalogModalVisible.value = false;
}

async function saveAssembly() {
  if (!form.name) { message.warning('Name is required'); return; }
  drawerSaving.value = true;
  try {
    let assemblyId = editingId.value;
    const payload = { name: form.name, category: form.category, description: form.description, active: form.active };
    if (assemblyId) {
      await requestClient.put(`${BASE}/assemblies/${assemblyId}`, payload);
    } else {
      const res = await requestClient.post(`${BASE}/assemblies`, payload);
      assemblyId = res.id;
    }
    // Save items: delete removed, update existing, create new
    for (const item of assemblyItems.value) {
      const data = {
        assembly_id: assemblyId,
        name: item.name,
        item_type: item.item_type,
        quantity: item.quantity,
        unit: item.unit,
        unit_cost: item.unit_cost,
        waste_factor: item.waste_factor,
        cost_item_id: item.cost_item_id || undefined,
      };
      if (item._new) {
        await requestClient.post(`${BASE}/assembly-items`, data);
      } else if (item.id) {
        await requestClient.put(`${BASE}/assembly-items/${item.id}`, data);
      }
    }
    message.success(editingId.value ? 'Assembly updated' : 'Assembly created');
    drawerVisible.value = false;
    fetchData();
  } catch {
    message.error('Failed to save assembly');
  } finally {
    drawerSaving.value = false;
  }
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/assemblies/${record.id}`);
    message.success('Assembly deleted');
    fetchData();
  } catch {
    message.error('Failed to delete assembly');
  }
}

onMounted(fetchData);
</script>

<template>
  <Page title="Assemblies" description="Reusable assembly templates for estimates">
    <ACard>
      <div class="mb-4 flex items-center justify-between">
        <ASpace>
          <span style="color: #888">{{ items.length }} assemblies</span>
        </ASpace>
        <ASpace>
          <AButton @click="fetchData">
            <template #icon><ReloadOutlined /></template>
            Refresh
          </AButton>
          <AButton type="primary" @click="openNew">
            <template #icon><PlusOutlined /></template>
            New Assembly
          </AButton>
        </ASpace>
      </div>

      <ATable
        :columns="columns"
        :data-source="items"
        :loading="loading"
        :expanded-row-keys="expandedRowKeys"
        row-key="id"
        size="middle"
        @expand="handleExpand"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'item_count'">
            {{ record.item_count || (record._items || []).length || 0 }}
          </template>
          <template v-else-if="column.key === 'total_cost'">
            {{ fmtCurrency(record.total_cost || calcTotalCost(record._items)) }}
          </template>
          <template v-else-if="column.key === 'active'">
            <ATag :color="record.active !== false ? 'green' : 'default'">
              {{ record.active !== false ? 'Yes' : 'No' }}
            </ATag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <ASpace>
              <AButton type="link" size="small" @click="openEdit(record)">
                <template #icon><EditOutlined /></template>
              </AButton>
              <APopconfirm title="Delete this assembly?" ok-text="Yes" cancel-text="No" @confirm="handleDelete(record)">
                <AButton type="link" size="small" danger>
                  <template #icon><DeleteOutlined /></template>
                </AButton>
              </APopconfirm>
            </ASpace>
          </template>
        </template>
        <template #expandedRowRender="{ record }">
          <ATable
            :columns="expandColumns"
            :data-source="record._items || []"
            row-key="id"
            size="small"
            :pagination="false"
          >
            <template #bodyCell="{ column, record: item }">
              <template v-if="column.key === 'item_type'">
                <ATag :color="typeColors[item.item_type] || 'default'" size="small">
                  {{ (item.item_type || '').replace(/^\w/, c => c.toUpperCase()) }}
                </ATag>
              </template>
              <template v-else-if="column.key === 'unit_cost'">
                {{ fmtCurrency(item.unit_cost) }}
              </template>
              <template v-else-if="column.key === 'waste_factor'">
                {{ (item.waste_factor || 0).toFixed(1) }}%
              </template>
              <template v-else-if="column.key === 'line_total'">
                {{ fmtCurrency((item.quantity || 0) * (item.unit_cost || 0) * (1 + (item.waste_factor || 0) / 100)) }}
              </template>
            </template>
          </ATable>
        </template>
      </ATable>
    </ACard>

    <!-- Assembly Drawer -->
    <ADrawer
      :open="drawerVisible"
      :title="drawerTitle"
      :width="600"
      @close="drawerVisible = false"
    >
      <AForm layout="vertical">
        <AFormItem label="Name" required>
          <AInput v-model:value="form.name" />
        </AFormItem>
        <AFormItem label="Category">
          <AInput v-model:value="form.category" placeholder="e.g. Framing, Plumbing" />
        </AFormItem>
        <AFormItem label="Description">
          <ATextarea v-model:value="form.description" :rows="2" />
        </AFormItem>
        <AFormItem label="Active">
          <ASwitch v-model:checked="form.active" />
        </AFormItem>
      </AForm>

      <ADivider>Assembly Items</ADivider>

      <div class="mb-2 flex justify-end">
        <ASpace>
          <AButton size="small" @click="openCatalogPicker">
            <template #icon><PlusOutlined /></template>
            Add from Catalog
          </AButton>
          <AButton size="small" type="primary" @click="addBlankItem">
            <template #icon><PlusOutlined /></template>
            Add Item
          </AButton>
        </ASpace>
      </div>

      <ATable
        :columns="drawerItemColumns"
        :data-source="assemblyItems"
        row-key="_key"
        size="small"
        :pagination="false"
      >
        <template #bodyCell="{ column, record, index }">
          <template v-if="column.dataIndex === 'name'">
            <AInput v-model:value="record.name" size="small" />
          </template>
          <template v-else-if="column.key === 'item_type'">
            <ASelect v-model:value="record.item_type" :options="typeOptions" size="small" style="width: 100%" />
          </template>
          <template v-else-if="column.dataIndex === 'quantity'">
            <AInputNumber v-model:value="record.quantity" :min="0" size="small" style="width: 100%" />
          </template>
          <template v-else-if="column.dataIndex === 'unit'">
            <AInput v-model:value="record.unit" size="small" />
          </template>
          <template v-else-if="column.key === 'unit_cost'">
            <AInputNumber v-model:value="record.unit_cost" :min="0" :precision="2" size="small" style="width: 100%" />
          </template>
          <template v-else-if="column.key === 'waste_factor'">
            <AInputNumber v-model:value="record.waste_factor" :min="0" :precision="1" size="small" style="width: 100%" />
          </template>
          <template v-else-if="column.key === 'remove'">
            <AButton type="link" size="small" danger @click="removeDrawerItem(index)">
              <template #icon><DeleteOutlined /></template>
            </AButton>
          </template>
        </template>
      </ATable>

      <div style="margin-top: 12px; text-align: right; font-weight: 600">
        Total: {{ fmtCurrency(calcTotalCost(assemblyItems)) }}
      </div>

      <template #footer>
        <ASpace>
          <AButton @click="drawerVisible = false">Cancel</AButton>
          <AButton type="primary" :loading="drawerSaving" @click="saveAssembly">Save</AButton>
        </ASpace>
      </template>
    </ADrawer>

    <!-- Catalog Picker Modal -->
    <AModal
      v-model:open="catalogModalVisible"
      title="Add Item from Catalog"
      :footer="null"
      :width="600"
    >
      <ATable
        :data-source="catalogItems"
        row-key="id"
        size="small"
        :pagination="{ pageSize: 10 }"
        :columns="[
          { title: 'Name', dataIndex: 'name', key: 'name' },
          { title: 'Type', dataIndex: 'item_type', key: 'item_type', width: 110 },
          { title: 'Unit Cost', key: 'uc', width: 100 },
          { title: '', key: 'add', width: 70 },
        ]"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'uc'">{{ fmtCurrency(record.unit_cost) }}</template>
          <template v-else-if="column.key === 'add'">
            <AButton type="link" size="small" @click="addFromCatalog(record)">Add</AButton>
          </template>
        </template>
      </ATable>
    </AModal>
  </Page>
</template>
