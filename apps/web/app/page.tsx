"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { getAuthToken } from "@/lib/auth";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    const token = getAuthToken();
    if (token) {
      router.replace("/dashboard");
      return;
    }
    router.replace("/login");
  }, [router]);

  return <main className="flex min-h-screen items-center justify-center text-slate-500">Redirecting...</main>;
}
