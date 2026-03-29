<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Checkbox,
  Col,
  DatePicker,
  Divider,
  Form,
  FormItem,
  message,
  Row,
  Space,
} from 'ant-design-vue';
import { ArrowLeftOutlined, CopyOutlined } from '@ant-design/icons-vue';

import { getDailyLogApi, makeLogApi } from '#/api/agcm';

defineOptions({ name: 'AGCMDailyLogCopy' });

const route = useRoute();
const router = useRouter();
const sourceId = computed(() => route.params.id);

const loading = ref(false);
const saving = ref(false);
const sourceLog = ref(null);

const formData = ref({
  source_log_id: null,
  date: null,
  copy_manpower: true,
  copy_safety: false,
  copy_observations: false,
  copy_inspections: false,
  copy_delays: false,
});

async function fetchSource() {
  if (!sourceId.value) return;
  loading.value = true;
  try {
    sourceLog.value = await getDailyLogApi(sourceId.value);
    formData.value.source_log_id = Number(sourceId.value);
  } catch (err) {
    message.error('Failed to load source log');
  } finally {
    loading.value = false;
  }
}

async function handleCopy() {
  if (!formData.value.date) {
    message.warning('Please select a target date');
    return;
  }
  saving.value = true;
  try {
    const result = await makeLogApi(formData.value);
    message.success('Daily log copied successfully');
    router.push(`/agcm/daily-logs/detail/${result.id}`);
  } catch (err) {
    const errMsg = err?.response?.data?.detail || 'Failed to copy daily log';
    message.error(errMsg);
  } finally {
    saving.value = false;
  }
}

function goBack() {
  router.push('/agcm/daily-logs');
}

onMounted(fetchSource);
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
          <h3 style="margin: 0;">Copy Daily Log</h3>
        </Space>
        <Button type="primary" :loading="saving" @click="handleCopy">
          <template #icon><CopyOutlined /></template>
          Copy Log
        </Button>
      </div>

      <Divider />

      <ASpin :spinning="loading">
        <template v-if="sourceLog">
          <!-- Source info -->
          <AAlert
            class="mb-4"
            type="info"
            show-icon
            :message="`Copying from: ${sourceLog.sequence_name} (${sourceLog.date})`"
            :description="`Project ID: ${sourceLog.project_id} | Manpower: ${sourceLog.manpower_count || 0} | Notes: ${sourceLog.notes_count || 0} | Inspections: ${sourceLog.inspection_count || 0}`"
          />

          <Form layout="vertical">
            <Row :gutter="16">
              <Col :span="8">
                <FormItem label="Target Date" required>
                  <DatePicker v-model:value="formData.date" style="width: 100%;" value-format="YYYY-MM-DD" />
                </FormItem>
              </Col>
            </Row>

            <Divider orientation="left">Select data to copy</Divider>

            <Row :gutter="[16, 12]">
              <Col :span="8">
                <Checkbox v-model:checked="formData.copy_manpower">
                  Manpower ({{ sourceLog.manpower_count || 0 }} entries)
                </Checkbox>
              </Col>
              <Col :span="8">
                <Checkbox v-model:checked="formData.copy_observations">
                  Observations ({{ sourceLog.notes_count || 0 }} entries)
                </Checkbox>
              </Col>
              <Col :span="8">
                <Checkbox v-model:checked="formData.copy_safety">
                  Safety Observations ({{ sourceLog.safety_violation_count || 0 }} entries)
                </Checkbox>
              </Col>
              <Col :span="8">
                <Checkbox v-model:checked="formData.copy_inspections">
                  Inspections ({{ sourceLog.inspection_count || 0 }} entries)
                </Checkbox>
              </Col>
              <Col :span="8">
                <Checkbox v-model:checked="formData.copy_delays">
                  Delays ({{ sourceLog.delay_count || 0 }} entries)
                </Checkbox>
              </Col>
            </Row>
          </Form>
        </template>
      </ASpin>
    </Card>
  </Page>
</template>
