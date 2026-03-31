/**
 * AGCM Portal Module API Client
 *
 * JavaScript API functions for the Portal module.
 * Loaded at runtime by vue3-sfc-loader.
 */

import { requestClient } from '#/api/request';

const BASE_URL = '/agcm_portal';

// =============================================================================
// SELECTIONS
// =============================================================================

export async function getSelectionsApi(params = {}) {
  return requestClient.get(`${BASE_URL}/selections`, { params });
}

export async function getSelectionApi(id) {
  return requestClient.get(`${BASE_URL}/selections/${id}`);
}

export async function createSelectionApi(data) {
  return requestClient.post(`${BASE_URL}/selections`, data);
}

export async function updateSelectionApi(id, data) {
  return requestClient.put(`${BASE_URL}/selections/${id}`, data);
}

export async function deleteSelectionApi(id) {
  return requestClient.delete(`${BASE_URL}/selections/${id}`);
}

export async function approveSelectionApi(id, optionId, decidedBy) {
  const params = { option_id: optionId };
  if (decidedBy) params.decided_by = decidedBy;
  return requestClient.post(`${BASE_URL}/selections/${id}/approve`, null, { params });
}

export async function rejectSelectionApi(id) {
  return requestClient.post(`${BASE_URL}/selections/${id}/reject`);
}

// --- Selection Options ---

export async function createOptionApi(selectionId, data) {
  return requestClient.post(`${BASE_URL}/selections/${selectionId}/options`, data);
}

export async function updateOptionApi(optionId, data) {
  return requestClient.put(`${BASE_URL}/options/${optionId}`, data);
}

export async function deleteOptionApi(optionId) {
  return requestClient.delete(`${BASE_URL}/options/${optionId}`);
}

// =============================================================================
// BID PACKAGES
// =============================================================================

export async function getBidPackagesApi(params = {}) {
  return requestClient.get(`${BASE_URL}/bid-packages`, { params });
}

export async function getBidPackageApi(id) {
  return requestClient.get(`${BASE_URL}/bid-packages/${id}`);
}

export async function createBidPackageApi(data) {
  return requestClient.post(`${BASE_URL}/bid-packages`, data);
}

export async function updateBidPackageApi(id, data) {
  return requestClient.put(`${BASE_URL}/bid-packages/${id}`, data);
}

export async function deleteBidPackageApi(id) {
  return requestClient.delete(`${BASE_URL}/bid-packages/${id}`);
}

// --- Submissions ---

export async function createSubmissionApi(bidPackageId, data) {
  return requestClient.post(`${BASE_URL}/bid-packages/${bidPackageId}/submissions`, data);
}

export async function updateSubmissionApi(submissionId, data) {
  return requestClient.put(`${BASE_URL}/submissions/${submissionId}`, data);
}

export async function deleteSubmissionApi(submissionId) {
  return requestClient.delete(`${BASE_URL}/submissions/${submissionId}`);
}

export async function awardBidApi(submissionId) {
  return requestClient.post(`${BASE_URL}/submissions/${submissionId}/award`);
}

// =============================================================================
// PORTAL CONFIG
// =============================================================================

export async function getPortalConfigApi(projectId) {
  return requestClient.get(`${BASE_URL}/portal-config/${projectId}`);
}

export async function savePortalConfigApi(data) {
  return requestClient.post(`${BASE_URL}/portal-config`, data);
}

export async function updatePortalConfigApi(configId, data) {
  return requestClient.put(`${BASE_URL}/portal-config/${configId}`, data);
}

export async function deletePortalConfigApi(configId) {
  return requestClient.delete(`${BASE_URL}/portal-config/${configId}`);
}

// =============================================================================
// DASHBOARDS
// =============================================================================

export async function getClientDashboardApi(projectId) {
  return requestClient.get(`${BASE_URL}/dashboard/client/${projectId}`);
}

export async function getSubDashboardApi(projectId, params = {}) {
  return requestClient.get(`${BASE_URL}/dashboard/sub/${projectId}`, { params });
}
