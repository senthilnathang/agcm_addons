/**
 * AG CM Safety Module API Client
 */

import { requestClient } from '#/api/request';

const BASE = '/agcm_safety';

// =============================================================================
// CHECKLIST TEMPLATES
// =============================================================================

export async function getChecklistsApi(params = {}) {
  return requestClient.get(`${BASE}/checklists`, { params });
}

export async function getChecklistApi(templateId) {
  return requestClient.get(`${BASE}/checklists/${templateId}`);
}

export async function createChecklistApi(data) {
  return requestClient.post(`${BASE}/checklists`, data);
}

export async function updateChecklistApi(templateId, data) {
  return requestClient.put(`${BASE}/checklists/${templateId}`, data);
}

export async function deleteChecklistApi(templateId) {
  return requestClient.delete(`${BASE}/checklists/${templateId}`);
}

// =============================================================================
// INSPECTIONS
// =============================================================================

export async function getInspectionsApi(params = {}) {
  return requestClient.get(`${BASE}/inspections`, { params });
}

export async function getInspectionApi(inspectionId) {
  return requestClient.get(`${BASE}/inspections/${inspectionId}`);
}

export async function createInspectionApi(data) {
  return requestClient.post(`${BASE}/inspections`, data);
}

export async function updateInspectionApi(inspectionId, data) {
  return requestClient.put(`${BASE}/inspections/${inspectionId}`, data);
}

export async function startInspectionApi(inspectionId) {
  return requestClient.post(`${BASE}/inspections/${inspectionId}/start`);
}

export async function completeInspectionApi(inspectionId, data) {
  return requestClient.post(`${BASE}/inspections/${inspectionId}/complete`, data);
}

export async function deleteInspectionApi(inspectionId) {
  return requestClient.delete(`${BASE}/inspections/${inspectionId}`);
}

// =============================================================================
// PUNCH LIST
// =============================================================================

export async function getPunchListApi(params = {}) {
  return requestClient.get(`${BASE}/punch-list`, { params });
}

export async function getPunchItemApi(itemId) {
  return requestClient.get(`${BASE}/punch-list/${itemId}`);
}

export async function createPunchItemApi(data) {
  return requestClient.post(`${BASE}/punch-list`, data);
}

export async function updatePunchItemApi(itemId, data) {
  return requestClient.put(`${BASE}/punch-list/${itemId}`, data);
}

export async function assignPunchItemApi(itemId, data) {
  return requestClient.post(`${BASE}/punch-list/${itemId}/assign`, data);
}

export async function completePunchItemApi(itemId) {
  return requestClient.post(`${BASE}/punch-list/${itemId}/complete`);
}

export async function verifyPunchItemApi(itemId) {
  return requestClient.post(`${BASE}/punch-list/${itemId}/verify`);
}

export async function deletePunchItemApi(itemId) {
  return requestClient.delete(`${BASE}/punch-list/${itemId}`);
}

// =============================================================================
// INCIDENTS
// =============================================================================

export async function getIncidentsApi(params = {}) {
  return requestClient.get(`${BASE}/incidents`, { params });
}

export async function getIncidentApi(incidentId) {
  return requestClient.get(`${BASE}/incidents/${incidentId}`);
}

export async function createIncidentApi(data) {
  return requestClient.post(`${BASE}/incidents`, data);
}

export async function updateIncidentApi(incidentId, data) {
  return requestClient.put(`${BASE}/incidents/${incidentId}`, data);
}

export async function investigateIncidentApi(incidentId, data) {
  return requestClient.post(`${BASE}/incidents/${incidentId}/investigate`, data);
}

export async function closeIncidentApi(incidentId, data) {
  return requestClient.post(`${BASE}/incidents/${incidentId}/close`, data);
}

export async function deleteIncidentApi(incidentId) {
  return requestClient.delete(`${BASE}/incidents/${incidentId}`);
}
