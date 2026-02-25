import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function RecommendationsPage() {
  const [recs, setRecs] = useState<any[]>([]);
  const [filter, setFilter] = useState("open");

  useEffect(() => {
    async function load() {
      try {
        const r = await api.getRecommendations(filter);
        setRecs(r.data || []);
      } catch {
        // API not available
      }
    }
    load();
  }, [filter]);

  const severityBadge = (severity: string) => {
    const map: Record<string, string> = {
      critical: "badge-red",
      high: "badge-red",
      medium: "badge-yellow",
      low: "badge-blue",
    };
    return map[severity] || "badge-blue";
  };

  const totalSavings = recs.reduce((s, r) => s + (r.estimated_savings || 0), 0);

  return (
    <div>
      <div className="page-header">
        <h2>Optimization Recommendations</h2>
        <p>AI-powered suggestions to reduce Databricks costs</p>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="label">Open Recommendations</div>
          <div className="value">{recs.length}</div>
        </div>
        <div className="stat-card">
          <div className="label">Potential Monthly Savings</div>
          <div className="value">${totalSavings.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
        </div>
      </div>

      <div style={{ marginBottom: "1rem", display: "flex", gap: "0.5rem" }}>
        {["open", "accepted", "dismissed", "implemented"].map((s) => (
          <button
            key={s}
            className={`btn ${s === filter ? "btn-primary" : ""}`}
            onClick={() => setFilter(s)}
          >
            {s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        {recs.map((r: any) => (
          <div key={r.id} className="card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div>
                <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginBottom: "0.5rem" }}>
                  <span className={`badge ${severityBadge(r.severity)}`}>{r.severity}</span>
                  <span className="badge badge-purple">{r.type}</span>
                  {r.resource_type && <span className="badge badge-blue">{r.resource_type}</span>}
                </div>
                <h4 style={{ marginBottom: "0.5rem" }}>{r.title}</h4>
                <p style={{ color: "#94a3b8", fontSize: "0.875rem" }}>{r.description}</p>
              </div>
              {r.estimated_savings > 0 && (
                <div style={{ textAlign: "right", flexShrink: 0, marginLeft: "1rem" }}>
                  <div style={{ color: "#64748b", fontSize: "0.75rem" }}>Est. Savings</div>
                  <div style={{ color: "#22c55e", fontSize: "1.25rem", fontWeight: 700 }}>
                    ${r.estimated_savings?.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        {recs.length === 0 && (
          <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
            No {filter} recommendations found.
          </div>
        )}
      </div>
    </div>
  );
}
