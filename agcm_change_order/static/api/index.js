/**
 * AG CM Change Order Module API Client
 */

import { requestClient } from '#/api/request';

const BASE = '/agcm_change_order';

// Change Orders
export async function getChangeOrdersApi(params = {}) {
  return requestClient.get(`${BASE}/change-orders`, { params });
}

export async function getChangeOrderApi(coId) {
  return requestClient.get(`${BASE}/change-orders/${coId}`);
}

export async function createChangeOrderApi(data) {
  return requestClient.post(`${BASE}/change-orders`, data);
}

export async function updateChangeOrderApi(coId, data) {
  return requestClient.put(`${BASE}/change-orders/${coId}`, data);
}

export async function deleteChangeOrderApi(coId) {
  return requestClient.delete(`${BASE}/change-orders/${coId}`);
}

export async function approveChangeOrderApi(coId) {
  return requestClient.post(`${BASE}/change-orders/${coId}/approve`);
}

export async function rejectChangeOrderApi(coId) {
  return requestClient.post(`${BASE}/change-orders/${coId}/reject`);
}

// Line Items
export async function createChangeOrderLineApi(changeOrderId, data) {
  return requestClient.post(`${BASE}/change-order-lines`, data, { params: { change_order_id: changeOrderId } });
}

export async function updateChangeOrderLineApi(lineId, data) {
  return requestClient.put(`${BASE}/change-order-lines/${lineId}`, data);
}

export async function deleteChangeOrderLineApi(lineId) {
  return requestClient.delete(`${BASE}/change-order-lines/${lineId}`);
}
