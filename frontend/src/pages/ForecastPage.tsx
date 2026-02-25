import { useEffect, useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { api } from "../api/client";

export default function ForecastPage() {
  const [forecast, setForecast] = useState<any>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getForecastSummary();
        setForecast(data);
      } catch {
        // API not available
      }
    }
    load();
  }, []);

  const chartData =
    forecast?.data?.map((d: any) => ({
      date: new Date(d.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      predicted: d.predicted,
      lower: d.lower,
      upper: d.upper,
    })) || [];

  return (
    <div>
      <div className="page-header">
        <h2>Cost Forecasting</h2>
        <p>Predictive cost forecasting for the next 30/60/90 days</p>
      </div>

      {forecast && forecast.status === "ok" && (
        <div className="stat-grid">
          <div className="stat-card">
            <div className="label">Forecast Period</div>
            <div className="value">{forecast.horizon_days} days</div>
          </div>
          <div className="stat-card">
            <div className="label">Predicted Total</div>
            <div className="value">
              ${forecast.total_predicted_cost?.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </div>
          </div>
          <div className="stat-card">
            <div className="label">Avg Daily Cost</div>
            <div className="value">
              ${forecast.avg_daily_cost?.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </div>
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-header">
          <h3>Cost Forecast with Confidence Interval</h3>
        </div>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="forecastGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="confidenceGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} tickFormatter={(v) => `$${v.toLocaleString()}`} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: "8px",
                  color: "#f8fafc",
                }}
                formatter={(value: number, name: string) => [
                  `$${value.toLocaleString()}`,
                  name === "predicted" ? "Predicted" : name === "upper" ? "Upper Bound" : "Lower Bound",
                ]}
              />
              <Area type="monotone" dataKey="upper" stroke="transparent" fill="url(#confidenceGradient)" />
              <Area type="monotone" dataKey="lower" stroke="transparent" fill="#0f172a" />
              <Area
                type="monotone"
                dataKey="predicted"
                stroke="#a855f7"
                strokeWidth={2}
                fill="url(#forecastGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ textAlign: "center", padding: "3rem", color: "#64748b" }}>
            No forecast data available. Generate a forecast to see predictions.
          </div>
        )}
      </div>
    </div>
  );
}
