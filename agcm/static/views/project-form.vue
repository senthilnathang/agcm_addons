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
  message,
  Row,
  Select,
  SelectOption,
  Space,
} from 'ant-design-vue';
import { ArrowLeftOutlined, SaveOutlined } from '@ant-design/icons-vue';

import { createProjectApi, getProjectApi, updateProjectApi } from '#/api/agcm';
import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMProjectForm' });

const route = useRoute();
const router = useRouter();
const projectId = computed(() => route.params.id);
const isEdit = computed(() => !!projectId.value);

const loading = ref(false);
const saving = ref(false);

const formData = ref({
  name: '',
  ref_number: '',
  start_date: null,
  end_date: null,
  status: 'new',
  trade_id: null,
  owner_id: null,
  street: '',
  city: '',
  zip: '',
  state: '',
  country: '',
  agcm_office: null,
  user_ids: [],
  partner_ids: [],
});

// Master data
const trades = ref([]);
const users = ref([]);

async function fetchMasterData() {
  try {
    const [usersData] = await Promise.all([
      requestClient.get('/users/', { params: { page_size: 200 } }),
    ]);
    users.value = (usersData.items || usersData || []).map((u) => ({
      value: u.id,
      label: u.full_name || u.username || u.email,
    }));
  } catch {}
}

async function loadProject() {
  if (!projectId.value) return;
  loading.value = true;
  try {
    const data = await getProjectApi(projectId.value);
    formData.value = {
      name: data.name || '',
      ref_number: data.ref_number || '',
      start_date: data.start_date || null,
      end_date: data.end_date || null,
      status: data.status || 'new',
      trade_id: data.trade_id || null,
      owner_id: data.owner_id || null,
      street: data.street || '',
      city: data.city || '',
      zip: data.zip || '',
      state: data.state || '',
      country: data.country || '',
      agcm_office: data.agcm_office || null,
      user_ids: data.user_ids || [],
      partner_ids: data.partner_ids || [],
    };
  } catch (err) {
    message.error('Failed to load project');
  } finally {
    loading.value = false;
  }
}

async function handleSave() {
  if (!formData.value.name) {
    message.warning('Project name is required');
    return;
  }
  if (!formData.value.ref_number) {
    message.warning('Project number is required');
    return;
  }
  if (!formData.value.owner_id) {
    message.warning('Project owner is required');
    return;
  }
  saving.value = true;
  try {
    if (isEdit.value) {
      await updateProjectApi(projectId.value, formData.value);
      message.success('Project updated successfully');
    } else {
      const result = await createProjectApi(formData.value);
      message.success('Project created successfully');
      router.replace(`/agcm/projects/form/${result.id}`);
    }
  } catch (err) {
    message.error('Failed to save project');
  } finally {
    saving.value = false;
  }
}

function goBack() {
  router.push('/agcm/projects');
}

onMounted(() => {
  fetchMasterData();
  if (isEdit.value) {
    loadProject();
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
            {{ isEdit ? 'Edit Project' : 'New Project' }}
          </h3>
        </Space>
        <Button type="primary" :loading="saving" @click="handleSave">
          <template #icon><SaveOutlined /></template>
          Save
        </Button>
      </div>

      <Divider />

      <Form layout="vertical">
        <!-- Row 1: Name, Project #, Status -->
        <Row :gutter="16">
          <Col :span="10">
            <FormItem label="Project Name" required>
              <Input v-model:value="formData.name" placeholder="Enter project name" />
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Project #" required>
              <Input v-model:value="formData.ref_number" placeholder="e.g. PRJ-001" />
            </FormItem>
          </Col>
          <Col :span="4">
            <FormItem label="Status">
              <Select v-model:value="formData.status" style="width: 100%;">
                <SelectOption value="new">New</SelectOption>
                <SelectOption value="inprogress">In Progress</SelectOption>
                <SelectOption value="completed">Completed</SelectOption>
              </Select>
            </FormItem>
          </Col>
          <Col :span="4">
            <FormItem label="Office">
              <Select v-model:value="formData.agcm_office" placeholder="Select" allow-clear style="width: 100%;">
                <SelectOption value="east">East</SelectOption>
                <SelectOption value="south">South</SelectOption>
                <SelectOption value="central">Central</SelectOption>
                <SelectOption value="north">North</SelectOption>
              </Select>
            </FormItem>
          </Col>
        </Row>

        <!-- Row 2: Dates, Owner -->
        <Row :gutter="16">
          <Col :span="6">
            <FormItem label="Start Date" required>
              <DatePicker v-model:value="formData.start_date" style="width: 100%;" value-format="YYYY-MM-DD" />
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="End Date" required>
              <DatePicker v-model:value="formData.end_date" style="width: 100%;" value-format="YYYY-MM-DD" />
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Project Owner" required>
              <Select
                v-model:value="formData.owner_id"
                :options="users"
                placeholder="Select owner"
                show-search
                :filter-option="(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
                style="width: 100%;"
              />
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Trade">
              <Select
                v-model:value="formData.trade_id"
                :options="trades"
                placeholder="Select trade"
                allow-clear
                style="width: 100%;"
              />
            </FormItem>
          </Col>
        </Row>

        <!-- Row 3: Address -->
        <Divider orientation="left">Location</Divider>
        <Row :gutter="16">
          <Col :span="8">
            <FormItem label="Street">
              <Input v-model:value="formData.street" placeholder="Street address" />
            </FormItem>
          </Col>
          <Col :span="4">
            <FormItem label="City">
              <Input v-model:value="formData.city" placeholder="City" />
            </FormItem>
          </Col>
          <Col :span="4">
            <FormItem label="State">
              <Input v-model:value="formData.state" placeholder="State" />
            </FormItem>
          </Col>
          <Col :span="4">
            <FormItem label="ZIP Code">
              <Input v-model:value="formData.zip" placeholder="ZIP" />
            </FormItem>
          </Col>
          <Col :span="4">
            <FormItem label="Country">
              <Input v-model:value="formData.country" placeholder="Country" />
            </FormItem>
          </Col>
        </Row>

        <!-- Row 4: Users & Contractors -->
        <Divider orientation="left">Team</Divider>
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Project Users">
              <Select
                v-model:value="formData.user_ids"
                :options="users"
                mode="multiple"
                placeholder="Select users"
                show-search
                :filter-option="(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
                style="width: 100%;"
              />
            </FormItem>
          </Col>
          <Col :span="12">
            <FormItem label="Contractors">
              <Select
                v-model:value="formData.partner_ids"
                :options="users"
                mode="multiple"
                placeholder="Select contractors"
                show-search
                :filter-option="(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
                style="width: 100%;"
              />
            </FormItem>
          </Col>
        </Row>
      </Form>
    </Card>
  </Page>
</template>
