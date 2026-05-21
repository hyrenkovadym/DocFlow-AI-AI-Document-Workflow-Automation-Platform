"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { api } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await api.register({ full_name: fullName, email, password });
      router.push("/login");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-md items-center px-6">
      <section className="card w-full p-6">
        <h1 className="text-2xl font-bold">Create account</h1>
        <p className="mt-1 text-sm text-slate-500">Start uploading and automating business documents.</p>
        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <div>
            <label className="mb-1 block text-sm font-medium">Full name</label>
            <input
              className="input"
              required
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Email</label>
            <input className="input" type="email" required value={email} onChange={(event) => setEmail(event.target.value)} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Password</label>
            <input
              className="input"
              type="password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>
          {error ? <p className="text-sm text-red-600">{error}</p> : null}
          <button className="btn-primary w-full" disabled={loading} type="submit">
            {loading ? "Creating account..." : "Create account"}
          </button>
        </form>
        <p className="mt-4 text-sm text-slate-600">
          Already registered? <Link href="/login" className="font-semibold text-accent">Sign in</Link>
        </p>
      </section>
    </main>
  );
}
