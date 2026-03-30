/**
 * AGCM Schedule Module API Client
 *
 * JavaScript API functions for the Construction Schedule module.
 * Loaded at runtime by vue3-sfc-loader.
 */

import { requestClient } from '#/api/request';

const BASE = '/agcm_schedule';

// =============================================================================
// SCHEDULES
// =============================================================================

export async function getSchedulesApi(params = {}) {
  return requestClient.get(`${BASE}/schedules`, { params });
}

export async function createScheduleApi(data) {
  return requestClient.post(`${BASE}/schedules`, data);
}

export async function updateScheduleApi(id, data) {
  return requestClient.put(`${BASE}/schedules/${id}`, data);
}

export async function activateScheduleApi(id) {
  return requestClient.post(`${BASE}/schedules/${id}/activate`);
}

export async function deleteScheduleApi(id) {
  return requestClient.delete(`${BASE}/schedules/${id}`);
}

// =============================================================================
// WBS
// =============================================================================

export async function getWbsApi(params = {}) {
  return requestClient.get(`${BASE}/wbs`, { params });
}

export async function createWbsApi(data) {
  return requestClient.post(`${BASE}/wbs`, data);
}

export async function updateWbsApi(id, data) {
  return requestClient.put(`${BASE}/wbs/${id}`, data);
}

export async function deleteWbsApi(id) {
  return requestClient.delete(`${BASE}/wbs/${id}`);
}

// =============================================================================
// TASKS
// =============================================================================

export async function getTasksApi(params = {}) {
  return requestClient.get(`${BASE}/tasks`, { params });
}

export async function getTaskApi(id) {
  return requestClient.get(`${BASE}/tasks/${id}`);
}

export async function createTaskApi(data) {
  return requestClient.post(`${BASE}/tasks`, data);
}

export async function updateTaskApi(id, data) {
  return requestClient.put(`${BASE}/tasks/${id}`, data);
}

export async function deleteTaskApi(id) {
  return requestClient.delete(`${BASE}/tasks/${id}`);
}

export async function updateTaskProgressApi(id, progress) {
  return requestClient.post(`${BASE}/tasks/${id}/progress`, { progress });
}

// =============================================================================
// DEPENDENCIES
// =============================================================================

export async function getDependenciesApi(params = {}) {
  return requestClient.get(`${BASE}/dependencies`, { params });
}

export async function createDependencyApi(data) {
  return requestClient.post(`${BASE}/dependencies`, data);
}

export async function deleteDependencyApi(id) {
  return requestClient.delete(`${BASE}/dependencies/${id}`);
}

// =============================================================================
// GANTT
// =============================================================================

export async function getGanttDataApi(params = {}) {
  return requestClient.get(`${BASE}/gantt`, { params });
}
