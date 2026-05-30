import { ChangeEvent, DragEvent, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { BatchDetail } from "../api/types";

const SAMPLE_CSV_HEADERS = [
  "student_ref",
  "school",
  "sex",
  "age",
  "address",
  "famsize",
  "Pstatus",
  "Medu",
  "Fedu",
  "Mjob",
  "Fjob",
  "reason",
  "guardian",
  "traveltime",
  "studytime",
  "failures",
  "schoolsup",
  "famsup",
  "paid",
  "activities",
  "nursery",
  "higher",
  "internet",
  "romantic",
  "famrel",
  "freetime",
  "goout",
  "Dalc",
  "Walc",
  "health",
  "absences",
];

export function UploadPage() {
  const fileInput = useRef<HTMLInputElement | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [label, setLabel] = useState("");
  const [drag, setDrag] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const navigate = useNavigate();

  const onPick = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setFile(f);
    if (f && !label) setLabel(f.name.replace(/\.csv$/i, ""));
  };

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDrag(false);
    const f = e.dataTransfer.files?.[0] ?? null;
    if (f && /\.csv$/i.test(f.name)) {
      setFile(f);
      if (!label) setLabel(f.name.replace(/\.csv$/i, ""));
    }
  };

  const submit = async () => {
    if (!file) return;
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      if (label) fd.append("label", label);
      const { data } = await api.post<BatchDetail>("/predict/csv", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setSuccess(
        `Scored ${data.n_students} students — ${data.n_at_risk} flagged as at-risk.`
      );
      setTimeout(() => navigate(`/batches/${data.id}`), 600);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Upload failed.";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const downloadTemplate = () => {
    const sample = `${SAMPLE_CSV_HEADERS.join(",")}\nS0001,GP,F,17,U,GT3,T,3,3,services,other,course,mother,1,2,1,no,yes,no,yes,yes,yes,yes,no,4,3,4,1,1,3,8\n`;
    const blob = new Blob([sample], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "failsafe_template.csv";
    a.click();
    URL.revokeObjectURL(a.href);
  };

  return (
    <div className="grid" style={{ gap: 24 }}>
      <div className="card">
        <h3>Bulk upload</h3>
        <p className="muted" style={{ marginTop: 0 }}>
          Drop in a CSV with one row per student. Required columns mirror the
          UCI Student Performance schema.
        </p>
        {error && <div className="error-banner">{error}</div>}
        {success && <div className="success-banner">{success}</div>}
        <div
          className={`dropzone ${drag ? "drag" : ""}`}
          onDragOver={(e) => {
            e.preventDefault();
            setDrag(true);
          }}
          onDragLeave={() => setDrag(false)}
          onDrop={onDrop}
          onClick={() => fileInput.current?.click()}
          style={{ cursor: "pointer" }}
        >
          <input
            ref={fileInput}
            type="file"
            accept=".csv,text/csv"
            onChange={onPick}
            style={{ display: "none" }}
          />
          {file ? (
            <div>
              <strong>{file.name}</strong>
              <p className="muted" style={{ margin: "4px 0 0 0" }}>
                {(file.size / 1024).toFixed(1)} KB · ready to score
              </p>
            </div>
          ) : (
            <div>
              <strong>Drop CSV here</strong>
              <p className="muted" style={{ margin: "4px 0 0 0" }}>
                or click to browse
              </p>
            </div>
          )}
        </div>
        <div className="grid cols-2" style={{ marginTop: 16 }}>
          <div>
            <label className="label">Batch label</label>
            <input
              className="input"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="Spring 2026 — Section A"
            />
          </div>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 10 }}>
            <button
              className="btn btn-primary"
              disabled={!file || submitting}
              onClick={submit}
            >
              {submitting ? <span className="spinner" /> : "Run predictions"}
            </button>
            <button className="btn" onClick={downloadTemplate}>
              Download template
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Required columns</h3>
        <p className="muted" style={{ marginTop: 0 }}>
          The model uses behavioural and contextual signals — it never sees
          G1/G2/G3 grades, so predictions remain truly early.
        </p>
        <code style={{ display: "block", padding: 12, background: "rgba(255,255,255,0.04)", borderRadius: 8, fontSize: 12, overflowX: "auto" }}>
          {SAMPLE_CSV_HEADERS.join(", ")}
        </code>
        <p className="muted" style={{ marginTop: 12, fontSize: 13 }}>
          See <Link to="/batches">past batches</Link> to inspect previous runs.
        </p>
      </div>
    </div>
  );
}
