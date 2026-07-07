/**
 * TypeScript type definitions for the entire application.
 * Mirrors the Pydantic schemas on the backend.
 */

// ── Email types ───────────────────────────────────────────────────────────────

export interface Email {
  id: number;
  subject: string;
  sender: string;
  recipient: string;
  body: string;
  ideal_reply: string;
  intent: string;
  tone: string;
  priority: "low" | "medium" | "high" | "critical";
  entities: Record<string, string | string[]>;
  expected_actions: string[];
  tags: string[];
  category: string;
  embedding_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface EmailListResponse {
  total: number;
  page: number;
  page_size: number;
  items: Email[];
}

export interface RetrievedEmail {
  id: number;
  subject: string;
  body: string;
  ideal_reply: string;
  intent: string;
  tone: string;
  category: string;
  similarity_score: number;
  retrieval_reason?: string;
}

// ── Generation types ──────────────────────────────────────────────────────────

export interface GenerateRequest {
  subject: string;
  body: string;
  sender?: string;
  top_k?: number;
  reference_reply?: string;
}

export interface GenerateResponse {
  response_id: number;
  generated_reply: string;
  model_used: string;
  retrieved_emails: RetrievedEmail[];
  prompt_tokens: number;
  completion_tokens: number;
  generation_time_ms: number;
}

// ── Evaluation types ──────────────────────────────────────────────────────────

export interface MetricScore {
  score: number;
  weight: number;
  weighted_contribution: number;
  explanation: string;
  why_lost_points?: string;
  how_to_improve?: string;
  details: Record<string, unknown>;
}

export interface MetricBreakdown {
  semantic_similarity: MetricScore;
  intent_match: MetricScore;
  completeness: MetricScore;
  tone_match: MetricScore;
  action_coverage: MetricScore;
  safety: MetricScore;
  grammar_quality: MetricScore;
  professionalism: MetricScore;
  length_penalty: MetricScore;
  hallucination_score: MetricScore;
  entity_coverage: MetricScore;
  retrieval_consistency: MetricScore;
}

export interface EvaluationRequest {
  response_id: number;
  generated_reply: string;
  reference_reply?: string;
  incoming_email: string;
  incoming_subject: string;
  intent?: string;
  tone?: string;
  expected_actions?: string[];
  entities?: Record<string, string | string[]>;
  retrieval_ids?: number[];
}

export interface EvaluationResponse {
  evaluation_id: number;
  response_id: number;
  overall_score: number;
  confidence: number;
  traffic_light: "green" | "amber" | "red";
  grade: "A" | "B" | "C" | "D" | "F";
  metric_breakdown: MetricBreakdown;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  created_at: string;
}

// ── Analytics types ───────────────────────────────────────────────────────────

export interface OverviewStats {
  total_emails: number;
  total_generated: number;
  total_evaluated: number;
  average_score: number;
  average_safety: number;
}

export interface RadarDataPoint {
  metric: string;
  score: number;
}

export interface EvalHistoryItem {
  id: number;
  response_id: number;
  overall_score: number;
  confidence: number;
  traffic_light: "green" | "amber" | "red";
  semantic_similarity: number;
  intent_match: number;
  completeness: number;
  safety: number;
  created_at: string;
}

export interface RecentActivity {
  response_id: number;
  subject: string;
  model: string;
  overall_score: number | null;
  traffic_light: "green" | "amber" | "red" | null;
  generated_at: string;
}

export interface SystemEvalSummary {
  total_evaluations: number;
  average_score: number;
  score_distribution: Record<string, number>;
  metric_averages: Record<string, number>;
  top_performers: Array<{ id: number; score: number; traffic: string }>;
  low_performers: Array<{ id: number; score: number; traffic: string }>;
  improvement_trend: Array<{ date: string; score: number }>;
}

export interface CategoryStat {
  category: string;
  count: number;
}
