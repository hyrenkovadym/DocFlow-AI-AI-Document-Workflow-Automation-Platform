export type DocumentStatus =
  | "uploaded"
  | "queued"
  | "processing"
  | "needs_review"
  | "approved"
  | "rejected"
  | "exported"
  | "failed";

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

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    full_name: string;
    role: "admin" | "reviewer" | "user";
    is_active: boolean;
    created_at: string;
  };
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
