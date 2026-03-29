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
} from 'ant-design-vue';
import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMSettingsTrades' });

const API_URL = '/agcm/trades';
const ENTITY_NAME = 'Trade';

const loading = ref(false);
const items = ref([]);
const modalVisible = ref(false);
const modalTitle = ref('');
const editingId = ref(null);
const formName = ref('');
const saving = ref(false);

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Actions', key: 'actions', width: 150 },
];

async function fetchData() {
  loading.value = true;
  try {
    const data = await requestClient.get(API_URL);
    items.value = data.items || data || [];
  } catch {
    message.error(`Failed to load ${ENTITY_NAME}s`);
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  editingId.value = null;
  formName.value = '';
  modalTitle.value = `New ${ENTITY_NAME}`;
  modalVisible.value = true;
}

function openEdit(record) {
  editingId.value = record.id;
  formName.value = record.name;
  modalTitle.value = `Edit ${ENTITY_NAME}`;
  modalVisible.value = true;
}

async function handleSave() {
  if (!formName.value.trim()) {
    message.warning('Name is required');
    return;
  }
  saving.value = true;
  try {
    if (editingId.value) {
      await requestClient.put(`${API_URL}/${editingId.value}`, { name: formName.value });
      message.success(`${ENTITY_NAME} updated`);
    } else {
      await requestClient.post(API_URL, { name: formName.value });
      message.success(`${ENTITY_NAME} created`);
    }
    modalVisible.value = false;
    fetchData();
  } catch {
    message.error(`Failed to save ${ENTITY_NAME}`);
  } finally {
    saving.value = false;
  }
}

async function handleDelete(record) {
  try {
    await requestClient.delete(`${API_URL}/${record.id}`);
    message.success(`${ENTITY_NAME} deleted`);
    fetchData();
  } catch {
    message.error(`Failed to delete ${ENTITY_NAME}`);
  }
}

onMounted(fetchData);
</script>

<template>
  <Page :title="`${ENTITY_NAME}s`" :description="`Manage ${ENTITY_NAME.toLowerCase()} list`">
    <Card>
      <div class="mb-4 flex items-center justify-end">
        <Space>
          <Button @click="fetchData">
            <template #icon><ReloadOutlined /></template>
            Refresh
          </Button>
          <Button type="primary" @click="openCreate">
            <template #icon><PlusOutlined /></template>
            Add {{ ENTITY_NAME }}
          </Button>
        </Space>
      </div>

      <Table
        :columns="columns"
        :data-source="items"
        :loading="loading"
        row-key="id"
        size="middle"
        :pagination="false"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'actions'">
            <Space>
              <Button type="link" size="small" @click="openEdit(record)">
                <template #icon><EditOutlined /></template>
              </Button>
              <Popconfirm
                :title="`Delete this ${ENTITY_NAME.toLowerCase()}?`"
                ok-text="Yes"
                cancel-text="No"
                @confirm="handleDelete(record)"
              >
                <Button type="link" size="small" danger>
                  <template #icon><DeleteOutlined /></template>
                </Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <Modal
      v-model:open="modalVisible"
      :title="modalTitle"
      :confirm-loading="saving"
      @ok="handleSave"
    >
      <Form layout="vertical" style="margin-top: 16px;">
        <FormItem label="Name" required>
          <Input
            v-model:value="formName"
            :placeholder="`Enter ${ENTITY_NAME.toLowerCase()} name`"
            @press-enter="handleSave"
          />
        </FormItem>
      </Form>
    </Modal>
  </Page>
</template>
