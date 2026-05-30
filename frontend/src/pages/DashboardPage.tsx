import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { DashboardStats } from "../api/types";

const RISK_COLORS: Record<string, string> = {
  low: "#10b981",
  medium: "#f59e0b",
  high: "#ef4444",
};

export function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<DashboardStats>("/dashboard")
      .then(({ data }) => setStats(data))
      .catch((err) => setError(err?.response?.data?.detail ?? "Failed to load"));
  }, []);

  if (error) return <div className="error-banner">{error}</div>;
  if (!stats)
    return (
      <div className="card">
        <span className="spinner" /> Loading dashboard…
      </div>
    );

  const { risk_band_counts, top_drivers, recent_batches } = stats;
  const bandData = (["low", "medium", "high"] as const).map((k) => ({
    name: k,
    value: risk_band_counts[k] ?? 0,
  }));
  const trend = [...recent_batches]
    .reverse()
    .map((b, i) => ({
      name: b.label.length > 12 ? `${b.label.slice(0, 12)}…` : b.label,
      avg_risk: Number((b.avg_risk * 100).toFixed(1)),
      at_risk: b.n_at_risk,
      step: i + 1,
    }));

  return (
    <div className="grid" style={{ gap: 24 }}>
      <section className="grid cols-4">
        <Stat label="Batches" value={stats.total_batches} />
        <Stat label="Students scored" value={stats.total_students} />
        <Stat label="At-risk students" value={stats.total_at_risk} accent="danger" />
        <Stat
          label="Avg risk score"
          value={`${(stats.avg_risk * 100).toFixed(1)}%`}
          accent="warning"
        />
      </section>

      <section className="grid cols-2">
        <div className="card">
          <h3>Risk band distribution</h3>
          <p className="muted" style={{ marginTop: 0 }}>
            How risk concentrates across all scored students.
          </p>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={bandData}
                dataKey="value"
                nameKey="name"
                outerRadius={95}
                innerRadius={60}
                paddingAngle={3}
              >
                {bandData.map((d) => (
                  <Cell key={d.name} fill={RISK_COLORS[d.name]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: "#0f1733", border: "1px solid #29335c" }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3>Risk trend across recent batches</h3>
          <p className="muted" style={{ marginTop: 0 }}>
            Average predicted risk per uploaded batch.
          </p>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#29335c" />
              <XAxis dataKey="name" stroke="#9aa3d6" />
              <YAxis stroke="#9aa3d6" unit="%" />
              <Tooltip
                contentStyle={{ background: "#0f1733", border: "1px solid #29335c" }}
              />
              <Line
                type="monotone"
                dataKey="avg_risk"
                stroke="#06b6d4"
                strokeWidth={2.5}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="grid cols-2">
        <div className="card">
          <h3>Top SHAP drivers (most recent 500 predictions)</h3>
          <p className="muted" style={{ marginTop: 0 }}>
            Features pushing students *toward* the at-risk class.
          </p>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={top_drivers} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#29335c" />
              <XAxis type="number" stroke="#9aa3d6" />
              <YAxis dataKey="feature" type="category" width={140} stroke="#9aa3d6" />
              <Tooltip
                contentStyle={{ background: "#0f1733", border: "1px solid #29335c" }}
              />
              <Bar dataKey="count" fill="#8b5cf6" radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3>Recent batches</h3>
          <table className="table">
            <thead>
              <tr>
                <th>Label</th>
                <th>Students</th>
                <th>At-risk</th>
                <th>Avg risk</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {recent_batches.length === 0 && (
                <tr>
                  <td colSpan={5} className="muted">
                    No batches yet. Upload a CSV to get started.
                  </td>
                </tr>
              )}
              {recent_batches.map((b) => (
                <tr key={b.id}>
                  <td>{b.label}</td>
                  <td>{b.n_students}</td>
                  <td>{b.n_at_risk}</td>
                  <td>{(b.avg_risk * 100).toFixed(1)}%</td>
                  <td>
                    <Link to={`/batches/${b.id}`} className="btn btn-ghost">
                      Open
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function Stat({
  label,
  value,
  accent,
}: {
  label: string;
  value: number | string;
  accent?: "danger" | "warning";
}) {
  return (
    <div className="card stat">
      <span className="label">{label}</span>
      <span
        className="num"
        style={
          accent === "danger"
            ? { background: "linear-gradient(135deg,#fff,#fca5a5)", WebkitBackgroundClip: "text", color: "transparent" }
            : accent === "warning"
            ? { background: "linear-gradient(135deg,#fff,#fcd34d)", WebkitBackgroundClip: "text", color: "transparent" }
            : undefined
        }
      >
        {value}
      </span>
    </div>
  );
}
