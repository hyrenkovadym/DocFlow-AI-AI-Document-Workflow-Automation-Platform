import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col justify-center px-6 py-16">
      <p className="mb-2 text-sm font-semibold uppercase tracking-wider text-accent">DocFlow AI</p>
      <h1 className="mb-4 text-4xl font-extrabold leading-tight text-ink">
        AI-powered document intake and workflow automation.
      </h1>
      <p className="mb-8 max-w-2xl text-slate-600">
        Upload contracts, invoices, and requests. Extract structured data with AI, review with role-based workflows,
        and export approved records for operations.
      </p>
      <div className="flex gap-3">
        <Link className="btn-primary" href="/login">
          Sign in
        </Link>
        <Link className="btn-secondary" href="/register">
          Create account
        </Link>
      </div>
    </main>
  );
}
