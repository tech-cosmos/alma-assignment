"use client";

import Link from "next/link";

import type { LeadCounts, LeadState } from "@/lib/api";
import { cn } from "@/lib/utils";

const TABS: ReadonlyArray<{ value: LeadState | undefined; label: string; href: string }> = [
  { value: undefined, label: "All", href: "/leads" },
  { value: "PENDING", label: "Pending", href: "/leads?state=PENDING" },
  { value: "REACHED_OUT", label: "Reached out", href: "/leads?state=REACHED_OUT" },
];

function countFor(value: LeadState | undefined, counts: LeadCounts): number {
  if (value === "PENDING") return counts.pending;
  if (value === "REACHED_OUT") return counts.reached_out;
  return counts.pending + counts.reached_out;
}

/** Segmented filter with live counts. Counts are global, so the pending number is always visible. */
export function StateTabs({ value, counts }: { value: LeadState | undefined; counts: LeadCounts | null }) {
  return (
    <nav aria-label="Filter by state" className="inline-flex rounded-lg border border-border bg-card p-0.5">
      {TABS.map((tab) => {
        const active = tab.value === value;
        const n = counts ? countFor(tab.value, counts) : null;
        return (
          <Link
            key={tab.label}
            href={tab.href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "inline-flex h-7 items-center gap-1.5 rounded-md px-3 text-sm no-underline transition-colors",
              active ? "bg-ink text-ink-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground",
            )}
          >
            {tab.label}
            {n !== null && (
              <span
                className={cn(
                  "rounded-full px-1.5 text-[0.65rem] font-semibold tabular-nums leading-4",
                  active ? "bg-ink-foreground/15" : "bg-muted",
                  tab.value === "PENDING" && n > 0 && !active && "bg-brass/25 text-brass-foreground",
                )}
              >
                {n}
              </span>
            )}
          </Link>
        );
      })}
    </nav>
  );
}
