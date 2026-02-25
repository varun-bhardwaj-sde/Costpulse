import { useEffect, useState } from "react";
import { api } from "../api/client";
import CostTrendChart from "../components/CostTrendChart";
import { CostBarChart } from "../components/BreakdownChart";
import type { UserCost, JobCost } from "../types";

export default function CostsPage() {
  const [trend, setTrend] = useState<any[]>([]);
  const [byUser, setByUser] = useState<{ name: string; value: number }[]>([]);
  const [byJob, setByJob] = useState<{ name: string; value: number }[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [days, setDays] = useState(30);

  useEffect(() => {
    async function load() {
      try {
        const [tr, users, jobs, sum] = await Promise.all([
          api.getCostTrend(days),
          api.getCostByUser(days),
          api.getCostByJob(days),
          api.getCostSummary(days),
        ]);
        setTrend(tr.data || []);
        setByUser(
          (users.data || []).map((u: UserCost) => ({
            name: u.user?.split("@")[0] || "unknown",
            value: u.cost,
          }))
        );
        setByJob(
          (jobs.data || []).map((j: JobCost) => ({
            name: j.job_name || `Job ${j.job_id}`,
            value: j.cost,
          }))
        );
        setSummary(sum);
      } catch {
        // API not available
      }
    }
    load();
  }, [days]);

  return (
    <div>
      <div className="page-header">
        <h2>Cost Explorer</h2>
        <p>Deep-dive into Databricks cost data</p>
      </div>

      <div style={{ marginBottom: "1rem", display: "flex", gap: "0.5rem" }}>
        {[7, 14, 30, 60, 90].map((d) => (
          <button
            key={d}
            className={`btn ${d === days ? "btn-primary" : ""}`}
            onClick={() => setDays(d)}
          >
            {d}d
          </button>
        ))}
      </div>

      {summary && (
        <div className="stat-grid">
          <div className="stat-card">
            <div className="label">Total Cost</div>
            <div className="value">${summary.total_cost?.toLocaleString()}</div>
          </div>
          <div className="stat-card">
            <div className="label">Avg Daily Cost</div>
            <div className="value">${summary.avg_daily_cost?.toLocaleString()}</div>
          </div>
          <div className="stat-card">
            <div className="label">Total DBUs</div>
            <div className="value">{summary.total_dbu?.toLocaleString()}</div>
          </div>
          <div className="stat-card">
            <div className="label">Records</div>
            <div className="value">{summary.total_records?.toLocaleString()}</div>
          </div>
        </div>
      )}

      <div className="chart-grid">
        <CostTrendChart data={trend} title={`Cost Trend (${days} days)`} />
      </div>

      <div className="chart-grid">
        <CostBarChart data={byUser} title="Top Users by Cost" />
        <CostBarChart data={byJob} title="Top Jobs by Cost" />
      </div>
    </div>
  );
}
