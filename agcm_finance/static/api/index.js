/**
 * AG CM Finance Module API Client
 */

import { requestClient } from '#/api/request';

const BASE = '/agcm_finance';

// =============================================================================
// COST CODES
// =============================================================================

export async function getCostCodesApi(params = {}) {
  return requestClient.get(`${BASE}/cost-codes`, { params });
}

export async function createCostCodeApi(data) {
  return requestClient.post(`${BASE}/cost-codes`, data);
}

export async function updateCostCodeApi(id, data) {
  return requestClient.put(`${BASE}/cost-codes/${id}`, data);
}

export async function deleteCostCodeApi(id) {
  return requestClient.delete(`${BASE}/cost-codes/${id}`);
}

// =============================================================================
// BUDGETS
// =============================================================================

export async function getBudgetsApi(params = {}) {
  return requestClient.get(`${BASE}/budgets`, { params });
}

export async function getBudgetSummaryApi(params = {}) {
  return requestClient.get(`${BASE}/budget/summary`, { params });
}

export async function createBudgetApi(data) {
  return requestClient.post(`${BASE}/budgets`, data);
}

export async function updateBudgetApi(id, data) {
  return requestClient.put(`${BASE}/budgets/${id}`, data);
}

export async function deleteBudgetApi(id) {
  return requestClient.delete(`${BASE}/budgets/${id}`);
}

// =============================================================================
// EXPENSES
// =============================================================================

export async function getExpensesApi(params = {}) {
  return requestClient.get(`${BASE}/expenses`, { params });
}

export async function getExpenseApi(id) {
  return requestClient.get(`${BASE}/expenses/${id}`);
}

export async function createExpenseApi(data) {
  return requestClient.post(`${BASE}/expenses`, data);
}

export async function updateExpenseApi(id, data) {
  return requestClient.put(`${BASE}/expenses/${id}`, data);
}

export async function deleteExpenseApi(id) {
  return requestClient.delete(`${BASE}/expenses/${id}`);
}

// Expense Lines
export async function createExpenseLineApi(expenseId, data) {
  return requestClient.post(`${BASE}/expense-lines`, data, { params: { expense_id: expenseId } });
}

export async function updateExpenseLineApi(lineId, data) {
  return requestClient.put(`${BASE}/expense-lines/${lineId}`, data);
}

export async function deleteExpenseLineApi(lineId) {
  return requestClient.delete(`${BASE}/expense-lines/${lineId}`);
}

// =============================================================================
// INVOICES
// =============================================================================

export async function getInvoicesApi(params = {}) {
  return requestClient.get(`${BASE}/invoices`, { params });
}

export async function getInvoiceApi(id) {
  return requestClient.get(`${BASE}/invoices/${id}`);
}

export async function createInvoiceApi(data) {
  return requestClient.post(`${BASE}/invoices`, data);
}

export async function updateInvoiceApi(id, data) {
  return requestClient.put(`${BASE}/invoices/${id}`, data);
}

export async function deleteInvoiceApi(id) {
  return requestClient.delete(`${BASE}/invoices/${id}`);
}

export async function recordInvoicePaymentApi(id, data) {
  return requestClient.post(`${BASE}/invoices/${id}/record-payment`, data);
}

// =============================================================================
// BILLS
// =============================================================================

export async function getBillsApi(params = {}) {
  return requestClient.get(`${BASE}/bills`, { params });
}

export async function getBillApi(id) {
  return requestClient.get(`${BASE}/bills/${id}`);
}

export async function createBillApi(data) {
  return requestClient.post(`${BASE}/bills`, data);
}

export async function updateBillApi(id, data) {
  return requestClient.put(`${BASE}/bills/${id}`, data);
}

export async function deleteBillApi(id) {
  return requestClient.delete(`${BASE}/bills/${id}`);
}

export async function recordBillPaymentApi(id, data) {
  return requestClient.post(`${BASE}/bills/${id}/record-payment`, data);
}
