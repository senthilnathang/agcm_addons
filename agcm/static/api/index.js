/**
 * AG CM Module API Client
 *
 * JavaScript API functions for the Construction Management module.
 * Loaded at runtime by vue3-sfc-loader.
 */

import { requestClient } from '#/api/request';

const BASE_URL = '/agcm';

// =============================================================================
// PERIODIC PROJECT REPORT
// =============================================================================

export function periodicReportUrl(projectId, dateFrom, dateTo) {
  const token = localStorage.getItem('accessToken') || '';
  const params = new URLSearchParams({ project_id: projectId });
  if (dateFrom) params.append('date_from', dateFrom);
  if (dateTo) params.append('date_to', dateTo);
  if (token) params.append('token', token);
  return `/api/v1${BASE_URL}/reports/periodic?${params.toString()}`;
}

// =============================================================================
// DASHBOARDS
// =============================================================================

export async function getDashboardOverviewApi(params = {}) {
  return requestClient.get(`${BASE_URL}/dashboard/overview`, { params });
}

export async function getDashboardProjectApi(projectId, params = {}) {
  return requestClient.get(`${BASE_URL}/dashboard/project/${projectId}`, { params });
}

export async function getDashboardDailylogApi(logId) {
  return requestClient.get(`${BASE_URL}/dashboard/dailylog/${logId}`);
}

// =============================================================================
// PROJECTS
// =============================================================================

export async function getProjectsApi(params = {}) {
  return requestClient.get(`${BASE_URL}/projects`, { params });
}

export async function getProjectApi(projectId) {
  return requestClient.get(`${BASE_URL}/projects/${projectId}`);
}

export async function createProjectApi(data) {
  return requestClient.post(`${BASE_URL}/projects`, data);
}

export async function updateProjectApi(projectId, data) {
  return requestClient.put(`${BASE_URL}/projects/${projectId}`, data);
}

export async function deleteProjectApi(projectId) {
  return requestClient.delete(`${BASE_URL}/projects/${projectId}`);
}

// =============================================================================
// DAILY ACTIVITY LOGS
// =============================================================================

export async function getDailyLogsApi(params = {}) {
  return requestClient.get(`${BASE_URL}/daily-logs`, { params });
}

export async function getDailyLogApi(logId) {
  return requestClient.get(`${BASE_URL}/daily-logs/${logId}`);
}

export async function createDailyLogApi(data) {
  return requestClient.post(`${BASE_URL}/daily-logs`, data);
}

export async function updateDailyLogApi(logId, data) {
  return requestClient.put(`${BASE_URL}/daily-logs/${logId}`, data);
}

export async function deleteDailyLogApi(logId) {
  return requestClient.delete(`${BASE_URL}/daily-logs/${logId}`);
}

export async function makeLogApi(data) {
  return requestClient.post(`${BASE_URL}/daily-logs/makelog`, data);
}

export async function exportDailyLogPdfApi(logId) {
  return requestClient.get(`${BASE_URL}/daily-logs/${logId}/report/pdf`, {
    responseType: 'blob',
  });
}

export function exportDailyLogHtmlUrl(logId) {
  // Token is stored as plain JWT at localStorage key 'accessToken'
  const token = localStorage.getItem('accessToken') || '';
  const qs = token ? `?token=${encodeURIComponent(token)}` : '';
  return `/api/v1${BASE_URL}/daily-logs/${logId}/report/html${qs}`;
}

// =============================================================================
// WEATHER (forecast + manual)
// =============================================================================

export async function fetchWeatherForecastApi(params = {}) {
  return requestClient.post(`${BASE_URL}/weather/fetch-forecast`, null, { params });
}

export async function getWeatherForecastApi(params = {}) {
  return requestClient.get(`${BASE_URL}/weather/forecast`, { params });
}

export async function getManualWeatherApi(params = {}) {
  return requestClient.get(`${BASE_URL}/weather/manual`, { params });
}

export async function createManualWeatherApi(dailylogId, data) {
  return requestClient.post(`${BASE_URL}/weather/manual?dailylog_id=${dailylogId}`, data);
}

// =============================================================================
// MANPOWER
// =============================================================================

export async function getManpowerApi(params = {}) {
  return requestClient.get(`${BASE_URL}/manpower`, { params });
}

export async function createManpowerApi(data) {
  return requestClient.post(`${BASE_URL}/manpower`, data);
}

export async function updateManpowerApi(id, data) {
  return requestClient.put(`${BASE_URL}/manpower/${id}`, data);
}

export async function deleteManpowerApi(id) {
  return requestClient.delete(`${BASE_URL}/manpower/${id}`);
}

// =============================================================================
// NOTES / OBSERVATIONS
// =============================================================================

export async function getNotesApi(params = {}) {
  return requestClient.get(`${BASE_URL}/notes`, { params });
}

export async function createNotesApi(data) {
  return requestClient.post(`${BASE_URL}/notes`, data);
}

export async function updateNotesApi(id, data) {
  return requestClient.put(`${BASE_URL}/notes/${id}`, data);
}

export async function deleteNotesApi(id) {
  return requestClient.delete(`${BASE_URL}/notes/${id}`);
}

// =============================================================================
// INSPECTIONS
// =============================================================================

export async function getInspectionsApi(params = {}) {
  return requestClient.get(`${BASE_URL}/inspections`, { params });
}

export async function createInspectionApi(data) {
  return requestClient.post(`${BASE_URL}/inspections`, data);
}

export async function updateInspectionApi(id, data) {
  return requestClient.put(`${BASE_URL}/inspections/${id}`, data);
}

export async function deleteInspectionApi(id) {
  return requestClient.delete(`${BASE_URL}/inspections/${id}`);
}

// =============================================================================
// ACCIDENTS
// =============================================================================

export async function getAccidentsApi(params = {}) {
  return requestClient.get(`${BASE_URL}/accidents`, { params });
}

export async function createAccidentApi(data) {
  return requestClient.post(`${BASE_URL}/accidents`, data);
}

export async function updateAccidentApi(id, data) {
  return requestClient.put(`${BASE_URL}/accidents/${id}`, data);
}

export async function deleteAccidentApi(id) {
  return requestClient.delete(`${BASE_URL}/accidents/${id}`);
}

// =============================================================================
// VISITORS
// =============================================================================

export async function getVisitorsApi(params = {}) {
  return requestClient.get(`${BASE_URL}/visitors`, { params });
}

export async function createVisitorApi(data) {
  return requestClient.post(`${BASE_URL}/visitors`, data);
}

export async function updateVisitorApi(id, data) {
  return requestClient.put(`${BASE_URL}/visitors/${id}`, data);
}

export async function deleteVisitorApi(id) {
  return requestClient.delete(`${BASE_URL}/visitors/${id}`);
}

// =============================================================================
// SAFETY VIOLATIONS / OBSERVATIONS
// =============================================================================

export async function getSafetyViolationsApi(params = {}) {
  return requestClient.get(`${BASE_URL}/safety-violations`, { params });
}

export async function createSafetyViolationApi(data) {
  return requestClient.post(`${BASE_URL}/safety-violations`, data);
}

export async function updateSafetyViolationApi(id, data) {
  return requestClient.put(`${BASE_URL}/safety-violations/${id}`, data);
}

export async function deleteSafetyViolationApi(id) {
  return requestClient.delete(`${BASE_URL}/safety-violations/${id}`);
}

// =============================================================================
// DELAYS
// =============================================================================

export async function getDelaysApi(params = {}) {
  return requestClient.get(`${BASE_URL}/delays`, { params });
}

export async function createDelayApi(data) {
  return requestClient.post(`${BASE_URL}/delays`, data);
}

export async function updateDelayApi(id, data) {
  return requestClient.put(`${BASE_URL}/delays/${id}`, data);
}

export async function deleteDelayApi(id) {
  return requestClient.delete(`${BASE_URL}/delays/${id}`);
}

// =============================================================================
// DEFICIENCIES
// =============================================================================

export async function getDeficienciesApi(params = {}) {
  return requestClient.get(`${BASE_URL}/deficiencies`, { params });
}

export async function createDeficiencyApi(data) {
  return requestClient.post(`${BASE_URL}/deficiencies`, data);
}

export async function updateDeficiencyApi(id, data) {
  return requestClient.put(`${BASE_URL}/deficiencies/${id}`, data);
}

export async function deleteDeficiencyApi(id) {
  return requestClient.delete(`${BASE_URL}/deficiencies/${id}`);
}

// =============================================================================
// PHOTOS
// =============================================================================

export async function getPhotosApi(params = {}) {
  return requestClient.get(`${BASE_URL}/photos`, { params });
}

export async function uploadPhotoApi(dailylogId, file, { name, location, album } = {}) {
  const formData = new FormData();
  formData.append('file', file);
  const params = new URLSearchParams({ dailylog_id: dailylogId });
  if (name) params.append('name', name);
  if (location) params.append('location', location);
  if (album) params.append('album', album);
  return requestClient.post(`${BASE_URL}/photos/upload?${params.toString()}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}

export async function deletePhotoApi(id) {
  return requestClient.delete(`${BASE_URL}/photos/${id}`);
}
