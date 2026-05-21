"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { StatusBadge } from "@/components/status-badge";
import { api } from "@/lib/api";

export default function DocumentDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [documentData, setDocumentData] = useState<any>(null);
  const [extraction, setExtraction] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = localStorage.getItem("docflow_token");
    if (!storedToken) {
      router.push("/login");
      return;
    }
    setToken(storedToken);
  }, [router]);

  useEffect(() => {
    if (!token) return;
    (async () => {
      try {
        const doc = await api.getDocument(params.id, token);
        setDocumentData(doc);
        try {
          const ext = await api.getExtraction(params.id, token);
          setExtraction(ext);
        } catch {
          setExtraction(null);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load document");
      }
    })();
  }, [params.id, token]);

  return (
    <AppShell>
      {error ? <p className="text-red-600">{error}</p> : null}
      {!documentData ? (
        <p className="text-slate-500">Loading...</p>
      ) : (
        <div className="space-y-6">
          <section className="card p-5">
            <h1 className="text-2xl font-extrabold">{documentData.original_filename}</h1>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <StatusBadge status={documentData.status} />
              <span className="rounded-lg bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">
                {documentData.document_type}
              </span>
              <span className="text-sm text-slate-600">Confidence: {documentData.ai_confidence_score ?? "n/a"}</span>
            </div>
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            <article className="card p-5">
              <h2 className="text-lg font-bold">Extracted Text</h2>
              <pre className="mt-3 max-h-[420px] overflow-auto whitespace-pre-wrap rounded-xl bg-slate-50 p-3 text-xs text-slate-700">
                {documentData.extracted_text || "No extracted text yet."}
              </pre>
            </article>
            <article className="card p-5">
              <h2 className="text-lg font-bold">Structured Fields</h2>
              <pre className="mt-3 max-h-[420px] overflow-auto whitespace-pre-wrap rounded-xl bg-slate-50 p-3 text-xs text-slate-700">
                {JSON.stringify(extraction?.structured_fields ?? {}, null, 2)}
              </pre>
            </article>
          </section>
        </div>
      )}
    </AppShell>
  );
}
