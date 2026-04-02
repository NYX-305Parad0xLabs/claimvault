"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { CaseSummary, fetchCases } from "@/lib/api/client";
import { getToken } from "@/lib/session";
import { Loader } from "@/components/Loader";
import { StatusMessage } from "@/components/StatusMessage";
import { claimContract } from "@/lib/contracts/claimContract";

const claimStatuses = claimContract.properties.status.enum;

export default function CasesPage() {
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      return;
    }
    fetchCases()
      .then(setCases)
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Unable to load cases");
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <section>
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold text-slate-900">Cases</h1>
        <p className="text-sm text-slate-500">Tracked claims built with strict contracts.</p>
      </div>

      {loading && (
        <div className="mt-4">
          <Loader />
        </div>
      )}

      {error && (
        <div className="mt-4">
          <StatusMessage variant="error">{error}</StatusMessage>
        </div>
      )}

      {!loading && !cases.length && !error && (
        <StatusMessage>No cases were found for this workspace yet.</StatusMessage>
      )}

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {cases.map((item) => (
          <Link
            href={`/cases/${item.id}`}
            key={item.id}
            className="group rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-slate-900"
          >
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
                {item.claim_type}
              </p>
              <span className="rounded-full border border-slate-200 px-3 py-1 text-[11px] font-semibold text-slate-600">
                {item.status}
              </span>
            </div>
            <h2 className="mt-3 text-xl font-semibold text-slate-900">{item.title}</h2>
            <p className="mt-2 text-sm text-slate-500 line-clamp-3">{item.summary || "No summary provided."}</p>
            <div className="mt-4 flex items-center justify-between text-xs uppercase tracking-[0.3em] text-slate-400">
              <span>{item.merchant_name ?? "Unknown merchant"}</span>
              <span>{new Date(item.updated_at).toLocaleDateString()}</span>
            </div>
          </Link>
        ))}
      </div>

      <div className="mt-8 rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
        ClaimVault uses the shared claim contract (status enums: {claimStatuses.join(", ")}) so front-end and
        backend expectations never diverge.
      </div>
    </section>
  );
}
