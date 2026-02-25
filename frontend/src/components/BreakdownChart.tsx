import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const COLORS = ["#3b82f6", "#22c55e", "#eab308", "#ef4444", "#a855f7", "#06b6d4", "#f97316", "#ec4899"];

interface BarProps {
  data: { name: string; value: number }[];
  title: string;
}

export function CostBarChart({ data, title }: BarProps) {
  return (
    <div className="card">
      <div className="card-header">
        <h3>{title}</h3>
      </div>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data.slice(0, 8)} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis type="number" stroke="#64748b" fontSize={11} tickFormatter={(v) => `$${v >= 1000 ? (v / 1000).toFixed(0) + "k" : v}`} />
          <YAxis type="category" dataKey="name" stroke="#64748b" fontSize={11} width={120} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1e293b",
              border: "1px solid #334155",
              borderRadius: "8px",
              color: "#f8fafc",
            }}
            formatter={(value: number) => [`$${value.toLocaleString()}`, "Cost"]}
          />
          <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

interface PieProps {
  data: { name: string; value: number }[];
  title: string;
}

export function CostPieChart({ data, title }: PieProps) {
  const total = data.reduce((s, d) => s + d.value, 0);

  return (
    <div className="card">
      <div className="card-header">
        <h3>{title}</h3>
      </div>
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={data.slice(0, 8)}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={90}
            paddingAngle={2}
            dataKey="value"
          >
            {data.slice(0, 8).map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: "#1e293b",
              border: "1px solid #334155",
              borderRadius: "8px",
              color: "#f8fafc",
            }}
            formatter={(value: number) => [
              `$${value.toLocaleString()} (${total > 0 ? ((value / total) * 100).toFixed(1) : "0.0"}%)`,
              "Cost",
            ]}
          />
        </PieChart>
      </ResponsiveContainer>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginTop: "0.5rem" }}>
        {data.slice(0, 8).map((d, i) => (
          <span key={i} style={{ fontSize: "0.7rem", color: "#94a3b8", display: "flex", alignItems: "center", gap: "4px" }}>
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: COLORS[i % COLORS.length], display: "inline-block" }} />
            {d.name}
          </span>
        ))}
      </div>
    </div>
  );
}
