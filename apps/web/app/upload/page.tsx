"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { Layout } from "@/components/Layout";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { ErrorState } from "@/components/ErrorState";
import { api, ApiError } from "@/lib/api";
import { getAuthToken } from "@/lib/auth";

const ACCEPTED_EXTENSIONS = ["txt", "pdf", "docx"];

export default function UploadPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const stored = getAuthToken();
    if (!stored) {
      router.replace("/login");
      return;
    }
    setToken(stored);
  }, [router]);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!file || !token) {
      return;
    }

    const extension = file.name.split(".").pop()?.toLowerCase();
    if (!extension || !ACCEPTED_EXTENSIONS.includes(extension)) {
      setError("Unsupported file type. Use TXT, PDF, or DOCX.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const document = await api.uploadDocument(file, token);
      router.push(`/documents/${document.id}`);
    } catch (err) {
      if (err instanceof ApiError && (err.status === 400 || err.status === 413)) {
        setError(err.message);
      } else if (err instanceof ApiError && err.status === 401) {
        router.replace("/login");
      } else if (err instanceof ApiError && err.status === 403) {
        setError("You do not have permission to upload documents.");
      } else if (err instanceof ApiError && err.status === 409) {
        setError(err.message);
      } else {
        setError(err instanceof Error ? err.message : "Failed to upload document.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout title="Upload" description="Submit business documents for extraction and review.">
      <Card className="max-w-2xl">
        <h2 className="text-lg font-semibold text-ink">Upload document</h2>
        <p className="mt-1 text-sm text-slate-600">Supported formats: TXT, PDF, DOCX.</p>

        <form className="mt-5 space-y-4" onSubmit={onSubmit}>
          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4">
            <label htmlFor="file" className="mb-2 block text-sm font-medium text-slate-700">
              Choose a file
            </label>
            <input
              id="file"
              className="input"
              type="file"
              accept=".txt,.pdf,.docx"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
            <p className="mt-2 text-xs text-slate-500">The backend applies file type and size validation from environment config.</p>
          </div>

          {error ? <ErrorState message={error} /> : null}

          <div className="flex gap-2">
            <Button type="submit" disabled={loading || !file}>
              {loading ? "Uploading and processing..." : "Upload document"}
            </Button>
            <Button type="button" variant="secondary" onClick={() => router.push("/documents")}>
              Go to documents
            </Button>
          </div>
        </form>
      </Card>
    </Layout>
  );
}
