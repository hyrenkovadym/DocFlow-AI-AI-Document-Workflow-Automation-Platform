"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { getStoredRole } from "@/lib/auth";
import { UserRole } from "@/lib/types";
import { cn } from "@/lib/utils";

interface NavItem {
  href: string;
  label: string;
  roles?: UserRole[];
}

const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/documents", label: "Documents" },
  { href: "/upload", label: "Upload" },
  { href: "/reviews", label: "Review Queue", roles: ["reviewer", "admin"] },
  { href: "/audit-logs", label: "Audit Logs", roles: ["admin"] },
];

export function Sidebar() {
  const pathname = usePathname();
  const role = getStoredRole();

  return (
    <aside className="border-b border-slate-200 bg-white px-4 py-5 lg:min-h-screen lg:border-b-0 lg:border-r lg:px-5 lg:py-8">
      <div className="mb-6">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">DocFlow AI</p>
        <p className="mt-2 text-lg font-bold text-ink">Workflow Console</p>
      </div>
      <nav className="grid gap-1">
        {NAV_ITEMS.filter((item) => {
          if (!item.roles || item.roles.length === 0) {
            return true;
          }
          if (!role) {
            return false;
          }
          return item.roles.includes(role);
        }).map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "rounded-xl px-3 py-2 text-sm font-medium transition",
                active ? "bg-blue-50 text-accent" : "text-slate-700 hover:bg-slate-100",
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
