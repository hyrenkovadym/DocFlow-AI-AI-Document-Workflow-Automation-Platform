"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { Layout } from "@/components/Layout";
import { Card } from "@/components/Card";
import { LoadingState } from "@/components/LoadingState";
import { ErrorState } from "@/components/ErrorState";
import { api, ApiError } from "@/lib/api";
import { getAuthToken } from "@/lib/auth";
import { DocumentItem } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const stored = getAuthToken();
    if (!stored) {
      router.replace("/login");
      return;
    }
    setToken(stored);
  }, [router]);

  useEffect(() => {
    if (!token) {
      return;
    }

    (async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await api.listDocuments(token);
        setDocuments(response.items);
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          setError("Session expired. Please sign in again.");
          router.replace("/login");
          return;
        }
        setError(err instanceof Error ? err.message : "Failed to load dashboard.");
      } finally {
        setLoading(false);
      }
    })();
  }, [router, token]);

  const metrics = useMemo(() => {
    const total = documents.length;
    const pendingReview = documents.filter((document) => document.status === "needs_review").length;
    const approved = documents.filter((document) => document.status === "approved").length;
    const failed = documents.filter((document) => document.status === "failed").length;
    return { total, pendingReview, approved, failed };
  }, [documents]);

  return (
    <Layout title="Dashboard" description="Monitor document intake and review workload.">
      {loading ? <LoadingState message="Loading dashboard metrics..." /> : null}
      {error ? <ErrorState message={error} /> : null}

      {!loading ? (
        <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Total documents" value={metrics.total} />
            <MetricCard label="Pending review" value={metrics.pendingReview} />
            <MetricCard label="Approved" value={metrics.approved} />
            <MetricCard label="Failed" value={metrics.failed} />
          </section>

          <section className="mt-6 grid gap-4 md:grid-cols-3">
            <ActionCard href="/upload" title="Upload a document" description="Submit TXT, PDF, or DOCX files for processing." />
            <ActionCard href="/documents" title="Browse documents" description="Inspect status, confidence, and processing results." />
            <ActionCard href="/reviews" title="Open review queue" description="Approve or reject extracted records." />
          </section>
        </>
      ) : null}
    </Layout>
  );
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-bold text-ink">{value}</p>
    </Card>
  );
}

function ActionCard({ href, title, description }: { href: string; title: string; description: string }) {
  return (
    <Card>
      <h2 className="text-base font-semibold text-ink">{title}</h2>
      <p className="mt-1 text-sm text-slate-600">{description}</p>
      <Link href={href} className="mt-4 inline-flex text-sm font-semibold text-accent hover:underline">
        Open
      </Link>
    </Card>
  );
}
