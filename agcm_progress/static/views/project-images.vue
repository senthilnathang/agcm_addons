<script lang="ts" setup>
import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Col,
  DatePicker,
  Form,
  FormItem,
  Image,
  Input,
  message,
  Modal,
  Popconfirm,
  Row,
  Select,
  Space,
  Tag,
  Textarea,
  Upload,
} from 'ant-design-vue';
import {
  DeleteOutlined,
  EditOutlined,
  InboxOutlined,
  PlusOutlined,
  ReloadOutlined,
  UploadOutlined,
} from '@ant-design/icons-vue';

import { getProjectsApi } from '#/api/agcm';
import {
  deleteProjectImageApi,
  getProjectImagesApi,
  updateProjectImageApi,
  uploadProjectImageApi,
} from '#/api/agcm_progress';

import dayjs from 'dayjs';

defineOptions({ name: 'AGCMProgressProjectImages' });

const loading = ref(false);
const items = ref<any[]>([]);
const projects = ref<any[]>([]);
const selectedProjectId = ref<number | null>(null);

const uploadModalVisible = ref(false);
const editModalVisible = ref(false);
const previewVisible = ref(false);
const previewUrl = ref('');
const editingItem = ref<any>(null);
const uploading = ref(false);

const uploadForm = ref({
  name: '',
  description: '',
  tags: '',
  taken_on: null as any,
});

const editForm = ref({
  name: '',
  description: '',
  tags: '',
  taken_on: null as any,
  display_order: 0,
});

async function loadProjects() {
  try {
    const res = await getProjectsApi({ page: 1, page_size: 200 });
    projects.value = res.items || [];
    if (projects.value.length > 0 && !selectedProjectId.value) {
      selectedProjectId.value = projects.value[0].id;
    }
  } catch (e: any) {
    message.error('Failed to load projects');
  }
}

async function fetchData() {
  if (!selectedProjectId.value) return;
  loading.value = true;
  try {
    const res = await getProjectImagesApi({ project_id: selectedProjectId.value });
    items.value = res.items || [];
  } catch (e: any) {
    message.error('Failed to load images');
  } finally {
    loading.value = false;
  }
}

function onProjectChange(val: number) {
  selectedProjectId.value = val;
  fetchData();
}

function openUploadModal() {
  uploadForm.value = { name: '', description: '', tags: '', taken_on: null };
  uploadModalVisible.value = true;
}

async function handleUpload(options: any) {
  const { file } = options;
  if (!selectedProjectId.value) return;

  uploading.value = true;
  try {
    await uploadProjectImageApi(selectedProjectId.value, file, {
      name: uploadForm.value.name || file.name,
      description: uploadForm.value.description || undefined,
      tags: uploadForm.value.tags || undefined,
      taken_on: uploadForm.value.taken_on ? dayjs(uploadForm.value.taken_on).format('YYYY-MM-DD') : undefined,
    });
    message.success('Image uploaded');
    uploadModalVisible.value = false;
    fetchData();
  } catch (e: any) {
    message.error(e?.message || 'Upload failed');
  } finally {
    uploading.value = false;
  }
}

function openEditModal(record: any) {
  editingItem.value = record;
  editForm.value = {
    name: record.name || '',
    description: record.description || '',
    tags: record.tags || '',
    taken_on: record.taken_on ? dayjs(record.taken_on) : null,
    display_order: record.display_order || 0,
  };
  editModalVisible.value = true;
}

async function handleEditSave() {
  if (!editingItem.value) return;
  try {
    await updateProjectImageApi(editingItem.value.id, {
      name: editForm.value.name,
      description: editForm.value.description || null,
      tags: editForm.value.tags || null,
      taken_on: editForm.value.taken_on ? dayjs(editForm.value.taken_on).format('YYYY-MM-DD') : null,
      display_order: editForm.value.display_order,
    });
    message.success('Image updated');
    editModalVisible.value = false;
    fetchData();
  } catch (e: any) {
    message.error('Failed to update');
  }
}

async function handleDelete(id: number) {
  try {
    await deleteProjectImageApi(id);
    message.success('Image deleted');
    fetchData();
  } catch (e: any) {
    message.error('Failed to delete');
  }
}

function openPreview(url: string) {
  previewUrl.value = url;
  previewVisible.value = true;
}

onMounted(async () => {
  await loadProjects();
  if (selectedProjectId.value) fetchData();
});
</script>

<template>
  <Page title="Project Images" description="Progress photo gallery">
    <Card>
      <div style="display: flex; justify-content: space-between; margin-bottom: 16px; flex-wrap: wrap; gap: 8px;">
        <Space>
          <Select
            v-model:value="selectedProjectId"
            style="width: 300px"
            placeholder="Select Project"
            show-search
            option-filter-prop="label"
            :options="projects.map(p => ({ value: p.id, label: p.name }))"
            @change="onProjectChange"
          />
          <Button @click="fetchData">
            <template #icon><ReloadOutlined /></template>
          </Button>
        </Space>
        <Button type="primary" @click="openUploadModal" :disabled="!selectedProjectId">
          <template #icon><UploadOutlined /></template>
          Upload Image
        </Button>
      </div>

      <!-- Photo gallery grid -->
      <div v-if="items.length === 0 && !loading" style="text-align: center; padding: 48px; color: #999;">
        No images found for this project.
      </div>

      <Row :gutter="[16, 16]">
        <Col v-for="img in items" :key="img.id" :xs="24" :sm="12" :md="8" :lg="6">
          <Card hoverable size="small" style="height: 100%;">
            <template #cover>
              <div
                style="height: 180px; overflow: hidden; display: flex; align-items: center; justify-content: center; background: #f5f5f5; cursor: pointer;"
                @click="img.file_url && openPreview(img.file_url)"
              >
                <img
                  v-if="img.file_url"
                  :src="img.file_url"
                  :alt="img.name"
                  style="max-width: 100%; max-height: 180px; object-fit: cover;"
                />
                <span v-else style="color: #ccc; font-size: 48px;">
                  <InboxOutlined />
                </span>
              </div>
            </template>
            <Card.Meta :title="img.name" :description="img.description || ''">
              <template #avatar>
                <Tag v-if="img.sequence_name" color="blue">{{ img.sequence_name }}</Tag>
              </template>
            </Card.Meta>
            <div style="margin-top: 8px;">
              <div v-if="img.tags" style="margin-bottom: 4px;">
                <Tag v-for="tag in img.tags.split(',')" :key="tag" size="small">{{ tag.trim() }}</Tag>
              </div>
              <div v-if="img.taken_on" style="font-size: 12px; color: #888;">Taken: {{ img.taken_on }}</div>
            </div>
            <div style="margin-top: 8px; display: flex; justify-content: flex-end; gap: 4px;">
              <Button size="small" @click="openEditModal(img)">
                <template #icon><EditOutlined /></template>
              </Button>
              <Popconfirm title="Delete this image?" @confirm="handleDelete(img.id)">
                <Button size="small" danger>
                  <template #icon><DeleteOutlined /></template>
                </Button>
              </Popconfirm>
            </div>
          </Card>
        </Col>
      </Row>
    </Card>

    <!-- Upload modal -->
    <Modal
      v-model:open="uploadModalVisible"
      title="Upload Image"
      :footer="null"
      :width="480"
    >
      <Form layout="vertical" style="margin-top: 16px">
        <FormItem label="Name">
          <Input v-model:value="uploadForm.name" placeholder="Image name (optional)" />
        </FormItem>
        <FormItem label="Description">
          <Textarea v-model:value="uploadForm.description" :rows="2" placeholder="Description" />
        </FormItem>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
          <FormItem label="Tags">
            <Input v-model:value="uploadForm.tags" placeholder="tag1, tag2" />
          </FormItem>
          <FormItem label="Date Taken">
            <DatePicker v-model:value="uploadForm.taken_on" style="width: 100%" />
          </FormItem>
        </div>
        <FormItem label="File">
          <Upload.Dragger
            :custom-request="handleUpload"
            :multiple="false"
            :show-upload-list="false"
            accept="image/*"
          >
            <p style="font-size: 32px; color: #999;"><InboxOutlined /></p>
            <p>Click or drag image to upload</p>
          </Upload.Dragger>
        </FormItem>
      </Form>
    </Modal>

    <!-- Edit modal -->
    <Modal
      v-model:open="editModalVisible"
      title="Edit Image"
      @ok="handleEditSave"
      :width="480"
    >
      <Form layout="vertical" style="margin-top: 16px">
        <FormItem label="Name">
          <Input v-model:value="editForm.name" placeholder="Image name" />
        </FormItem>
        <FormItem label="Description">
          <Textarea v-model:value="editForm.description" :rows="2" placeholder="Description" />
        </FormItem>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
          <FormItem label="Tags">
            <Input v-model:value="editForm.tags" placeholder="tag1, tag2" />
          </FormItem>
          <FormItem label="Date Taken">
            <DatePicker v-model:value="editForm.taken_on" style="width: 100%" />
          </FormItem>
        </div>
        <FormItem label="Display Order">
          <Input v-model:value="editForm.display_order" type="number" />
        </FormItem>
      </Form>
    </Modal>

    <!-- Preview modal -->
    <Modal
      v-model:open="previewVisible"
      :footer="null"
      :width="800"
      title="Image Preview"
    >
      <img :src="previewUrl" style="width: 100%;" />
    </Modal>
  </Page>
</template>
