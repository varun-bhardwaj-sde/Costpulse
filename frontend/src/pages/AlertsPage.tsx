import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const [a, h] = await Promise.all([
          api.getAlerts(),
          api.getAlertHistory(),
        ]);
        setAlerts(a.data || []);
        setHistory(h.data || []);
      } catch {
        // API not available
      }
    }
    load();
  }, []);

  return (
    <div>
      <div className="page-header">
        <h2>Alerts</h2>
        <p>Budget thresholds and cost anomaly alerts</p>
      </div>

      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <div className="card-header">
          <h3>Alert Configurations</h3>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Threshold</th>
              <th>Status</th>
              <th>Channels</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((a: any) => (
              <tr key={a.id}>
                <td style={{ color: "#f8fafc", fontWeight: 500 }}>{a.name}</td>
                <td>
                  <span className="badge badge-blue">{a.alert_type}</span>
                </td>
                <td>
                  {a.threshold_type === "percentage"
                    ? `${a.threshold_value}%`
                    : `$${a.threshold_value?.toLocaleString()}`}
                </td>
                <td>
                  <span className={`badge ${a.is_active ? "badge-green" : "badge-red"}`}>
                    {a.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td>
                  {a.notification_channels?.slack && (
                    <span className="badge badge-purple" style={{ marginRight: 4 }}>Slack</span>
                  )}
                  {a.notification_channels?.email && (
                    <span className="badge badge-blue">Email</span>
                  )}
                </td>
              </tr>
            ))}
            {alerts.length === 0 && (
              <tr>
                <td colSpan={5} style={{ textAlign: "center", padding: "2rem" }}>
                  No alerts configured. Create an alert to monitor cost thresholds.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Alert History</h3>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Triggered At</th>
              <th>Status</th>
              <th>Value</th>
              <th>Message</th>
            </tr>
          </thead>
          <tbody>
            {history.map((h: any) => (
              <tr key={h.id}>
                <td>{h.triggered_at ? new Date(h.triggered_at).toLocaleString() : "-"}</td>
                <td>
                  <span
                    className={`badge ${
                      h.status === "triggered"
                        ? "badge-red"
                        : h.status === "resolved"
                        ? "badge-green"
                        : "badge-yellow"
                    }`}
                  >
                    {h.status}
                  </span>
                </td>
                <td>${h.current_value?.toLocaleString()}</td>
                <td style={{ maxWidth: 400, overflow: "hidden", textOverflow: "ellipsis" }}>
                  {h.message}
                </td>
              </tr>
            ))}
            {history.length === 0 && (
              <tr>
                <td colSpan={4} style={{ textAlign: "center", padding: "2rem" }}>
                  No alerts have been triggered yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
