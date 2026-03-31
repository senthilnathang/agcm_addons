/**
 * AG CM Resource Module API Client
 *
 * JavaScript API functions for the Construction Resource Management module.
 * Loaded at runtime by vue3-sfc-loader.
 */

import { requestClient } from '#/api/request';

const BASE = '/agcm_resource';

// =============================================================================
// WORKERS
// =============================================================================

export async function getWorkersApi(params = {}) {
  return requestClient.get(`${BASE}/workers`, { params });
}

export async function getWorkerApi(workerId) {
  return requestClient.get(`${BASE}/workers/${workerId}`);
}

export async function createWorkerApi(data) {
  return requestClient.post(`${BASE}/workers`, data);
}

export async function updateWorkerApi(workerId, data) {
  return requestClient.put(`${BASE}/workers/${workerId}`, data);
}

export async function deleteWorkerApi(workerId) {
  return requestClient.delete(`${BASE}/workers/${workerId}`);
}

// =============================================================================
// EQUIPMENT
// =============================================================================

export async function getEquipmentListApi(params = {}) {
  return requestClient.get(`${BASE}/equipment`, { params });
}

export async function getEquipmentApi(equipmentId) {
  return requestClient.get(`${BASE}/equipment/${equipmentId}`);
}

export async function createEquipmentApi(data) {
  return requestClient.post(`${BASE}/equipment`, data);
}

export async function updateEquipmentApi(equipmentId, data) {
  return requestClient.put(`${BASE}/equipment/${equipmentId}`, data);
}

export async function deleteEquipmentApi(equipmentId) {
  return requestClient.delete(`${BASE}/equipment/${equipmentId}`);
}

export async function getEquipmentUtilizationApi(equipmentId) {
  return requestClient.get(`${BASE}/equipment/${equipmentId}/utilization`);
}

// =============================================================================
// TIMESHEETS
// =============================================================================

export async function getTimesheetsApi(params = {}) {
  return requestClient.get(`${BASE}/timesheets`, { params });
}

export async function getTimesheetApi(timesheetId) {
  return requestClient.get(`${BASE}/timesheets/${timesheetId}`);
}

export async function createTimesheetApi(data) {
  return requestClient.post(`${BASE}/timesheets`, data);
}

export async function updateTimesheetApi(timesheetId, data) {
  return requestClient.put(`${BASE}/timesheets/${timesheetId}`, data);
}

export async function deleteTimesheetApi(timesheetId) {
  return requestClient.delete(`${BASE}/timesheets/${timesheetId}`);
}

export async function submitTimesheetApi(timesheetId) {
  return requestClient.post(`${BASE}/timesheets/${timesheetId}/submit`);
}

export async function approveTimesheetApi(timesheetId) {
  return requestClient.post(`${BASE}/timesheets/${timesheetId}/approve`);
}

export async function rejectTimesheetApi(timesheetId) {
  return requestClient.post(`${BASE}/timesheets/${timesheetId}/reject`);
}

// =============================================================================
// EQUIPMENT ASSIGNMENTS
// =============================================================================

export async function getEquipmentAssignmentsApi(params = {}) {
  return requestClient.get(`${BASE}/equipment-assignments`, { params });
}

export async function getEquipmentAssignmentApi(assignmentId) {
  return requestClient.get(`${BASE}/equipment-assignments/${assignmentId}`);
}

export async function createEquipmentAssignmentApi(data) {
  return requestClient.post(`${BASE}/equipment-assignments`, data);
}

export async function updateEquipmentAssignmentApi(assignmentId, data) {
  return requestClient.put(`${BASE}/equipment-assignments/${assignmentId}`, data);
}

export async function deleteEquipmentAssignmentApi(assignmentId) {
  return requestClient.delete(`${BASE}/equipment-assignments/${assignmentId}`);
}
