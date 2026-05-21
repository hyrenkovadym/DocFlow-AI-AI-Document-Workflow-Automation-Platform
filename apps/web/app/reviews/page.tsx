"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { api } from "@/lib/api";
import { ReviewQueueItem } from "@/types/index";

export default function ReviewsPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [items, setItems] = useState<ReviewQueueItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = async (authToken: string) => {
    try {
      const queue = await api.listReviewQueue(authToken);
      setItems(queue);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load review queue");
    }
  };

  useEffect(() => {
    const storedToken = localStorage.getItem("docflow_token");
    if (!storedToken) {
      router.push("/login");
      return;
    }
    setToken(storedToken);
    load(storedToken);
  }, [router]);

  const decide = async (documentId: string, decision: "approve" | "reject") => {
    if (!token) return;
    try {
      if (decision === "approve") {
        await api.approveReview(documentId, token, "Approved from UI");
      } else {
        await api.rejectReview(documentId, token, "Rejected from UI");
      }
      await load(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Decision failed");
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <header>
          <h1 className="text-2xl font-extrabold">Review Queue</h1>
          <p className="text-sm text-slate-600">Reviewer/Admin actions for AI-extracted documents.</p>
        </header>

        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        <section className="card overflow-hidden">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Document</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Confidence</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr className="border-t border-slate-100" key={item.document_id}>
                  <td className="px-4 py-3 font-medium">{item.filename}</td>
                  <td className="px-4 py-3">{item.document_type}</td>
                  <td className="px-4 py-3">{item.confidence_score?.toFixed?.(2) ?? "n/a"}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button className="btn-primary" onClick={() => decide(item.document_id, "approve")}>
                        Approve
                      </button>
                      <button className="btn-secondary" onClick={() => decide(item.document_id, "reject")}>
                        Reject
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.length === 0 ? (
                <tr>
                  <td className="px-4 py-8 text-center text-slate-500" colSpan={4}>
                    No items in the review queue.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </section>
      </div>
    </AppShell>
  );
}
