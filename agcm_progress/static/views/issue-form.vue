<script lang="ts" setup>
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Col,
  DatePicker,
  Form,
  FormItem,
  Input,
  message,
  Row,
  Select,
  Space,
  Textarea,
} from 'ant-design-vue';
import {
  ArrowLeftOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SaveOutlined,
} from '@ant-design/icons-vue';

import {
  closeIssueApi,
  createIssueApi,
  getIssueApi,
  resolveIssueApi,
  updateIssueApi,
} from '#/api/agcm_progress';

import dayjs from 'dayjs';

defineOptions({ name: 'AGCMProgressIssueForm' });

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const saving = ref(false);
const issueId = ref<number | null>(null);
const projectId = ref<number | null>(null);
const isEdit = ref(false);

const form = ref({
  title: '',
  description: '',
  severity: 'minor',
  status: 'open',
  priority: 'medium',
  location: '',
  due_date: null as any,
  assigned_to: null as number | null,
  reported_by: null as number | null,
});

const severityOptions = [
  { value: 'critical', label: 'Critical' },
  { value: 'major', label: 'Major' },
  { value: 'minor', label: 'Minor' },
  { value: 'trivial', label: 'Trivial' },
];

const statusOptions = [
  { value: 'open', label: 'Open' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'closed', label: 'Closed' },
];

const priorityOptions = [
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
];

async function loadIssue() {
  if (!issueId.value) return;
  loading.value = true;
  try {
    const data = await getIssueApi(issueId.value);
    form.value = {
      title: data.title || '',
      description: data.description || '',
      severity: data.severity || 'minor',
      status: data.status || 'open',
      priority: data.priority || 'medium',
      location: data.location || '',
      due_date: data.due_date ? dayjs(data.due_date) : null,
      assigned_to: data.assigned_to || null,
      reported_by: data.reported_by || null,
    };
    projectId.value = data.project_id;
  } catch (e: any) {
    message.error('Failed to load issue');
  } finally {
    loading.value = false;
  }
}

async function handleSave() {
  if (!form.value.title) {
    message.warning('Title is required');
    return;
  }
  saving.value = true;
  try {
    const payload: any = {
      title: form.value.title,
      description: form.value.description || null,
      severity: form.value.severity,
      status: form.value.status,
      priority: form.value.priority,
      location: form.value.location || null,
      due_date: form.value.due_date ? dayjs(form.value.due_date).format('YYYY-MM-DD') : null,
      assigned_to: form.value.assigned_to || null,
      reported_by: form.value.reported_by || null,
    };

    if (isEdit.value && issueId.value) {
      await updateIssueApi(issueId.value, payload);
      message.success('Issue updated');
    } else {
      payload.project_id = projectId.value;
      const created = await createIssueApi(payload);
      issueId.value = created.id;
      isEdit.value = true;
      message.success('Issue created');
    }
  } catch (e: any) {
    message.error(e?.message || 'Failed to save');
  } finally {
    saving.value = false;
  }
}

async function handleResolve() {
  if (!issueId.value) return;
  try {
    await resolveIssueApi(issueId.value);
    message.success('Issue resolved');
    await loadIssue();
  } catch (e: any) {
    message.error('Failed to resolve');
  }
}

async function handleClose() {
  if (!issueId.value) return;
  try {
    await closeIssueApi(issueId.value);
    message.success('Issue closed');
    await loadIssue();
  } catch (e: any) {
    message.error('Failed to close');
  }
}

function goBack() {
  router.push({ path: '/agcm/issues', query: { project_id: projectId.value } });
}

onMounted(() => {
  const q = route.query;
  if (q.id) {
    issueId.value = Number(q.id);
    isEdit.value = true;
    loadIssue();
  }
  if (q.project_id) {
    projectId.value = Number(q.project_id);
  }
});
</script>

<template>
  <Page :title="isEdit ? 'Edit Issue' : 'New Issue'" description="Create or edit a project issue">
    <Card :loading="loading">
      <div style="margin-bottom: 16px; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
        <Button @click="goBack">
          <template #icon><ArrowLeftOutlined /></template>
          Back to Issues
        </Button>
        <Space v-if="isEdit">
          <Button type="primary" style="background: #52c41a; border-color: #52c41a;" @click="handleResolve" :disabled="form.status === 'resolved' || form.status === 'closed'">
            <template #icon><CheckCircleOutlined /></template>
            Resolve
          </Button>
          <Button @click="handleClose" :disabled="form.status === 'closed'">
            <template #icon><CloseCircleOutlined /></template>
            Close
          </Button>
        </Space>
      </div>

      <Form layout="vertical">
        <FormItem label="Title" required>
          <Input v-model:value="form.title" placeholder="Issue title" />
        </FormItem>
        <FormItem label="Description">
          <Textarea v-model:value="form.description" :rows="4" placeholder="Describe the issue..." />
        </FormItem>

        <Row :gutter="16">
          <Col :span="8">
            <FormItem label="Severity">
              <Select v-model:value="form.severity" :options="severityOptions" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Priority">
              <Select v-model:value="form.priority" :options="priorityOptions" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Status">
              <Select v-model:value="form.status" :options="statusOptions" />
            </FormItem>
          </Col>
        </Row>

        <Row :gutter="16">
          <Col :span="8">
            <FormItem label="Location">
              <Input v-model:value="form.location" placeholder="Location" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Due Date">
              <DatePicker v-model:value="form.due_date" style="width: 100%" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Assigned To (User ID)">
              <Input v-model:value="form.assigned_to" placeholder="User ID" type="number" />
            </FormItem>
          </Col>
        </Row>

        <Row :gutter="16">
          <Col :span="8">
            <FormItem label="Reported By (User ID)">
              <Input v-model:value="form.reported_by" placeholder="User ID" type="number" />
            </FormItem>
          </Col>
        </Row>

        <FormItem>
          <Button type="primary" :loading="saving" @click="handleSave">
            <template #icon><SaveOutlined /></template>
            {{ isEdit ? 'Update Issue' : 'Create Issue' }}
          </Button>
        </FormItem>
      </Form>
    </Card>
  </Page>
</template>
