/**
 * AG CM Estimating Module API Client
 */
import { requestClient } from '#/api/request';

const BASE = '/agcm_estimate';

// Cost Catalogs
export const getCatalogsApi = (params) => requestClient.get(`${BASE}/catalogs`, { params });
export const createCatalogApi = (data) => requestClient.post(`${BASE}/catalogs`, data);
export const updateCatalogApi = (id, data) => requestClient.put(`${BASE}/catalogs/${id}`, data);
export const deleteCatalogApi = (id) => requestClient.delete(`${BASE}/catalogs/${id}`);

// Cost Items
export const getCostItemsApi = (params) => requestClient.get(`${BASE}/cost-items`, { params });
export const createCostItemApi = (data) => requestClient.post(`${BASE}/cost-items`, data);
export const updateCostItemApi = (id, data) => requestClient.put(`${BASE}/cost-items/${id}`, data);
export const deleteCostItemApi = (id) => requestClient.delete(`${BASE}/cost-items/${id}`);

// Assemblies
export const getAssembliesApi = (params) => requestClient.get(`${BASE}/assemblies`, { params });
export const getAssemblyApi = (id) => requestClient.get(`${BASE}/assemblies/${id}`);
export const createAssemblyApi = (data) => requestClient.post(`${BASE}/assemblies`, data);
export const updateAssemblyApi = (id, data) => requestClient.put(`${BASE}/assemblies/${id}`, data);
export const deleteAssemblyApi = (id) => requestClient.delete(`${BASE}/assemblies/${id}`);
export const createAssemblyItemApi = (data) => requestClient.post(`${BASE}/assembly-items`, data);
export const updateAssemblyItemApi = (id, data) => requestClient.put(`${BASE}/assembly-items/${id}`, data);
export const deleteAssemblyItemApi = (id) => requestClient.delete(`${BASE}/assembly-items/${id}`);

// Estimates
export const getEstimatesApi = (params) => requestClient.get(`${BASE}/estimates`, { params });
export const getEstimateApi = (id) => requestClient.get(`${BASE}/estimates/${id}`);
export const createEstimateApi = (data) => requestClient.post(`${BASE}/estimates`, data);
export const updateEstimateApi = (id, data) => requestClient.put(`${BASE}/estimates/${id}`, data);
export const deleteEstimateApi = (id) => requestClient.delete(`${BASE}/estimates/${id}`);
export const recalculateEstimateApi = (id) => requestClient.post(`${BASE}/estimates/${id}/recalculate`);
export const createEstimateVersionApi = (id) => requestClient.post(`${BASE}/estimates/${id}/create-version`);
export const sendToBudgetApi = (id) => requestClient.post(`${BASE}/estimates/${id}/send-to-budget`);
export const approveEstimateApi = (id) => requestClient.post(`${BASE}/estimates/${id}/approve`);
export const addAssemblyToEstimateApi = (id, data) => requestClient.post(`${BASE}/estimates/${id}/add-assembly`, data);

// Estimate Groups
export const createEstimateGroupApi = (data) => requestClient.post(`${BASE}/estimate-groups`, data);
export const updateEstimateGroupApi = (id, data) => requestClient.put(`${BASE}/estimate-groups/${id}`, data);
export const deleteEstimateGroupApi = (id) => requestClient.delete(`${BASE}/estimate-groups/${id}`);

// Estimate Line Items
export const createLineItemApi = (data) => requestClient.post(`${BASE}/estimate-line-items`, data);
export const updateLineItemApi = (id, data) => requestClient.put(`${BASE}/estimate-line-items/${id}`, data);
export const deleteLineItemApi = (id) => requestClient.delete(`${BASE}/estimate-line-items/${id}`);

// Estimate Markups
export const createMarkupApi = (data) => requestClient.post(`${BASE}/estimate-markups`, data);
export const updateMarkupApi = (id, data) => requestClient.put(`${BASE}/estimate-markups/${id}`, data);
export const deleteMarkupApi = (id) => requestClient.delete(`${BASE}/estimate-markups/${id}`);

// Proposals
export const getProposalsApi = (params) => requestClient.get(`${BASE}/proposals`, { params });
export const getProposalApi = (id) => requestClient.get(`${BASE}/proposals/${id}`);
export const createProposalApi = (data) => requestClient.post(`${BASE}/proposals`, data);
export const updateProposalApi = (id, data) => requestClient.put(`${BASE}/proposals/${id}`, data);
export const deleteProposalApi = (id) => requestClient.delete(`${BASE}/proposals/${id}`);
export const sendProposalApi = (id) => requestClient.post(`${BASE}/proposals/${id}/send`);
export const approveProposalApi = (id) => requestClient.post(`${BASE}/proposals/${id}/approve`);
export const rejectProposalApi = (id) => requestClient.post(`${BASE}/proposals/${id}/reject`);
export const getProposalPdfApi = (id) => requestClient.get(`${BASE}/proposals/${id}/pdf`, { responseType: 'blob' });

// Takeoff Sheets
export const getTakeoffSheetsApi = (params) => requestClient.get(`${BASE}/takeoff-sheets`, { params });
export const createTakeoffSheetApi = (data) => requestClient.post(`${BASE}/takeoff-sheets`, data);
export const updateTakeoffSheetApi = (id, data) => requestClient.put(`${BASE}/takeoff-sheets/${id}`, data);
export const deleteTakeoffSheetApi = (id) => requestClient.delete(`${BASE}/takeoff-sheets/${id}`);

// Measurements
export const getMeasurementsApi = (params) => requestClient.get(`${BASE}/measurements`, { params });
export const createMeasurementApi = (data) => requestClient.post(`${BASE}/measurements`, data);
export const updateMeasurementApi = (id, data) => requestClient.put(`${BASE}/measurements/${id}`, data);
export const deleteMeasurementApi = (id) => requestClient.delete(`${BASE}/measurements/${id}`);
export const linkMeasurementApi = (id, data) => requestClient.post(`${BASE}/measurements/${id}/link-to-line`, data);
