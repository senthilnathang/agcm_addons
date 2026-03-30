<script setup>
import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Form,
  FormItem,
  Input,
  message,
  Modal,
  Popconfirm,
  Space,
  Table,
  Tag,
} from 'ant-design-vue';
import {
  DeleteOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMSettingsRFILabels' });

const BASE = '/agcm_rfi';
const loading = ref(false);
const items = ref([]);
const modalVisible = ref(false);
const formName = ref('');
const formColor = ref('#1890ff');
const saving = ref(false);

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Color', dataIndex: 'color', key: 'color', width: 120 },
  { title: 'Actions', key: 'actions', width: 100 },
];

async function fetchData() {
  loading.value = true;
  try {
    const data = await requestClient.get(`${BASE}/rfi-labels`);
    items.value = data.items || data || [];
  } catch { message.error('Failed to load labels'); }
  finally { loading.value = false; }
}

function openCreate() {
  formName.value = '';
  formColor.value = '#1890ff';
  modalVisible.value = true;
}

async function handleSave() {
  if (!formName.value.trim()) { message.warning('Name is required'); return; }
  saving.value = true;
  try {
    await requestClient.post(`${BASE}/rfi-labels`, { name: formName.value, color: formColor.value });
    message.success('Label created');
    modalVisible.value = false;
    fetchData();
  } catch { message.error('Failed to save label'); }
  finally { saving.value = false; }
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${BASE}/rfi-labels/${record.id}`);
    message.success('Label deleted');
    fetchData();
  } catch { message.error('Failed to delete label'); }
}

onMounted(fetchData);
</script>

<template>
  <Page title="RFI Labels" description="Manage custom labels for RFI categorization">
    <Card>
      <div class="mb-4 flex items-center justify-end">
        <Space>
          <Button @click="fetchData"><template #icon><ReloadOutlined /></template>Refresh</Button>
          <Button type="primary" @click="openCreate"><template #icon><PlusOutlined /></template>Add Label</Button>
        </Space>
      </div>

      <Table :columns="columns" :data-source="items" :loading="loading" row-key="id" size="middle" :pagination="false">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'color'">
            <Tag :color="record.color">{{ record.color }}</Tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <Popconfirm title="Delete this label?" @confirm="handleDelete(record)">
              <Button type="link" size="small" danger><DeleteOutlined /></Button>
            </Popconfirm>
          </template>
        </template>
      </Table>
    </Card>

    <Modal v-model:open="modalVisible" title="New RFI Label" :confirm-loading="saving" @ok="handleSave">
      <Form layout="vertical" class="mt-4">
        <FormItem label="Name" required>
          <Input v-model:value="formName" placeholder="Label name" @press-enter="handleSave" />
        </FormItem>
        <FormItem label="Color">
          <Input v-model:value="formColor" type="color" style="width: 80px; height: 32px; padding: 2px;" />
        </FormItem>
      </Form>
    </Modal>
  </Page>
</template>
