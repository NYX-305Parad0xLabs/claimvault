"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { CaseDetail, fetchCase } from "@/lib/api/client";
import { getToken } from "@/lib/session";
import { Loader } from "@/components/Loader";
import { StatusMessage } from "@/components/StatusMessage";

type Props = {
  params: { id: string };
};

export default function CaseDetailPage({ params }: Props) {
  const [caseDetail, setCaseDetail] = useState<CaseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      return;
    }
    fetchCase(params.id)
      .then(setCaseDetail)
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Unable to load case");
      })
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6">
        <Loader />
      </div>
    );
  }

  if (error) {
    return (
      <StatusMessage variant="error">
        {error}.{" "}
        <Link className="text-slate-900 underline" href="/cases">
          Back to list
        </Link>
      </StatusMessage>
    );
  }

  if (!caseDetail) {
    return (
      <StatusMessage>
        Case not found.{" "}
        <Link className="text-slate-900 underline" href="/cases">
          Return to cases
        </Link>
      </StatusMessage>
    );
  }

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-900/5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-3xl font-semibold text-slate-900">{caseDetail.title}</h1>
        <span className="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold uppercase tracking-[0.3em] text-slate-600">
          {caseDetail.status}
        </span>
      </div>
      <p className="mt-3 text-sm uppercase tracking-[0.2em] text-slate-500">{caseDetail.claim_type}</p>
      <dl className="mt-6 grid gap-4 md:grid-cols-2">
        <div>
          <dt className="text-xs uppercase tracking-[0.2em] text-slate-500">Merchant</dt>
          <dd className="text-base font-semibold text-slate-900">
            {caseDetail.merchant_name ?? "Unknown"}
          </dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-[0.2em] text-slate-500">Order ref</dt>
          <dd className="text-base font-semibold text-slate-900">
            {caseDetail.order_reference ?? "N/A"}
          </dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-[0.2em] text-slate-500">Amount</dt>
          <dd className="text-base font-semibold text-slate-900">
            {caseDetail.amount_value} USD
          </dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-[0.2em] text-slate-500">Created</dt>
          <dd className="text-base font-semibold text-slate-900">
            {new Date(caseDetail.created_at).toLocaleDateString()}
          </dd>
        </div>
      </dl>
      <section className="mt-6 rounded-2xl border border-slate-100 bg-slate-50 p-4 text-sm text-slate-600">
        <h2 className="mb-2 text-xs uppercase tracking-[0.3em] text-slate-500">Summary</h2>
        <p>{caseDetail.summary || "No summary recorded."}</p>
      </section>
    </article>
  );
}
