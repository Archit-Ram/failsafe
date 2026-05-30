import type { Contribution } from "../api/types";

export function ShapBars({
  contributions,
  max = 8,
}: {
  contributions: Contribution[];
  max?: number;
}) {
  const top = [...contributions]
    .sort((a, b) => Math.abs(b.shap) - Math.abs(a.shap))
    .slice(0, max);
  const peak = Math.max(0.001, ...top.map((c) => Math.abs(c.shap)));
  return (
    <div>
      {top.map((c) => {
        const pct = (Math.abs(c.shap) / peak) * 100;
        const positive = c.shap >= 0;
        return (
          <div
            key={c.feature}
            className={`shap-bar ${positive ? "pos" : "neg"}`}
            title={`Raw value: ${c.value ?? "—"}`}
          >
            <span className="name">{c.feature}</span>
            <div className="bar-track">
              <div
                className="bar-fill"
                style={{
                  width: `${pct}%`,
                  left: positive ? "0" : `${100 - pct}%`,
                }}
              />
            </div>
            <span className="value">
              {c.shap >= 0 ? "+" : ""}
              {c.shap.toFixed(3)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
