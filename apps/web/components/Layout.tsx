"use client";

import { ReactNode } from "react";
import { useRouter } from "next/navigation";

import { clearAuthSession, getStoredRole } from "@/lib/auth";
import { UserRole } from "@/lib/types";
import { Sidebar } from "@/components/Sidebar";
import { Button } from "@/components/Button";

interface LayoutProps {
  title: string;
  description?: string;
  children: ReactNode;
}

export function Layout({ title, description, children }: LayoutProps) {
  const router = useRouter();
  const role: UserRole | null = getStoredRole();

  return (
    <div className="min-h-screen bg-bg lg:grid lg:grid-cols-[250px_1fr]">
      <Sidebar />
      <main className="p-4 sm:p-6 lg:p-8">
        <header className="mb-6 flex flex-wrap items-start justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div>
            <h1 className="text-2xl font-bold text-ink">{title}</h1>
            {description ? <p className="mt-1 text-sm text-slate-600">{description}</p> : null}
          </div>
          <div className="flex items-center gap-3">
            {role ? (
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-700">
                {role}
              </span>
            ) : null}
            <Button
              variant="secondary"
              onClick={() => {
                clearAuthSession();
                router.push("/login");
              }}
            >
              Log out
            </Button>
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
