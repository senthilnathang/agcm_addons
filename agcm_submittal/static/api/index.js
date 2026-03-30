/**
 * AG CM Submittal Module API Client
 *
 * JavaScript API functions for the Submittal Management module.
 * Loaded at runtime by vue3-sfc-loader.
 */

import { requestClient } from '#/api/request';

const BASE = '/agcm_submittal';

// =============================================================================
// SUBMITTALS
// =============================================================================

export async function getSubmittalsApi(params = {}) {
  return requestClient.get(`${BASE}/submittals`, { params });
}

export async function getSubmittalApi(id) {
  return requestClient.get(`${BASE}/submittals/${id}`);
}

export async function createSubmittalApi(data) {
  return requestClient.post(`${BASE}/submittals`, data);
}

export async function updateSubmittalApi(id, data) {
  return requestClient.put(`${BASE}/submittals/${id}`, data);
}

export async function deleteSubmittalApi(id) {
  return requestClient.delete(`${BASE}/submittals/${id}`);
}

export async function approveSubmittalApi(id, data) {
  return requestClient.post(`${BASE}/submittals/${id}/approve`, data);
}

export async function resubmitSubmittalApi(id) {
  return requestClient.post(`${BASE}/submittals/${id}/resubmit`);
}

// =============================================================================
// PACKAGES
// =============================================================================

export async function getSubmittalPackagesApi(params = {}) {
  return requestClient.get(`${BASE}/submittal-packages`, { params });
}

export async function createSubmittalPackageApi(data) {
  return requestClient.post(`${BASE}/submittal-packages`, data);
}

export async function deleteSubmittalPackageApi(id) {
  return requestClient.delete(`${BASE}/submittal-packages/${id}`);
}

// =============================================================================
// TYPES
// =============================================================================

export async function getSubmittalTypesApi() {
  return requestClient.get(`${BASE}/submittal-types`);
}

export async function createSubmittalTypeApi(data) {
  return requestClient.post(`${BASE}/submittal-types`, data);
}

export async function deleteSubmittalTypeApi(id) {
  return requestClient.delete(`${BASE}/submittal-types/${id}`);
}

// =============================================================================
// LABELS
// =============================================================================

export async function getSubmittalLabelsApi() {
  return requestClient.get(`${BASE}/submittal-labels`);
}

export async function createSubmittalLabelApi(data) {
  return requestClient.post(`${BASE}/submittal-labels`, data);
}

export async function deleteSubmittalLabelApi(id) {
  return requestClient.delete(`${BASE}/submittal-labels/${id}`);
}
