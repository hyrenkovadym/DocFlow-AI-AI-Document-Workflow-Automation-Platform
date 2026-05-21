import { cn } from "@/lib/utils";

const STYLES: Record<string, string> = {
  uploaded: "bg-slate-100 text-slate-700",
  queued: "bg-blue-100 text-blue-800",
  processing: "bg-cyan-100 text-cyan-800",
  needs_review: "bg-amber-100 text-amber-800",
  approved: "bg-emerald-100 text-emerald-800",
  rejected: "bg-rose-100 text-rose-800",
  exported: "bg-indigo-100 text-indigo-800",
  failed: "bg-red-100 text-red-800",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold uppercase tracking-wide",
        STYLES[status] ?? "bg-slate-100 text-slate-700",
      )}
    >
      {status.replaceAll("_", " ")}
    </span>
  );
}
