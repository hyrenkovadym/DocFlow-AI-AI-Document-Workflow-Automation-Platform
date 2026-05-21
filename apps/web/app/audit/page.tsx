"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { api } from "@/lib/api";
import { AuditLogItem } from "@/types/index";

export default function AuditPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
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
        const rows = await api.listAuditLogs(token);
        setLogs(rows);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load audit logs");
      }
    })();
  }, [token]);

  return (
    <AppShell>
      <div className="space-y-6">
        <header>
          <h1 className="text-2xl font-extrabold">Audit Logs</h1>
          <p className="text-sm text-slate-600">Trace critical events across document lifecycle and user actions.</p>
        </header>

        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        <section className="card overflow-hidden">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Time</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Entity</th>
                <th className="px-4 py-3">Actor</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr className="border-t border-slate-100" key={log.id}>
                  <td className="px-4 py-3 text-slate-600">{new Date(log.created_at).toLocaleString()}</td>
                  <td className="px-4 py-3 font-medium">{log.action}</td>
                  <td className="px-4 py-3 text-slate-600">
                    {log.entity_type}:{log.entity_id}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{log.actor_id ?? "system"}</td>
                </tr>
              ))}
              {logs.length === 0 ? (
                <tr>
                  <td className="px-4 py-8 text-center text-slate-500" colSpan={4}>
                    No audit events found.
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
