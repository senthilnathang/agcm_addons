<script setup>
import { onMounted, ref } from 'vue';
import {
  FilePdfOutlined,
  PrinterOutlined,
} from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';

import { Page } from '@vben/common-ui';
import { getProjectsApi, periodicReportUrl } from '#/api/agcm';

defineOptions({ name: 'AGCMPeriodicReport' });

const projects = ref([]);
const modalVisible = ref(true); // opens on load
const generating = ref(false);

const formData = ref({
  project_id: null,
  date_from: null,
  date_to: null,
});

async function fetchProjects() {
  try {
    const res = await getProjectsApi({ page_size: 200 });
    projects.value = (res.items || []).map(p => ({
      value: p.id,
      label: `${p.sequence_name} - ${p.name}`,
    }));
  } catch {}
}

function handleGenerate() {
  if (!formData.value.project_id) {
    message.warning('Please select a project');
    return;
  }

  generating.value = true;
  try {
    const url = periodicReportUrl(
      formData.value.project_id,
      formData.value.date_from,
      formData.value.date_to,
    );
    window.open(url, '_blank');
    message.success('Report generated — opening in new tab');
  } catch (error) {
    message.error('Failed to generate report');
  } finally {
    generating.value = false;
  }
}

function handleReset() {
  formData.value = { project_id: null, date_from: null, date_to: null };
}

onMounted(fetchProjects);
</script>

<template>
  <Page title="Periodic Project Report" description="Generate a combined daily log report for a project within a date range">
    <ACard style="max-width: 700px; margin: 0 auto; border-radius: 12px;">
      <!-- Header -->
      <div style="text-align: center; margin-bottom: 24px;">
        <div style="font-size: 48px; margin-bottom: 8px;">
          <FilePdfOutlined style="color: #f5222d;" />
        </div>
        <h2 style="margin: 0;">Generate Project Report</h2>
        <p style="color: #888; margin-top: 4px;">
          Select a project and optional date range to generate a combined PDF report of all daily logs.
        </p>
      </div>

      <ADivider />

      <!-- Form -->
      <AForm layout="vertical">
        <AFormItem label="Project" required>
          <ASelect
            v-model:value="formData.project_id"
            :options="projects"
            placeholder="Select a project"
            show-search
            size="large"
            :filter-option="(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
            style="width: 100%;"
          />
        </AFormItem>

        <ARow :gutter="16">
          <ACol :span="12">
            <AFormItem label="Date From (optional)">
              <ADatePicker
                v-model:value="formData.date_from"
                style="width: 100%;"
                size="large"
                value-format="YYYY-MM-DD"
                placeholder="Start date"
              />
            </AFormItem>
          </ACol>
          <ACol :span="12">
            <AFormItem label="Date To (optional)">
              <ADatePicker
                v-model:value="formData.date_to"
                style="width: 100%;"
                size="large"
                value-format="YYYY-MM-DD"
                placeholder="End date"
              />
            </AFormItem>
          </ACol>
        </ARow>

        <AAlert
          v-if="!formData.date_from && !formData.date_to"
          type="info"
          show-icon
          message="No date range selected — all daily logs for this project will be included."
          style="margin-bottom: 16px;"
        />

        <ADivider />

        <div style="display: flex; justify-content: space-between;">
          <AButton @click="handleReset">Reset</AButton>
          <ASpace>
            <AButton
              type="primary"
              size="large"
              :loading="generating"
              @click="handleGenerate"
            >
              <template #icon><PrinterOutlined /></template>
              Generate Report
            </AButton>
          </ASpace>
        </div>
      </AForm>
    </ACard>
  </Page>
</template>
