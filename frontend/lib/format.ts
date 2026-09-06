const dateTime = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  year: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

const dateOnly = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric" });

const relative = new Intl.RelativeTimeFormat("en-US", { numeric: "auto" });

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : dateTime.format(d);
}

const MINUTE = 60;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

/**
 * "just now", "12 minutes ago", "3 hours ago", "yesterday", then the plain date once it is
 * more than a week old. Pair with the exact timestamp in a `title` so nothing is lost.
 */
export function formatRelative(iso: string, now: number = Date.now()): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const seconds = Math.round((d.getTime() - now) / 1000);
  const magnitude = Math.abs(seconds);
  if (magnitude < 45) return "just now";
  if (magnitude < HOUR) return relative.format(Math.round(seconds / MINUTE), "minute");
  if (magnitude < DAY) return relative.format(Math.round(seconds / HOUR), "hour");
  if (magnitude < 7 * DAY) return relative.format(Math.round(seconds / DAY), "day");
  return dateOnly.format(d);
}

const stateLabels = { PENDING: "Pending", REACHED_OUT: "Reached out" } as const;

export function stateLabel(state: keyof typeof stateLabels | string): string {
  return (stateLabels as Record<string, string>)[state] ?? state;
}

export type ResumeKind = "pdf" | "doc" | "docx" | "other";

/** Classify the server-detected MIME type; only PDFs can be previewed in the browser. */
export function resumeKind(mimeType: string): ResumeKind {
  if (mimeType === "application/pdf") return "pdf";
  if (mimeType === "application/msword") return "doc";
  if (mimeType === "application/vnd.openxmlformats-officedocument.wordprocessingml.document") return "docx";
  return "other";
}

export function resumeKindLabel(kind: ResumeKind): string {
  return kind === "other" ? "File" : kind.toUpperCase();
}

/** Two-letter avatar initials from an email address ("jane.doe@x" -> "JD"). */
export function initialsFromEmail(email: string): string {
  const local = email.split("@")[0] ?? "";
  const parts = local.split(/[._-]+/).filter(Boolean);
  const letters = parts.length >= 2 ? parts[0][0] + parts[1][0] : local.slice(0, 2);
  return letters.toUpperCase();
}
