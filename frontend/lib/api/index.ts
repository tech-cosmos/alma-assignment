import { client } from "./client";
import { type ApiResult, networkFailure, toFailure } from "./errors";
import type { components, operations } from "./schema";

export type Lead = components["schemas"]["LeadRead"];
export type LeadState = components["schemas"]["LeadState"];
export type LeadList = components["schemas"]["LeadList"];
export type User = components["schemas"]["UserRead"];

export { API_URL, API_MOCK, resumeUrl } from "./client";
export type { ApiFailure, ApiResult } from "./errors";

export type LeadInput = {
  first_name: string;
  last_name: string;
  email: string;
  resume: File;
};

async function run<T>(call: () => Promise<{ data?: T; error?: unknown; response: Response }>): Promise<ApiResult<T>> {
  try {
    const { data, error, response } = await call();
    if (response.ok && data !== undefined) return { ok: true, data };
    if (response.ok) return { ok: true, data: undefined as T };
    return { ok: false, error: toFailure(response.status, error) };
  } catch (err) {
    return { ok: false, error: networkFailure(err) };
  }
}

/** POST /api/v1/leads — public multipart submission. */
export function createLead(input: LeadInput): Promise<ApiResult<Lead>> {
  return run(() =>
    client.POST("/api/v1/leads", {
      // The generated type says `resume: string` (binary); the serializer below sends the File.
      body: { ...input, resume: input.resume as unknown as string },
      bodySerializer: () => {
        const fd = new FormData();
        fd.append("first_name", input.first_name);
        fd.append("last_name", input.last_name);
        fd.append("email", input.email);
        fd.append("resume", input.resume, input.resume.name);
        return fd;
      },
    }),
  );
}

/** GET /api/v1/leads — tolerates either the `{items,...}` envelope or a bare array. */
export async function listLeads(params: { state?: LeadState; limit?: number; offset?: number } = {}): Promise<ApiResult<LeadList>> {
  const query: NonNullable<operations["list_leads_api_v1_leads_get"]["parameters"]["query"]> = {};
  if (params.state) query.state = params.state;
  if (params.limit !== undefined) query.limit = params.limit;
  if (params.offset !== undefined) query.offset = params.offset;

  const result = await run(() => client.GET("/api/v1/leads", { params: { query } }));
  if (!result.ok) return result;
  const raw: unknown = result.data;
  if (Array.isArray(raw)) {
    const items = raw as Lead[];
    return { ok: true, data: { items, total: items.length, limit: params.limit ?? items.length, offset: params.offset ?? 0 } };
  }
  return result;
}

/** GET /api/v1/leads/{id} */
export function getLead(id: string): Promise<ApiResult<Lead>> {
  return run(() => client.GET("/api/v1/leads/{lead_id}", { params: { path: { lead_id: id } } }));
}

/** PATCH /api/v1/leads/{id}/state — the only legal transition is PENDING -> REACHED_OUT. */
export function markReachedOut(id: string): Promise<ApiResult<Lead>> {
  return run(() =>
    client.PATCH("/api/v1/leads/{lead_id}/state", {
      params: { path: { lead_id: id } },
      body: { state: "REACHED_OUT" },
    }),
  );
}

/** POST /api/v1/auth/login — the API sets the httpOnly cookie itself. */
export function login(email: string, password: string): Promise<ApiResult<User>> {
  return run(() => client.POST("/api/v1/auth/login", { body: { email, password } }));
}

/** POST /api/v1/auth/logout */
export function logout(): Promise<ApiResult<void>> {
  return run(() => client.POST("/api/v1/auth/logout"));
}
