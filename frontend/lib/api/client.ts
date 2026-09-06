import createClient from "openapi-fetch";
import type { paths } from "./schema";
import { mockFetch } from "./mock";

/** Browser-visible base URL of the FastAPI service (docs/PLAN.md section 6). */
export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");

/** When true the client never touches the network; see ./mock.ts. */
export const API_MOCK = process.env.NEXT_PUBLIC_API_MOCK === "true";

export const client = createClient<paths>({
  baseUrl: API_URL,
  // The API authenticates with an httpOnly cookie; always send it.
  credentials: "include",
  ...(API_MOCK ? { fetch: mockFetch } : {}),
});

/** Direct link to the resume endpoint; the browser sends the auth cookie on navigation. */
export function resumeUrl(leadId: string): string {
  return `${API_URL}/api/v1/leads/${encodeURIComponent(leadId)}/resume`;
}
