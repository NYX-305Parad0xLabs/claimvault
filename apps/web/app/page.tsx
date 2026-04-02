const features = [
  "Schema-first claim ingestion with FastAPI and SQLModel",
  "Verdant dashboard that surfaces proof-of-reserve status",
  "Shared JSON contracts to keep backend + frontend in sync",
  "Bootstrap scripts + Makefile for fast local onboarding",
];

export default function Page() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <section className="space-y-4">
        <p className="text-sm uppercase tracking-[0.4em] text-slate-400">
          Parad0x Labs · ClaimVault
        </p>
        <h1 className="text-4xl font-semibold text-white">ClaimVault</h1>
        <p className="text-lg text-slate-300">
          A modern custody + compliance claim hub that keeps data typed, auditable,
          and human readable. The app pairs a FastAPI contract layer with a Next.js
          story-driven marketing surface so teams can ship proof statements with
          confidence.
        </p>
      </section>

      <section className="mt-10 space-y-4">
        <h2 className="text-2xl font-semibold text-white">Why now?</h2>
        <p className="text-slate-300">
          Compliance teams need a reliable way to transmit proof-of-reserve claims,
          catalog audits, and feed operating playbooks without reinventing the
          data contract every sprint.
        </p>
        <div className="grid gap-4 md:grid-cols-2">
          {features.map((feature) => (
            <article
              key={feature}
              className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 shadow-lg shadow-slate-900/50"
            >
              <p className="text-slate-200">{feature}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mt-12 rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <h3 className="text-xl font-semibold text-white">API Health Preview</h3>
        <p className="text-slate-400">
          Sample API routes include `/api/health` and `/api/claims`. The FastAPI
          service is wired to read contracts from `packages/contracts/schemas`,
          so whatever data the backend accepts, the Next.js frontend can render
          without drift.
        </p>
        <dl className="mt-6 grid gap-4 md:grid-cols-3">
          <div>
            <dt className="text-xs uppercase tracking-[0.2em] text-slate-500">
              backend
            </dt>
            <dd className="text-lg font-semibold text-white">FastAPI</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-[0.2em] text-slate-500">
              frontend
            </dt>
            <dd className="text-lg font-semibold text-white">Next.js 15</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-[0.2em] text-slate-500">
              contracts
            </dt>
            <dd className="text-lg font-semibold text-white">JSON Schema</dd>
          </div>
        </dl>
      </section>
    </div>
  );
}
