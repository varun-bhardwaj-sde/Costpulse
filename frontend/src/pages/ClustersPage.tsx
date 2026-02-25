import { useEffect, useState } from "react";
import { api } from "../api/client";
import StatCard from "../components/StatCard";

export default function ClustersPage() {
  const [clusters, setClusters] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);

  useEffect(() => {
    async function load() {
      try {
        const [cl, sum] = await Promise.all([
          api.getClusters(),
          api.getClusterSummary(),
        ]);
        setClusters(cl.data || []);
        setSummary(sum);
      } catch {
        // API not available
      }
    }
    load();
  }, []);

  const stateColor = (state: string) => {
    if (state === "RUNNING") return "badge-green";
    if (state === "TERMINATED") return "badge-red";
    return "badge-yellow";
  };

  return (
    <div>
      <div className="page-header">
        <h2>Clusters</h2>
        <p>Monitor and optimize Databricks compute resources</p>
      </div>

      {summary && (
        <div className="stat-grid">
          <StatCard label="Total Clusters" value={String(summary.total_clusters)} />
          <StatCard label="Running" value={String(summary.running)} />
          <StatCard label="Idle" value={String(summary.idle)} />
          <StatCard label="Total Cost" value={summary.total_cost?.toLocaleString()} prefix="$" />
        </div>
      )}

      <div className="card">
        <div className="card-header">
          <h3>All Clusters</h3>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Cluster Name</th>
              <th>State</th>
              <th>Workers</th>
              <th>Type</th>
              <th>Cost (USD)</th>
              <th>Runtime (hrs)</th>
              <th>Idle (hrs)</th>
              <th>Creator</th>
            </tr>
          </thead>
          <tbody>
            {clusters.map((c: any) => (
              <tr key={c.cluster_id}>
                <td style={{ color: "#f8fafc", fontWeight: 500 }}>{c.cluster_name}</td>
                <td>
                  <span className={`badge ${stateColor(c.state)}`}>{c.state}</span>
                  {c.is_idle && <span className="badge badge-yellow" style={{ marginLeft: 4 }}>IDLE</span>}
                </td>
                <td>{c.num_workers}</td>
                <td>{c.node_type || "-"}</td>
                <td>${c.total_cost_usd?.toLocaleString()}</td>
                <td>{c.total_runtime_hours}</td>
                <td>{c.idle_time_hours}</td>
                <td>{c.creator_email?.split("@")[0] || "-"}</td>
              </tr>
            ))}
            {clusters.length === 0 && (
              <tr>
                <td colSpan={8} style={{ textAlign: "center", padding: "2rem" }}>
                  No clusters found. Connect a Databricks workspace to get started.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
