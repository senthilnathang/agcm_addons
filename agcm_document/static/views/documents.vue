<script setup>
import { computed, onMounted, ref, watch } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Badge,
  Button,
  Card,
  Col,
  Drawer,
  Empty,
  Form,
  FormItem,
  Input,
  message,
  Modal,
  Popconfirm,
  Row,
  Select,
  SelectOption,
  Space,
  Spin,
  Table,
  Tag,
  Textarea,
  Tree,
  Upload,
} from 'ant-design-vue';
import {
  DeleteOutlined,
  EditOutlined,
  FileOutlined,
  FolderAddOutlined,
  FolderOutlined,
  InboxOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
  UploadOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMDocuments' });

const BASE = '/agcm_document';

// State
const loading = ref(false);
const projectId = ref(null);
const projects = ref([]);
const folderTree = ref([]);
const selectedFolderId = ref(null);
const documents = ref([]);
const docTotal = ref(0);
const docPage = ref(1);
const docPageSize = ref(20);
const searchText = ref('');
const filterType = ref(null);
const filterStatus = ref(null);

// Folder modal
const folderModalVisible = ref(false);
const folderModalTitle = ref('');
const editingFolderId = ref(null);
const folderName = ref('');
const folderParentId = ref(null);
const folderSaving = ref(false);

// Upload drawer
const uploadDrawerVisible = ref(false);
const uploadForm = ref({ name: '', description: '', document_type: 'other', folder_id: null });
const uploadFile = ref(null);
const uploading = ref(false);

// Edit doc modal
const editDocVisible = ref(false);
const editDocData = ref({});
const editDocSaving = ref(false);

const docTypeOptions = [
  { value: 'blueprint', label: 'Blueprint' },
  { value: 'contract', label: 'Contract' },
  { value: 'permit', label: 'Permit' },
  { value: 'invoice', label: 'Invoice' },
  { value: 'inspection_report', label: 'Inspection Report' },
  { value: 'change_order', label: 'Change Order' },
  { value: 'specification', label: 'Specification' },
  { value: 'schedule', label: 'Schedule' },
  { value: 'safety_report', label: 'Safety Report' },
  { value: 'material_list', label: 'Material List' },
  { value: 'submittal', label: 'Submittal' },
  { value: 'rfi', label: 'RFI' },
  { value: 'other', label: 'Other' },
];

const statusOptions = [
  { value: 'draft', label: 'Draft' },
  { value: 'under_review', label: 'Under Review' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'archived', label: 'Archived' },
];

const statusColors = {
  draft: 'default',
  under_review: 'processing',
  approved: 'success',
  rejected: 'error',
  archived: 'warning',
};

const columns = [
  { title: 'Seq', dataIndex: 'sequence_name', key: 'sequence_name', width: 120 },
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Type', dataIndex: 'document_type', key: 'document_type', width: 140 },
  { title: 'Status', dataIndex: 'status', key: 'status', width: 130 },
  { title: 'Rev', dataIndex: 'revision', key: 'revision', width: 60 },
  { title: 'File', dataIndex: 'file_name', key: 'file_name', width: 200 },
  { title: 'Actions', key: 'actions', width: 120 },
];

const treeData = computed(() => {
  function mapNode(node) {
    return {
      key: node.id,
      title: `${node.name} (${node.document_count || 0})`,
      children: (node.children || []).map(mapNode),
    };
  }
  return folderTree.value.map(mapNode);
});

// Fetch projects
async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = data.items || data.results || [];
    if (projects.value.length && !projectId.value) {
      projectId.value = projects.value[0].id;
    }
  } catch {
    message.error('Failed to load projects');
  }
}

// Fetch folders
async function fetchFolders() {
  if (!projectId.value) return;
  try {
    const data = await requestClient.get(`${BASE}/folders`, { params: { project_id: projectId.value } });
    folderTree.value = data || [];
  } catch {
    message.error('Failed to load folders');
  }
}

// Fetch documents
async function fetchDocuments() {
  if (!projectId.value) return;
  loading.value = true;
  try {
    const params = {
      project_id: projectId.value,
      page: docPage.value,
      page_size: docPageSize.value,
    };
    if (selectedFolderId.value) params.folder_id = selectedFolderId.value;
    if (filterType.value) params.document_type = filterType.value;
    if (filterStatus.value) params.status = filterStatus.value;
    if (searchText.value) params.search = searchText.value;

    const data = await requestClient.get(`${BASE}/documents`, { params });
    documents.value = data.items || [];
    docTotal.value = data.total || 0;
  } catch {
    message.error('Failed to load documents');
  } finally {
    loading.value = false;
  }
}

function onSelectFolder(keys) {
  selectedFolderId.value = keys.length ? keys[0] : null;
  docPage.value = 1;
  fetchDocuments();
}

function clearFolderFilter() {
  selectedFolderId.value = null;
  docPage.value = 1;
  fetchDocuments();
}

// Folder CRUD
function openCreateFolder() {
  editingFolderId.value = null;
  folderName.value = '';
  folderParentId.value = selectedFolderId.value;
  folderModalTitle.value = 'New Folder';
  folderModalVisible.value = true;
}

async function handleSaveFolder() {
  if (!folderName.value.trim()) { message.warning('Folder name required'); return; }
  folderSaving.value = true;
  try {
    if (editingFolderId.value) {
      await requestClient.put(`${BASE}/folders/${editingFolderId.value}`, { name: folderName.value, parent_id: folderParentId.value });
      message.success('Folder updated');
    } else {
      await requestClient.post(`${BASE}/folders`, { name: folderName.value, parent_id: folderParentId.value, project_id: projectId.value });
      message.success('Folder created');
    }
    folderModalVisible.value = false;
    fetchFolders();
  } catch { message.error('Failed to save folder'); }
  finally { folderSaving.value = false; }
}

async function handleDeleteFolder(folderId) {
  try {
    await requestClient.delete(`${BASE}/folders/${folderId}`);
    message.success('Folder deleted');
    if (selectedFolderId.value === folderId) selectedFolderId.value = null;
    fetchFolders();
    fetchDocuments();
  } catch { message.error('Failed to delete folder'); }
}

// Upload
function openUpload() {
  uploadForm.value = { name: '', description: '', document_type: 'other', folder_id: selectedFolderId.value };
  uploadFile.value = null;
  uploadDrawerVisible.value = true;
}

function beforeUpload(file) {
  uploadFile.value = file;
  if (!uploadForm.value.name) uploadForm.value.name = file.name;
  return false;
}

async function handleUpload() {
  if (!uploadFile.value) { message.warning('Select a file'); return; }
  if (!uploadForm.value.name.trim()) { message.warning('Name is required'); return; }
  uploading.value = true;
  try {
    const fd = new FormData();
    fd.append('file', uploadFile.value);
    fd.append('project_id', projectId.value);
    fd.append('name', uploadForm.value.name);
    if (uploadForm.value.description) fd.append('description', uploadForm.value.description);
    fd.append('document_type', uploadForm.value.document_type);
    if (uploadForm.value.folder_id) fd.append('folder_id', uploadForm.value.folder_id);

    await requestClient.post(`${BASE}/documents/upload`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
    message.success('Document uploaded');
    uploadDrawerVisible.value = false;
    fetchDocuments();
    fetchFolders();
  } catch { message.error('Upload failed'); }
  finally { uploading.value = false; }
}

// Edit doc
function openEditDoc(record) {
  editDocData.value = { ...record };
  editDocVisible.value = true;
}

async function handleSaveDoc() {
  editDocSaving.value = true;
  try {
    await requestClient.put(`${BASE}/documents/${editDocData.value.id}`, {
      name: editDocData.value.name,
      description: editDocData.value.description,
      document_type: editDocData.value.document_type,
      status: editDocData.value.status,
      folder_id: editDocData.value.folder_id,
    });
    message.success('Document updated');
    editDocVisible.value = false;
    fetchDocuments();
  } catch { message.error('Failed to update document'); }
  finally { editDocSaving.value = false; }
}

async function handleDeleteDoc(record) {
  try {
    await requestClient.delete(`${BASE}/documents/${record.id}`);
    message.success('Document deleted');
    fetchDocuments();
    fetchFolders();
  } catch { message.error('Failed to delete document'); }
}

watch(projectId, () => {
  selectedFolderId.value = null;
  docPage.value = 1;
  fetchFolders();
  fetchDocuments();
});

onMounted(async () => {
  await fetchProjects();
  fetchFolders();
  fetchDocuments();
});
</script>

<template>
  <Page title="Documents" description="Manage project documents and folders">
    <div class="mb-4 flex items-center gap-3">
      <span class="font-medium">Project:</span>
      <Select v-model:value="projectId" style="width: 300px" placeholder="Select project" show-search option-filter-prop="label">
        <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.sequence_name }} - {{ p.name }}</SelectOption>
      </Select>
    </div>

    <Row :gutter="16">
      <!-- Folder tree sidebar -->
      <Col :span="6">
        <Card title="Folders" size="small">
          <template #extra>
            <Space>
              <Button size="small" @click="clearFolderFilter" title="Show all">All</Button>
              <Button size="small" type="primary" @click="openCreateFolder">
                <template #icon><FolderAddOutlined /></template>
              </Button>
            </Space>
          </template>
          <Tree
            v-if="treeData.length"
            :tree-data="treeData"
            :selected-keys="selectedFolderId ? [selectedFolderId] : []"
            @select="onSelectFolder"
            default-expand-all
          >
            <template #title="{ title, key }">
              <span class="flex items-center justify-between" style="width:100%">
                <span><FolderOutlined class="mr-1" />{{ title }}</span>
                <Popconfirm title="Delete this folder?" @confirm="handleDeleteFolder(key)">
                  <Button type="link" size="small" danger class="ml-2"><DeleteOutlined /></Button>
                </Popconfirm>
              </span>
            </template>
          </Tree>
          <Empty v-else description="No folders" />
        </Card>
      </Col>

      <!-- Document list -->
      <Col :span="18">
        <Card size="small">
          <div class="mb-4 flex flex-wrap items-center gap-2">
            <Input v-model:value="searchText" placeholder="Search documents..." style="width: 200px" allow-clear @press-enter="fetchDocuments">
              <template #prefix><SearchOutlined /></template>
            </Input>
            <Select v-model:value="filterType" placeholder="Type" style="width: 150px" allow-clear @change="fetchDocuments">
              <SelectOption v-for="t in docTypeOptions" :key="t.value" :value="t.value">{{ t.label }}</SelectOption>
            </Select>
            <Select v-model:value="filterStatus" placeholder="Status" style="width: 130px" allow-clear @change="fetchDocuments">
              <SelectOption v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</SelectOption>
            </Select>
            <div class="flex-1" />
            <Button @click="fetchDocuments"><template #icon><ReloadOutlined /></template>Refresh</Button>
            <Button type="primary" @click="openUpload"><template #icon><UploadOutlined /></template>Upload</Button>
          </div>

          <Table
            :columns="columns"
            :data-source="documents"
            :loading="loading"
            row-key="id"
            size="middle"
            :pagination="{ current: docPage, pageSize: docPageSize, total: docTotal, showSizeChanger: true, showTotal: (t) => `${t} documents` }"
            @change="(p) => { docPage = p.current; docPageSize = p.pageSize; fetchDocuments(); }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'document_type'">
                <Tag>{{ (record.document_type || '').replace(/_/g, ' ') }}</Tag>
              </template>
              <template v-else-if="column.key === 'status'">
                <Badge :status="statusColors[record.status] || 'default'" :text="(record.status || '').replace(/_/g, ' ')" />
              </template>
              <template v-else-if="column.key === 'file_name'">
                <a v-if="record.file_url" :href="record.file_url" target="_blank">{{ record.file_name || 'Download' }}</a>
                <span v-else class="text-gray-400">No file</span>
              </template>
              <template v-else-if="column.key === 'actions'">
                <Space>
                  <Button type="link" size="small" @click="openEditDoc(record)"><EditOutlined /></Button>
                  <Popconfirm title="Delete this document?" @confirm="handleDeleteDoc(record)">
                    <Button type="link" size="small" danger><DeleteOutlined /></Button>
                  </Popconfirm>
                </Space>
              </template>
            </template>
          </Table>
        </Card>
      </Col>
    </Row>

    <!-- Folder Modal -->
    <Modal v-model:open="folderModalVisible" :title="folderModalTitle" :confirm-loading="folderSaving" @ok="handleSaveFolder">
      <Form layout="vertical" class="mt-4">
        <FormItem label="Folder Name" required>
          <Input v-model:value="folderName" placeholder="Enter folder name" @press-enter="handleSaveFolder" />
        </FormItem>
      </Form>
    </Modal>

    <!-- Upload Drawer -->
    <Drawer v-model:open="uploadDrawerVisible" title="Upload Document" :width="480" placement="right">
      <Form layout="vertical">
        <FormItem label="File" required>
          <Upload :before-upload="beforeUpload" :max-count="1" :file-list="uploadFile ? [uploadFile] : []">
            <Button><UploadOutlined /> Select File</Button>
          </Upload>
        </FormItem>
        <FormItem label="Name" required>
          <Input v-model:value="uploadForm.name" placeholder="Document name" />
        </FormItem>
        <FormItem label="Description">
          <Textarea v-model:value="uploadForm.description" :rows="3" placeholder="Optional description" />
        </FormItem>
        <FormItem label="Type">
          <Select v-model:value="uploadForm.document_type" style="width: 100%">
            <SelectOption v-for="t in docTypeOptions" :key="t.value" :value="t.value">{{ t.label }}</SelectOption>
          </Select>
        </FormItem>
        <FormItem>
          <Button type="primary" :loading="uploading" block @click="handleUpload">Upload Document</Button>
        </FormItem>
      </Form>
    </Drawer>

    <!-- Edit Document Modal -->
    <Modal v-model:open="editDocVisible" title="Edit Document" :confirm-loading="editDocSaving" @ok="handleSaveDoc">
      <Form layout="vertical" class="mt-4">
        <FormItem label="Name" required>
          <Input v-model:value="editDocData.name" />
        </FormItem>
        <FormItem label="Description">
          <Textarea v-model:value="editDocData.description" :rows="2" />
        </FormItem>
        <FormItem label="Type">
          <Select v-model:value="editDocData.document_type" style="width: 100%">
            <SelectOption v-for="t in docTypeOptions" :key="t.value" :value="t.value">{{ t.label }}</SelectOption>
          </Select>
        </FormItem>
        <FormItem label="Status">
          <Select v-model:value="editDocData.status" style="width: 100%">
            <SelectOption v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</SelectOption>
          </Select>
        </FormItem>
      </Form>
    </Modal>
  </Page>
</template>
