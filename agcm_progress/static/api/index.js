/**
 * AGCM Progress Module API Client
 *
 * JavaScript API functions for the Progress Tracking module.
 * Loaded at runtime by vue3-sfc-loader.
 */

import { requestClient } from '#/api/request';

const BASE = '/agcm_progress';

// =============================================================================
// MILESTONES
// =============================================================================

export async function getMilestonesApi(params = {}) {
  return requestClient.get(`${BASE}/milestones`, { params });
}

export async function createMilestoneApi(data) {
  return requestClient.post(`${BASE}/milestones`, data);
}

export async function updateMilestoneApi(id, data) {
  return requestClient.put(`${BASE}/milestones/${id}`, data);
}

export async function deleteMilestoneApi(id) {
  return requestClient.delete(`${BASE}/milestones/${id}`);
}

export async function toggleMilestoneCompletedApi(id) {
  return requestClient.post(`${BASE}/milestones/${id}/toggle-completed`);
}

// =============================================================================
// ISSUES
// =============================================================================

export async function getIssuesApi(params = {}) {
  return requestClient.get(`${BASE}/issues`, { params });
}

export async function getIssueApi(id) {
  return requestClient.get(`${BASE}/issues/${id}`);
}

export async function createIssueApi(data) {
  return requestClient.post(`${BASE}/issues`, data);
}

export async function updateIssueApi(id, data) {
  return requestClient.put(`${BASE}/issues/${id}`, data);
}

export async function deleteIssueApi(id) {
  return requestClient.delete(`${BASE}/issues/${id}`);
}

export async function resolveIssueApi(id) {
  return requestClient.post(`${BASE}/issues/${id}/resolve`);
}

export async function closeIssueApi(id) {
  return requestClient.post(`${BASE}/issues/${id}/close`);
}

// =============================================================================
// ESTIMATION
// =============================================================================

export async function getEstimationTreeApi(params = {}) {
  return requestClient.get(`${BASE}/estimation`, { params });
}

export async function createEstimationItemApi(data) {
  return requestClient.post(`${BASE}/estimation`, data);
}

export async function updateEstimationItemApi(id, data) {
  return requestClient.put(`${BASE}/estimation/${id}`, data);
}

export async function deleteEstimationItemApi(id) {
  return requestClient.delete(`${BASE}/estimation/${id}`);
}

// =============================================================================
// S-CURVE
// =============================================================================

export async function getScurveDataApi(params = {}) {
  return requestClient.get(`${BASE}/scurve`, { params });
}

export async function createScurveDataApi(data) {
  return requestClient.post(`${BASE}/scurve`, data);
}

export async function updateScurveDataApi(id, data) {
  return requestClient.put(`${BASE}/scurve/${id}`, data);
}

export async function deleteScurveDataApi(id) {
  return requestClient.delete(`${BASE}/scurve/${id}`);
}

// =============================================================================
// PROJECT IMAGES
// =============================================================================

export async function getProjectImagesApi(params = {}) {
  return requestClient.get(`${BASE}/project-images`, { params });
}

export async function uploadProjectImageApi(projectId, file, { name, description, tags, taken_on } = {}) {
  const formData = new FormData();
  formData.append('file', file);
  const params = new URLSearchParams({ project_id: projectId });
  if (name) params.append('name', name);
  if (description) params.append('description', description);
  if (tags) params.append('tags', tags);
  if (taken_on) params.append('taken_on', taken_on);
  return requestClient.post(`${BASE}/project-images/upload?${params.toString()}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}

export async function updateProjectImageApi(id, data) {
  return requestClient.put(`${BASE}/project-images/${id}`, data);
}

export async function deleteProjectImageApi(id) {
  return requestClient.delete(`${BASE}/project-images/${id}`);
}
