/**
 * In-memory stand-in for the FastAPI service, enabled with NEXT_PUBLIC_API_MOCK=true.
 * It implements the contract in docs/PLAN.md section 5 closely enough to drive every
 * screen: multipart lead creation, listing with a state filter and counts, the single legal
 * state transition (409 otherwise) with a history entry, append-only attorney notes, and
 * cookie-based login/logout.
 *
 * Login: attorney@example.com / password123 (matches the seeded user in section 6).
 * The auth cookie is set with document.cookie (not httpOnly) so middleware.ts sees it.
 */
import type { components } from "./schema";

type Lead = components["schemas"]["LeadRead"];
type LeadDetail = components["schemas"]["LeadDetail"];
type LeadEvent = components["schemas"]["LeadEventRead"];
type LeadNote = components["schemas"]["LeadNoteRead"];
type LeadState = components["schemas"]["LeadState"];

const COOKIE = "access_token";
const USER = { id: "6b1c2f3e-0000-4000-8000-000000000001", email: "attorney@example.com", created_at: "2026-09-01T09:00:00Z" };
const PASSWORD = "password123";
const LATENCY_MS = 350;

const events = new Map<string, LeadEvent[]>();
const notes = new Map<string, LeadNote[]>();
const NOTE_MAX_CHARS = 2000;

const seed: Lead[] = [
  lead("Priya", "Natarajan", "priya.natarajan@example.com", "priya-natarajan-cv.pdf", "application/pdf", "2026-09-05T14:12:00Z", "REACHED_OUT"),
  lead("Mateo", "Alvarez", "mateo.alvarez@example.com", "Mateo_Alvarez_Resume.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "2026-09-06T08:41:00Z"),
  lead("Chen", "Wei", "chen.wei@example.com", "resume-chen-wei.pdf", "application/pdf", "2026-09-06T10:03:00Z"),
  lead("Amara", "Okafor", "amara.okafor@example.com", "Amara Okafor CV.doc", "application/msword", "2026-09-06T11:27:00Z"),
];

let leads: Lead[] = [...seed];

function lead(first: string, last: string, email: string, name: string, type: string, created: string, state: LeadState = "PENDING"): Lead {
  const id = crypto.randomUUID();
  const reached = state === "REACHED_OUT";
  // Seeded reached-out leads were moved a couple of hours after submission.
  const reachedAt = reached ? new Date(new Date(created).getTime() + 2 * 60 * 60 * 1000).toISOString() : null;
  const history: LeadEvent[] = [event(null, "PENDING", null, created)];
  if (reachedAt) history.push(event("PENDING", "REACHED_OUT", USER, reachedAt));
  events.set(id, history);
  if (reachedAt) {
    const noteAt = new Date(new Date(created).getTime() + 90 * 60 * 1000).toISOString();
    notes.set(id, [note("Spoke briefly on the phone; sending the intake questionnaire today.", noteAt)]);
  }
  return {
    id,
    first_name: first,
    last_name: last,
    email,
    resume_name: name,
    resume_type: type,
    state,
    created_at: created,
    updated_at: reachedAt ?? created,
    reached_out_at: reachedAt,
    reached_out_by: reached ? USER.id : null,
    reached_out_by_email: reached ? USER.email : null,
  };
}

function event(from: LeadState | null, to: LeadState, actor: typeof USER | null, at: string): LeadEvent {
  return { id: crypto.randomUUID(), from_state: from, to_state: to, actor_id: actor?.id ?? null, actor_email: actor?.email ?? null, created_at: at };
}

function note(body: string, at: string): LeadNote {
  return { id: crypto.randomUUID(), author_id: USER.id, author_email: USER.email, body, created_at: at };
}

function hasCookie(): boolean {
  if (typeof document === "undefined") return false;
  return document.cookie.split(";").some((c) => c.trim().startsWith(`${COOKIE}=`));
}

function setCookie(value: string | null) {
  if (typeof document === "undefined") return;
  document.cookie = value ? `${COOKIE}=${value}; Path=/; SameSite=Lax` : `${COOKIE}=; Path=/; Max-Age=0`;
}

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

const detail = (status: number, msg: string) => json(status, { detail: msg });
const unauthorized = () => detail(401, "Not authenticated");

function validation(errors: Array<[string, string]>): Response {
  return json(422, { detail: errors.map(([field, msg]) => ({ loc: ["body", field], msg, type: "value_error" })) });
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export async function mockFetch(input: Request): Promise<Response> {
  await sleep(LATENCY_MS);
  const url = new URL(input.url);
  const method = input.method.toUpperCase();
  const path = url.pathname.replace(/\/+$/, "");

  if (method === "GET" && path === "/api/v1/health") return json(200, { status: "ok", db: "ok" });

  if (method === "POST" && path === "/api/v1/auth/login") {
    const body = (await input.json().catch(() => ({}))) as { email?: string; password?: string };
    if (body.email?.toLowerCase() === USER.email && body.password === PASSWORD) {
      setCookie("mock-token");
      return json(200, USER);
    }
    return detail(401, "Incorrect email or password");
  }

  if (method === "POST" && path === "/api/v1/auth/logout") {
    setCookie(null);
    return new Response(null, { status: 204 });
  }

  if (method === "GET" && path === "/api/v1/auth/me") {
    return hasCookie() ? json(200, USER) : unauthorized();
  }

  if (method === "POST" && path === "/api/v1/leads") {
    const fd = await input.formData();
    const errors: Array<[string, string]> = [];
    const first = String(fd.get("first_name") ?? "").trim();
    const last = String(fd.get("last_name") ?? "").trim();
    const email = String(fd.get("email") ?? "").trim();
    const resume = fd.get("resume");
    if (!first) errors.push(["first_name", "Field required"]);
    if (!last) errors.push(["last_name", "Field required"]);
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) errors.push(["email", "value is not a valid email address"]);
    if (!(resume instanceof File) || resume.size === 0) errors.push(["resume", "Field required"]);
    if (errors.length) return validation(errors);
    const file = resume as File;
    if (file.size > 5 * 1024 * 1024) return detail(413, "Resume exceeds the 5 MB limit");
    if (!/\.(pdf|docx?)$/i.test(file.name)) return detail(400, "Resume must be a PDF, DOC, or DOCX file");
    if (email.endsWith("@fail.test")) return detail(500, "Simulated server failure");
    const now = new Date().toISOString();
    const created = lead(first, last, email, file.name, file.type || "application/octet-stream", now);
    leads = [created, ...leads];
    return json(201, created);
  }

  if (path.startsWith("/api/v1/leads")) {
    if (!hasCookie()) return unauthorized();

    if (method === "GET" && path === "/api/v1/leads") {
      const state = url.searchParams.get("state");
      const limit = Number(url.searchParams.get("limit") ?? 50);
      const offset = Number(url.searchParams.get("offset") ?? 0);
      if (state && state !== "PENDING" && state !== "REACHED_OUT") {
        return json(422, { detail: [{ loc: ["query", "state"], msg: "Input should be 'PENDING' or 'REACHED_OUT'", type: "enum" }] });
      }
      const filtered = leads
        .filter((l) => !state || l.state === state)
        .sort((a, b) => b.created_at.localeCompare(a.created_at));
      const counts = {
        pending: leads.filter((l) => l.state === "PENDING").length,
        reached_out: leads.filter((l) => l.state === "REACHED_OUT").length,
      };
      return json(200, { items: filtered.slice(offset, offset + limit), total: filtered.length, limit, offset, counts });
    }

    const single = path.match(/^\/api\/v1\/leads\/([^/]+)(\/state|\/resume|\/notes)?$/);
    if (single) {
      const target = leads.find((l) => l.id === single[1]);
      if (!target) return detail(404, "Lead not found");
      const sub = single[2];
      if (!sub && method === "GET") {
        const body: LeadDetail = { ...target, events: events.get(target.id) ?? [], notes: notes.get(target.id) ?? [] };
        return json(200, body);
      }
      if (sub === "/notes" && method === "POST") {
        const payload = (await input.json().catch(() => ({}))) as { body?: unknown };
        const text = typeof payload.body === "string" ? payload.body.trim() : "";
        if (typeof payload.body !== "string") return validation([["body", "Field required"]]);
        if (!text) return validation([["body", "String should have at least 1 character"]]);
        if (text.length > NOTE_MAX_CHARS) return validation([["body", `String should have at most ${NOTE_MAX_CHARS} characters`]]);
        const created = note(text, new Date().toISOString());
        notes.set(target.id, [...(notes.get(target.id) ?? []), created]);
        return json(201, created);
      }
      if (sub === "/resume" && method === "GET") {
        const disposition = url.searchParams.get("download") === "true" ? "attachment" : "inline";
        return new Response(`Mock resume for ${target.first_name} ${target.last_name}\n`, {
          status: 200,
          headers: { "Content-Type": "text/plain", "Content-Disposition": `${disposition}; filename="${target.resume_name}"` },
        });
      }
      if (sub === "/state" && method === "PATCH") {
        const body = (await input.json().catch(() => ({}))) as { state?: string };
        if (body.state !== "REACHED_OUT") {
          return json(422, { detail: [{ loc: ["body", "state"], msg: "Input should be 'REACHED_OUT'", type: "enum" }] });
        }
        if (target.state !== "PENDING") return detail(409, "Lead is already marked as reached out");
        const now = new Date().toISOString();
        const updated: Lead = {
          ...target,
          state: "REACHED_OUT",
          updated_at: now,
          reached_out_at: now,
          reached_out_by: USER.id,
          reached_out_by_email: USER.email,
        };
        leads = leads.map((l) => (l.id === updated.id ? updated : l));
        events.set(updated.id, [...(events.get(updated.id) ?? []), event("PENDING", "REACHED_OUT", USER, now)]);
        return json(200, updated);
      }
    }
  }

  return detail(404, "Not Found");
}
