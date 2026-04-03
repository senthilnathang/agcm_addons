<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Col,
  Descriptions,
  DescriptionsItem,
  Divider,
  Empty,
  message,
  Modal,
  Row,
  Space,
  Spin,
  Steps,
  Tag,
  Tabs,
  Timeline,
  TimelineItem,
  Textarea,
  Tooltip,
} from 'ant-design-vue';
import {
  ArrowLeftOutlined,
  CalendarOutlined,
  CheckCircleFilled,
  CheckCircleOutlined,
  ClockCircleFilled,
  ClockCircleOutlined,
  CloseCircleFilled,
  CloseCircleOutlined,
  EditOutlined,
  ExclamationCircleFilled,
  ExclamationCircleOutlined,
  FileTextOutlined,
  ReloadOutlined,
  SendOutlined,
  UserOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMSubmittalDetail' });

const route = useRoute();
const router = useRouter();
const BASE = '/agcm_submittal';

const submittalId = computed(() => route.query.id);
const loading = ref(false);
const submittal = ref(null);
const activeTab = ref('details');

function getAccessToken() {
  try {
    return localStorage?.getItem('accessToken') || '';
  } catch {
    return '';
  }
}

const statusConfig = {
  draft: { color: 'default', label: 'Draft' },
  pending_review: { color: 'processing', label: 'Pending Review' },
  in_review: { color: 'processing', label: 'In Review' },
  approved: { color: 'success', label: 'Approved' },
  approved_with_comments: { color: 'warning', label: 'Approved w/ Comments' },
  rejected: { color: 'error', label: 'Rejected' },
  resubmitted: { color: 'cyan', label: 'Resubmitted' },
};

const priorityConfig = {
  low: { color: '#52c41a', bg: '#f6ffed', border: '#b7eb8f', label: 'Low' },
  medium: { color: '#1890ff', bg: '#e6f7ff', border: '#91d5ff', label: 'Medium' },
  high: { color: '#fa8c16', bg: '#fff7e6', border: '#ffd591', label: 'High' },
  urgent: { color: '#f5222d', bg: '#fff1f0', border: '#ffa39e', label: 'Urgent' },
};

const approverStatusConfig = {
  pending: { icon: ClockCircleFilled, color: '#8c8c8c', bg: '#fafafa', label: 'Pending' },
  approved: { icon: CheckCircleFilled, color: '#52c41a', bg: '#f6ffed', label: 'Approved' },
  approved_as_noted: { icon: ExclamationCircleFilled, color: '#faad14', bg: '#fffbe6', label: 'Approved as Noted' },
  rejected: { icon: CloseCircleFilled, color: '#f5222d', bg: '#fff1f0', label: 'Rejected' },
  revise_and_submit: { icon: ReloadOutlined, color: '#722ed1', bg: '#f9f0ff', label: 'Revise & Submit' },
};

// Approve modal
const approveModalVisible = ref(false);
const approveAction = ref('');
const approveComments = ref('');
const approving = ref(false);

async function fetchSubmittal() {
  if (!submittalId.value) return;
  loading.value = true;
  try {
    submittal.value = await requestClient.get(`${BASE}/submittals/${submittalId.value}`);
  } catch {
    message.error('Failed to load submittal');
  } finally {
    loading.value = false;
  }
}

function handleEdit() {
  router.push(`/agcm/submittals/form?id=${submittalId.value}`);
}

function handleBack() {
  router.push('/agcm/submittals/list');
}

function openApproveModal(action) {
  approveAction.value = action;
  approveComments.value = '';
  approveModalVisible.value = true;
}

async function handleApprove() {
  approving.value = true;
  try {
    await requestClient.post(`${BASE}/submittals/${submittalId.value}/approve`, {
      action: approveAction.value,
      comments: approveComments.value || null,
    });
    message.success('Action submitted successfully');
    approveModalVisible.value = false;
    fetchSubmittal();
  } catch (err) {
    const detail = err?.response?.data?.detail || 'Failed to process action';
    message.error(detail);
  } finally {
    approving.value = false;
  }
}

async function handleResubmit() {
  try {
    await requestClient.post(`${BASE}/submittals/${submittalId.value}/resubmit`);
    message.success('Submittal resubmitted');
    fetchSubmittal();
  } catch {
    message.error('Failed to resubmit');
  }
}

const actionLabel = computed(() => {
  const map = {
    approve: 'Approve',
    approved_as_noted: 'Approve as Noted',
    reject: 'Reject',
    revise_and_submit: 'Revise & Submit',
  };
  return map[approveAction.value] || approveAction.value;
});

function formatDate(d) {
  if (!d) return '-';
  return new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function formatDateTime(d) {
  if (!d) return '';
  return new Date(d).toLocaleString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

const approvalProgress = computed(() => {
  if (!submittal.value?.approvers?.length) return { done: 0, total: 0, pct: 0 };
  const total = submittal.value.approvers.length;
  const done = submittal.value.approvers.filter(
    a => a.status === 'approved' || a.status === 'approved_as_noted'
  ).length;
  return { done, total, pct: Math.round((done / total) * 100) };
});

onMounted(fetchSubmittal);
</script>

<template>
  <Page title="Submittal Detail">
    <ASpin :spinning="loading">
      <template v-if="submittal">
        <!-- Header Card -->
        <ACard class="mb-4">
          <div class="flex items-start justify-between">
            <div style="flex: 1;">
              <div class="flex items-center gap-2 mb-2">
                <ATag color="blue" style="font-size: 13px; font-weight: 600; margin: 0;">
                  {{ submittal.sequence_name }}
                </ATag>
                <ATag
                  :color="statusConfig[submittal.status]?.color || 'default'"
                  style="margin: 0;"
                >
                  {{ statusConfig[submittal.status]?.label || submittal.status }}
                </ATag>
              </div>
              <h2 style="font-size: 22px; font-weight: 700; margin: 0 0 8px 0; line-height: 1.3;">
                {{ submittal.title }}
              </h2>
              <ASpace :size="8" wrap>
                <span
                  v-if="submittal.spec_section"
                  style="color: #595959; font-size: 13px;"
                >
                  <FileTextOutlined /> Spec: {{ submittal.spec_section }}
                </span>
                <ATag
                  v-if="submittal.priority"
                  :style="{
                    color: priorityConfig[submittal.priority]?.color || '#595959',
                    background: priorityConfig[submittal.priority]?.bg || '#fafafa',
                    borderColor: priorityConfig[submittal.priority]?.border || '#d9d9d9',
                    margin: 0,
                  }"
                >
                  {{ priorityConfig[submittal.priority]?.label || submittal.priority }} Priority
                </ATag>
                <ATag color="geekblue" style="margin: 0;">Rev {{ submittal.revision }}</ATag>
                <ATag
                  v-for="label in (submittal.labels || [])"
                  :key="label.id"
                  :color="label.color"
                  style="margin: 0;"
                >
                  {{ label.name }}
                </ATag>
              </ASpace>
            </div>
            <ASpace>
              <AButton @click="handleBack">
                <template #icon><ArrowLeftOutlined /></template>
                Back
              </AButton>
              <AButton @click="handleEdit">
                <template #icon><EditOutlined /></template>
                Edit
              </AButton>
              <AButton
                v-if="submittal.status === 'rejected' || submittal.status === 'draft'"
                type="primary"
                @click="handleResubmit"
              >
                <template #icon><ReloadOutlined /></template>
                Resubmit
              </AButton>
            </ASpace>
          </div>
        </ACard>

        <!-- Tabs Card -->
        <Card class="mt-4">
          <Tabs v-model:activeKey="activeTab">
            <!-- ==================== DETAILS TAB ==================== -->
            <Tabs.TabPane key="details" tab="Details">
              <div style="padding: 16px 0 24px;">
                <!-- Key Info Grid -->
                <ARow :gutter="16" class="mb-4">
                  <ACol :span="4">
                    <div class="detail-info-card">
                      <div class="detail-info-label">Package</div>
                      <div class="detail-info-value">{{ submittal.package_name || '-' }}</div>
                    </div>
                  </ACol>
                  <ACol :span="4">
                    <div class="detail-info-card">
                      <div class="detail-info-label">Type</div>
                      <div class="detail-info-value">{{ submittal.type_name || '-' }}</div>
                    </div>
                  </ACol>
                  <ACol :span="4">
                    <div class="detail-info-card">
                      <div class="detail-info-label">Due Date</div>
                      <div class="detail-info-value">
                        <CalendarOutlined style="margin-right: 4px; color: #8c8c8c;" />
                        {{ formatDate(submittal.due_date) }}
                      </div>
                    </div>
                  </ACol>
                  <ACol :span="4">
                    <div class="detail-info-card">
                      <div class="detail-info-label">Submitted</div>
                      <div class="detail-info-value">{{ formatDate(submittal.submitted_date) }}</div>
                    </div>
                  </ACol>
                  <ACol :span="4">
                    <div class="detail-info-card">
                      <div class="detail-info-label">Received</div>
                      <div class="detail-info-value">{{ formatDate(submittal.received_date) }}</div>
                    </div>
                  </ACol>
                  <ACol :span="4">
                    <div class="detail-info-card">
                      <div class="detail-info-label">Revision</div>
                      <div class="detail-info-value">#{{ submittal.revision }}</div>
                    </div>
                  </ACol>
                </ARow>

                <!-- Description -->
                <div v-if="submittal.description" class="detail-section">
                  <h4 class="detail-section-title">Description</h4>
                  <div class="detail-section-body">
                    <p style="white-space: pre-wrap; margin: 0; color: #434343; line-height: 1.7;">
                      {{ submittal.description }}
                    </p>
                  </div>
                </div>

                <!-- Approval Summary (compact) -->
                <div v-if="(submittal.approvers || []).length > 0" class="detail-section" style="margin-top: 16px;">
                  <h4 class="detail-section-title">Approval Summary</h4>
                  <div style="display: flex; align-items: center; gap: 16px; padding: 12px 16px; background: #fafafa; border-radius: 8px;">
                    <div style="flex: 1;">
                      <div style="background: #f0f0f0; border-radius: 4px; height: 8px; overflow: hidden;">
                        <div
                          :style="{
                            width: approvalProgress.pct + '%',
                            height: '100%',
                            background: approvalProgress.pct === 100 ? '#52c41a' : '#1890ff',
                            borderRadius: '4px',
                            transition: 'width 0.3s ease',
                          }"
                        ></div>
                      </div>
                    </div>
                    <span style="font-size: 13px; color: #595959; white-space: nowrap;">
                      {{ approvalProgress.done }} / {{ approvalProgress.total }} approved
                    </span>
                  </div>
                </div>
              </div>
            </Tabs.TabPane>

            <!-- ==================== APPROVAL CHAIN TAB ==================== -->
            <Tabs.TabPane key="approvers" tab="Approval Chain">
              <div style="padding: 16px 0 24px;">
                <div v-if="(submittal.approvers || []).length === 0">
                  <AEmpty description="No approvers assigned" :image="Empty.PRESENTED_IMAGE_SIMPLE" />
                </div>
                <template v-else>
                  <!-- Approval Steps -->
                  <div class="approval-chain">
                    <div
                      v-for="(approver, idx) in submittal.approvers"
                      :key="approver.id"
                      class="approval-step"
                      :style="{
                        background: approverStatusConfig[approver.status]?.bg || '#fafafa',
                        borderLeft: `3px solid ${approverStatusConfig[approver.status]?.color || '#d9d9d9'}`,
                      }"
                    >
                      <div class="approval-step-header">
                        <div style="display: flex; align-items: center; gap: 10px;">
                          <component
                            :is="approverStatusConfig[approver.status]?.icon || ClockCircleFilled"
                            :style="{
                              color: approverStatusConfig[approver.status]?.color || '#8c8c8c',
                              fontSize: '22px',
                            }"
                          />
                          <div>
                            <div style="font-weight: 600; font-size: 14px; color: #262626;">
                              Step {{ approver.sequence }}
                            </div>
                            <div style="font-size: 13px; color: #595959;">
                              <UserOutlined style="margin-right: 4px;" />
                              {{ approver.user_name || `User #${approver.user_id}` }}
                            </div>
                          </div>
                        </div>
                        <ATag
                          :style="{
                            color: approverStatusConfig[approver.status]?.color || '#8c8c8c',
                            background: 'white',
                            borderColor: approverStatusConfig[approver.status]?.color || '#d9d9d9',
                            fontWeight: 500,
                            margin: 0,
                          }"
                        >
                          {{ approverStatusConfig[approver.status]?.label || approver.status }}
                        </ATag>
                      </div>
                      <div v-if="approver.comments" style="margin-top: 8px; padding-left: 32px; font-size: 13px; color: #595959; line-height: 1.5;">
                        {{ approver.comments }}
                      </div>
                      <div v-if="approver.signed_at" style="margin-top: 4px; padding-left: 32px; font-size: 12px; color: #8c8c8c;">
                        Signed {{ formatDateTime(approver.signed_at) }}
                      </div>

                      <!-- Connector line -->
                      <div
                        v-if="idx < submittal.approvers.length - 1"
                        class="approval-connector"
                      ></div>
                    </div>
                  </div>

                  <!-- Action Buttons -->
                  <ADivider style="margin: 16px 0;" />
                  <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                    <AButton type="primary" @click="openApproveModal('approve')">
                      <template #icon><CheckCircleOutlined /></template>
                      Approve
                    </AButton>
                    <AButton @click="openApproveModal('approved_as_noted')">
                      <template #icon><ExclamationCircleOutlined /></template>
                      Approve as Noted
                    </AButton>
                    <AButton danger @click="openApproveModal('reject')">
                      <template #icon><CloseCircleOutlined /></template>
                      Reject
                    </AButton>
                    <AButton @click="openApproveModal('revise_and_submit')">
                      <template #icon><ReloadOutlined /></template>
                      Revise & Submit
                    </AButton>
                  </div>
                </template>
              </div>
            </Tabs.TabPane>

            <!-- ==================== ACTIVITY TAB ==================== -->
            <Tabs.TabPane key="activity" tab="Activity">
              <div style="padding: 16px 0 24px;">
                <ActivityThread
                  :model-name="'agcm_submittals'"
                  :record-id="submittalId"
                  :access-token="getAccessToken()"
                  :api-base="'/api/v1'"
                  :show-messages="true"
                  :show-activities="true"
                />
              </div>
            </Tabs.TabPane>
          </Tabs>
        </Card>
      </template>

      <AEmpty v-else-if="!loading" description="Submittal not found" />
    </ASpin>

    <!-- Approve Modal -->
    <AModal
      v-model:open="approveModalVisible"
      :title="actionLabel"
      :confirm-loading="approving"
      @ok="handleApprove"
      :width="480"
    >
      <AForm layout="vertical" style="margin-top: 16px;">
        <AFormItem label="Comments (optional)">
          <ATextarea
            v-model:value="approveComments"
            :rows="4"
            placeholder="Enter comments..."
          />
        </AFormItem>
      </AForm>
    </AModal>
  </Page>
</template>
