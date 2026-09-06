import type { LeadEvent, LeadNote } from "@/lib/api";
import { stateLabel } from "@/lib/format";
import { RelativeTime } from "@/components/relative-time";
import { cn } from "@/lib/utils";

type Entry =
  | { kind: "event"; id: string; created_at: string; title: string; tone: string; actor: string | null }
  | { kind: "note"; id: string; created_at: string; body: string; author: string };

function describe(event: LeadEvent): { title: string; tone: string } {
  if (event.from_state === null) return { title: "Submitted through the intake form", tone: "bg-brass" };
  if (event.to_state === "REACHED_OUT") return { title: "Marked as reached out", tone: "bg-success" };
  return { title: `Moved from ${stateLabel(event.from_state)} to ${stateLabel(event.to_state)}`, tone: "bg-muted-foreground" };
}

/** State changes and attorney notes interleaved by time, oldest first. */
function merge(events: LeadEvent[], notes: LeadNote[]): Entry[] {
  const entries: Entry[] = [
    ...events.map((e): Entry => ({ kind: "event", id: `event-${e.id}`, created_at: e.created_at, actor: e.actor_email, ...describe(e) })),
    ...notes.map((n): Entry => ({ kind: "note", id: `note-${n.id}`, created_at: n.created_at, body: n.body, author: n.author_email })),
  ];
  // Stable sort: ties keep server order (events before notes).
  return entries.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
}

/** Who moved what, plus what the team wrote down, oldest first. Every entry comes from the server. */
export function LeadTimeline({ events, notes = [] }: { events: LeadEvent[]; notes?: LeadNote[] }) {
  const entries = merge(events, notes);
  if (entries.length === 0) {
    return <p className="text-sm text-muted-foreground">No history recorded for this lead.</p>;
  }
  return (
    <ol className="relative ml-1.5 space-y-5 border-l border-border pl-5">
      {entries.map((entry) => (
        <li key={entry.id} className="relative">
          <span
            aria-hidden
            className={cn("absolute -left-[1.55rem] top-1 size-2.5 rounded-full ring-4 ring-card", entry.kind === "note" ? "bg-ink" : entry.tone)}
          />
          {entry.kind === "note" ? (
            <p className="whitespace-pre-wrap text-sm leading-snug">{entry.body}</p>
          ) : (
            <p className="text-sm font-medium leading-tight">{entry.title}</p>
          )}
          <p className="mt-0.5 text-xs text-muted-foreground">
            {entry.kind === "note" ? (
              <>
                Note by <span className="text-foreground/80">{entry.author}</span>
                <span aria-hidden> · </span>
              </>
            ) : entry.actor ? (
              <>
                by <span className="text-foreground/80">{entry.actor}</span>
                <span aria-hidden> · </span>
              </>
            ) : null}
            <RelativeTime iso={entry.created_at} />
          </p>
        </li>
      ))}
    </ol>
  );
}
