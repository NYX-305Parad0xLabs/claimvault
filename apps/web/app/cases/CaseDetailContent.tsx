"use client";

import {
  ChangeEvent,
  FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { Loader } from "@/components/Loader";
import { StatusMessage } from "@/components/StatusMessage";
import {
  ApiError,
  AuditEvent,
  CaseDetail,
  CaseTransitionRequest,
  EvidenceItem,
  EvidenceKind,
  ExtractionStatus,
  MAX_EVIDENCE_SIZE_BYTES,
  DISALLOWED_EVIDENCE_MIMES,
  evidenceKindOptions,
  updateEvidenceExtraction,
  createTimelineNote,
  downloadEvidence,
  fetchAuditEvents,
  fetchCase,
  fetchReadiness,
  fetchTimeline,
  listEvidence,
  transitionCase,
  updateCase,
  uploadEvidence,
  ReadinessReport,
  TimelineEvent,
  fetchCaseSummaryPreview,
} from "@/lib/api/client";
import { claimContract } from "@/lib/contracts/claimContract";

const workflowTransitions: Record<string, { value: string; label: string }[]> = {
  draft: [{ value: "collecting_evidence", label: "Start collecting evidence" }],
  collecting_evidence: [
    { value: "needs_user_input", label: "Flag missing input" },
    { value: "ready_for_export", label: "Mark ready to export" },
  ],
  needs_user_input: [{ value: "collecting_evidence", label: "Resume collecting evidence" }],
  ready_for_export: [{ value: "exported", label: "Record export" }],
  exported: [{ value: "submitted", label: "Submit proof bundle" }],
  submitted: [
    { value: "resolved", label: "Resolve case" },
    { value: "closed", label: "Close case" },
  ],
  resolved: [{ value: "closed", label: "Close case" }],
};

const statusLabels: Record<string, string> = claimContract.properties.status.enum.reduce(
  (acc, entry: string) => {
    acc[entry] = entry.replace(/_/g, " ");
    return acc;
  },
  {} as Record<string, string>
);

const kindIcons: Record<EvidenceKind, string> = {
  receipt: "🧾",
  screenshot: "📸",
  email_pdf: "📧",
  tracking_doc: "📦",
  chat_export: "💬",
  photo: "📷",
  note: "🗒️",
  other: "📁",
};

const formatDateTime = (value: string) => new Date(value).toLocaleString();
const humanFileSize = (bytes: number) => {
  if (bytes >= 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
  if (bytes >= 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${bytes} B`;
};

const sortTimeline = (events: TimelineEvent[]) =>
  [...events].sort(
    (a, b) => new Date(b.happened_at).getTime() - new Date(a.happened_at).getTime()
  );

const getKindLabel = (kind: EvidenceKind) =>
  evidenceKindOptions.find((option) => option.value === kind)?.label ?? kind;
const getKindIcon = (kind: EvidenceKind) => kindIcons[kind] ?? "📁";
const summarizeText = (value?: string | null, limit = 160) => {
  if (!value) {
    return null;
  }
  return value.length > limit ? `${value.slice(0, limit)}…` : value;
};

const extractionStatusOptions: Array<{ value: ExtractionStatus; label: string }> = [
  { value: "not_started", label: "Not started" },
  { value: "pending", label: "Pending" },
  { value: "extracted", label: "Extracted" },
  { value: "failed", label: "Failed" },
  { value: "manual", label: "Manual entry" },
];

const extractionStatusLabels: Record<ExtractionStatus, string> = {
  not_started: "Not started",
  pending: "Pending",
  extracted: "Extracted",
  failed: "Failed",
  manual: "Manual entry",
};

const auditActionLabels: Record<string, string> = {
  create: "Case created",
  update: "Case updated",
  upload: "Evidence uploaded",
  transition: "Workflow transition",
  export: "Export generated",
  create_event: "Timeline event created",
  create_note: "Timeline note added",
};

const formatAuditAction = (action: string) =>
  auditActionLabels[action] ?? action.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());

const shortKey = (value: string) => {
  if (value.length <= 20) {
    return value;
  }
  return `${value.slice(0, 12)}…${value.slice(-4)}`;
};

const formatActorLabel = (event: AuditEvent) => {
  if (event.actor_type === "user" && event.actor_id) {
    return `User #${event.actor_id}`;
  }
  return event.actor_type.charAt(0).toUpperCase() + event.actor_type.slice(1);
};

const describeAuditMetadata = (event: AuditEvent) => {
  const metadata = event.metadata_json ?? {};
  const details: string[] = [];
  const from = metadata["from"];
  const to = metadata["to"];
  if (typeof from === "string" && typeof to === "string") {
    details.push(`${from} → ${to}`);
  }
  const storageKey = metadata["storage_key"];
  if (typeof storageKey === "string") {
    details.push(`Storage ${shortKey(storageKey)}`);
  }
  const exportId = metadata["case_export_id"];
  if (typeof exportId === "string" || typeof exportId === "number") {
    details.push(`Export #${exportId}`);
  }
  const updatedFields = metadata["updated_fields"];
  if (Array.isArray(updatedFields) && updatedFields.every((field) => typeof field === "string")) {
    details.push(`Fields: ${(updatedFields as string[]).join(", ")}`);
  }
  const noteType = metadata["note_type"];
  if (typeof noteType === "string") {
    details.push(`Note type: ${noteType}`);
  }
  const corrects = metadata["corrects_event_id"];
  if (typeof corrects === "string" || typeof corrects === "number") {
    details.push(`Correcting event #${corrects}`);
  }
  const fields = metadata["fields"];
  if (Array.isArray(fields) && fields.every((field) => typeof field === "string")) {
    details.push(`Fields: ${(fields as string[]).join(", ")}`);
  } else if (fields && typeof fields === "object") {
    details.push(
      `Fields captured: ${Object.keys(fields as Record<string, unknown>).length}`
    );
  }
  return details;
};

const counterpartyTypeLabels: Record<string, string> = {
  merchant: "Merchant",
  landlord: "Landlord",
  carrier: "Carrier",
  manufacturer: "Manufacturer",
  marketplace: "Marketplace",
};

const formatCounterpartyType = (type?: string) =>
  type ? counterpartyTypeLabels[type] ?? type.replace(/_/g, " ") : "Manual entry";

type CaseDetailContentProps = {
  caseId: string;
};

export default function CaseDetailContent({ caseId }: CaseDetailContentProps) {
  const [caseDetail, setCaseDetail] = useState<CaseDetail | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [readiness, setReadiness] = useState<ReadinessReport | null>(null);
  const [evidenceList, setEvidenceList] = useState<EvidenceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [summaryDraft, setSummaryDraft] = useState("");
  const [summarySaving, setSummarySaving] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [summaryMessage, setSummaryMessage] = useState<string | null>(null);
  const [templateSummary, setTemplateSummary] = useState<string | null>(null);
  const [templateLoading, setTemplateLoading] = useState(false);
  const [templateError, setTemplateError] = useState<string | null>(null);

  const [noteBody, setNoteBody] = useState("");
  const [noteSubmitting, setNoteSubmitting] = useState(false);
  const [noteError, setNoteError] = useState<string | null>(null);

  const [transitionLoading, setTransitionLoading] = useState(false);
  const [transitionError, setTransitionError] = useState<string | null>(null);
  const [transitionMessage, setTransitionMessage] = useState<string | null>(null);
  const [transitionReason, setTransitionReason] = useState("");

  const [evidenceLoading, setEvidenceLoading] = useState(true);
  const [evidenceError, setEvidenceError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [selectedKind, setSelectedKind] = useState<EvidenceKind>("receipt");
  const [dragActive, setDragActive] = useState(false);
  const [downloadingEvidenceId, setDownloadingEvidenceId] = useState<number | null>(null);
  const [editingExtractionId, setEditingExtractionId] = useState<number | null>(null);
  const [extractionDraft, setExtractionDraft] = useState("");
  const [extractionStatusDraft, setExtractionStatusDraft] =
    useState<ExtractionStatus>("not_started");
  const [extractionSaving, setExtractionSaving] = useState(false);
  const [extractionError, setExtractionError] = useState<string | null>(null);
  const [extractionMessage, setExtractionMessage] = useState<string | null>(null);

  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditError, setAuditError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"timeline" | "audit">("timeline");

  const fileInputRef = useRef<HTMLInputElement>(null);

  const sortedTimeline = useMemo(() => sortTimeline(timeline), [timeline]);
  const activityTabs: Array<{ key: "timeline" | "audit"; label: string }> = [
    { key: "timeline", label: "Timeline" },
    { key: "audit", label: "Audit log" },
  ];

  const refreshTimeline = useCallback(async () => {
    try {
      const events = await fetchTimeline(caseId);
      setTimeline(events);
    } catch (err) {
      console.error(err);
    }
  }, [caseId]);

  const refreshReadiness = useCallback(async () => {
    try {
      const report = await fetchReadiness(caseId);
      setReadiness(report);
    } catch (err) {
      console.error(err);
    }
  }, [caseId]);

  const refreshEvidence = useCallback(async () => {
    setEvidenceLoading(true);
    setEvidenceError(null);
    try {
      const list = await listEvidence(caseId);
      setEvidenceList(list);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Unable to load evidence";
      setEvidenceError(message);
    } finally {
      setEvidenceLoading(false);
    }
  }, [caseId]);

  const refreshAudit = useCallback(async () => {
    setAuditLoading(true);
    setAuditError(null);
    try {
      const events = await fetchAuditEvents(caseId);
      setAuditEvents(events);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Unable to load audit log";
      setAuditError(message);
    } finally {
      setAuditLoading(false);
    }
  }, [caseId]);

  const refreshTemplatePreview = useCallback(async () => {
    setTemplateLoading(true);
    setTemplateError(null);
    try {
      const preview = await fetchCaseSummaryPreview(caseId);
      setTemplateSummary(preview.summary);
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Unable to load template summary";
      setTemplateError(message);
    } finally {
      setTemplateLoading(false);
    }
  }, [caseId]);

  const loadCaseData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [detail, events, report, evidence] = await Promise.all([
        fetchCase(caseId),
        fetchTimeline(caseId),
        fetchReadiness(caseId),
        listEvidence(caseId),
      ]);
      setCaseDetail(detail);
      setSummaryDraft(detail.summary ?? "");
      setTimeline(events);
      setReadiness(report);
      setEvidenceList(evidence);
      await refreshAudit();
      await refreshTemplatePreview();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to load case data");
    } finally {
      setLoading(false);
    }
  }, [caseId, refreshAudit, refreshTemplatePreview]);

  useEffect(() => {
    loadCaseData();
  }, [loadCaseData]);

  const handleSaveSummary = async () => {
    setSummarySaving(true);
    setSummaryError(null);
    setSummaryMessage(null);
    try {
      const updated = await updateCase(caseId, {
        summary: summaryDraft.trim() || null,
      });
      setCaseDetail(updated);
      setSummaryMessage("Summary saved.");
      await refreshTemplatePreview();
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Unable to save summary";
      setSummaryError(message);
    } finally {
      setSummarySaving(false);
    }
  };

  const handleAddNote = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = noteBody.trim();
    if (!trimmed) {
      setNoteError("Add some context before saving the note.");
      return;
    }
    setNoteSubmitting(true);
    setNoteError(null);
    try {
      const note = await createTimelineNote(caseId, { body: trimmed });
      setTimeline((prev) => [...prev, note]);
      setNoteBody("");
      await refreshReadiness();
      await refreshAudit();
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Unable to save note";
      setNoteError(message);
    } finally {
      setNoteSubmitting(false);
    }
  };

  const handleTransition = async (target: CaseTransitionRequest["target_status"]) => {
    setTransitionLoading(true);
    setTransitionError(null);
    setTransitionMessage(null);
    try {
      const transitionPayload: CaseTransitionRequest = { target_status: target };
      const trimmedReason = transitionReason.trim();
      if (trimmedReason) {
        transitionPayload.reason = trimmedReason;
      }
      const updated = await transitionCase(caseId, transitionPayload);
      setCaseDetail(updated);
      const label = statusLabels[target] ?? target.replace(/_/g, " ");
      setTransitionMessage(`Case moved to ${label}.`);
      setTransitionReason("");
      await refreshTimeline();
      await refreshReadiness();
      await refreshAudit();
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Unable to transition case";
      setTransitionError(message);
    } finally {
      setTransitionLoading(false);
    }
  };

  const handleUpload = async (file: File) => {
    if (!file) {
      return;
    }
    if (file.size > MAX_EVIDENCE_SIZE_BYTES) {
      setUploadError("File is too large.");
      return;
    }
    if (file.type && DISALLOWED_EVIDENCE_MIMES.has(file.type)) {
      setUploadError("This file type is not allowed.");
      return;
    }
    setUploading(true);
    setUploadError(null);
    setUploadProgress(0);
    try {
      const item = await uploadEvidence(caseId, file, selectedKind, {
        onProgress: (percent) => setUploadProgress(percent),
      });
      setEvidenceList((prev) => [item, ...prev]);
      await refreshTimeline();
      await refreshReadiness();
      await refreshEvidence();
      await refreshAudit();
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Upload failed";
      setUploadError(message);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleFileInput = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      handleUpload(file);
    }
    event.target.value = "";
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragActive(false);
    const file = event.dataTransfer.files?.[0];
    if (file) {
      handleUpload(file);
    }
  };

  const handleDownloadEvidence = async (item: EvidenceItem) => {
    setDownloadingEvidenceId(item.id);
    setEvidenceError(null);
    try {
      await downloadEvidence(caseId, item.id, item.original_filename);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Unable to download";
      setEvidenceError(message);
    } finally {
      setDownloadingEvidenceId(null);
    }
  };

  const startExtractionEdit = (item: EvidenceItem) => {
    setEditingExtractionId(item.id);
    setExtractionDraft(item.extracted_text ?? "");
    setExtractionStatusDraft(item.extraction_status ?? "not_started");
    setExtractionError(null);
    setExtractionMessage(null);
  };

  const closeExtractionEditor = () => {
    setEditingExtractionId(null);
    setExtractionError(null);
    setExtractionMessage(null);
  };

  const handleSaveExtraction = async (
    event: FormEvent<HTMLFormElement>,
    evidenceId: number
  ) => {
    event.preventDefault();
    setExtractionSaving(true);
    setExtractionError(null);
    setExtractionMessage(null);
    try {
      const updated = await updateEvidenceExtraction(caseId, evidenceId, {
        extracted_text: extractionDraft.trim() || null,
        extraction_status: extractionStatusDraft,
      });
      setEvidenceList((prev) => prev.map((item) => (item.id === evidenceId ? updated : item)));
      setExtractionMessage("Extraction details saved.");
      closeExtractionEditor();
      await refreshTimeline();
      await refreshAudit();
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Unable to update extraction";
      setExtractionError(message);
    } finally {
      setExtractionSaving(false);
    }
  };

  if (loading) {
    return (
      <section className="space-y-4">
        <header>
          <h1 className="text-3xl font-semibold text-slate-900">Case details</h1>
          <p className="text-sm text-slate-500">Loading case data...</p>
        </header>
        <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center">
          <Loader />
        </div>
      </section>
    );
  }

  if (error) {
    return <StatusMessage variant="error">{error}</StatusMessage>;
  }

  if (!caseDetail) {
    return null;
  }

  const counterpartyProfile = caseDetail.counterparty_profile;
  const counterpartyDisplayName =
    counterpartyProfile?.name ?? caseDetail.counterparty_name ?? "Unnamed counterparty";
  const counterpartyTypeLabel = counterpartyProfile
    ? formatCounterpartyType(counterpartyProfile.profile_type)
    : "Manual entry";

  const availableTransitions = workflowTransitions[caseDetail.status] ?? [];

  return (
    <section className="space-y-6">
      <header className="space-y-3 rounded-2xl border border-slate-200 bg-white p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.4em] text-slate-500">
          {statusLabels[caseDetail.status] ?? caseDetail.status.replace(/_/g, " ")}
        </p>
        <div className="flex flex-col gap-1">
          <h1 className="text-3xl font-semibold text-slate-900">{caseDetail.title}</h1>
          <div className="flex flex-wrap gap-3 text-sm text-slate-500">
            <span className="uppercase tracking-[0.4em] text-slate-400">{caseDetail.claim_type}</span>
            <span>{caseDetail.merchant_name ?? "Unknown merchant"}</span>
            {caseDetail.due_date && (
              <span>Due {new Date(caseDetail.due_date).toLocaleDateString()}</span>
            )}
            <span>Updated {new Date(caseDetail.updated_at).toLocaleDateString()}</span>
          </div>
        </div>
      </header>

      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-slate-500">Counterparty</p>
            <h2 className="text-2xl font-semibold text-slate-900">{counterpartyDisplayName}</h2>
          </div>
          <span className="text-xs uppercase tracking-[0.3em] text-slate-500">
            {counterpartyTypeLabel}
          </span>
        </div>
        <div className="mt-4 grid gap-4 text-sm text-slate-600 sm:grid-cols-3">
          <div>
            <p className="text-[11px] uppercase tracking-[0.3em] text-slate-400">Website</p>
            {counterpartyProfile?.website ? (
              <a
                href={counterpartyProfile.website}
                target="_blank"
                rel="noreferrer"
                className="text-slate-900 underline-offset-2 transition hover:text-slate-700"
              >
                {counterpartyProfile.website}
              </a>
            ) : (
              <p className="text-sm text-slate-500">Not provided</p>
            )}
          </div>
          <div>
            <p className="text-[11px] uppercase tracking-[0.3em] text-slate-400">Support email</p>
            {counterpartyProfile?.support_email ? (
              <a
                href={`mailto:${counterpartyProfile.support_email}`}
                className="text-slate-900 underline-offset-2 transition hover:text-slate-700"
              >
                {counterpartyProfile.support_email}
              </a>
            ) : (
              <p className="text-sm text-slate-500">Not provided</p>
            )}
          </div>
          <div>
            <p className="text-[11px] uppercase tracking-[0.3em] text-slate-400">Support URL</p>
            {counterpartyProfile?.support_url ? (
              <a
                href={counterpartyProfile.support_url}
                target="_blank"
                rel="noreferrer"
                className="text-slate-900 underline-offset-2 transition hover:text-slate-700"
              >
                {counterpartyProfile.support_url}
              </a>
            ) : (
              <p className="text-sm text-slate-500">Not provided</p>
            )}
          </div>
        </div>
        <p className="mt-4 text-sm text-slate-600">
          {counterpartyProfile?.notes ?? "No additional counterparty details recorded."}
        </p>
      </section>

      <div className="grid gap-6 lg:grid-cols-[1.45fr,0.85fr]">
        <div className="space-y-6">
          <section className="space-y-3 rounded-2xl border border-slate-200 bg-white p-5">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Summary</h2>
              <button
                className="rounded-2xl border border-slate-200 px-4 py-2 text-xs font-semibold uppercase tracking-[0.3em] text-slate-600 transition hover:border-slate-900"
                onClick={handleSaveSummary}
                disabled={summarySaving}
              >
                {summarySaving ? "Saving..." : "Save"}
              </button>
            </div>
            <textarea
              value={summaryDraft}
              onChange={(event) => setSummaryDraft(event.target.value)}
              rows={4}
              className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 focus:border-slate-900"
              placeholder="Capture the claim narrative here."
            />
            {summaryError && <StatusMessage variant="error">{summaryError}</StatusMessage>}
            {summaryMessage && <div className="text-sm text-slate-600">{summaryMessage}</div>}
            <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
              <div className="flex items-center justify-between">
                <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Template preview</p>
                <button
                  type="button"
                  onClick={refreshTemplatePreview}
                  disabled={templateLoading}
                  className="rounded-2xl border border-slate-200 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.3em] text-slate-500 transition hover:border-slate-900 disabled:opacity-50"
                >
                  {templateLoading ? "Refreshing..." : "Refresh"}
                </button>
              </div>
              <div className="mt-3 min-h-[120px] rounded-2xl border border-dashed border-slate-200 bg-white/80 p-3 text-[12px] leading-relaxed text-slate-800">
                {templateLoading && (
                  <div className="flex items-center justify-center text-sm text-slate-500">
                    <Loader />
                  </div>
                )}
                {!templateLoading && templateError && (
                  <StatusMessage variant="error">{templateError}</StatusMessage>
                )}
                {!templateLoading && !templateError && templateSummary && (
                  <pre className="whitespace-pre-wrap text-[11px] text-slate-800">
                    {templateSummary}
                  </pre>
                )}
                {!templateLoading && !templateSummary && !templateError && (
                  <p>Preview will appear once the template renders.</p>
                )}
              </div>
            </div>
          </section>

          <section className="space-y-3 rounded-2xl border border-slate-200 bg-white p-5">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">
                  {activeTab === "timeline" ? "Timeline" : "Audit log"}
                </h2>
                <p className="text-xs uppercase tracking-[0.3em] text-slate-500">
                  {activeTab === "timeline"
                    ? `${sortedTimeline.length} events`
                    : `${auditEvents.length} audit entries`}
                </p>
              </div>
              <div className="flex gap-2">
                {activityTabs.map((tab) => (
                  <button
                    key={tab.key}
                    type="button"
                    onClick={() => setActiveTab(tab.key)}
                    className={`rounded-2xl border px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.3em] transition ${
                      activeTab === tab.key
                        ? "border-slate-900 bg-slate-900 text-white"
                        : "border-transparent bg-slate-50 text-slate-500 hover:border-slate-200"
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              {activeTab === "timeline" ? (
                <>
                  {sortedTimeline.length === 0 && (
                    <StatusMessage>No events recorded yet.</StatusMessage>
                  )}
                  <div className="space-y-4">
                    {sortedTimeline.map((event) => (
                      <div
                        key={event.id}
                        className="rounded-2xl border border-slate-100 bg-slate-50/80 p-4"
                      >
                        <div className="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-slate-500">
                          <span>{event.event_type.replace(/_/g, " ")}</span>
                          <span>{formatDateTime(event.happened_at)}</span>
                        </div>
                        <p className="mt-2 text-sm text-slate-700">{event.body}</p>
                        <p className="mt-1 text-[11px] uppercase tracking-[0.3em] text-slate-400">
                          {event.actor_type}
                        </p>
                      </div>
                    ))}
                  </div>
                  <form className="space-y-3" onSubmit={handleAddNote}>
                    <label className="text-sm font-semibold text-slate-600">
                      Add a note
                      <textarea
                        value={noteBody}
                        onChange={(event) => setNoteBody(event.target.value)}
                        rows={3}
                        className="mt-1 w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-slate-900"
                        placeholder="What should future reviewers know?"
                      />
                    </label>
                    {noteError && <StatusMessage variant="error">{noteError}</StatusMessage>}
                    <div className="flex justify-end">
                      <button
                        type="submit"
                        className="rounded-2xl bg-slate-900 px-4 py-2 text-xs font-semibold uppercase tracking-[0.3em] text-white transition hover:bg-slate-800 disabled:opacity-60"
                        disabled={noteSubmitting}
                      >
                        {noteSubmitting ? "Saving..." : "Add note"}
                      </button>
                    </div>
                  </form>
                </>
              ) : (
                <>
                  {auditError && <StatusMessage variant="error">{auditError}</StatusMessage>}
                  {auditLoading && (
                    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-center text-sm text-slate-500">
                      <Loader />
                    </div>
                  )}
                  {!auditLoading && !auditEvents.length && (
                    <StatusMessage>No audit events recorded yet.</StatusMessage>
                  )}
                  <div className="space-y-4">
                    {auditEvents.map((event) => {
                      const metadataDetails = describeAuditMetadata(event);
                      return (
                        <div
                          key={event.id}
                          className="rounded-2xl border border-slate-100 bg-slate-50/80 p-4"
                        >
                          <div className="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-slate-500">
                            <span>{formatAuditAction(event.action)}</span>
                            <span>{formatDateTime(event.happened_at)}</span>
                          </div>
                          {metadataDetails.length > 0 && (
                            <p className="mt-2 text-sm text-slate-700">
                              {metadataDetails.join(" · ")}
                            </p>
                          )}
                          <p className="mt-1 text-[11px] uppercase tracking-[0.3em] text-slate-400">
                            {formatActorLabel(event)}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </>
              )}
            </div>
          </section>

          <section className="space-y-3 rounded-2xl border border-slate-200 bg-white p-5">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Evidence</h2>
              <button
                type="button"
                className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500"
                onClick={() => fileInputRef.current?.click()}
              >
                Choose file
              </button>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              onChange={handleFileInput}
            />
            <div
              onDrop={handleDrop}
              onDragOver={(event) => {
                event.preventDefault();
                setDragActive(true);
              }}
              onDragLeave={(event) => {
                event.preventDefault();
                setDragActive(false);
              }}
              onClick={() => fileInputRef.current?.click()}
              className={`rounded-2xl border-2 border-dashed px-4 py-6 text-center text-sm transition ${
                dragActive
                  ? "border-slate-900 bg-slate-50"
                  : "border-slate-200 bg-white"
              }`}
            >
              <p className="text-slate-500">Drag & drop or click to upload evidence</p>
              <p className="text-[11px] uppercase tracking-[0.3em] text-slate-400">
                {humanFileSize(MAX_EVIDENCE_SIZE_BYTES)} max, no executables
              </p>
            </div>
            <div className="flex items-center justify-between gap-2 text-sm">
              <label className="flex-1 text-xs uppercase tracking-[0.3em] text-slate-600">
                Kind
                <select
                  value={selectedKind}
                  onChange={(event) => setSelectedKind(event.target.value as EvidenceKind)}
                  className="mt-1 w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900"
                >
                  {evidenceKindOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="button"
                className="rounded-2xl bg-slate-900 px-4 py-2 text-xs font-semibold uppercase tracking-[0.3em] text-white transition hover:bg-slate-800 disabled:opacity-60"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
              >
                {uploading ? "Uploading..." : "Upload"}
              </button>
            </div>
            {uploading && (
              <div className="w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-1 bg-slate-900 transition-[width] duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            )}
            {uploadError && <StatusMessage variant="error">{uploadError}</StatusMessage>}
            {evidenceError && <StatusMessage variant="error">{evidenceError}</StatusMessage>}
            {evidenceLoading && (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-center text-sm text-slate-500">
                <Loader />
              </div>
            )}
            {!evidenceLoading && !evidenceList.length && (
              <StatusMessage>
                No evidence yet. Upload receipts, screenshots, or notes to build the timeline.
              </StatusMessage>
            )}
            <div className="space-y-3">
              {evidenceList.map((item) => (
                <div
                  key={item.id}
                  className="rounded-2xl border border-slate-100 bg-slate-50/60 p-4"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2 text-sm font-semibold text-slate-800">
                        <span>{getKindIcon(item.kind)}</span>
                        <span>{getKindLabel(item.kind)}</span>
                        <span className="text-xs uppercase tracking-[0.2em] text-slate-400">
                          {item.mime_type}
                        </span>
                      </div>
                      <p className="text-lg font-semibold text-slate-900">{item.original_filename}</p>
                      <p className="text-[11px] uppercase tracking-[0.3em] text-slate-500">
                        Uploaded {formatDateTime(item.uploaded_at)} · {humanFileSize(item.size_bytes)}
                      </p>
                      <p className="text-[11px] uppercase tracking-[0.3em] text-slate-500">
                        SHA256 {item.sha256.slice(0, 8)}…
                      </p>
                    </div>
                  <div className="flex flex-col gap-2 text-xs uppercase tracking-[0.3em]">
                    <button
                      type="button"
                      className="rounded-2xl border border-slate-200 px-4 py-2 text-[11px] font-semibold text-slate-700 transition hover:border-slate-900"
                      onClick={() => handleDownloadEvidence(item)}
                      disabled={downloadingEvidenceId === item.id}
                    >
                      {downloadingEvidenceId === item.id ? "Downloading" : "Download"}
                    </button>
                    <span className="text-xs text-slate-500">
                      Source {item.source_label ?? "upload"}
                    </span>
                  </div>
                </div>
                <div className="mt-4 space-y-2 rounded-2xl border border-slate-200 bg-white/90 p-4 text-sm text-slate-700">
                  <div className="flex items-center justify-between text-[11px] uppercase tracking-[0.3em] text-slate-500">
                    <span>Extraction</span>
                    <span>{extractionStatusLabels[item.extraction_status] ?? item.extraction_status}</span>
                  </div>
                  <p className="text-sm leading-relaxed text-slate-600">
                    {summarizeText(item.extracted_text) ?? "No extraction text recorded yet."}
                  </p>
                  <button
                    type="button"
                    className="rounded-2xl border border-slate-200 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.3em] text-slate-600 transition hover:border-slate-900"
                    onClick={() =>
                      editingExtractionId === item.id ? closeExtractionEditor() : startExtractionEdit(item)
                    }
                  >
                    {editingExtractionId === item.id ? "Close extraction editor" : "Manage extraction"}
                  </button>
                  {editingExtractionId === item.id && (
                    <form
                      className="space-y-3"
                      onSubmit={(event) => handleSaveExtraction(event, item.id)}
                    >
                      <label className="block text-xs uppercase tracking-[0.3em] text-slate-500">
                        Status
                        <select
                          value={extractionStatusDraft}
                          onChange={(event) =>
                            setExtractionStatusDraft(event.target.value as ExtractionStatus)
                          }
                          className="mt-1 w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900"
                        >
                          {extractionStatusOptions.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label className="block text-xs uppercase tracking-[0.3em] text-slate-500">
                        Extracted text
                        <textarea
                          value={extractionDraft}
                          onChange={(event) => setExtractionDraft(event.target.value)}
                          rows={3}
                          className="mt-1 w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-slate-900"
                          placeholder="Capture notes, receipt text, or extraction overrides."
                        />
                      </label>
                      {extractionError && <StatusMessage variant="error">{extractionError}</StatusMessage>}
                      {extractionMessage && (
                        <div className="text-xs text-emerald-700">{extractionMessage}</div>
                      )}
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="submit"
                          disabled={extractionSaving}
                          className="rounded-2xl border border-slate-200 px-4 py-2 text-[10px] font-semibold uppercase tracking-[0.3em] text-slate-700 transition hover:border-slate-900 disabled:opacity-60"
                        >
                          {extractionSaving ? "Saving..." : "Save extraction"}
                        </button>
                        <button
                          type="button"
                          onClick={closeExtractionEditor}
                          className="rounded-2xl border border-slate-200 px-4 py-2 text-[10px] font-semibold uppercase tracking-[0.3em] text-slate-500 transition hover:border-slate-900"
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  )}
                </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        <div className="space-y-6">
          <section className="space-y-3 rounded-2xl border border-slate-200 bg-white p-5">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Readiness</h2>
              <div className="text-sm font-semibold text-slate-700">{readiness?.score ?? 0}/100</div>
            </div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Score</p>
            <div className="space-y-2 text-sm text-slate-600">
              {readiness?.missing.length ? (
                <div>
                  <p className="font-semibold text-slate-800">Missing</p>
                  <ul className="list-disc pl-5">
                    {readiness.missing.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p>All required items appear present.</p>
              )}
              {readiness?.recommended.length ? (
                <div>
                  <p className="font-semibold text-slate-800">Recommended</p>
                  <ul className="list-disc pl-5">
                    {readiness.recommended.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p>No further recommendations.</p>
              )}
              {readiness?.blockers.length ? (
                <div>
                  <p className="font-semibold text-slate-800">Blockers</p>
                  <ul className="list-disc pl-5 text-rose-700">
                    {readiness.blockers.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p>No export blockers.</p>
              )}
            </div>
          </section>

          <section className="space-y-3 rounded-2xl border border-slate-200 bg-white p-5">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Workflow</h2>
              <span className="text-xs uppercase tracking-[0.3em] text-slate-400">
                {caseDetail.status.replace(/_/g, " ").toUpperCase()}
              </span>
            </div>
            {transitionError && <StatusMessage variant="error">{transitionError}</StatusMessage>}
            {transitionMessage && <div className="text-sm text-slate-600">{transitionMessage}</div>}
            {!availableTransitions.length && (
              <p className="text-sm text-slate-500">No further transitions available.</p>
            )}
            <label className="mt-3 block text-sm font-medium text-slate-600">
              Reason (optional)
              <textarea
                value={transitionReason}
                onChange={(event) => setTransitionReason(event.target.value)}
                rows={2}
                className="mt-1 w-full resize-y rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 focus:border-slate-900"
                placeholder="Add context for the transition"
              />
            </label>
            <div className="flex flex-wrap gap-2">
              {availableTransitions.map((transition) => (
                <button
                  key={transition.value}
                  type="button"
                  className="rounded-2xl border border-slate-200 px-4 py-2 text-xs font-semibold uppercase tracking-[0.3em] text-slate-700 transition hover:border-slate-900"
                  onClick={() => handleTransition(transition.value)}
                  disabled={transitionLoading}
                >
                  {transition.label}
                </button>
              ))}
            </div>
          </section>
        </div>
      </div>
    </section>
  );
}
