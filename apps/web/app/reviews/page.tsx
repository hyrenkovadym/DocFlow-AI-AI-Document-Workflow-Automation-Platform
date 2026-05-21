"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { Layout } from "@/components/Layout";
import { Card } from "@/components/Card";
import { DataTable } from "@/components/DataTable";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { Button } from "@/components/Button";
import { StatusBadge } from "@/components/StatusBadge";
import { api, ApiError } from "@/lib/api";
import { getAuthToken } from "@/lib/auth";
import { DocumentDetail, DocumentExtractionResponse, ReviewQueueItem } from "@/lib/types";
import { formatConfidence, formatDate, safeStringify } from "@/lib/utils";

export default function ReviewsPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [queue, setQueue] = useState<ReviewQueueItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<DocumentDetail | null>(null);
  const [selectedExtraction, setSelectedExtraction] = useState<DocumentExtractionResponse | null>(null);
  const [fieldsDraft, setFieldsDraft] = useState<string>("{}");
  const [reviewerComment, setReviewerComment] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadQueue = useCallback(async (authToken: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.listReviewQueue(authToken);
      setQueue(response);
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setError("Review queue is available only for reviewer/admin roles.");
        setQueue([]);
        return;
      }
      if (err instanceof ApiError && err.status === 401) {
        router.replace("/login");
        return;
      }
      setError(err instanceof Error ? err.message : "Failed to load review queue.");
    } finally {
      setLoading(false);
    }
  }, [router]);

  const loadSelection = useCallback(async (authToken: string, documentId: string) => {
    try {
      const [documentResponse, extractionResponse] = await Promise.all([
        api.getDocument(documentId, authToken),
        api.getExtraction(documentId, authToken),
      ]);
      setSelectedDocument(documentResponse);
      setSelectedExtraction(extractionResponse);
      setFieldsDraft(safeStringify(extractionResponse.structured_fields));
      setSelectedId(documentId);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.replace("/login");
        return;
      }
      if (err instanceof ApiError && err.status === 403) {
        setError("You do not have permission to open this document.");
        return;
      }
      setError(err instanceof Error ? err.message : "Failed to load selected document.");
    }
  }, [router]);

  useEffect(() => {
    const stored = getAuthToken();
    if (!stored) {
      router.replace("/login");
      return;
    }
    setToken(stored);
    loadQueue(stored);
  }, [loadQueue, router]);

  const rows = useMemo(
    () =>
      queue.map((item) => ({
        filename: (
          <button
            className="font-semibold text-accent hover:underline"
            disabled={actionLoading}
            onClick={() => {
              if (!token) {
                return;
              }
              loadSelection(token, item.document_id);
            }}
          >
            {item.filename}
          </button>
        ),
        type: item.document_type,
        status: <StatusBadge status="needs_review" />,
        confidence: formatConfidence(item.confidence_score),
        created: formatDate(item.created_at),
      })),
    [actionLoading, loadSelection, queue, token],
  );

  const onPatchFields = async (event: FormEvent) => {
    event.preventDefault();
    if (!token || !selectedId) {
      return;
    }

    let parsedFields: Record<string, unknown>;
    try {
      parsedFields = JSON.parse(fieldsDraft) as Record<string, unknown>;
    } catch {
      setError("Structured fields must be valid JSON.");
      return;
    }

    setActionLoading(true);
    setError(null);
    try {
      await api.patchReviewFields(selectedId, token, parsedFields);
      await loadSelection(token, selectedId);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.replace("/login");
        return;
      }
      if (err instanceof ApiError && err.status === 403) {
        setError("You do not have permission to update extracted fields.");
        return;
      }
      setError(err instanceof Error ? err.message : "Failed to update fields.");
    } finally {
      setActionLoading(false);
    }
  };

  const onDecision = async (decision: "approve" | "reject") => {
    if (!token || !selectedId) {
      return;
    }

    setActionLoading(true);
    setError(null);
    try {
      if (decision === "approve") {
        await api.approveReview(selectedId, token, reviewerComment || "Approved from UI");
      } else {
        await api.rejectReview(selectedId, token, reviewerComment || "Rejected from UI");
      }

      await loadQueue(token);
      setSelectedId(null);
      setSelectedDocument(null);
      setSelectedExtraction(null);
      setReviewerComment("");
      setFieldsDraft("{}");
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.replace("/login");
        return;
      }
      if (err instanceof ApiError && err.status === 403) {
        setError("You do not have permission to submit review decisions.");
        return;
      }
      if (err instanceof ApiError && err.status === 409) {
        setError(err.message);
        return;
      }
      setError(err instanceof Error ? err.message : "Failed to apply review decision.");
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <Layout title="Review Queue" description="Reviewer/admin actions for documents awaiting human validation.">
      <div className="space-y-4">
        {error ? <ErrorState message={error} /> : null}

        <Card className="overflow-hidden p-0">
          {loading ? (
            <div className="p-4">
              <LoadingState message="Loading review queue..." />
            </div>
          ) : (
            <DataTable
              columns={[
                { key: "filename", title: "Filename" },
                { key: "type", title: "Type" },
                { key: "status", title: "Status" },
                { key: "confidence", title: "Confidence" },
                { key: "created", title: "Created" },
              ]}
              rows={rows}
              emptyMessage="No pending documents in the review queue."
            />
          )}
        </Card>

        {selectedDocument && selectedExtraction ? (
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <h2 className="text-lg font-semibold text-ink">Selected document</h2>
              <p className="mt-2 text-sm text-slate-700">{selectedDocument.original_filename}</p>
              <p className="text-sm text-slate-600">Type: {selectedDocument.document_type}</p>
              <p className="text-sm text-slate-600">Confidence: {formatConfidence(selectedDocument.ai_confidence_score)}</p>
              <p className="text-sm text-slate-600">Status: {selectedDocument.status}</p>
              <p className="text-sm text-slate-600">Created: {formatDate(selectedDocument.created_at)}</p>
            </Card>

            <Card>
              <h2 className="text-lg font-semibold text-ink">Review decision</h2>
              <label htmlFor="reviewer_comment" className="mt-3 block text-sm font-medium text-slate-700">
                Reviewer comment
              </label>
              <textarea
                id="reviewer_comment"
                className="input mt-1 min-h-[90px]"
                value={reviewerComment}
                onChange={(event) => setReviewerComment(event.target.value)}
                placeholder="Add approval/rejection context"
              />
              <div className="mt-3 flex flex-wrap gap-2">
                <Button onClick={() => onDecision("approve")} disabled={actionLoading}>
                  {actionLoading ? "Saving..." : "Approve"}
                </Button>
                <Button variant="danger" onClick={() => onDecision("reject")} disabled={actionLoading}>
                  {actionLoading ? "Saving..." : "Reject"}
                </Button>
              </div>
            </Card>

            <Card className="lg:col-span-2">
              <h2 className="text-lg font-semibold text-ink">Structured fields editor</h2>
              <p className="mt-1 text-sm text-slate-600">Edit extracted fields as JSON and submit via PATCH review endpoint.</p>
              <form onSubmit={onPatchFields}>
                <textarea
                  className="mt-3 min-h-[260px] w-full rounded-xl border border-slate-300 bg-slate-50 p-3 font-mono text-xs text-slate-700 focus:border-accent focus:outline-none focus:ring-2 focus:ring-blue-100"
                  value={fieldsDraft}
                  onChange={(event) => setFieldsDraft(event.target.value)}
                />
                <div className="mt-3 flex gap-2">
                  <Button type="submit" variant="secondary" disabled={actionLoading}>
                    Update fields
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => setFieldsDraft(safeStringify(selectedExtraction.structured_fields))}
                    disabled={actionLoading}
                  >
                    Reset
                  </Button>
                </div>
              </form>
            </Card>
          </div>
        ) : null}
      </div>
    </Layout>
  );
}
