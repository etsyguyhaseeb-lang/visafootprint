const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface AccountInput {
  platform: string;
  handle: string;
  manual_posts?: string;
}

export interface ScreeningRequest {
  name: string;
  email: string;
  country: string;
  accounts: AccountInput[];
  reason: string;
  timeline: string;
  consent: boolean;
  tier?: string;
}

export interface ScreeningResponse {
  job_id: string;
  status: string;
}

export interface StatusResponse {
  job_id: string;
  status: "queued" | "processing" | "done" | "failed";
  error?: string;
}

export interface FlaggedPost {
  text: string;
  platform: string;
  date: string | null;
  risk_level: "HIGH" | "MEDIUM" | "LOW";
  risk_category: string;
  explanation: string;
  post_url?: string;
}

export interface ReportData {
  name: string;
  country: string;
  reason: string;
  accounts: AccountInput[];
  overall_risk: "HIGH" | "MEDIUM" | "LOW";
  risk_score: number;
  scores: { political: number; content: number; network: number };
  summary: string;
  flagged_posts: FlaggedPost[];
  risk_topics: string[];
  sentiment: { positive: number; neutral: number; negative: number };
  recommendations: string[];
  overall_assessment: string;
  posts_analyzed: number;
  platforms_analyzed: string[];
}

function parseDetail(detail: unknown): string {
  if (!detail) return "";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    // FastAPI validation error: [{loc, msg, type}]
    return detail.map((e) => (typeof e === "object" && e !== null && "msg" in e ? String((e as Record<string, unknown>).msg) : JSON.stringify(e))).join(". ");
  }
  return JSON.stringify(detail);
}

export async function submitScreening(data: ScreeningRequest): Promise<ScreeningResponse> {
  const res = await fetch(`${BASE}/api/screen`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const msg = parseDetail(err.detail) || `Request failed: ${res.status}`;
    throw new Error(msg);
  }
  return res.json();
}

export async function getStatus(jobId: string): Promise<StatusResponse> {
  const res = await fetch(`${BASE}/api/status/${jobId}`);
  if (!res.ok) throw new Error(`Status check failed: ${res.status}`);
  return res.json();
}

export async function getReport(jobId: string): Promise<ReportData> {
  const res = await fetch(`${BASE}/api/report/${jobId}`);
  if (!res.ok) throw new Error(`Report fetch failed: ${res.status}`);
  return res.json();
}

export function getPdfUrl(jobId: string): string {
  return `${BASE}/api/report/${jobId}/pdf`;
}
