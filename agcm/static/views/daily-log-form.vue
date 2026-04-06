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
  message,
  Row,
  Select,
  Space,
} from 'ant-design-vue';
import { ArrowLeftOutlined, SaveOutlined } from '@ant-design/icons-vue';

import { createDailyLogApi, getProjectsApi } from '#/api/agcm';

defineOptions({ name: 'AGCMDailyLogForm' });

const route = useRoute();
const router = useRouter();

const saving = ref(false);
const projects = ref([]);

const formData = ref({
  project_id: Number(route.query.project_id) || null,
  date: null,
});

async function fetchProjects() {
  try {
    const data = await getProjectsApi({ page_size: 200 });
    projects.value = (data.items || []).map((p) => ({
      value: p.id,
      label: `${p.sequence_name || ''} - ${p.name}`,
    }));
  } catch {}
}

async function handleSave() {
  if (!formData.value.project_id) {
    message.warning('Please select a project');
    return;
  }
  if (!formData.value.date) {
    message.warning('Please select a date');
    return;
  }
  saving.value = true;
  try {
    const result = await createDailyLogApi(formData.value);
    message.success('Daily log created successfully');
    router.push(`/agcm/daily-logs/detail/${result.id}`);
  } catch (err) {
    const errMsg = err?.response?.data?.detail || 'Failed to create daily log';
    message.error(errMsg);
  } finally {
    saving.value = false;
  }
}

function goBack() {
  router.push('/agcm/daily-logs');
}

onMounted(fetchProjects);
</script>

<template>
  <Page auto-content-height>
    <Card :bordered="false">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <Space>
          <Button @click="goBack">
            <template #icon><ArrowLeftOutlined /></template>
            Back
          </Button>
          <h3 style="margin: 0;">New Daily Log</h3>
        </Space>
        <Button type="primary" :loading="saving" @click="handleSave">
          <template #icon><SaveOutlined /></template>
          Create
        </Button>
      </div>

      <Divider />

      <Form layout="vertical">
        <Row :gutter="16">
          <Col :span="12">
            <FormItem label="Project" required>
              <Select
                v-model:value="formData.project_id"
                :options="projects"
                placeholder="Select project"
                show-search
                :filter-option="(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
                style="width: 100%;"
              />
            </FormItem>
          </Col>
          <Col :span="6">
            <FormItem label="Date" required>
              <DatePicker v-model:value="formData.date" style="width: 100%;" value-format="YYYY-MM-DD" />
            </FormItem>
          </Col>
        </Row>
      </Form>
    </Card>
  </Page>
</template>
