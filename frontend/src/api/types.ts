export type Role = "faculty" | "hod";

export interface User {
  id: number;
  email: string;
  full_name: string;
  department: string | null;
  role: Role;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Contribution {
  feature: string;
  value: number | null;
  shap: number;
}

export interface Intervention {
  title: string;
  detail: string;
  category: string;
  driver: string;
  impact: number;
}

export type RiskBand = "low" | "medium" | "high";

export interface PredictionResult {
  student_ref: string | null;
  risk_score: number;
  at_risk: boolean;
  risk_band: RiskBand;
  base_value: number;
  contributions: Contribution[];
  interventions: Intervention[];
}

export interface BatchSummary {
  id: number;
  label: string;
  source_filename: string | null;
  n_students: number;
  n_at_risk: number;
  avg_risk: number;
  created_at: string;
}

export interface BatchDetail extends BatchSummary {
  predictions: PredictionResult[];
}

export interface DashboardStats {
  total_batches: number;
  total_students: number;
  total_at_risk: number;
  avg_risk: number;
  risk_band_counts: Record<RiskBand, number>;
  top_drivers: { feature: string; count: number; avg_impact: number }[];
  recent_batches: BatchSummary[];
}
