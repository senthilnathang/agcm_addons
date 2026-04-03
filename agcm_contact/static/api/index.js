import { requestClient } from '#/api/request';

const BASE = '/agcm_contact';

export function listVendors(params) {
  return requestClient.get(`${BASE}/vendors`, { params });
}

export function searchVendors(query, limit = 10) {
  return requestClient.get(`${BASE}/vendors/search`, { params: { q: query, limit } });
}

export function getVendor(id) {
  return requestClient.get(`${BASE}/vendors/${id}`);
}

export function createVendor(data) {
  return requestClient.post(`${BASE}/vendors`, data);
}

export function updateVendor(id, data) {
  return requestClient.put(`${BASE}/vendors/${id}`, data);
}

export function deleteVendor(id) {
  return requestClient.delete(`${BASE}/vendors/${id}`);
}
