/**
 * AGCM Reporting Module API Client
 *
 * JavaScript API functions for the Reporting module.
 * Loaded at runtime by vue3-sfc-loader.
 */

import { requestClient } from '#/api/request';

const BASE_URL = '/agcm_reporting';

// =============================================================================
// REPORT DEFINITIONS
// =============================================================================

export async function getReportsApi(params = {}) {
  return requestClient.get(`${BASE_URL}/reports`, { params });
}

export async function getReportApi(id) {
  return requestClient.get(`${BASE_URL}/reports/${id}`);
}

export async function createReportApi(data) {
  return requestClient.post(`${BASE_URL}/reports`, data);
}

export async function updateReportApi(id, data) {
  return requestClient.put(`${BASE_URL}/reports/${id}`, data);
}

export async function deleteReportApi(id) {
  return requestClient.delete(`${BASE_URL}/reports/${id}`);
}

export async function executeReportApi(id, filters = {}) {
  return requestClient.post(`${BASE_URL}/reports/${id}/execute`, filters);
}

export function exportReportUrl(id, format = 'csv') {
  const token = localStorage.getItem('accessToken') || '';
  const params = new URLSearchParams({ format });
  if (token) params.append('token', token);
  return `/api/v1${BASE_URL}/reports/${id}/export?${params.toString()}`;
}

// --- Schedules ---

export async function createScheduleApi(reportId, data) {
  return requestClient.post(`${BASE_URL}/reports/${reportId}/schedules`, data);
}

export async function updateScheduleApi(scheduleId, data) {
  return requestClient.put(`${BASE_URL}/schedules/${scheduleId}`, data);
}

export async function deleteScheduleApi(scheduleId) {
  return requestClient.delete(`${BASE_URL}/schedules/${scheduleId}`);
}

// =============================================================================
// DASHBOARD LAYOUTS
// =============================================================================

export async function getLayoutsApi(params = {}) {
  return requestClient.get(`${BASE_URL}/dashboard-layouts`, { params });
}

export async function getLayoutApi(id) {
  return requestClient.get(`${BASE_URL}/dashboard-layouts/${id}`);
}

export async function getDefaultLayoutApi(layoutType = 'executive') {
  return requestClient.get(`${BASE_URL}/dashboard-layouts/default`, {
    params: { layout_type: layoutType },
  });
}

export async function createLayoutApi(data) {
  return requestClient.post(`${BASE_URL}/dashboard-layouts`, data);
}

export async function updateLayoutApi(id, data) {
  return requestClient.put(`${BASE_URL}/dashboard-layouts/${id}`, data);
}

export async function deleteLayoutApi(id) {
  return requestClient.delete(`${BASE_URL}/dashboard-layouts/${id}`);
}

// --- Widgets ---

export async function createWidgetApi(layoutId, data) {
  return requestClient.post(`${BASE_URL}/dashboard-layouts/${layoutId}/widgets`, data);
}

export async function updateWidgetApi(widgetId, data) {
  return requestClient.put(`${BASE_URL}/widgets/${widgetId}`, data);
}

export async function deleteWidgetApi(widgetId) {
  return requestClient.delete(`${BASE_URL}/widgets/${widgetId}`);
}

// =============================================================================
// KPIs
// =============================================================================

export async function getPortfolioKpisApi() {
  return requestClient.get(`${BASE_URL}/kpis/portfolio`);
}

export async function getProjectKpisApi(projectId) {
  return requestClient.get(`${BASE_URL}/kpis/project/${projectId}`);
}

export async function getFinancialSummaryApi(projectId) {
  return requestClient.get(`${BASE_URL}/kpis/financial/${projectId}`);
}
