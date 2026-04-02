import { getToken } from "../session";

const baseUrl =
  (process.env.NEXT_PUBLIC_API_BASE_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    "http://localhost:8000/api"
  ).replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data: unknown) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

async function request<T>(
  path: string,
  options: {
    method?: "GET" | "POST" | "PATCH" | "DELETE";
    body?: unknown;
    token?: string | null;
  } = {}
): Promise<T> {
  const resolvedToken = options.token ?? getToken();
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (resolvedToken) {
    headers["Authorization"] = `Bearer ${resolvedToken}`;
  }

  const response = await fetch(`${baseUrl}${normalizedPath}`, {
    method: options.method ?? "GET",
    body: options.body ? JSON.stringify(options.body) : undefined,
    headers,
  });

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    const message =
      (payload && typeof payload === "object" && "detail" in payload
        ? (payload as { detail?: string }).detail
        : response.statusText) ?? "Request failed";
    throw new ApiError(message, response.status, payload);
  }

  return payload;
}

export type AuthRequest = {
  email: string;
  password: string;
};

export type RegisterRequest = AuthRequest & {
  full_name: string;
  workspace_name: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
};

export type CaseSummary = {
  id: number;
  title: string;
  status: string;
  claim_type: string;
  counterparty_name?: string | null;
  counterparty_profile_id?: number | null;
  merchant_name?: string | null;
  due_date?: string | null;
  summary?: string | null;
  updated_at: string;
};

export type CounterpartyProfile = {
  id: number;
  workspace_id: number;
  name: string;
  profile_type: string;
  website?: string | null;
  support_email?: string | null;
  support_url?: string | null;
  notes?: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type CaseDetail = CaseSummary & {
  counterparty_profile?: CounterpartyProfile | null;
  order_reference?: string | null;
  amount_value: number;
  created_at: string;
  due_date?: string | null;
};

export type CaseSummaryPreview = {
  case_id: number;
  claim_type: string;
  summary: string;
};

export type CaseUpdateRequest = {
  title?: string;
  summary?: string | null;
  counterparty_name?: string | null;
  counterparty_profile_id?: number | null;
  merchant_name?: string | null;
  order_reference?: string | null;
  amount_currency?: string | null;
  amount_value?: number | null;
  purchase_date?: string | null;
  incident_date?: string | null;
  due_date?: string | null;
};

export type TimelineEvent = {
  id: number;
  case_id: number;
  event_type: string;
  body: string;
  happened_at: string;
  actor_type: string;
  evidence_id?: number | null;
  metadata_json: Record<string, unknown>;
};

export type ReadinessReport = {
  score: number;
  missing: string[];
  recommended: string[];
  blockers: string[];
};

export type AuditEvent = {
  id: number;
  entity_type: string;
  entity_id: number;
  action: string;
  actor_type: string;
  actor_id?: number | null;
  happened_at: string;
  metadata_json: Record<string, unknown>;
};

export type CaseFilter = {
  status?: string;
  claim_type?: string;
};

export type CaseCreateRequest = {
  title: string;
  claim_type: string;
  summary: string;
  counterparty_name?: string;
  counterparty_profile_id?: number;
  merchant_name?: string;
  order_reference?: string;
  due_date?: string;
};

export const MAX_EVIDENCE_SIZE_BYTES = 10 * 1024 * 1024;
export const DISALLOWED_EVIDENCE_MIMES = new Set([
  "application/x-msdownload",
  "application/x-msdos-program",
  "application/x-sh",
  "application/x-executable",
]);

export type EvidenceKind =
  | "receipt"
  | "screenshot"
  | "email_pdf"
  | "tracking_doc"
  | "chat_export"
  | "photo"
  | "note"
  | "other";

export const evidenceKindOptions: Array<{ value: EvidenceKind; label: string }> = [
  { value: "receipt", label: "Receipt / order" },
  { value: "screenshot", label: "Screenshot" },
  { value: "email_pdf", label: "Email / PDF" },
  { value: "tracking_doc", label: "Tracking doc" },
  { value: "chat_export", label: "Chat export" },
  { value: "photo", label: "Photo" },
  { value: "note", label: "Note" },
  { value: "other", label: "Other" },
];

export type EvidenceItem = {
  id: number;
  case_id: number;
  original_filename: string;
  mime_type: string;
  sha256: string;
  size_bytes: number;
  uploaded_at: string;
  storage_key: string;
  source_label?: string | null;
  kind: EvidenceKind;
};

type EvidenceUploadOptions = {
  onProgress?: (progress: number) => void;
};

const parseErrorMessage = (body: string | null) => {
  if (!body) {
    return "Request failed";
  }
  try {
    const parsed = JSON.parse(body);
    if (parsed && typeof parsed === "object" && "detail" in parsed && parsed.detail) {
      return parsed.detail as string;
    }
  } catch {
    // ignore
  }
  return "Request failed";
};

export function login(payload: AuthRequest) {
  return request<AuthResponse>("/auth/login", {
    method: "POST",
    body: payload,
  });
}

export function register(payload: RegisterRequest) {
  return request<AuthResponse>("/auth/register", {
    method: "POST",
    body: payload,
  });
}

export function fetchCase(id: string) {
  return request<CaseDetail>(`/cases/${id}`);
}

export function updateCase(id: string, payload: CaseUpdateRequest) {
  return request<CaseDetail>(`/cases/${id}`, {
    method: "PATCH",
    body: payload,
  });
}

function buildQuery(filters?: CaseFilter) {
  const params = new URLSearchParams();
  params.set("limit", "30");
  if (filters?.status) {
    params.set("status", filters.status);
  }
  if (filters?.claim_type) {
    params.set("claim_type", filters.claim_type);
  }
  return params.toString();
}

export function fetchCases(filters?: CaseFilter) {
  const query = buildQuery(filters);
  return request<CaseSummary[]>(`/cases?${query}`);
}

export function createCase(payload: CaseCreateRequest) {
  return request<CaseDetail>("/cases", {
    method: "POST",
    body: payload,
  });
}

const buildAuthHeaders = () => {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
};

export function listEvidence(caseId: string) {
  return request<EvidenceItem[]>(`/cases/${caseId}/evidence`);
}

export function uploadEvidence(
  caseId: string,
  file: File,
  kind: EvidenceKind,
  options?: EvidenceUploadOptions
) {
  return new Promise<EvidenceItem>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${baseUrl}/cases/${caseId}/evidence`);
    const headers = buildAuthHeaders();
    Object.entries(headers).forEach(([key, value]) => xhr.setRequestHeader(key, value));
    const form = new FormData();
    form.append("file", file, file.name);
    form.append("kind", kind);
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && options?.onProgress) {
        options.onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch {
          reject(new ApiError("Upload failed", xhr.status, xhr.responseText));
        }
        return;
      }
      const message = parseErrorMessage(xhr.responseText);
      reject(new ApiError(message, xhr.status, xhr.responseText));
    };
    xhr.onerror = () => {
      reject(new ApiError("Upload failed", xhr.status || 0, null));
    };
    xhr.send(form);
  });
}

export async function downloadEvidence(caseId: string, evidenceId: number, filename: string) {
  const headers = buildAuthHeaders();
  const response = await fetch(
    `${baseUrl}/cases/${caseId}/evidence/${evidenceId}/download`,
    {
      headers,
    }
  );
  if (!response.ok) {
    const body = await response.text().catch(() => null);
    throw new ApiError(parseErrorMessage(body), response.status, body);
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export type CaseTransitionRequest = {
  target_status: string;
};

export function transitionCase(caseId: string, payload: CaseTransitionRequest) {
  return request<CaseDetail>(`/cases/${caseId}/transition`, {
    method: "POST",
    body: payload,
  });
}

export type TimelineNoteCreateRequest = {
  body: string;
  note_type?: string;
  corrects_event_id?: number;
};

export function createTimelineNote(caseId: string, payload: TimelineNoteCreateRequest) {
  return request<TimelineEvent>(`/cases/${caseId}/notes`, {
    method: "POST",
    body: { ...payload, event_type: "note" },
  });
}

export function fetchTimeline(caseId: string) {
  return request<TimelineEvent[]>(`/cases/${caseId}/timeline`);
}

export function fetchReadiness(caseId: string) {
  return request<ReadinessReport>(`/cases/${caseId}/readiness`);
}

export function fetchCaseSummaryPreview(caseId: string) {
  return request<CaseSummaryPreview>(`/cases/${caseId}/summary-preview`);
}

export function fetchAuditEvents(
  caseId: string,
  options?: { limit?: number; offset?: number }
) {
  const params = new URLSearchParams();
  params.set("limit", String(options?.limit ?? 50));
  params.set("offset", String(options?.offset ?? 0));
  return request<AuditEvent[]>(`/cases/${caseId}/audit-events?${params.toString()}`);
}
