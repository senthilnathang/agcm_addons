/**
 * AG CM BIM Module API Client
 */

import { requestClient } from '#/api/request';

const BASE = '/agcm_bim';

// ─── BIM Models ─────────────────────────────────────────────────────────────

export async function getBIMModelsApi(params = {}) {
  return requestClient.get(`${BASE}/models`, { params });
}

export async function getBIMModelApi(modelId) {
  return requestClient.get(`${BASE}/models/${modelId}`);
}

export async function createBIMModelApi(data) {
  return requestClient.post(`${BASE}/models`, data);
}

export async function updateBIMModelApi(modelId, data) {
  return requestClient.put(`${BASE}/models/${modelId}`, data);
}

export async function deleteBIMModelApi(modelId) {
  return requestClient.delete(`${BASE}/models/${modelId}`);
}

export async function uploadBIMModelFileApi(modelId, params) {
  return requestClient.post(`${BASE}/models/${modelId}/upload`, null, { params });
}

export async function processBIMModelApi(modelId) {
  return requestClient.post(`${BASE}/models/${modelId}/process`);
}

export async function createModelVersionApi(modelId) {
  return requestClient.post(`${BASE}/models/${modelId}/new-version`);
}

export async function getModelVersionsApi(modelId) {
  return requestClient.get(`${BASE}/models/${modelId}/versions`);
}

export async function getModelSummaryApi(modelId) {
  return requestClient.get(`${BASE}/models/${modelId}/summary`);
}

export async function searchElementsApi(modelId, params = {}) {
  return requestClient.get(`${BASE}/models/${modelId}/elements`, { params });
}

// ─── Viewpoints ─────────────────────────────────────────────────────────────

export async function getViewpointsApi(params = {}) {
  return requestClient.get(`${BASE}/viewpoints`, { params });
}

export async function getViewpointApi(viewpointId) {
  return requestClient.get(`${BASE}/viewpoints/${viewpointId}`);
}

export async function createViewpointApi(data) {
  return requestClient.post(`${BASE}/viewpoints`, data);
}

export async function updateViewpointApi(viewpointId, data) {
  return requestClient.put(`${BASE}/viewpoints/${viewpointId}`, data);
}

export async function deleteViewpointApi(viewpointId) {
  return requestClient.delete(`${BASE}/viewpoints/${viewpointId}`);
}

// ─── Clash Tests ────────────────────────────────────────────────────────────

export async function getClashTestsApi(params = {}) {
  return requestClient.get(`${BASE}/clash-tests`, { params });
}

export async function getClashTestApi(testId) {
  return requestClient.get(`${BASE}/clash-tests/${testId}`);
}

export async function createClashTestApi(data) {
  return requestClient.post(`${BASE}/clash-tests`, data);
}

export async function updateClashTestApi(testId, data) {
  return requestClient.put(`${BASE}/clash-tests/${testId}`, data);
}

export async function deleteClashTestApi(testId) {
  return requestClient.delete(`${BASE}/clash-tests/${testId}`);
}

export async function runClashTestApi(testId) {
  return requestClient.post(`${BASE}/clash-tests/${testId}/run`);
}

// ─── Clash Results ──────────────────────────────────────────────────────────

export async function getClashResultsApi(testId, params = {}) {
  return requestClient.get(`${BASE}/clash-tests/${testId}/results`, { params });
}

export async function getClashResultApi(resultId) {
  return requestClient.get(`${BASE}/clash-results/${resultId}`);
}

export async function updateClashResultApi(resultId, data) {
  return requestClient.put(`${BASE}/clash-results/${resultId}`, data);
}

export async function resolveClashApi(resultId, data = {}) {
  return requestClient.post(`${BASE}/clash-results/${resultId}/resolve`, data);
}

export async function assignClashApi(resultId, data) {
  return requestClient.post(`${BASE}/clash-results/${resultId}/assign`, data);
}

export async function ignoreClashApi(resultId) {
  return requestClient.post(`${BASE}/clash-results/${resultId}/ignore`);
}
