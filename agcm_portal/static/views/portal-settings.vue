<script setup>
import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Col,
  Divider,
  Form,
  FormItem,
  message,
  Row,
  Select,
  SelectOption,
  Switch,
  Textarea,
} from 'ant-design-vue';
import {
  ReloadOutlined,
  SaveOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMPortalSettings' });

const BASE_URL = '/agcm_portal';

const loading = ref(false);
const saving = ref(false);
const projects = ref([]);
const selectedProjectId = ref(null);
const configId = ref(null);

const form = ref({
  client_portal_enabled: true,
  sub_portal_enabled: true,
  show_budget: false,
  show_schedule: true,
  show_documents: true,
  show_photos: true,
  show_daily_logs: false,
  welcome_message: '',
});

async function fetchProjects() {
  try {
    const data = await requestClient.get('/agcm/projects', { params: { page_size: 200 } });
    projects.value = data.items || data.results || [];
  } catch { /* ignore */ }
}

async function loadConfig() {
  if (!selectedProjectId.value) return;
  loading.value = true;
  try {
    const data = await requestClient.get(`${BASE_URL}/portal-config/${selectedProjectId.value}`);
    configId.value = data.id || null;
    form.value = {
      client_portal_enabled: data.client_portal_enabled ?? true,
      sub_portal_enabled: data.sub_portal_enabled ?? true,
      show_budget: data.show_budget ?? false,
      show_schedule: data.show_schedule ?? true,
      show_documents: data.show_documents ?? true,
      show_photos: data.show_photos ?? true,
      show_daily_logs: data.show_daily_logs ?? false,
      welcome_message: data.welcome_message || '',
    };
  } catch {
    message.error('Failed to load portal config');
  } finally {
    loading.value = false;
  }
}

async function handleSave() {
  if (!selectedProjectId.value) {
    message.warning('Please select a project first');
    return;
  }
  saving.value = true;
  try {
    const payload = {
      project_id: selectedProjectId.value,
      ...form.value,
    };
    await requestClient.post(`${BASE_URL}/portal-config`, payload);
    message.success('Portal settings saved');
    await loadConfig();
  } catch {
    message.error('Failed to save portal settings');
  } finally {
    saving.value = false;
  }
}

function handleProjectChange() {
  configId.value = null;
  form.value = {
    client_portal_enabled: true,
    sub_portal_enabled: true,
    show_budget: false,
    show_schedule: true,
    show_documents: true,
    show_photos: true,
    show_daily_logs: false,
    welcome_message: '',
  };
  loadConfig();
}

onMounted(() => {
  fetchProjects();
});
</script>

<template>
  <Page title="Portal Settings" description="Configure client and subcontractor portal visibility per project">
    <Card>
      <div style="margin-bottom: 24px; display: flex; gap: 12px; align-items: center">
        <span style="font-weight: 500">Project:</span>
        <Select
          v-model:value="selectedProjectId"
          placeholder="Select a project"
          style="width: 300px"
          show-search
          option-filter-prop="children"
          @change="handleProjectChange"
        >
          <SelectOption v-for="p in projects" :key="p.id" :value="p.id">
            {{ p.name }}
          </SelectOption>
        </Select>
        <Button @click="loadConfig" :disabled="!selectedProjectId"><ReloadOutlined /> Refresh</Button>
      </div>

      <template v-if="selectedProjectId">
        <Form layout="vertical" :loading="loading">
          <Divider orientation="left">Portal Access</Divider>
          <Row :gutter="[32, 16]">
            <Col :span="12">
              <FormItem label="Client Portal Enabled">
                <Switch v-model:checked="form.client_portal_enabled" />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="Subcontractor Portal Enabled">
                <Switch v-model:checked="form.sub_portal_enabled" />
              </FormItem>
            </Col>
          </Row>

          <Divider orientation="left">Visibility Options</Divider>
          <Row :gutter="[32, 16]">
            <Col :span="8">
              <FormItem label="Show Budget">
                <Switch v-model:checked="form.show_budget" />
              </FormItem>
            </Col>
            <Col :span="8">
              <FormItem label="Show Schedule">
                <Switch v-model:checked="form.show_schedule" />
              </FormItem>
            </Col>
            <Col :span="8">
              <FormItem label="Show Documents">
                <Switch v-model:checked="form.show_documents" />
              </FormItem>
            </Col>
            <Col :span="8">
              <FormItem label="Show Photos">
                <Switch v-model:checked="form.show_photos" />
              </FormItem>
            </Col>
            <Col :span="8">
              <FormItem label="Show Daily Logs">
                <Switch v-model:checked="form.show_daily_logs" />
              </FormItem>
            </Col>
          </Row>

          <Divider orientation="left">Welcome Message</Divider>
          <FormItem label="Portal Welcome Message">
            <Textarea
              v-model:value="form.welcome_message"
              :rows="4"
              placeholder="Optional welcome message displayed on the portal home page"
            />
          </FormItem>

          <div style="margin-top: 24px; text-align: right">
            <Button type="primary" :loading="saving" @click="handleSave">
              <SaveOutlined /> Save Settings
            </Button>
          </div>
        </Form>
      </template>

      <template v-else>
        <div style="text-align: center; padding: 48px; color: #999">
          Select a project to configure portal settings
        </div>
      </template>
    </Card>
  </Page>
</template>
