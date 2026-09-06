import type { LeadEvent } from "@/lib/api";
import { stateLabel } from "@/lib/format";
import { RelativeTime } from "@/components/relative-time";
import { cn } from "@/lib/utils";

function describe(event: LeadEvent): { title: string; tone: string } {
  if (event.from_state === null) return { title: "Submitted through the intake form", tone: "bg-brass" };
  if (event.to_state === "REACHED_OUT") return { title: "Marked as reached out", tone: "bg-success" };
  return { title: `Moved from ${stateLabel(event.from_state)} to ${stateLabel(event.to_state)}`, tone: "bg-muted-foreground" };
}

/** Who moved what, oldest first. Every entry comes from the server-side `lead_events` table. */
export function LeadTimeline({ events }: { events: LeadEvent[] }) {
  if (events.length === 0) {
    return <p className="text-sm text-muted-foreground">No history recorded for this lead.</p>;
  }
  return (
    <ol className="relative ml-1.5 space-y-5 border-l border-border pl-5">
      {events.map((event) => {
        const { title, tone } = describe(event);
        return (
          <li key={event.id} className="relative">
            <span aria-hidden className={cn("absolute -left-[1.55rem] top-1 size-2.5 rounded-full ring-4 ring-card", tone)} />
            <p className="text-sm font-medium leading-tight">{title}</p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {event.actor_email ? (
                <>
                  by <span className="text-foreground/80">{event.actor_email}</span>
                  <span aria-hidden> · </span>
                </>
              ) : null}
              <RelativeTime iso={event.created_at} />
            </p>
          </li>
        );
      })}
    </ol>
  );
}
