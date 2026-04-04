<script setup>
import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Col,
  DatePicker,
  Form,
  FormItem,
  Input,
  InputNumber,
  message,
  Row,
  Select,
  SelectOption,
  Space,
  Textarea,
} from 'ant-design-vue';
import { ArrowLeftOutlined, SaveOutlined } from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';
import { useRoute, useRouter } from 'vue-router';
import { RecordPager } from '#/components'

defineOptions({ name: 'AGCMRFIForm' });

const route = useRoute();
const router = useRouter();
const BASE = '/agcm_rfi';

const rfiId = ref(route.query.id ? Number(route.query.id) : null);
const isEdit = ref(!!rfiId.value);
const saving = ref(false);
const projects = ref([]);
const users = ref([]);
const labels = ref([]);

const form = ref({
  subject: '',
  question: '',
  priority: 'medium',
  status: 'draft',
  schedule_impact_days: 0,
  cost_impact: 0,
  due_date: null,
  project_id: route.query.project_id ? Number(route.query.project_id) : null,
  assignee_ids: [],
  label_ids: [],
});

const priorityOptions = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
];

const statusOptions = [
  { value: 'draft', label: 'Draft' },
  { value: 'open', label: 'Open' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'answered', label: 'Answered' },
  { value: 'closed', label: 'Closed' },
];

async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = data.items || data.results || [];
  } catch {}
}

async function fetchUsers() {
  try {
    const data = await requestClient.get('/users', { params: { page_size: 200 } });
    users.value = data.items || data.results || data || [];
  } catch {}
}

async function fetchLabels() {
  try {
    const data = await requestClient.get(`${BASE}/rfi-labels`);
    labels.value = data.items || data || [];
  } catch {}
}

async function fetchRFI() {
  if (!rfiId.value) return;
  try {
    const data = await requestClient.get(`${BASE}/rfis/${rfiId.value}`);
    form.value = {
      subject: data.subject || '',
      question: data.question || '',
      priority: data.priority || 'medium',
      status: data.status || 'draft',
      schedule_impact_days: data.schedule_impact_days || 0,
      cost_impact: data.cost_impact || 0,
      due_date: data.due_date || null,
      project_id: data.project_id,
      assignee_ids: data.assignee_ids || [],
      label_ids: data.label_ids || [],
    };
  } catch { message.error('Failed to load RFI'); }
}

async function handleSave() {
  if (!form.value.subject.trim()) { message.warning('Subject is required'); return; }
  if (!form.value.project_id) { message.warning('Project is required'); return; }

  saving.value = true;
  try {
    if (isEdit.value) {
      await requestClient.put(`${BASE}/rfis/${rfiId.value}`, form.value);
      message.success('RFI updated');
    } else {
      await requestClient.post(`${BASE}/rfis`, form.value);
      message.success('RFI created');
    }
    router.push('/agcm/rfi');
  } catch { message.error('Failed to save RFI'); }
  finally { saving.value = false; }
}

onMounted(async () => {
  await Promise.all([fetchProjects(), fetchUsers(), fetchLabels()]);
  if (isEdit.value) fetchRFI();
});
</script>

<template>
  <Page :title="isEdit ? 'Edit RFI' : 'New RFI'">
    <Card>
      <Form layout="vertical">
        <Row :gutter="16">
          <Col :span="16">
            <FormItem label="Subject" required>
              <Input v-model:value="form.subject" placeholder="Enter RFI subject" />
            </FormItem>
          </Col>
          <Col :span="8">
            <FormItem label="Project" required>
              <Select v-model:value="form.project_id" placeholder="Select project" show-search option-filter-prop="label" style="width: 100%">
                <SelectOption v-for="p in projects" :key="p.id" :value="p.id" :label="p.name">{{ p.name }}</SelectOption>
              </Select>
            </FormItem>
          </Col>
        </Row>

        <FormItem label="Question / Details">
          <Textarea v-model:value="form.question" :rows="4" placeholder="Describe the information needed..." />
        </FormItem>

        <Row :gutter="16">
          <Col :span="6">
            <FormItem label="Priority">
              <Select v-model:value="form.priority" style="width: 100%">
                <SelectOption v-for="p in priorityOptions" :key="p.value" :value="p.value">{{ p.label }}</SelectOption>
              </Select>
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Status">
              <Select v-model:value="form.status" style="width: 100%">
                <SelectOption v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</SelectOption>
              </Select>
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Due Date">
              <DatePicker v-model:value="form.due_date" style="width: 100%" value-format="YYYY-MM-DD" />
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Schedule Impact (days)">
              <InputNumber v-model:value="form.schedule_impact_days" :min="0" style="width: 100%" />
            </FormItem>
          </Col>
        </Row>

        <Row :gutter="16">
          <Col :span="6">
            <FormItem label="Cost Impact ($)">
              <InputNumber v-model:value="form.cost_impact" :min="0" :precision="2" style="width: 100%" />
            </FormItem>
          </Col>
          <Col :span="9">
            <FormItem label="Assignees">
              <Select v-model:value="form.assignee_ids" mode="multiple" placeholder="Select assignees" style="width: 100%" option-filter-prop="label">
                <SelectOption v-for="u in users" :key="u.id" :value="u.id" :label="u.full_name || u.username">{{ u.full_name || u.username }}</SelectOption>
              </Select>
            </FormItem>
          </Col>
          <Col :span="9">
            <FormItem label="Labels">
              <Select v-model:value="form.label_ids" mode="multiple" placeholder="Select labels" style="width: 100%" option-filter-prop="label">
                <SelectOption v-for="l in labels" :key="l.id" :value="l.id" :label="l.name">{{ l.name }}</SelectOption>
              </Select>
            </FormItem>
          </Col>
        </Row>

        <div class="flex justify-end gap-2 mt-4">
          <Button @click="router.push('/agcm/rfi')"><ArrowLeftOutlined /> Back</Button>
          <Button type="primary" :loading="saving" @click="handleSave"><SaveOutlined /> {{ isEdit ? 'Update' : 'Create' }} RFI</Button>
        </div>
      </Form>
    </Card>
  </Page>
</template>
