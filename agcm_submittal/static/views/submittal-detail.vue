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
  Input,
  message,
  Modal,
  Row,
  Space,
  Steps,
  Tag,
  Timeline,
  TimelineItem,
  Textarea,
} from 'ant-design-vue';
import {
  ArrowLeftOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  EditOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';

import { requestClient } from '#/api/request';
import { useUserStore } from '#/store/user';

defineOptions({ name: 'AGCMSubmittalDetail' });

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const BASE = '/agcm_submittal';

const submittalId = computed(() => route.params.id);
const loading = ref(false);
const submittal = ref(null);
const activeTab = ref('details');

const statusColors = {
  draft: 'default',
  pending_review: 'processing',
  in_review: 'processing',
  approved: 'success',
  approved_with_comments: 'warning',
  rejected: 'error',
  resubmitted: 'cyan',
};

const statusLabels = {
  draft: 'Draft',
  pending_review: 'Pending Review',
  in_review: 'In Review',
  approved: 'Approved',
  approved_with_comments: 'Approved w/ Comments',
  rejected: 'Rejected',
  resubmitted: 'Resubmitted',
};

const priorityColors = {
  low: 'green',
  medium: 'blue',
  high: 'orange',
  urgent: 'red',
};

const approverStatusIcons = {
  pending: ClockCircleOutlined,
  approved: CheckCircleOutlined,
  approved_as_noted: ExclamationCircleOutlined,
  rejected: CloseCircleOutlined,
  revise_and_submit: ReloadOutlined,
};

const approverStatusColors = {
  pending: '#999',
  approved: '#52c41a',
  approved_as_noted: '#faad14',
  rejected: '#f5222d',
  revise_and_submit: '#722ed1',
};

const approverStatusLabels = {
  pending: 'Pending',
  approved: 'Approved',
  approved_as_noted: 'Approved as Noted',
  rejected: 'Rejected',
  revise_and_submit: 'Revise & Submit',
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
  router.push(`/agcm/submittals/form/${submittalId.value}`);
}

function handleBack() {
  router.push('/agcm/submittals');
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

onMounted(fetchSubmittal);
</script>

<template>
  <div class="p-6">
    <ASpin :spinning="loading">
      <!-- Header -->
      <div class="mb-4 flex items-center gap-3">
        <AButton @click="handleBack">
          <template #icon><ArrowLeftOutlined /></template>
          Back
        </AButton>
        <template v-if="submittal">
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
        </template>
      </div>

      <template v-if="submittal">
        <!-- Title Card -->
        <ACard class="mb-4">
          <div class="flex items-start justify-between">
            <div>
              <h1 class="text-2xl font-bold mb-1">{{ submittal.title }}</h1>
              <p class="text-gray-500 mb-2">
                {{ submittal.sequence_name }}
                <span v-if="submittal.spec_section"> | Spec: {{ submittal.spec_section }}</span>
              </p>
              <ASpace wrap>
                <ATag :color="statusColors[submittal.status] || 'default'">
                  {{ statusLabels[submittal.status] || submittal.status }}
                </ATag>
                <ATag :color="priorityColors[submittal.priority] || 'default'">
                  {{ (submittal.priority || '').replace(/^\w/, c => c.toUpperCase()) }} Priority
                </ATag>
                <ATag color="blue">Rev {{ submittal.revision }}</ATag>
                <ATag
                  v-for="label in (submittal.labels || [])"
                  :key="label.id"
                  :color="label.color"
                >
                  {{ label.name }}
                </ATag>
              </ASpace>
            </div>
          </div>
        </ACard>

        <!-- Tabs -->
        <ACard>
          <ATabs v-model:activeKey="activeTab">
            <ATabs.TabPane key="details" tab="Details">
              <!-- Details Section -->
              <ADescriptions :column="3" bordered size="small" class="mb-4">
                <ADescriptionsItem label="Package">{{ submittal.package_name || '-' }}</ADescriptionsItem>
                <ADescriptionsItem label="Type">{{ submittal.type_name || '-' }}</ADescriptionsItem>
                <ADescriptionsItem label="Due Date">{{ submittal.due_date || '-' }}</ADescriptionsItem>
                <ADescriptionsItem label="Submitted Date">{{ submittal.submitted_date || '-' }}</ADescriptionsItem>
                <ADescriptionsItem label="Received Date">{{ submittal.received_date || '-' }}</ADescriptionsItem>
                <ADescriptionsItem label="Revision">{{ submittal.revision }}</ADescriptionsItem>
              </ADescriptions>
              <div v-if="submittal.description" class="mt-4">
                <h4 class="font-semibold mb-2">Description</h4>
                <p style="white-space: pre-wrap;">{{ submittal.description }}</p>
              </div>
            </ATabs.TabPane>

            <!-- Approval Chain Tab -->
            <ATabs.TabPane key="approvers" tab="Approval Chain">
              <div v-if="(submittal.approvers || []).length === 0" class="text-gray-400">
                No approvers assigned.
              </div>
              <ATimeline v-else>
                <ATimelineItem
                  v-for="approver in submittal.approvers"
                  :key="approver.id"
                  :color="approverStatusColors[approver.status] || '#999'"
                >
                  <div class="flex items-center gap-3">
                    <div>
                      <component
                        :is="approverStatusIcons[approver.status] || ClockCircleOutlined"
                        :style="{ color: approverStatusColors[approver.status] || '#999', fontSize: '18px' }"
                      />
                    </div>
                    <div style="flex: 1;">
                      <div class="font-semibold">
                        Step {{ approver.sequence }}: {{ approver.user_name || `User #${approver.user_id}` }}
                      </div>
                      <ATag
                        :color="approverStatusColors[approver.status]"
                        size="small"
                        style="margin-top: 4px;"
                      >
                        {{ approverStatusLabels[approver.status] || approver.status }}
                      </ATag>
                      <div v-if="approver.comments" class="text-gray-500 mt-1" style="font-size: 13px;">
                        {{ approver.comments }}
                      </div>
                      <div v-if="approver.signed_at" class="text-gray-400 mt-1" style="font-size: 12px;">
                        Signed: {{ new Date(approver.signed_at).toLocaleString() }}
                      </div>
                    </div>
                  </div>
                </ATimelineItem>
              </ATimeline>

              <!-- Action buttons for approvers -->
              <ADivider v-if="(submittal.approvers || []).length > 0" />
              <ASpace v-if="(submittal.approvers || []).length > 0">
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
              </ASpace>
            </ATabs.TabPane>

            <!-- Activity Tab -->
            <ATabs.TabPane key="activity" tab="Activity">
              <ActivityThread
                :model-name="'agcm_submittals'"
                :record-id="submittalId"
                :access-token="userStore.accessToken"
                :api-base="'/api/v1'"
                :show-messages="true"
                :show-activities="true"
              />
            </ATabs.TabPane>
          </ATabs>
        </ACard>
      </template>

      <AEmpty v-else-if="!loading" description="Submittal not found" />
    </ASpin>

    <!-- Approve Modal -->
    <AModal
      v-model:open="approveModalVisible"
      :title="actionLabel"
      :confirm-loading="approving"
      @ok="handleApprove"
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
  </div>
</template>
