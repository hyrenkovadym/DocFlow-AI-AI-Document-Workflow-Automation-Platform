import { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface CardProps {
  children: ReactNode;
  className?: string;
}

export function Card({ children, className }: CardProps) {
  return <section className={cn("rounded-2xl border border-slate-200 bg-white p-4 shadow-sm", className)}>{children}</section>;
}
