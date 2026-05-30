import type { Intervention } from "../api/types";

export function InterventionList({ items }: { items: Intervention[] }) {
  if (!items?.length) {
    return <p className="muted">No interventions generated.</p>;
  }
  return (
    <div>
      {items.map((it, idx) => (
        <div key={`${it.title}-${idx}`} className="intervention-card">
          <h4>
            <span>{it.title}</span>
            <span className="tag">{it.category}</span>
          </h4>
          <p style={{ margin: "6px 0", fontSize: 14 }}>{it.detail}</p>
          <span className="muted" style={{ fontSize: 12 }}>
            Driven by <strong>{it.driver}</strong> · impact {it.impact.toFixed(3)}
          </span>
        </div>
      ))}
    </div>
  );
}
