import { AuditLogItem, DocumentItem, LoginResponse, ReviewQueueItem } from "@/types/index";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new ApiError(payload.detail ?? "Request failed", response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type");
  if (contentType?.includes("text/plain")) {
    return (await response.text()) as T;
  }

  return (await response.json()) as T;
}

export const api = {
  register: (payload: { email: string; full_name: string; password: string }) =>
    request("/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload: { email: string; password: string }) =>
    request<LoginResponse>("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  me: (token: string) => request("/auth/me", {}, token),
  listDocuments: (token: string) => request<{ items: DocumentItem[]; total: number }>("/documents", {}, token),
  getDocument: (id: string, token: string) => request(`/documents/${id}`, {}, token),
  getExtraction: (id: string, token: string) => request(`/documents/${id}/extraction`, {}, token),
  uploadDocument: (file: File, token: string) => {
    const form = new FormData();
    form.append("file", file);
    return request("/documents/upload", { method: "POST", body: form }, token);
  },
  listReviewQueue: (token: string) => request<ReviewQueueItem[]>(`/reviews/queue`, {}, token),
  approveReview: (id: string, token: string, reviewer_comment?: string) =>
    request(`/reviews/${id}/approve`, { method: "POST", body: JSON.stringify({ reviewer_comment }) }, token),
  rejectReview: (id: string, token: string, reviewer_comment?: string) =>
    request(`/reviews/${id}/reject`, { method: "POST", body: JSON.stringify({ reviewer_comment }) }, token),
  listAuditLogs: (token: string) => request<AuditLogItem[]>(`/audit-logs`, {}, token),
};
