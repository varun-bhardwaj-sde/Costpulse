import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function TeamsPage() {
  const [teams, setTeams] = useState<any[]>([]);
  const [allocations, setAllocations] = useState<any[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const [t, a] = await Promise.all([
          api.getTeams(),
          api.getAllocations(),
        ]);
        setTeams(t.data || []);
        setAllocations(a.data || []);
      } catch {
        // API not available
      }
    }
    load();
  }, []);

  return (
    <div>
      <div className="page-header">
        <h2>Teams & Cost Allocation</h2>
        <p>Manage teams and track cost attribution</p>
      </div>

      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <div className="card-header">
          <h3>Teams</h3>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Team</th>
              <th>Department</th>
              <th>Cost Center</th>
              <th>Manager</th>
              <th>Members</th>
            </tr>
          </thead>
          <tbody>
            {teams.map((t: any) => (
              <tr key={t.id}>
                <td style={{ color: "#f8fafc", fontWeight: 500 }}>{t.name}</td>
                <td>{t.department || "-"}</td>
                <td>{t.cost_center || "-"}</td>
                <td>{t.manager_email || "-"}</td>
                <td>{t.member_count}</td>
              </tr>
            ))}
            {teams.length === 0 && (
              <tr>
                <td colSpan={5} style={{ textAlign: "center", padding: "2rem" }}>
                  No teams configured. Add teams to enable cost allocation.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Recent Allocations</h3>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Team</th>
              <th>Period</th>
              <th>Total Cost</th>
              <th>DBU Cost</th>
              <th>Compute Cost</th>
              <th>Method</th>
            </tr>
          </thead>
          <tbody>
            {allocations.map((a: any) => (
              <tr key={a.id}>
                <td style={{ color: "#f8fafc" }}>{a.team_id.slice(0, 8)}</td>
                <td>
                  {new Date(a.period_start).toLocaleDateString()} -{" "}
                  {new Date(a.period_end).toLocaleDateString()}
                </td>
                <td>${a.total_cost?.toLocaleString()}</td>
                <td>${a.dbu_cost?.toLocaleString()}</td>
                <td>${a.compute_cost?.toLocaleString()}</td>
                <td>
                  <span className="badge badge-blue">{a.allocation_method}</span>
                </td>
              </tr>
            ))}
            {allocations.length === 0 && (
              <tr>
                <td colSpan={6} style={{ textAlign: "center", padding: "2rem" }}>
                  No allocations yet. Run the allocation engine to attribute costs to teams.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
