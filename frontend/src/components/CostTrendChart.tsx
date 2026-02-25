import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { CostTrendPoint } from "../types";

interface Props {
  data: CostTrendPoint[];
  title: string;
}

export default function CostTrendChart({ data, title }: Props) {
  const formatted = data.map((d) => {
    const parsed = new Date(d.period);
    const label = isNaN(parsed.getTime())
      ? d.period
      : parsed.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    return { ...d, date: label };
  });

  return (
    <div className="card full-width">
      <div className="card-header">
        <h3>{title}</h3>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={formatted}>
          <defs>
            <linearGradient id="costGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
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
            formatter={(value: number) => [`$${value.toLocaleString()}`, "Cost"]}
          />
          <Area
            type="monotone"
            dataKey="cost"
            stroke="#3b82f6"
            strokeWidth={2}
            fill="url(#costGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
