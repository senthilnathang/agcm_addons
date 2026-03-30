/**
 * AG CM Document Module API Client
 */

import { requestClient } from '#/api/request';

const BASE = '/agcm_document';

// Folders
export async function getFolderTreeApi(projectId) {
  return requestClient.get(`${BASE}/folders`, { params: { project_id: projectId } });
}

export async function createFolderApi(data) {
  return requestClient.post(`${BASE}/folders`, data);
}

export async function updateFolderApi(folderId, data) {
  return requestClient.put(`${BASE}/folders/${folderId}`, data);
}

export async function deleteFolderApi(folderId) {
  return requestClient.delete(`${BASE}/folders/${folderId}`);
}

// Documents
export async function getDocumentsApi(params = {}) {
  return requestClient.get(`${BASE}/documents`, { params });
}

export async function getDocumentApi(docId) {
  return requestClient.get(`${BASE}/documents/${docId}`);
}

export async function uploadDocumentApi(formData) {
  return requestClient.post(`${BASE}/documents/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}

export async function updateDocumentApi(docId, data) {
  return requestClient.put(`${BASE}/documents/${docId}`, data);
}

export async function deleteDocumentApi(docId) {
  return requestClient.delete(`${BASE}/documents/${docId}`);
}
