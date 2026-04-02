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
  merchant_name?: string | null;
  summary?: string | null;
  updated_at: string;
};

export type CaseDetail = CaseSummary & {
  order_reference?: string | null;
  amount_value: number;
  created_at: string;
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

export function fetchCases() {
  return request<CaseSummary[]>("/cases?limit=30");
}

export function fetchCase(id: string) {
  return request<CaseDetail>(`/cases/${id}`);
}
