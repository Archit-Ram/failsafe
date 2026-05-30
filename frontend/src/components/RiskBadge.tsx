import type { RiskBand } from "../api/types";

export function RiskBadge({ band }: { band: RiskBand }) {
  const label =
    band === "high" ? "High risk" : band === "medium" ? "Medium risk" : "Low risk";
  return <span className={`badge ${band}`}>{label}</span>;
}
