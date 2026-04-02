type StatusMessageProps = {
  variant?: "info" | "error";
  children: React.ReactNode;
};

export function StatusMessage({ variant = "info", children }: StatusMessageProps) {
  const colors =
    variant === "error"
      ? "bg-rose-50 border-rose-200 text-rose-700"
      : "bg-slate-50 border-slate-200 text-slate-700";
  return (
    <div className={`rounded-2xl border px-4 py-3 text-sm ${colors}`}>
      {children}
    </div>
  );
}
