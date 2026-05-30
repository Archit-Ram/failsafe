import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { InterventionList } from "../components/InterventionList";
import { RiskBadge } from "../components/RiskBadge";
import { ShapBars } from "../components/ShapBars";
import type { BatchDetail, PredictionResult, RiskBand } from "../api/types";

const FILTERS: Array<{ key: "all" | RiskBand; label: string }> = [
  { key: "all", label: "All" },
  { key: "high", label: "High" },
  { key: "medium", label: "Medium" },
  { key: "low", label: "Low" },
];

export function BatchDetailPage() {
  const { id } = useParams();
  const [batch, setBatch] = useState<BatchDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | RiskBand>("all");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<PredictionResult | null>(null);

  useEffect(() => {
    if (!id) return;
    api
      .get<BatchDetail>(`/batches/${id}`)
      .then(({ data }) => {
        setBatch(data);
        const flagged = [...data.predictions].sort(
          (a, b) => b.risk_score - a.risk_score
        )[0];
        if (flagged) setSelected(flagged);
      })
      .catch((err) => setError(err?.response?.data?.detail ?? "Failed to load"));
  }, [id]);

  const filtered = useMemo(() => {
    if (!batch) return [];
    let preds = [...batch.predictions];
    if (filter !== "all") {
      preds = preds.filter((p) => p.risk_band === filter);
    }
    if (search) {
      const q = search.toLowerCase();
      preds = preds.filter((p) =>
        (p.student_ref ?? "").toLowerCase().includes(q)
      );
    }
    return preds.sort((a, b) => b.risk_score - a.risk_score);
  }, [batch, filter, search]);

  if (error) return <div className="error-banner">{error}</div>;
  if (!batch)
    return (
      <div className="card">
        <span className="spinner" /> Loading batch…
      </div>
    );

  return (
    <div className="grid" style={{ gap: 24 }}>
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 14 }}>
          <div>
            <h3 style={{ margin: 0 }}>{batch.label}</h3>
            <p className="muted" style={{ margin: "4px 0 0 0" }}>
              {batch.source_filename ?? "ad-hoc"} ·{" "}
              {new Date(batch.created_at).toLocaleString()}
            </p>
          </div>
          <div className="grid cols-3" style={{ gap: 14, minWidth: 360 }}>
            <Stat label="Students" value={batch.n_students} />
            <Stat label="At-risk" value={batch.n_at_risk} accent="danger" />
            <Stat
              label="Avg risk"
              value={`${(batch.avg_risk * 100).toFixed(1)}%`}
              accent="warning"
            />
          </div>
        </div>
      </div>

      <div className="grid cols-2" style={{ gap: 24, alignItems: "start" }}>
        <div className="card">
          <div style={{ display: "flex", gap: 10, marginBottom: 12, flexWrap: "wrap" }}>
            {FILTERS.map((f) => (
              <button
                key={f.key}
                className={`btn ${filter === f.key ? "btn-primary" : ""}`}
                onClick={() => setFilter(f.key)}
              >
                {f.label}
              </button>
            ))}
            <input
              className="input"
              placeholder="Search student ref"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ flex: 1, minWidth: 140 }}
            />
          </div>
          <div style={{ maxHeight: 560, overflowY: "auto" }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Ref</th>
                  <th>Risk</th>
                  <th>Band</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((p, idx) => (
                  <tr
                    key={`${p.student_ref}-${idx}`}
                    onClick={() => setSelected(p)}
                    style={{
                      cursor: "pointer",
                      background:
                        selected?.student_ref === p.student_ref
                          ? "rgba(99,102,241,0.12)"
                          : undefined,
                    }}
                  >
                    <td>{p.student_ref ?? `#${idx + 1}`}</td>
                    <td>{(p.risk_score * 100).toFixed(1)}%</td>
                    <td>
                      <RiskBadge band={p.risk_band} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filtered.length === 0 && (
              <p className="muted" style={{ padding: 18 }}>
                No students match this filter.
              </p>
            )}
          </div>
        </div>

        <div className="card">
          {selected ? (
            <>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h3 style={{ margin: 0 }}>{selected.student_ref ?? "Student"}</h3>
                <RiskBadge band={selected.risk_band} />
              </div>
              <p className="muted" style={{ marginTop: 4 }}>
                Risk score{" "}
                <strong style={{ color: "white" }}>
                  {(selected.risk_score * 100).toFixed(1)}%
                </strong>{" "}
                · base {selected.base_value.toFixed(3)}
              </p>
              <hr className="sep" />
              <h4 style={{ marginBottom: 8 }}>Why this student was flagged</h4>
              <p className="muted" style={{ marginTop: 0, fontSize: 13 }}>
                Bars in red push the student toward the at-risk class; teal bars
                lower the risk.
              </p>
              <ShapBars contributions={selected.contributions} />
              <hr className="sep" />
              <h4 style={{ marginBottom: 8 }}>Recommended interventions</h4>
              <InterventionList items={selected.interventions} />
            </>
          ) : (
            <p className="muted">Pick a student on the left to see details.</p>
          )}
        </div>
      </div>
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
    <div className="stat">
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
