"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

const nav = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/reviews", label: "Review Queue" },
  { href: "/audit", label: "Audit Logs" },
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[260px_1fr]">
      <aside className="border-b border-slate-200 bg-white/90 p-6 lg:border-b-0 lg:border-r">
        <div className="mb-8">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">DocFlow AI</p>
          <h2 className="mt-2 text-xl font-extrabold text-ink">Operations Console</h2>
        </div>
        <nav className="space-y-2">
          {nav.map((item) => {
            const active = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`block rounded-xl px-3 py-2 text-sm font-medium transition ${
                  active ? "bg-blue-50 text-accent" : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <button
          className="btn-secondary mt-10 w-full"
          onClick={() => {
            localStorage.removeItem("docflow_token");
            localStorage.removeItem("docflow_user_role");
            router.push("/login");
          }}
        >
          Log out
        </button>
      </aside>
      <section className="p-4 lg:p-8">{children}</section>
    </div>
  );
}
