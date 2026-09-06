"use client";

import { useEffect, useState } from "react";

import { formatDateTime, formatRelative } from "@/lib/format";
import { cn } from "@/lib/utils";

/** Ticks once a minute so "3 minutes ago" keeps up without a reload. */
function useNow(intervalMs: number): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), intervalMs);
    return () => window.clearInterval(id);
  }, [intervalMs]);
  return now;
}

/**
 * Relative time ("2 hours ago") with the exact timestamp on hover and in the accessible name.
 * Only render after data has loaded on the client; the value depends on the current clock.
 */
export function RelativeTime({ iso, className }: { iso: string; className?: string }) {
  const now = useNow(60_000);
  const exact = formatDateTime(iso);
  return (
    <time
      dateTime={iso}
      title={exact}
      aria-label={exact}
      className={cn("cursor-help underline decoration-border decoration-dotted underline-offset-4", className)}
    >
      {formatRelative(iso, now)}
    </time>
  );
}
