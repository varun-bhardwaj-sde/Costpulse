/**
 * API client for CostPulse backend.
 */

const API_BASE = "/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Dashboard
  getOverview: (days = 30) => request<any>(`/dashboard/overview?days=${days}`),
  getCostTrend: (days = 30, granularity = "daily") =>
    request<any>(`/dashboard/cost-trend?days=${days}&granularity=${granularity}`),
  getCostByWorkspace: (days = 30) => request<any>(`/dashboard/cost-by-workspace?days=${days}`),
  getCostBySku: (days = 30) => request<any>(`/dashboard/cost-by-sku?days=${days}`),
  getCostByUser: (days = 30) => request<any>(`/dashboard/cost-by-user?days=${days}`),
  getCostByJob: (days = 30) => request<any>(`/dashboard/cost-by-job?days=${days}`),

  // Costs
  getCosts: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<any>(`/costs/${qs}`);
  },
  getCostSummary: (days = 30) => request<any>(`/costs/summary?days=${days}`),

  // Workspaces
  getWorkspaces: () => request<any>("/workspaces/"),
  createWorkspace: (data: any) =>
    request<any>("/workspaces/", { method: "POST", body: JSON.stringify(data) }),

  // Teams
  getTeams: () => request<any>("/teams/"),
  createTeam: (data: any) =>
    request<any>("/teams/", { method: "POST", body: JSON.stringify(data) }),
  getTeam: (id: string) => request<any>(`/teams/${id}`),

  // Allocations
  getAllocations: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<any>(`/allocations/${qs}`);
  },
  runAllocation: (periodStart: string, periodEnd: string) =>
    request<any>(
      `/allocations/run?period_start=${periodStart}&period_end=${periodEnd}`,
      { method: "POST" }
    ),

  // Alerts
  getAlerts: () => request<any>("/alerts/"),
  createAlert: (data: any) =>
    request<any>("/alerts/", { method: "POST", body: JSON.stringify(data) }),
  checkAlerts: () => request<any>("/alerts/check", { method: "POST" }),
  getAlertHistory: () => request<any>("/alerts/history"),

  // Reports
  getReports: () => request<any>("/reports/"),
  generateReport: (data: any) =>
    request<any>("/reports/generate", { method: "POST", body: JSON.stringify(data) }),

  // Recommendations
  getRecommendations: (status = "open") =>
    request<any>(`/recommendations/?status=${status}`),
  generateRecommendations: () =>
    request<any>("/recommendations/generate", { method: "POST" }),
  updateRecommendationStatus: (id: string, status: string) =>
    request<any>(`/recommendations/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),

  // Forecasts
  getForecastSummary: () => request<any>("/forecasts/summary"),
  generateForecast: (days = 30) =>
    request<any>(`/forecasts/generate?horizon_days=${days}`, { method: "POST" }),

  // Tags
  getTagCompliance: () => request<any>("/tags/compliance"),

  // Clusters
  getClusters: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<any>(`/clusters/${qs}`);
  },
  getClusterSummary: () => request<any>("/clusters/summary"),
};
