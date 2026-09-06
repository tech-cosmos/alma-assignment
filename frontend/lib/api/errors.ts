import { API_URL } from "./client";

export type ApiFailure = {
  /** HTTP status, or 0 when the request never reached the server. */
  status: number;
  /** Human-readable message suitable for a form-level alert. */
  message: string;
  /** Field-level messages keyed by the multipart/JSON field name (from FastAPI 422 `loc`). */
  fields: Record<string, string>;
};

export type ApiResult<T> = { ok: true; data: T } | { ok: false; error: ApiFailure };

type ValidationItem = { loc?: unknown[]; msg?: string };

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null;
}

/** Normalise a FastAPI error body (`{detail: string | ValidationError[]}`) into ApiFailure. */
export function toFailure(status: number, body: unknown, fallback?: string): ApiFailure {
  const fields: Record<string, string> = {};
  let message = fallback ?? defaultMessage(status);

  if (isRecord(body) && "detail" in body) {
    const detail = body.detail;
    if (typeof detail === "string" && detail.trim()) {
      message = detail;
    } else if (Array.isArray(detail)) {
      for (const item of detail as ValidationItem[]) {
        const loc = Array.isArray(item.loc) ? item.loc : [];
        // loc looks like ["body", "email"] or ["query", "state"]; take the last string segment.
        const field = [...loc].reverse().find((p): p is string => typeof p === "string" && p !== "body");
        if (field && item.msg && !fields[field]) fields[field] = humanise(item.msg);
      }
      if (Object.keys(fields).length > 0) message = "Please fix the highlighted fields.";
    }
  } else if (typeof body === "string" && body.trim() && status !== 0) {
    message = body.slice(0, 200);
  }

  return { status, message, fields };
}

export function networkFailure(err: unknown): ApiFailure {
  const reason = err instanceof Error ? err.message : String(err);
  return {
    status: 0,
    message: `Could not reach the server at ${API_URL}. ${reason}`,
    fields: {},
  };
}

function defaultMessage(status: number): string {
  switch (status) {
    case 400:
      return "The request was rejected. Check the form and try again.";
    case 401:
      return "You need to sign in to do that.";
    case 403:
      return "You do not have permission to do that.";
    case 404:
      return "That record no longer exists.";
    case 409:
      return "This change conflicts with the current state.";
    case 413:
      return "The file is too large (5 MB maximum).";
    case 422:
      return "Some fields are invalid.";
    default:
      return status >= 500 ? "The server hit an error. Please try again in a moment." : "Something went wrong.";
  }
}

/** FastAPI/Pydantic messages read like "Value error, x" or "value is not a valid email address". */
function humanise(msg: string): string {
  const cleaned = msg.replace(/^value error,\s*/i, "").trim();
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
}
