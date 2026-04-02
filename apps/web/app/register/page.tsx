"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { register } from "@/lib/api/client";
import { setToken } from "@/lib/session";
import { StatusMessage } from "@/components/StatusMessage";

export default function RegisterPage() {
  const [values, setValues] = useState({
    email: "",
    password: "",
    workspaceName: "",
    fullName: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  function handleChange(event: React.ChangeEvent<HTMLInputElement>) {
    setValues((prev) => ({ ...prev, [event.target.name]: event.target.value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await register({
        email: values.email,
        password: values.password,
        workspace_name: values.workspaceName,
        full_name: values.fullName,
      });
      setToken(response.access_token);
      router.replace("/cases");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Cannot register");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-8 shadow-lg shadow-slate-400/10">
      <h1 className="text-2xl font-semibold text-slate-900">Create workspace</h1>
      <p className="mt-2 text-sm text-slate-500">
        Register a workspace to start building claims.
      </p>
      <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
        <label className="block text-sm font-medium text-slate-600">
          Full name
          <input
            className="mt-1 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-900 focus:border-slate-800 focus:outline-none"
            name="fullName"
            value={values.fullName}
            onChange={handleChange}
            required
          />
        </label>
        <label className="block text-sm font-medium text-slate-600">
          Workspace name
          <input
            className="mt-1 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-900 focus:border-slate-800 focus:outline-none"
            name="workspaceName"
            value={values.workspaceName}
            onChange={handleChange}
            required
          />
        </label>
        <label className="block text-sm font-medium text-slate-600">
          Email
          <input
            className="mt-1 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-900 focus:border-slate-800 focus:outline-none"
            type="email"
            name="email"
            value={values.email}
            onChange={handleChange}
            required
          />
        </label>
        <label className="block text-sm font-medium text-slate-600">
          Password
          <input
            className="mt-1 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-900 focus:border-slate-800 focus:outline-none"
            type="password"
            name="password"
            value={values.password}
            onChange={handleChange}
            required
          />
        </label>
        {error && <StatusMessage variant="error">{error}</StatusMessage>}
        <button
          className="w-full rounded-2xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
          type="submit"
          disabled={loading}
        >
          {loading ? "Creating..." : "Create workspace"}
        </button>
      </form>
      <p className="mt-4 text-xs text-slate-500">
        Already have access?{" "}
        <Link className="text-slate-900 underline" href="/login">
          Sign in
        </Link>
      </p>
    </section>
  );
}
