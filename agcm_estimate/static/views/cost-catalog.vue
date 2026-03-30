<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { requestClient } from '#/api/request';
import { message } from 'ant-design-vue';
import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
} from '@ant-design/icons-vue';

defineOptions({ name: 'AGCMCostCatalog' });

const BASE = '/agcm_estimate';

const loading = ref(false);
const catalogs = ref([]);
const selectedCatalogId = ref(null);
const costItems = ref([]);
const searchText = ref('');
const typeFilter = ref(null);

const drawerVisible = ref(false);
const drawerTitle = ref('New Cost Item');
const drawerSaving = ref(false);
const editingItemId = ref(null);
const itemForm = reactive({
  catalog_id: null,
  name: '',
  item_type: 'material',
  description: '',
  unit: '',
  unit_cost: 0,
  unit_price: 0,
  taxable: false,
  cost_code: '',
  vendor: '',
  active: true,
});

const catalogDrawerVisible = ref(false);
const catalogSaving = ref(false);
const catalogForm = reactive({
  name: '',
  description: '',
});
const editingCatalogId = ref(null);

const typeOptions = [
  { value: 'material', label: 'Material' },
  { value: 'labor', label: 'Labor' },
  { value: 'equipment', label: 'Equipment' },
  { value: 'subcontractor', label: 'Subcontractor' },
  { value: 'fee', label: 'Fee' },
  { value: 'other', label: 'Other' },
];

const typeColors = {
  material: 'blue',
  labor: 'green',
  equipment: 'orange',
  subcontractor: 'purple',
  fee: 'red',
  other: 'default',
};

function fmtCurrency(val) {
  if (val == null) return '$0.00';
  return Number(val).toLocaleString('en-US', { style: 'currency', currency: 'USD' });
}

const columns = computed(() => [
  { title: 'Name', dataIndex: 'name', key: 'name', ellipsis: true },
  { title: 'Type', key: 'item_type', width: 130 },
  { title: 'Unit', dataIndex: 'unit', key: 'unit', width: 80 },
  { title: 'Unit Cost', key: 'unit_cost', width: 120, align: 'right' },
  { title: 'Unit Price', key: 'unit_price', width: 120, align: 'right' },
  { title: 'Taxable', key: 'taxable', width: 90, align: 'center' },
  { title: 'Cost Code', dataIndex: 'cost_code', key: 'cost_code', width: 110 },
  { title: 'Vendor', dataIndex: 'vendor', key: 'vendor', width: 130, ellipsis: true },
  { title: 'Active', key: 'active', width: 80, align: 'center' },
  { title: 'Actions', key: 'actions', width: 100, fixed: 'right' },
]);

async function fetchCatalogs() {
  try {
    const res = await requestClient.get(`${BASE}/catalogs`, { params: { page_size: 200 } });
    catalogs.value = (res.items || res || []).map((c) => ({
      value: c.id,
      label: c.name,
      raw: c,
    }));
    if (catalogs.value.length && !selectedCatalogId.value) {
      selectedCatalogId.value = catalogs.value[0].value;
    }
  } catch {
    message.error('Failed to load catalogs');
  }
}

async function fetchCostItems() {
  if (!selectedCatalogId.value) { costItems.value = []; return; }
  loading.value = true;
  try {
    const params = {
      catalog_id: selectedCatalogId.value,
      search: searchText.value || undefined,
      item_type: typeFilter.value || undefined,
      page_size: 200,
    };
    const res = await requestClient.get(`${BASE}/cost-items`, { params });
    costItems.value = res.items || res || [];
  } catch {
    message.error('Failed to load cost items');
  } finally {
    loading.value = false;
  }
}

function handleCatalogChange() {
  fetchCostItems();
}

function handleSearch() {
  fetchCostItems();
}

function openNewItem() {
  editingItemId.value = null;
  drawerTitle.value = 'New Cost Item';
  Object.assign(itemForm, {
    catalog_id: selectedCatalogId.value,
    name: '', item_type: 'material', description: '', unit: '',
    unit_cost: 0, unit_price: 0, taxable: false, cost_code: '', vendor: '', active: true,
  });
  drawerVisible.value = true;
}

function openEditItem(record) {
  editingItemId.value = record.id;
  drawerTitle.value = 'Edit Cost Item';
  Object.assign(itemForm, {
    catalog_id: record.catalog_id,
    name: record.name,
    item_type: record.item_type,
    description: record.description || '',
    unit: record.unit || '',
    unit_cost: record.unit_cost || 0,
    unit_price: record.unit_price || 0,
    taxable: record.taxable || false,
    cost_code: record.cost_code || '',
    vendor: record.vendor || '',
    active: record.active !== false,
  });
  drawerVisible.value = true;
}

async function saveItem() {
  if (!itemForm.name) { message.warning('Name is required'); return; }
  drawerSaving.value = true;
  try {
    if (editingItemId.value) {
      await requestClient.put(`${BASE}/cost-items/${editingItemId.value}`, { ...itemForm });
      message.success('Cost item updated');
    } else {
      await requestClient.post(`${BASE}/cost-items`, { ...itemForm });
      message.success('Cost item created');
    }
    drawerVisible.value = false;
    fetchCostItems();
  } catch {
    message.error('Failed to save cost item');
  } finally {
    drawerSaving.value = false;
  }
}

async function handleDeleteItem(record) {
  try {
    await requestClient.delete(`${BASE}/cost-items/${record.id}`);
    message.success('Cost item deleted');
    fetchCostItems();
  } catch {
    message.error('Failed to delete cost item');
  }
}

async function toggleActive(record) {
  try {
    await requestClient.put(`${BASE}/cost-items/${record.id}`, { active: !record.active });
    record.active = !record.active;
  } catch {
    message.error('Failed to update item');
  }
}

async function toggleTaxable(record) {
  try {
    await requestClient.put(`${BASE}/cost-items/${record.id}`, { taxable: !record.taxable });
    record.taxable = !record.taxable;
  } catch {
    message.error('Failed to update item');
  }
}

function openNewCatalog() {
  editingCatalogId.value = null;
  Object.assign(catalogForm, { name: '', description: '' });
  catalogDrawerVisible.value = true;
}

async function saveCatalog() {
  if (!catalogForm.name) { message.warning('Name is required'); return; }
  catalogSaving.value = true;
  try {
    if (editingCatalogId.value) {
      await requestClient.put(`${BASE}/catalogs/${editingCatalogId.value}`, { ...catalogForm });
      message.success('Catalog updated');
    } else {
      const res = await requestClient.post(`${BASE}/catalogs`, { ...catalogForm });
      message.success('Catalog created');
      selectedCatalogId.value = res.id;
    }
    catalogDrawerVisible.value = false;
    await fetchCatalogs();
    fetchCostItems();
  } catch {
    message.error('Failed to save catalog');
  } finally {
    catalogSaving.value = false;
  }
}

onMounted(async () => {
  await fetchCatalogs();
  fetchCostItems();
});
</script>

<template>
  <Page title="Cost Catalog" description="Manage cost items and catalogs">
    <ACard>
      <div class="mb-4 flex items-center justify-between">
        <ASpace>
          <ASelect
            v-model:value="selectedCatalogId"
            :options="catalogs"
            placeholder="Select Catalog"
            style="width: 260px"
            show-search
            :filter-option="(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
            @change="handleCatalogChange"
          />
          <AButton @click="openNewCatalog">
            <template #icon><PlusOutlined /></template>
            New Catalog
          </AButton>
          <AInput
            v-model:value="searchText"
            placeholder="Search items..."
            style="width: 220px"
            @press-enter="handleSearch"
          >
            <template #prefix><SearchOutlined /></template>
          </AInput>
          <ASelect
            v-model:value="typeFilter"
            :options="typeOptions"
            placeholder="All Types"
            allow-clear
            style="width: 150px"
            @change="handleSearch"
          />
        </ASpace>
        <ASpace>
          <AButton @click="fetchCostItems">
            <template #icon><ReloadOutlined /></template>
            Refresh
          </AButton>
          <AButton type="primary" @click="openNewItem" :disabled="!selectedCatalogId">
            <template #icon><PlusOutlined /></template>
            New Cost Item
          </AButton>
        </ASpace>
      </div>

      <ATable
        :columns="columns"
        :data-source="costItems"
        :loading="loading"
        row-key="id"
        size="middle"
        :pagination="{ pageSize: 50, showSizeChanger: true }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'item_type'">
            <ATag :color="typeColors[record.item_type] || 'default'">
              {{ (record.item_type || '').replace(/^\w/, c => c.toUpperCase()) }}
            </ATag>
          </template>
          <template v-else-if="column.key === 'unit_cost'">
            {{ fmtCurrency(record.unit_cost) }}
          </template>
          <template v-else-if="column.key === 'unit_price'">
            {{ fmtCurrency(record.unit_price) }}
          </template>
          <template v-else-if="column.key === 'taxable'">
            <ASwitch :checked="record.taxable" size="small" @change="toggleTaxable(record)" />
          </template>
          <template v-else-if="column.key === 'active'">
            <ASwitch :checked="record.active" size="small" @change="toggleActive(record)" />
          </template>
          <template v-else-if="column.key === 'actions'">
            <ASpace>
              <AButton type="link" size="small" @click="openEditItem(record)">
                <template #icon><EditOutlined /></template>
              </AButton>
              <APopconfirm title="Delete this item?" ok-text="Yes" cancel-text="No" @confirm="handleDeleteItem(record)">
                <AButton type="link" size="small" danger>
                  <template #icon><DeleteOutlined /></template>
                </AButton>
              </APopconfirm>
            </ASpace>
          </template>
        </template>
      </ATable>
    </ACard>

    <!-- Cost Item Drawer -->
    <ADrawer
      :open="drawerVisible"
      :title="drawerTitle"
      :width="560"
      @close="drawerVisible = false"
    >
      <AForm layout="vertical">
        <AFormItem label="Name" required>
          <AInput v-model:value="itemForm.name" />
        </AFormItem>
        <AFormItem label="Type">
          <ASelect v-model:value="itemForm.item_type" :options="typeOptions" />
        </AFormItem>
        <AFormItem label="Description">
          <ATextarea v-model:value="itemForm.description" :rows="2" />
        </AFormItem>
        <div style="display: flex; gap: 16px">
          <AFormItem label="Unit" style="flex: 1">
            <AInput v-model:value="itemForm.unit" placeholder="e.g. SF, LF, EA" />
          </AFormItem>
          <AFormItem label="Unit Cost" style="flex: 1">
            <AInputNumber v-model:value="itemForm.unit_cost" :min="0" :precision="2" prefix="$" style="width: 100%" />
          </AFormItem>
          <AFormItem label="Unit Price" style="flex: 1">
            <AInputNumber v-model:value="itemForm.unit_price" :min="0" :precision="2" prefix="$" style="width: 100%" />
          </AFormItem>
        </div>
        <AFormItem label="Cost Code">
          <AInput v-model:value="itemForm.cost_code" />
        </AFormItem>
        <AFormItem label="Vendor">
          <AInput v-model:value="itemForm.vendor" />
        </AFormItem>
        <div style="display: flex; gap: 24px">
          <AFormItem label="Taxable">
            <ASwitch v-model:checked="itemForm.taxable" />
          </AFormItem>
          <AFormItem label="Active">
            <ASwitch v-model:checked="itemForm.active" />
          </AFormItem>
        </div>
      </AForm>
      <template #footer>
        <ASpace>
          <AButton @click="drawerVisible = false">Cancel</AButton>
          <AButton type="primary" :loading="drawerSaving" @click="saveItem">Save</AButton>
        </ASpace>
      </template>
    </ADrawer>

    <!-- Catalog Drawer -->
    <ADrawer
      :open="catalogDrawerVisible"
      title="New Catalog"
      :width="420"
      @close="catalogDrawerVisible = false"
    >
      <AForm layout="vertical">
        <AFormItem label="Name" required>
          <AInput v-model:value="catalogForm.name" />
        </AFormItem>
        <AFormItem label="Description">
          <ATextarea v-model:value="catalogForm.description" :rows="3" />
        </AFormItem>
      </AForm>
      <template #footer>
        <ASpace>
          <AButton @click="catalogDrawerVisible = false">Cancel</AButton>
          <AButton type="primary" :loading="catalogSaving" @click="saveCatalog">Save</AButton>
        </ASpace>
      </template>
    </ADrawer>
  </Page>
</template>
