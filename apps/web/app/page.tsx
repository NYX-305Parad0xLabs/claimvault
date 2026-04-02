import Link from "next/link";

export default function HomePage() {
  return (
    <section className="bg-white/80 rounded-3xl border border-slate-200 p-8 shadow-lg shadow-slate-400/10">
      <p className="text-xs uppercase tracking-[0.4em] text-slate-400">Parad0x Labs</p>
      <h1 className="mt-4 text-4xl font-semibold text-slate-900">ClaimVault</h1>
      <p className="mt-4 text-lg text-slate-600">
        ClaimVault is your teams’ claim-building shell. Capture disputes, returns, and
        warranty incidents, keep them auditable, and export concise proof bundles
        whenever decision makers are ready.
      </p>
      <div className="mt-6 flex flex-wrap gap-3">
        <Link
          className="rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
          href="/cases"
        >
          View cases
        </Link>
        <Link
          className="rounded-full border border-slate-400 px-5 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-600"
          href="/register"
        >
          Get started
        </Link>
      </div>
    </section>
  );
}
