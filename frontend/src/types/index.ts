export interface Overview {
  period_days: number;
  total_cost: number;
  total_dbu: number;
  record_count: number;
  cost_change_pct: number;
  prev_period_cost: number;
  active_clusters: number;
  idle_clusters: number;
  open_recommendations: number;
  potential_savings: number;
}

export interface CostTrendPoint {
  period: string;
  cost: number;
  dbu: number;
}

export interface WorkspaceCost {
  workspace_id: string;
  cost: number;
  dbu: number;
  records: number;
}

export interface SkuCost {
  sku: string;
  cost: number;
  dbu: number;
}

export interface UserCost {
  user: string;
  cost: number;
  dbu: number;
}

export interface JobCost {
  job_id: string;
  job_name: string;
  cost: number;
  dbu: number;
}

export interface Team {
  id: string;
  name: string;
  department: string | null;
  cost_center: string | null;
  manager_email: string | null;
  member_count: number;
}

export interface Alert {
  id: string;
  name: string;
  alert_type: string;
  threshold_value: number;
  is_active: boolean;
}

export interface Recommendation {
  id: string;
  type: string;
  severity: string;
  title: string;
  description: string;
  estimated_savings: number | null;
  status: string;
  resource_type: string | null;
}

export interface ClusterInfo {
  cluster_id: string;
  cluster_name: string;
  state: string;
  num_workers: number;
  total_cost_usd: number;
  is_idle: boolean;
  idle_time_hours: number;
}
