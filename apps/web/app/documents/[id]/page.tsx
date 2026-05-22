"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { Layout } from "@/components/Layout";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { StatusBadge } from "@/components/StatusBadge";
import { api, ApiError } from "@/lib/api";
import { getAuthToken } from "@/lib/auth";
import { DocumentDetail, DocumentExtractionResponse } from "@/lib/types";
import { formatConfidence, formatDate, safeStringify } from "@/lib/utils";

export default function DocumentDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const documentId = params.id;

  const [token, setToken] = useState<string | null>(null);
  const [documentData, setDocumentData] = useState<DocumentDetail | null>(null);
  const [extractedText, setExtractedText] = useState<string>("");
  const [extraction, setExtraction] = useState<DocumentExtractionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyAction, setBusyAction] = useState<"reprocess" | "export" | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDocument = useCallback(async (authToken: string, options: { silent?: boolean } = {}) => {
    if (!options.silent) {
      setLoading(true);
      setError(null);
    }
    try {
      const [doc, textResponse] = await Promise.all([
        api.getDocument(documentId, authToken),
        api.getDocumentText(documentId, authToken).catch(() => ({ document_id: documentId, text: "" })),
      ]);

      setDocumentData(doc);
      setExtractedText(textResponse.text || doc.extracted_text || "");

      try {
        const extractionResponse = await api.getExtraction(documentId, authToken);
        setExtraction(extractionResponse);
      } catch {
        setExtraction(null);
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.replace("/login");
        return;
      }
      setError(err instanceof Error ? err.message : "Failed to load document details.");
    } finally {
      if (!options.silent) {
        setLoading(false);
      }
    }
  }, [documentId, router]);

  useEffect(() => {
    const stored = getAuthToken();
    if (!stored) {
      router.replace("/login");
      return;
    }
    setToken(stored);
    loadDocument(stored);
  }, [loadDocument, router]);

  useEffect(() => {
    if (!token || !documentData) {
      return;
    }
    if (documentData.status !== "queued" && documentData.status !== "processing") {
      return;
    }

    const pollInterval = window.setInterval(() => {
      loadDocument(token, { silent: true });
    }, 5000);

    return () => window.clearInterval(pollInterval);
  }, [documentData, loadDocument, token]);

  const onRefresh = async () => {
    if (!token) {
      return;
    }
    setRefreshing(true);
    setError(null);
    try {
      await loadDocument(token);
    } finally {
      setRefreshing(false);
    }
  };

  const onReprocess = async () => {
    if (!token) {
      return;
    }
    setBusyAction("reprocess");
    setError(null);
    try {
      await api.reprocessDocument(documentId, token);
      await loadDocument(token);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.replace("/login");
        return;
      }
      if (err instanceof ApiError && err.status === 403) {
        setError("You do not have permission to reprocess this document.");
        return;
      }
      if (err instanceof ApiError && err.status === 409) {
        setError(err.message);
        return;
      }
      setError(err instanceof Error ? err.message : "Failed to reprocess document.");
    } finally {
      setBusyAction(null);
    }
  };

  const onExport = async () => {
    if (!token) {
      return;
    }
    setBusyAction("export");
    setError(null);
    try {
      const payload = await api.exportDocumentJson(documentId, token);
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const anchor = window.document.createElement("a");
      anchor.href = url;
      anchor.download = `${documentData?.original_filename ?? documentId}.export.json`;
      anchor.click();
      URL.revokeObjectURL(url);
      await loadDocument(token);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.replace("/login");
        return;
      }
      if (err instanceof ApiError && err.status === 403) {
        setError("You do not have permission to export this document.");
        return;
      }
      if (err instanceof ApiError && err.status === 409) {
        setError(err.message);
        return;
      }
      setError(err instanceof Error ? err.message : "Failed to export document.");
    } finally {
      setBusyAction(null);
    }
  };

  const isLowConfidence = documentData?.metadata_json?.below_threshold === true;
  const aiProviderLabel =
    typeof documentData?.metadata_json?.ai_provider === "string" ? documentData.metadata_json.ai_provider : "unknown";

  return (
    <Layout title="Document Detail" description="Inspect extracted text, structured fields, and workflow actions.">
      {loading ? <LoadingState message="Loading document..." /> : null}
      {error ? <ErrorState message={error} /> : null}

      {!loading && documentData ? (
        <div className="space-y-4">
          {isLowConfidence ? (
            <Card className="border border-amber-200 bg-amber-50">
              <p className="text-sm font-medium text-amber-900">
                Low-confidence extraction detected. Please review fields carefully before approval.
              </p>
            </Card>
          ) : null}

          <Card>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-xl font-bold text-ink">{documentData.original_filename}</h2>
                <p className="mt-1 text-sm text-slate-600">Created: {formatDate(documentData.created_at)}</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge status={documentData.status} />
                <span className="rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-slate-700">
                  {documentData.document_type}
                </span>
              </div>
            </div>

            <div className="mt-4 grid gap-3 text-sm md:grid-cols-2">
              <p>
                <span className="font-semibold text-slate-700">File type:</span> {documentData.file_type}
              </p>
              <p>
                <span className="font-semibold text-slate-700">Confidence:</span> {formatConfidence(documentData.ai_confidence_score)}
              </p>
              <p>
                <span className="font-semibold text-slate-700">AI provider:</span>{" "}
                {aiProviderLabel}
              </p>
              <p>
                <span className="font-semibold text-slate-700">Owner ID:</span> {documentData.owner_id}
              </p>
              <p>
                <span className="font-semibold text-slate-700">Updated:</span> {formatDate(documentData.updated_at)}
              </p>
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              <Button variant="secondary" onClick={onRefresh} disabled={busyAction !== null || refreshing}>
                {refreshing ? "Refreshing..." : "Refresh status"}
              </Button>
              <Button variant="secondary" onClick={onReprocess} disabled={busyAction !== null}>
                {busyAction === "reprocess" ? "Reprocessing..." : "Reprocess"}
              </Button>
              {documentData.status === "approved" || documentData.status === "exported" ? (
                <Button onClick={onExport} disabled={busyAction !== null}>
                  {busyAction === "export" ? "Exporting..." : "Export JSON"}
                </Button>
              ) : null}
            </div>

            {documentData.status === "queued" || documentData.status === "processing" ? (
              <p className="mt-3 text-sm text-slate-600">Processing is running in the background. Refresh status to see updates.</p>
            ) : null}
          </Card>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <h3 className="text-base font-semibold text-ink">Extracted Text</h3>
              <pre className="mt-3 max-h-[460px] overflow-auto whitespace-pre-wrap rounded-xl bg-slate-50 p-3 text-xs text-slate-700">
                {extractedText || "No extracted text available."}
              </pre>
            </Card>
            <Card>
              <h3 className="text-base font-semibold text-ink">Structured Fields</h3>
              <pre className="mt-3 max-h-[460px] overflow-auto whitespace-pre-wrap rounded-xl bg-slate-50 p-3 text-xs text-slate-700">
                {safeStringify(extraction?.structured_fields ?? {})}
              </pre>
            </Card>
          </div>
        </div>
      ) : null}
    </Layout>
  );
}
