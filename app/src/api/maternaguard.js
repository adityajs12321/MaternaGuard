import { apiClient } from "@/api/client";

export const maternaguardApi = {
  health: () => apiClient.get("/health"),

  loginDoctor: (username, password) =>
    apiClient.post("/auth/login", { username, password }),

  predict: (payload) => apiClient.post("/predict", payload),

  sync: (assessments) => apiClient.post("/sync", { assessments }),

  getDeviceAssessments: (deviceId, limit = 50) =>
    apiClient.get(`/assessments/device/${encodeURIComponent(deviceId)}?limit=${limit}`),

  getPatients: (token, params = {}) => {
    const query = new URLSearchParams();
    if (params.riskLevel) query.set("risk_level", params.riskLevel);
    if (params.limit) query.set("limit", String(params.limit));
    if (params.offset) query.set("offset", String(params.offset));
    const suffix = query.toString() ? `?${query.toString()}` : "";
    return apiClient.get(`/patients${suffix}`, { Authorization: `Bearer ${token}` });
  },

  getPatientAssessmentsByAbha: (token, abhaId) =>
    apiClient.get(`/patients/${encodeURIComponent(abhaId)}/assessments`, { Authorization: `Bearer ${token}` }),

  getPatientAssessmentsByDevice: (token, deviceId, limit = 50) =>
    apiClient.get(`/assessments/provider/device/${encodeURIComponent(deviceId)}?limit=${limit}`, {
      Authorization: `Bearer ${token}`,
    }),
};
