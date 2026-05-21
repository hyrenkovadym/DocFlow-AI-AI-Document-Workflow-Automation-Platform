import {
  AuditLogItem,
  DocumentDetail,
  DocumentExtractionResponse,
  DocumentListResponse,
  DocumentTextResponse,
  ExportPayload,
  LoginResponse,
  ReviewQueueItem,
  UserSummary,
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

interface ApiRequestOptions extends Omit<RequestInit, "body"> {
  body?: BodyInit | Record<string, unknown> | null;
  token?: string;
  responseType?: "json" | "text" | "blob";
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

function normalizeBody(body: ApiRequestOptions["body"], headers: Headers): BodyInit | undefined {
  if (body === null || body === undefined) {
    return undefined;
  }
  if (body instanceof FormData || typeof body === "string" || body instanceof Blob) {
    return body;
  }
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return JSON.stringify(body);
}

async function request<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`);
  }

  const body = normalizeBody(options.body, headers);

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    body,
    cache: "no-store",
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Request failed" }));
    const detail = payload?.detail ?? "Request failed";
    throw new ApiError(detail, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  if (options.responseType === "text") {
    return (await response.text()) as T;
  }
  if (options.responseType === "blob") {
    return (await response.blob()) as T;
  }

  return (await response.json()) as T;
}

export const api = {
  register: (payload: { email: string; full_name: string; password: string }) =>
    request<UserSummary>("/auth/register", { method: "POST", body: payload }),

  login: (payload: { email: string; password: string }) =>
    request<LoginResponse>("/auth/login", { method: "POST", body: payload }),

  me: (token: string) => request<UserSummary>("/auth/me", { token }),

  listDocuments: (token: string) => request<DocumentListResponse>("/documents", { token }),

  getDocument: (documentId: string, token: string) => request<DocumentDetail>(`/documents/${documentId}`, { token }),

  getDocumentText: (documentId: string, token: string) =>
    request<DocumentTextResponse>(`/documents/${documentId}/text`, { token }),

  getExtraction: (documentId: string, token: string) =>
    request<DocumentExtractionResponse>(`/documents/${documentId}/extraction`, { token }),

  uploadDocument: (file: File, token: string) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<DocumentDetail>("/documents/upload", { method: "POST", body: formData, token });
  },

  reprocessDocument: (documentId: string, token: string) =>
    request<DocumentDetail>(`/documents/${documentId}/reprocess`, { method: "POST", token }),

  exportDocumentJson: (documentId: string, token: string) =>
    request<ExportPayload>(`/documents/${documentId}/export.json`, { token }),

  exportDocumentCsv: (documentId: string, token: string) =>
    request<string>(`/documents/${documentId}/export.csv`, { token, responseType: "text" }),

  listReviewQueue: (token: string) => request<ReviewQueueItem[]>("/reviews/queue", { token }),

  approveReview: (documentId: string, token: string, reviewerComment?: string) =>
    request<{ status: string; document_id: string }>(`/reviews/${documentId}/approve`, {
      method: "POST",
      body: { reviewer_comment: reviewerComment ?? null },
      token,
    }),

  rejectReview: (documentId: string, token: string, reviewerComment?: string) =>
    request<{ status: string; document_id: string }>(`/reviews/${documentId}/reject`, {
      method: "POST",
      body: { reviewer_comment: reviewerComment ?? null },
      token,
    }),

  patchReviewFields: (documentId: string, token: string, structuredFields: Record<string, unknown>) =>
    request<{ status: string; document_id: string }>(`/reviews/${documentId}/fields`, {
      method: "PATCH",
      body: { structured_fields: structuredFields },
      token,
    }),

  listAuditLogs: (token: string) => request<AuditLogItem[]>("/audit-logs", { token }),
};
