/**
 * AG CM Procurement Module API Client
 */

import { requestClient } from '#/api/request';

const BASE = '/agcm_procurement';

// =============================================================================
// PURCHASE ORDERS
// =============================================================================

export async function getPurchaseOrdersApi(params = {}) {
  return requestClient.get(`${BASE}/purchase-orders`, { params });
}

export async function getPurchaseOrderApi(id) {
  return requestClient.get(`${BASE}/purchase-orders/${id}`);
}

export async function createPurchaseOrderApi(data) {
  return requestClient.post(`${BASE}/purchase-orders`, data);
}

export async function updatePurchaseOrderApi(id, data) {
  return requestClient.put(`${BASE}/purchase-orders/${id}`, data);
}

export async function deletePurchaseOrderApi(id) {
  return requestClient.delete(`${BASE}/purchase-orders/${id}`);
}

export async function approvePurchaseOrderApi(id) {
  return requestClient.post(`${BASE}/purchase-orders/${id}/approve`);
}

export async function receiveDeliveryApi(id, data) {
  return requestClient.post(`${BASE}/purchase-orders/${id}/receive`, data);
}

export async function createPoFromEstimateApi(data) {
  return requestClient.post(`${BASE}/purchase-orders/from-estimate`, data);
}

// PO Lines
export async function createPoLineApi(poId, data) {
  return requestClient.post(`${BASE}/po-lines`, data, { params: { po_id: poId } });
}

export async function updatePoLineApi(lineId, data) {
  return requestClient.put(`${BASE}/po-lines/${lineId}`, data);
}

export async function deletePoLineApi(lineId) {
  return requestClient.delete(`${BASE}/po-lines/${lineId}`);
}

// =============================================================================
// SUBCONTRACTS
// =============================================================================

export async function getSubcontractsApi(params = {}) {
  return requestClient.get(`${BASE}/subcontracts`, { params });
}

export async function getSubcontractApi(id) {
  return requestClient.get(`${BASE}/subcontracts/${id}`);
}

export async function createSubcontractApi(data) {
  return requestClient.post(`${BASE}/subcontracts`, data);
}

export async function updateSubcontractApi(id, data) {
  return requestClient.put(`${BASE}/subcontracts/${id}`, data);
}

export async function deleteSubcontractApi(id) {
  return requestClient.delete(`${BASE}/subcontracts/${id}`);
}

export async function approveSubcontractApi(id) {
  return requestClient.post(`${BASE}/subcontracts/${id}/approve`);
}

export async function updateBillingApi(id, data) {
  return requestClient.post(`${BASE}/subcontracts/${id}/update-billing`, data);
}

// SOV Lines
export async function createSovLineApi(subcontractId, data) {
  return requestClient.post(`${BASE}/sov-lines`, data, { params: { subcontract_id: subcontractId } });
}

export async function updateSovLineApi(lineId, data) {
  return requestClient.put(`${BASE}/sov-lines/${lineId}`, data);
}

export async function deleteSovLineApi(lineId) {
  return requestClient.delete(`${BASE}/sov-lines/${lineId}`);
}

// Compliance Docs
export async function createComplianceDocApi(data) {
  return requestClient.post(`${BASE}/compliance-docs`, data);
}

export async function updateComplianceDocApi(docId, data) {
  return requestClient.put(`${BASE}/compliance-docs/${docId}`, data);
}

export async function deleteComplianceDocApi(docId) {
  return requestClient.delete(`${BASE}/compliance-docs/${docId}`);
}

// =============================================================================
// VENDOR BILLS
// =============================================================================

export async function getVendorBillsApi(params = {}) {
  return requestClient.get(`${BASE}/vendor-bills`, { params });
}

export async function getVendorBillApi(id) {
  return requestClient.get(`${BASE}/vendor-bills/${id}`);
}

export async function createVendorBillApi(data) {
  return requestClient.post(`${BASE}/vendor-bills`, data);
}

export async function updateVendorBillApi(id, data) {
  return requestClient.put(`${BASE}/vendor-bills/${id}`, data);
}

export async function deleteVendorBillApi(id) {
  return requestClient.delete(`${BASE}/vendor-bills/${id}`);
}

export async function approveVendorBillApi(id) {
  return requestClient.post(`${BASE}/vendor-bills/${id}/approve`);
}

export async function recordBillPaymentApi(id, data) {
  return requestClient.post(`${BASE}/vendor-bills/${id}/record-payment`, data);
}

export async function checkDuplicateBillApi(id) {
  return requestClient.post(`${BASE}/vendor-bills/${id}/check-duplicate`);
}

export async function autoMatchPoApi(id) {
  return requestClient.post(`${BASE}/vendor-bills/${id}/auto-match-po`);
}

// Bill Lines
export async function createBillLineApi(billId, data) {
  return requestClient.post(`${BASE}/bill-lines`, data, { params: { bill_id: billId } });
}

export async function updateBillLineApi(lineId, data) {
  return requestClient.put(`${BASE}/bill-lines/${lineId}`, data);
}

export async function deleteBillLineApi(lineId) {
  return requestClient.delete(`${BASE}/bill-lines/${lineId}`);
}
