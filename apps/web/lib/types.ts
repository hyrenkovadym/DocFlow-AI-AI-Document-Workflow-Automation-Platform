export type UserRole = "admin" | "reviewer" | "user";

export type DocumentStatus =
  | "uploaded"
  | "queued"
  | "processing"
  | "needs_review"
  | "approved"
  | "rejected"
  | "exported"
  | "failed";

export interface UserSummary {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserSummary;
}

export interface DocumentItem {
  id: string;
  owner_id: string;
  original_filename: string;
  file_type: string;
  status: DocumentStatus;
  document_type: string;
  ai_confidence_score: number | null;
  processing_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentDetail extends DocumentItem {
  extracted_text: string | null;
  metadata_json: Record<string, unknown>;
}

export interface DocumentListResponse {
  items: DocumentItem[];
  total: number;
}

export interface DocumentTextResponse {
  document_id: string;
  text: string;
}

export interface DocumentExtractionResponse {
  document_id: string;
  structured_fields: Record<string, unknown>;
  raw_response: Record<string, unknown>;
  confidence_score: number;
}

export interface ReviewQueueItem {
  document_id: string;
  filename: string;
  document_type: string;
  confidence_score: number | null;
  owner_id: string;
  created_at: string;
}

export interface AuditLogItem {
  id: string;
  actor_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
}

export interface ExportPayload {
  document_id: string;
  owner_id: string;
  original_filename: string;
  status: string;
  document_type: string;
  confidence_score: number | null;
  review_status: string;
  reviewer_comment: string | null;
  exported_at: string;
  exported_by_id: string;
  structured_fields: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}
