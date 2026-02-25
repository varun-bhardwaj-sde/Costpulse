interface StatCardProps {
  label: string;
  value: string;
  change?: number;
  prefix?: string;
}

export default function StatCard({ label, value, change, prefix }: StatCardProps) {
  const changeClass =
    change !== undefined ? (change > 0 ? "positive" : change < 0 ? "negative" : "") : "";

  return (
    <div className="stat-card">
      <div className="label">{label}</div>
      <div className="value">
        {prefix}
        {value}
      </div>
      {change !== undefined && (
        <div className={`change ${changeClass}`}>
          {change > 0 ? "+" : ""}
          {change.toFixed(1)}% vs prev period
        </div>
      )}
    </div>
  );
}
