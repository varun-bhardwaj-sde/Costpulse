import { useEffect, useState } from "react";
import { api } from "../api/client";
import StatCard from "../components/StatCard";
import CostTrendChart from "../components/CostTrendChart";
import { CostBarChart, CostPieChart } from "../components/BreakdownChart";
import type { Overview, CostTrendPoint, WorkspaceCost, SkuCost } from "../types";

export default function Dashboard() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [trend, setTrend] = useState<CostTrendPoint[]>([]);
  const [byWorkspace, setByWorkspace] = useState<{ name: string; value: number }[]>([]);
  const [bySku, setBySku] = useState<{ name: string; value: number }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [ov, tr, ws, sk] = await Promise.all([
          api.getOverview(30),
          api.getCostTrend(30),
          api.getCostByWorkspace(30),
          api.getCostBySku(30),
        ]);
        setOverview(ov);
        setTrend(tr.data || []);
        setByWorkspace(
          (ws.data || []).map((w: WorkspaceCost) => ({
            name: w.workspace_id.slice(0, 16),
            value: w.cost,
          }))
        );
        setBySku(
          (sk.data || []).map((s: SkuCost) => ({
            name: s.sku.replace(/_/g, " "),
            value: s.cost,
          }))
        );
      } catch {
        // API not available — show empty state
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <div className="loading">Loading dashboard...</div>;

  return (
    <div>
      <div className="page-header">
        <h2>Cost Dashboard</h2>
        <p>Databricks cost overview for the last 30 days</p>
      </div>

      <div className="stat-grid">
        <StatCard
          label="Total Spend"
          value={overview ? `${overview.total_cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "0"}
          prefix="$"
          change={overview?.cost_change_pct}
        />
        <StatCard
          label="Total DBUs"
          value={overview ? overview.total_dbu.toLocaleString(undefined, { maximumFractionDigits: 0 }) : "0"}
        />
        <StatCard
          label="Active Clusters"
          value={overview ? `${overview.active_clusters}` : "0"}
        />
        <StatCard
          label="Idle Clusters"
          value={overview ? `${overview.idle_clusters}` : "0"}
        />
        <StatCard
          label="Open Recommendations"
          value={overview ? `${overview.open_recommendations}` : "0"}
        />
        <StatCard
          label="Potential Savings"
          value={overview ? overview.potential_savings.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 }) : "0"}
          prefix="$"
        />
      </div>

      <div className="chart-grid">
        <CostTrendChart data={trend} title="Daily Cost Trend" />
      </div>

      <div className="chart-grid">
        <CostBarChart data={byWorkspace} title="Cost by Workspace" />
        <CostPieChart data={bySku} title="Cost by SKU" />
      </div>
    </div>
  );
}
