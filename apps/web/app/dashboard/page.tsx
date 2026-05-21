"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { StatusBadge } from "@/components/status-badge";
import { api } from "@/lib/api";
import { DocumentItem } from "@/types/index";

export default function DashboardPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = localStorage.getItem("docflow_token");
    if (!storedToken) {
      router.push("/login");
      return;
    }
    setToken(storedToken);
  }, [router]);

  const loadDocuments = async (authToken: string) => {
    try {
      const payload = await api.listDocuments(authToken);
      setDocuments(payload.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load documents");
    }
  };

  useEffect(() => {
    if (!token) return;
    loadDocuments(token);
  }, [token]);

  const metrics = useMemo(() => {
    const total = documents.length;
    const pendingReview = documents.filter((doc) => doc.status === "needs_review").length;
    const approved = documents.filter((doc) => doc.status === "approved").length;
    const failed = documents.filter((doc) => doc.status === "failed").length;
    return { total, pendingReview, approved, failed };
  }, [documents]);

  const onUpload = async (event: FormEvent) => {
    event.preventDefault();
    if (!file || !token) return;

    setLoading(true);
    setError(null);
    try {
      await api.uploadDocument(file, token);
      setFile(null);
      await loadDocuments(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <header>
          <h1 className="text-2xl font-extrabold">Document Operations Dashboard</h1>
          <p className="text-sm text-slate-600">Upload files, monitor processing, and move records to review and export.</p>
        </header>

        <section className="grid gap-4 md:grid-cols-4">
          <MetricCard label="Total documents" value={metrics.total} />
          <MetricCard label="Pending review" value={metrics.pendingReview} />
          <MetricCard label="Approved" value={metrics.approved} />
          <MetricCard label="Failed" value={metrics.failed} />
        </section>

        <section className="card p-5">
          <h2 className="text-lg font-bold">Upload Document</h2>
          <p className="mb-4 mt-1 text-sm text-slate-500">Supported formats: PDF, DOCX, TXT.</p>
          <form className="flex flex-col gap-3 md:flex-row" onSubmit={onUpload}>
            <input
              className="input"
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
            <button className="btn-primary" disabled={!file || loading} type="submit">
              {loading ? "Uploading..." : "Upload"}
            </button>
          </form>
          {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
        </section>

        <section className="card overflow-hidden">
          <div className="border-b border-slate-200 p-4">
            <h2 className="text-lg font-bold">Documents</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3">File</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Confidence</th>
                  <th className="px-4 py-3">Created</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr className="border-t border-slate-100" key={doc.id}>
                    <td className="px-4 py-3 font-medium text-slate-800">
                      <Link className="text-accent hover:underline" href={`/documents/${doc.id}`}>
                        {doc.original_filename}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{doc.document_type}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={doc.status} />
                    </td>
                    <td className="px-4 py-3 text-slate-600">{doc.ai_confidence_score?.toFixed(2) ?? "n/a"}</td>
                    <td className="px-4 py-3 text-slate-600">{new Date(doc.created_at).toLocaleString()}</td>
                  </tr>
                ))}
                {documents.length === 0 ? (
                  <tr>
                    <td className="px-4 py-8 text-center text-slate-500" colSpan={5}>
                      No documents yet. Upload your first one.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </AppShell>
  );
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <article className="card p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-extrabold text-ink">{value}</p>
    </article>
  );
}
