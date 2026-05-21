"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { Layout } from "@/components/Layout";
import { Card } from "@/components/Card";
import { DataTable } from "@/components/DataTable";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/Button";
import { api, ApiError } from "@/lib/api";
import { getAuthToken } from "@/lib/auth";
import { DocumentItem } from "@/lib/types";
import { formatConfidence, formatDate } from "@/lib/utils";

export default function DocumentsPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDocuments = useCallback(async (authToken: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.listDocuments(authToken);
      setDocuments(response.items);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.replace("/login");
        return;
      }
      setError(err instanceof Error ? err.message : "Failed to load documents.");
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    const stored = getAuthToken();
    if (!stored) {
      router.replace("/login");
      return;
    }
    setToken(stored);
    loadDocuments(stored);
  }, [loadDocuments, router]);

  const rows = useMemo(
    () =>
      documents.map((document) => ({
        filename: (
          <Link href={`/documents/${document.id}`} className="font-semibold text-accent hover:underline">
            {document.original_filename}
          </Link>
        ),
        document_type: <span className="uppercase tracking-wide text-slate-600">{document.document_type}</span>,
        status: <StatusBadge status={document.status} />,
        confidence: formatConfidence(document.ai_confidence_score),
        created: formatDate(document.created_at),
        actions: (
          <div className="flex flex-wrap gap-2">
            <Link href={`/documents/${document.id}`} className="text-sm font-semibold text-accent hover:underline">
              View
            </Link>
            {document.status === "approved" && token ? (
              <button
                className="text-sm font-semibold text-emerald-700 hover:underline"
                onClick={async () => {
                  try {
                    const payload = await api.exportDocumentJson(document.id, token);
                    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
                    const url = URL.createObjectURL(blob);
                    const anchor = window.document.createElement("a");
                    anchor.href = url;
                    anchor.download = `${document.original_filename}.export.json`;
                    anchor.click();
                    URL.revokeObjectURL(url);
                    await loadDocuments(token);
                  } catch (err) {
                    setError(err instanceof Error ? err.message : "Export failed.");
                  }
                }}
              >
                Export JSON
              </button>
            ) : null}
          </div>
        ),
      })),
    [documents, loadDocuments, token],
  );

  return (
    <Layout title="Documents" description="Track ingestion status and open each document workflow record.">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-600">All accessible documents for your role.</p>
          <Button variant="secondary" onClick={() => (token ? loadDocuments(token) : null)}>
            Refresh
          </Button>
        </div>

        {error ? <ErrorState message={error} /> : null}

        <Card className="overflow-hidden p-0">
          {loading ? (
            <div className="p-4">
              <LoadingState message="Loading documents..." />
            </div>
          ) : (
            <DataTable
              columns={[
                { key: "filename", title: "Filename" },
                { key: "document_type", title: "Document type" },
                { key: "status", title: "Status" },
                { key: "confidence", title: "Confidence score" },
                { key: "created", title: "Created date" },
                { key: "actions", title: "Actions" },
              ]}
              rows={rows}
              emptyMessage="No documents found. Upload your first file from the Upload page."
            />
          )}
        </Card>
      </div>
    </Layout>
  );
}
