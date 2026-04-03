<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Col,
  DatePicker,
  Divider,
  Form,
  FormItem,
  Input,
  InputNumber,
  message,
  Row,
  Select,
  Space,
  Textarea,
} from 'ant-design-vue';
import {
  ArrowLeftOutlined,
  MinusCircleOutlined,
  PlusOutlined,
  SaveOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMSubmittalForm' });

const route = useRoute();
const router = useRouter();
const BASE = '/agcm_submittal';

const submittalId = computed(() => route.query.id);
const isEdit = computed(() => !!submittalId.value);

const loading = ref(false);
const saving = ref(false);

const formData = ref({
  title: '',
  description: '',
  spec_section: '',
  project_id: null,
  package_id: null,
  type_id: null,
  priority: 'medium',
  due_date: null,
  submitted_date: null,
  received_date: null,
  label_ids: [],
  approver_ids: [],
});

// Master data
const projects = ref([]);
const packages = ref([]);
const types = ref([]);
const labels = ref([]);
const users = ref([]);

const priorityOptions = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'urgent', label: 'Urgent' },
];

async function fetchMasterData() {
  try {
    const [usersData, typesData, labelsData, projectsData] = await Promise.all([
      requestClient.get('/users/', { params: { page_size: 200 } }),
      requestClient.get(`${BASE}/submittal-types`),
      requestClient.get(`${BASE}/submittal-labels`),
      requestClient.get('/agcm/projects', { params: { page_size: 200 } }),
    ]);
    users.value = (usersData.items || usersData || []).map((u) => ({
      value: u.id,
      label: u.full_name || u.username || u.email,
    }));
    types.value = (typesData.items || typesData || []).map((t) => ({
      value: t.id,
      label: t.name,
    }));
    labels.value = (labelsData.items || labelsData || []).map((l) => ({
      value: l.id,
      label: l.name,
      color: l.color,
    }));
    projects.value = (projectsData.items || projectsData || []).map((p) => ({
      value: p.id,
      label: p.name,
    }));
  } catch {
    message.error('Failed to load master data');
  }
}

async function fetchPackages() {
  if (!formData.value.project_id) {
    packages.value = [];
    return;
  }
  try {
    const data = await requestClient.get(`${BASE}/submittal-packages`, {
      params: { project_id: formData.value.project_id },
    });
    packages.value = (data.items || data || []).map((p) => ({
      value: p.id,
      label: p.name,
    }));
  } catch {}
}

async function loadSubmittal() {
  if (!submittalId.value) return;
  loading.value = true;
  try {
    const data = await requestClient.get(`${BASE}/submittals/${submittalId.value}`);
    formData.value = {
      title: data.title || '',
      description: data.description || '',
      spec_section: data.spec_section || '',
      project_id: data.project_id || null,
      package_id: data.package_id || null,
      type_id: data.type_id || null,
      priority: data.priority || 'medium',
      due_date: data.due_date || null,
      submitted_date: data.submitted_date || null,
      received_date: data.received_date || null,
      label_ids: data.label_ids || [],
      approver_ids: (data.approvers || []).map((a) => ({
        user_id: a.user_id,
        sequence: a.sequence,
      })),
    };
    await fetchPackages();
  } catch {
    message.error('Failed to load submittal');
  } finally {
    loading.value = false;
  }
}

function onProjectChange() {
  formData.value.package_id = null;
  fetchPackages();
}

function addApprover() {
  const nextSeq = formData.value.approver_ids.length + 1;
  formData.value.approver_ids.push({ user_id: null, sequence: nextSeq });
}

function removeApprover(index) {
  formData.value.approver_ids.splice(index, 1);
  // Re-sequence
  formData.value.approver_ids.forEach((a, i) => { a.sequence = i + 1; });
}

async function handleSave() {
  if (!formData.value.title) {
    message.warning('Title is required');
    return;
  }
  if (!formData.value.project_id) {
    message.warning('Project is required');
    return;
  }

  // Filter out approvers without user_id
  const payload = {
    ...formData.value,
    approver_ids: formData.value.approver_ids.filter((a) => a.user_id),
  };

  saving.value = true;
  try {
    if (isEdit.value) {
      await requestClient.put(`${BASE}/submittals/${submittalId.value}`, payload);
      message.success('Submittal updated');
    } else {
      const result = await requestClient.post(`${BASE}/submittals`, payload);
      message.success('Submittal created');
      router.replace({ path: '/agcm/submittals/form', query: { id: result.id } });
    }
  } catch {
    message.error('Failed to save submittal');
  } finally {
    saving.value = false;
  }
}

function goBack() {
  router.push('/agcm/submittals');
}

onMounted(() => {
  fetchMasterData();
  if (isEdit.value) {
    loadSubmittal();
  }
});
</script>

<template>
  <Page auto-content-height>
    <Card :bordered="false">
      <!-- Header -->
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <Space>
          <Button @click="goBack">
            <template #icon><ArrowLeftOutlined /></template>
            Back
          </Button>
          <h3 style="margin: 0;">
            {{ isEdit ? 'Edit Submittal' : 'New Submittal' }}
          </h3>
        </Space>
        <Button type="primary" :loading="saving" @click="handleSave">
          <template #icon><SaveOutlined /></template>
          Save
        </Button>
      </div>

      <Divider />

      <Form layout="vertical">
        <!-- Row 1: Title, Spec Section -->
        <Row :gutter="16">
          <Col :span="14">
            <FormItem label="Title" required>
              <Input v-model:value="formData.title" placeholder="Enter submittal title" />
            </FormItem>
          </Col>
          <Col :span="5">
            <FormItem label="Spec Section">
              <Input v-model:value="formData.spec_section" placeholder="e.g. 03 30 00" />
            </FormItem>
          </Col>
          <Col :span="5">
            <FormItem label="Priority">
              <Select v-model:value="formData.priority" :options="priorityOptions" style="width: 100%;" />
            </FormItem>
          </Col>
        </Row>

        <!-- Row 2: Project, Package, Type -->
        <Row :gutter="16">
          <Col :span="8">
            <FormItem label="Project" required>
              <Select
                v-model:value="formData.project_id"
                :options="projects"
                placeholder="Select project"
                show-search
                :filter-option="(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
                style="width: 100%;"
                @change="onProjectChange"
              />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Package">
              <Select
                v-model:value="formData.package_id"
                :options="packages"
                placeholder="Select package"
                allow-clear
                style="width: 100%;"
              />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Type">
              <Select
                v-model:value="formData.type_id"
                :options="types"
                placeholder="Select type"
                allow-clear
                style="width: 100%;"
              />
            </FormItem>
          </Col>
        </Row>

        <!-- Row 3: Dates -->
        <Row :gutter="16">
          <Col :span="8">
            <FormItem label="Due Date">
              <DatePicker v-model:value="formData.due_date" style="width: 100%;" value-format="YYYY-MM-DD" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Submitted Date">
              <DatePicker v-model:value="formData.submitted_date" style="width: 100%;" value-format="YYYY-MM-DD" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Received Date">
              <DatePicker v-model:value="formData.received_date" style="width: 100%;" value-format="YYYY-MM-DD" />
            </FormItem>
          </Col>
        </Row>

        <!-- Labels -->
        <Row :gutter="16">
          <Col :span="24">
            <FormItem label="Labels">
              <Select
                v-model:value="formData.label_ids"
                :options="labels"
                mode="multiple"
                placeholder="Select labels"
                style="width: 100%;"
              />
            </FormItem>
          </Col>
        </Row>

        <!-- Description -->
        <Row :gutter="16">
          <Col :span="24">
            <FormItem label="Description">
              <Textarea v-model:value="formData.description" :rows="4" placeholder="Enter description" />
            </FormItem>
          </Col>
        </Row>

        <!-- Approvers -->
        <Divider orientation="left">Approval Chain</Divider>
        <div v-for="(approver, index) in formData.approver_ids" :key="index" style="margin-bottom: 12px;">
          <Row :gutter="16" align="middle">
            <Col :span="3">
              <FormItem :label="index === 0 ? 'Seq' : ''" style="margin-bottom: 0;">
                <InputNumber v-model:value="approver.sequence" :min="1" style="width: 100%;" />
              </FormItem>
            </Col>
            <Col :span="18">
              <FormItem :label="index === 0 ? 'Approver' : ''" style="margin-bottom: 0;">
                <Select
                  v-model:value="approver.user_id"
                  :options="users"
                  placeholder="Select approver"
                  show-search
                  :filter-option="(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
                  style="width: 100%;"
                />
              </FormItem>
            </Col>
            <Col :span="3" style="text-align: center;">
              <FormItem :label="index === 0 ? ' ' : ''" style="margin-bottom: 0;">
                <Button type="text" danger @click="removeApprover(index)">
                  <template #icon><MinusCircleOutlined /></template>
                </Button>
              </FormItem>
            </Col>
          </Row>
        </div>
        <Button type="dashed" block @click="addApprover">
          <template #icon><PlusOutlined /></template>
          Add Approver
        </Button>
      </Form>
    </Card>
  </Page>
</template>
