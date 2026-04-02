"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  CaseCreateRequest,
  CaseFilter,
  CaseSummary,
  createCase,
  fetchCases,
} from "@/lib/api/client";
import { getToken } from "@/lib/session";
import { Loader } from "@/components/Loader";
import { StatusMessage } from "@/components/StatusMessage";
import { claimContract } from "@/lib/contracts/claimContract";

const claimTypes = [
  { value: "", label: "All claim types" },
  { value: "return", label: "Return" },
  { value: "dispute", label: "Dispute" },
  { value: "warranty", label: "Warranty" },
];

const statusOptions = [
  { value: "", label: "All statuses" },
  ...claimContract.properties.status.enum.map((entry: string) => ({
    value: entry,
    label: entry.replace(/_/g, " "),
  })),
];

export default function CasesPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formValues, setFormValues] = useState({
    title: "",
    comment: "",
    claim_type: "return",
    merchant_name: "",
    due_date: "",
  });
  const [submitting, setSubmitting] = useState(false);

  const filters: CaseFilter = useMemo(
    () => ({
      status: searchParams.get("status") ?? undefined,
      claim_type: searchParams.get("claim_type") ?? undefined,
    }),
    [searchParams]
  );

  const loadCases = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const items = await fetchCases(filters);
      setCases(items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load cases");
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    if (!getToken()) {
      setError("Authenticate to view cases.");
      setLoading(false);
      return;
    }
    loadCases();
  }, [loadCases]);

  function updateFilter(key: "status" | "claim_type", value: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    const query = params.toString();
    router.push(`/cases${query ? `?${query}` : ""}`);
  }

  async function handleCreateCase(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!formValues.title || !formValues.comment || !formValues.claim_type) {
      setFormError("Title, type, and summary are required.");
      return;
    }
    setSubmitting(true);
    setFormError(null);
    try {
      const payload: CaseCreateRequest = {
        title: formValues.title,
        claim_type: formValues.claim_type,
        summary: formValues.comment,
        merchant_name: formValues.merchant_name || undefined,
        due_date: formValues.due_date || undefined,
      };
      const created = await createCase(payload);
      setCases((prev) => [created, ...prev]);
      setModalOpen(false);
      setFormValues({
        title: "",
        comment: "",
        claim_type: "return",
        merchant_name: "",
        due_date: "",
      });
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Unable to create case");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-slate-900">Cases</h1>
          <p className="text-sm text-slate-500">
            Managed claims filtered by status or type.
          </p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="rounded-full bg-slate-900 px-5 py-2 text-xs font-semibold uppercase tracking-[0.4em] text-white transition hover:bg-slate-800"
        >
          New case
        </button>
      </div>

      <div className="grid gap-3 rounded-2xl border border-slate-200 bg-white/60 p-4 shadow-sm shadow-slate-900/5 md:grid-cols-2">
        <label className="space-y-1 text-xs font-semibold uppercase tracking-[0.4em] text-slate-500">
          Status
          <select
            value={filters.status ?? ""}
            onChange={(event) => updateFilter("status", event.target.value)}
            className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700"
          >
            {statusOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label className="space-y-1 text-xs font-semibold uppercase tracking-[0.4em] text-slate-500">
          Claim type
          <select
            value={filters.claim_type ?? ""}
            onChange={(event) => updateFilter("claim_type", event.target.value)}
            className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700"
          >
            {claimTypes.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {loading && (
        <div className="mt-4">
          <Loader />
        </div>
      )}

      {error && <StatusMessage variant="error">{error}</StatusMessage>}

      {!loading && !cases.length && !error && (
        <StatusMessage>
          No cases match those filters yet. Use the{" "}
          <span className="font-semibold text-slate-900">New case</span> button to start one.
        </StatusMessage>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {cases.map((item) => (
          <Link
            key={item.id}
            href={`/cases/${item.id}`}
            className="group rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-slate-900"
          >
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
                {item.claim_type}
              </p>
              <span className="rounded-full border border-slate-200 px-3 py-1 text-[11px] font-semibold text-slate-600">
                {item.status.replace(/_/g, " ")}
              </span>
            </div>
            <h2 className="mt-3 text-xl font-semibold text-slate-900">{item.title}</h2>
            <p className="mt-2 text-sm text-slate-500 line-clamp-3">
              {item.summary || "No summary recorded."}
            </p>
            <div className="mt-4 grid gap-2 text-xs uppercase tracking-[0.3em] text-slate-400 sm:grid-cols-2">
              <span>{item.merchant_name ?? "Unknown merchant"}</span>
              <span>Updated {new Date(item.updated_at).toLocaleDateString()}</span>
              {item.due_date && (
                <span className="text-slate-500">
                  Due {new Date(item.due_date).toLocaleDateString()}
                </span>
              )}
            </div>
          </Link>
        ))}
      </div>

      {modalOpen && (
        <div className="fixed inset-0 z-10 flex items-center justify-center bg-black/40 px-4">
          <form
            className="w-full max-w-md space-y-4 rounded-2xl bg-white p-6 shadow-lg shadow-slate-900/20"
            onSubmit={handleCreateCase}
          >
            <h2 className="text-xl font-semibold text-slate-900">Create a case</h2>
            <label className="block text-sm font-medium text-slate-600">
              Title
              <input
                value={formValues.title}
                onChange={(event) =>
                  setFormValues((prev) => ({ ...prev, title: event.target.value }))
                }
                className="mt-1 w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 focus:border-slate-900"
                placeholder="E.g. Return - wireless earbuds"
                required
              />
            </label>
            <label className="block text-sm font-medium text-slate-600">
              Type
              <select
                value={formValues.claim_type}
                onChange={(event) =>
                  setFormValues((prev) => ({ ...prev, claim_type: event.target.value }))
                }
                className="mt-1 w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 focus:border-slate-900"
              >
                {claimTypes
                  .filter((option) => option.value)
                  .map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
              </select>
            </label>
            <label className="block text-sm font-medium text-slate-600">
              Summary
              <textarea
                value={formValues.comment}
                onChange={(event) =>
                  setFormValues((prev) => ({ ...prev, comment: event.target.value }))
                }
                className="mt-1 w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 focus:border-slate-900"
                rows={3}
                required
              />
            </label>
            <label className="block text-sm font-medium text-slate-600">
              Merchant
              <input
                value={formValues.merchant_name}
                onChange={(event) =>
                  setFormValues((prev) => ({ ...prev, merchant_name: event.target.value }))
                }
                className="mt-1 w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 focus:border-slate-900"
              />
            </label>
            <label className="block text-sm font-medium text-slate-600">
              Due date
              <input
                type="date"
                value={formValues.due_date}
                onChange={(event) =>
                  setFormValues((prev) => ({ ...prev, due_date: event.target.value }))
                }
                className="mt-1 w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 focus:border-slate-900"
              />
            </label>
            {formError && <StatusMessage variant="error">{formError}</StatusMessage>}
            <div className="flex items-center justify-between gap-2 text-sm">
              <button
                className="flex-1 rounded-2xl border border-slate-200 px-4 py-2 font-semibold text-slate-900 transition hover:border-slate-900"
                type="button"
                onClick={() => setModalOpen(false)}
              >
                Cancel
              </button>
              <button
                className="flex-1 rounded-2xl bg-slate-900 px-4 py-2 font-semibold text-white transition hover:bg-slate-800 disabled:opacity-60"
                type="submit"
                disabled={submitting}
              >
                {submitting ? "Creating..." : "Create"}
              </button>
            </div>
          </form>
        </div>
      )}
    </section>
  );
}
