/**
 * Type-safe API client for all backend endpoints.
 * Uses fetch with proper error handling and TypeScript generics.
 */

import type {
  CategoryStat,
  Email,
  EmailListResponse,
  EvalHistoryItem,
  EvaluationRequest,
  EvaluationResponse,
  GenerateRequest,
  GenerateResponse,
  OverviewStats,
  RadarDataPoint,
  RecentActivity,
  SystemEvalSummary,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class APIError extends Error {
  constructor(
    public status: number,
    message: string,
    public detail?: unknown
  ) {
    super(message);
    this.name = "APIError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let detail: unknown;
    try {
      detail = await response.json();
    } catch {
      detail = await response.text();
    }
    throw new APIError(
      response.status,
      `API Error ${response.status}: ${response.statusText}`,
      detail
    );
  }

  return response.json() as Promise<T>;
}

// ── Health ────────────────────────────────────────────────────────────────────
export const healthApi = {
  check: () =>
    request<{
      status: string;
      version: string;
      faiss_index_size: number;
      gemini_configured: boolean;
      using_fallback: boolean;
    }>("/health"),
};

// ── Emails ────────────────────────────────────────────────────────────────────
export const emailsApi = {
  list: (params?: {
    page?: number;
    page_size?: number;
    category?: string;
    intent?: string;
    search?: string;
  }) => {
    const qs = new URLSearchParams();
    if (params?.page) qs.set("page", String(params.page));
    if (params?.page_size) qs.set("page_size", String(params.page_size));
    if (params?.category) qs.set("category", params.category);
    if (params?.intent) qs.set("intent", params.intent);
    if (params?.search) qs.set("search", params.search);
    return request<EmailListResponse>(`/api/emails?${qs.toString()}`);
  },

  get: (id: number) => request<Email>(`/api/emails/${id}`),

  categoryStats: () => request<CategoryStat[]>("/api/emails/stats/categories"),
};

// ── Generation ────────────────────────────────────────────────────────────────
export const generateApi = {
  generate: (payload: GenerateRequest) =>
    request<GenerateResponse>("/api/generate/", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};

// ── Evaluation ────────────────────────────────────────────────────────────────
export const evaluateApi = {
  evaluate: (payload: EvaluationRequest) =>
    request<EvaluationResponse>("/api/evaluate/", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  history: (limit = 20) =>
    request<EvalHistoryItem[]>(`/api/evaluate/history?limit=${limit}`),

  summary: () => request<SystemEvalSummary>("/api/evaluate/summary"),

  get: (id: number) => request<EvaluationResponse>(`/api/evaluate/${id}`),
};

// ── Analytics ─────────────────────────────────────────────────────────────────
export const analyticsApi = {
  overview: () => request<OverviewStats>("/api/analytics/overview"),
  radarData: () => request<RadarDataPoint[]>("/api/analytics/metric-radar"),
  recentActivity: (limit = 10) =>
    request<RecentActivity[]>(`/api/analytics/recent-activity?limit=${limit}`),
  scoreDistribution: () =>
    request<Array<{ range: string; count: number }>>(
      "/api/analytics/score-distribution"
    ),
};

// ── Dataset ───────────────────────────────────────────────────────────────────
export const datasetApi = {
  status: () =>
    request<{
      email_count: number;
      faiss_index_size: number;
      dataset_path: string;
      dataset_exists: boolean;
    }>("/api/dataset/status"),

  seed: (force = false) =>
    request<{ status: string; emails_seeded: number }>("/api/dataset/seed", {
      method: "POST",
      body: JSON.stringify({ force }),
    }),

  rebuildIndex: () =>
    request<{ status: string; email_count: number }>(
      "/api/dataset/rebuild-index",
      { method: "POST" }
    ),
};
