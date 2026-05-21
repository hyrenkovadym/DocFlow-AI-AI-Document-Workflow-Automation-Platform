"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { Layout } from "@/components/Layout";
import { Card } from "@/components/Card";
import { DataTable } from "@/components/DataTable";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { api, ApiError } from "@/lib/api";
import { getAuthToken } from "@/lib/auth";
import { AuditLogItem } from "@/lib/types";
import { formatDate, safeStringify } from "@/lib/utils";

export default function AuditLogsPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
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
        const response = await api.listAuditLogs(token);
        setLogs(response);
      } catch (err) {
        if (err instanceof ApiError && err.status === 403) {
          setError("Audit logs are available only for admin role.");
          return;
        }
        if (err instanceof ApiError && err.status === 401) {
          router.replace("/login");
          return;
        }
        setError(err instanceof Error ? err.message : "Failed to load audit logs.");
      } finally {
        setLoading(false);
      }
    })();
  }, [router, token]);

  const rows = useMemo(
    () =>
      logs.map((log) => ({
        created_at: formatDate(log.created_at),
        action: <span className="font-semibold text-slate-800">{log.action}</span>,
        entity: (
          <span className="text-slate-700">
            {log.entity_type}:{log.entity_id}
          </span>
        ),
        actor: log.actor_id ?? "system",
        metadata: <pre className="max-w-[320px] overflow-auto whitespace-pre-wrap text-xs">{safeStringify(log.metadata_json)}</pre>,
      })),
    [logs],
  );

  return (
    <Layout title="Audit Logs" description="Admin visibility into workflow lifecycle and user actions.">
      {error ? <ErrorState message={error} /> : null}
      <Card className="overflow-hidden p-0">
        {loading ? (
          <div className="p-4">
            <LoadingState message="Loading audit log events..." />
          </div>
        ) : (
          <DataTable
            columns={[
              { key: "created_at", title: "Created" },
              { key: "action", title: "Action" },
              { key: "entity", title: "Entity" },
              { key: "actor", title: "Actor" },
              { key: "metadata", title: "Metadata" },
            ]}
            rows={rows}
            emptyMessage="No audit events available."
          />
        )}
      </Card>
    </Layout>
  );
}
