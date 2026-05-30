import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { BatchSummary } from "../api/types";

export function BatchesPage() {
  const [batches, setBatches] = useState<BatchSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<BatchSummary[]>("/batches", { params: { limit: 100 } })
      .then(({ data }) => setBatches(data))
      .catch((err) => setError(err?.response?.data?.detail ?? "Failed to load"));
  }, []);

  if (error) return <div className="error-banner">{error}</div>;
  if (!batches)
    return (
      <div className="card">
        <span className="spinner" /> Loading batches…
      </div>
    );

  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0 }}>All batches</h3>
        <Link to="/upload" className="btn btn-primary">
          Upload new batch
        </Link>
      </div>
      <hr className="sep" />
      <table className="table">
        <thead>
          <tr>
            <th>Label</th>
            <th>File</th>
            <th>Students</th>
            <th>At-risk</th>
            <th>Avg risk</th>
            <th>Created</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {batches.length === 0 && (
            <tr>
              <td colSpan={7} className="muted">
                No batches yet — upload a CSV to score students.
              </td>
            </tr>
          )}
          {batches.map((b) => (
            <tr key={b.id}>
              <td>
                <strong>{b.label}</strong>
              </td>
              <td className="muted">{b.source_filename ?? "—"}</td>
              <td>{b.n_students}</td>
              <td>{b.n_at_risk}</td>
              <td>{(b.avg_risk * 100).toFixed(1)}%</td>
              <td className="muted">{new Date(b.created_at).toLocaleString()}</td>
              <td>
                <Link to={`/batches/${b.id}`} className="btn btn-ghost">
                  View
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
