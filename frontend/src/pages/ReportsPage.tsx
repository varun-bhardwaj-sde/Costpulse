import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function ReportsPage() {
  const [reports, setReports] = useState<any[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const r = await api.getReports();
        setReports(r.data || []);
      } catch {
        // API not available
      }
    }
    load();
  }, []);

  const formatBadge = (format: string) => {
    const map: Record<string, string> = {
      csv: "badge-green",
      excel: "badge-blue",
      pdf: "badge-red",
    };
    return map[format] || "badge-yellow";
  };

  return (
    <div>
      <div className="page-header">
        <h2>Reports</h2>
        <p>Showback, chargeback, and executive cost reports</p>
      </div>

      <div style={{ marginBottom: "1rem" }}>
        <button className="btn btn-primary">Generate Report</button>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Generated Reports</h3>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Format</th>
              <th>Period</th>
              <th>Status</th>
              <th>Size</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((r: any) => (
              <tr key={r.id}>
                <td style={{ color: "#f8fafc", fontWeight: 500 }}>{r.name}</td>
                <td>
                  <span className="badge badge-blue">{r.report_type}</span>
                </td>
                <td>
                  <span className={`badge ${formatBadge(r.format)}`}>{r.format.toUpperCase()}</span>
                </td>
                <td>
                  {new Date(r.period_start).toLocaleDateString()} -{" "}
                  {new Date(r.period_end).toLocaleDateString()}
                </td>
                <td>
                  <span
                    className={`badge ${
                      r.status === "completed" ? "badge-green" : r.status === "failed" ? "badge-red" : "badge-yellow"
                    }`}
                  >
                    {r.status}
                  </span>
                </td>
                <td>{r.file_size_bytes ? `${(r.file_size_bytes / 1024).toFixed(1)} KB` : "-"}</td>
                <td>{r.created_at ? new Date(r.created_at).toLocaleDateString() : "-"}</td>
              </tr>
            ))}
            {reports.length === 0 && (
              <tr>
                <td colSpan={7} style={{ textAlign: "center", padding: "2rem" }}>
                  No reports generated yet. Click "Generate Report" to create one.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
