/**
 * AG CM RFI Module API Client
 */

import { requestClient } from '#/api/request';

const BASE = '/agcm_rfi';

// RFIs
export async function getRFIsApi(params = {}) {
  return requestClient.get(`${BASE}/rfis`, { params });
}

export async function getRFIApi(rfiId) {
  return requestClient.get(`${BASE}/rfis/${rfiId}`);
}

export async function createRFIApi(data) {
  return requestClient.post(`${BASE}/rfis`, data);
}

export async function updateRFIApi(rfiId, data) {
  return requestClient.put(`${BASE}/rfis/${rfiId}`, data);
}

export async function deleteRFIApi(rfiId) {
  return requestClient.delete(`${BASE}/rfis/${rfiId}`);
}

export async function closeRFIApi(rfiId) {
  return requestClient.post(`${BASE}/rfis/${rfiId}/close`);
}

export async function reopenRFIApi(rfiId) {
  return requestClient.post(`${BASE}/rfis/${rfiId}/reopen`);
}

// Responses
export async function createRFIResponseApi(rfiId, data) {
  return requestClient.post(`${BASE}/rfis/${rfiId}/responses`, data);
}

export async function updateRFIResponseApi(responseId, data) {
  return requestClient.put(`${BASE}/rfi-responses/${responseId}`, data);
}

// Labels
export async function getRFILabelsApi() {
  return requestClient.get(`${BASE}/rfi-labels`);
}

export async function createRFILabelApi(data) {
  return requestClient.post(`${BASE}/rfi-labels`, data);
}

export async function deleteRFILabelApi(labelId) {
  return requestClient.delete(`${BASE}/rfi-labels/${labelId}`);
}
