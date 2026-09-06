"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ExternalLink, Loader2, RefreshCw } from "lucide-react";

import { type ApiFailure, type Lead, type LeadCounts, type LeadState, listLeads, logout, markReachedOut, resumeUrl } from "@/lib/api";
import { stateLabel } from "@/lib/format";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Pagination } from "@/components/pagination";
import { RelativeTime } from "@/components/relative-time";
import { StateBadge } from "@/components/state-badge";
import { StateTabs } from "@/components/state-tabs";
import { cn } from "@/lib/utils";

export const PAGE_SIZE = 50;
const COLUMNS = 7;

type Status =
  | { kind: "loading" }
  | { kind: "error"; error: ApiFailure }
  | { kind: "ready"; leads: Lead[]; total: number };

type Props = { state: LeadState | undefined; page: number };

export function LeadsTable({ state, page }: Props) {
  const router = useRouter();
  const [status, setStatus] = useState<Status>({ kind: "loading" });
  // Counts survive a reload so the tabs do not flicker while the table refreshes.
  const [counts, setCounts] = useState<LeadCounts | null>(null);
  const [rowError, setRowError] = useState<{ id: string; message: string } | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const listHref = useCallback(
    (targetPage: number) => {
      const params = new URLSearchParams();
      if (state) params.set("state", state);
      if (targetPage > 1) params.set("page", String(targetPage));
      const query = params.toString();
      return query ? `/leads?${query}` : "/leads";
    },
    [state],
  );

  const load = useCallback(async () => {
    setStatus({ kind: "loading" });
    const result = await listLeads({ state, limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE });
    if (!result.ok) {
      if (result.error.status === 401) {
        // Stale or missing session: clear the cookie so middleware stops letting us through, then bounce.
        await logout();
        router.replace(`/login?next=${encodeURIComponent(listHref(page))}`);
        return;
      }
      setStatus({ kind: "error", error: result.error });
      return;
    }
    setCounts(result.data.counts);
    setStatus({ kind: "ready", leads: result.data.items, total: result.data.total });
  }, [state, page, router, listHref]);

  useEffect(() => {
    void load();
  }, [load]);

  async function reachOut(lead: Lead) {
    setRowError(null);
    setBusyId(lead.id);
    const result = await markReachedOut(lead.id);
    setBusyId(null);
    if (result.ok) {
      const updated = result.data;
      setStatus((s) =>
        s.kind === "ready"
          ? {
              ...s,
              // Keep the row visible even when filtering on PENDING so the change is legible; a reload re-filters.
              leads: s.leads.map((l) => (l.id === updated.id ? updated : l)),
            }
          : s,
      );
      setCounts((c) => (c ? { pending: Math.max(0, c.pending - 1), reached_out: c.reached_out + 1 } : c));
      return;
    }
    if (result.error.status === 401) {
      await logout();
      router.replace(`/login?next=${encodeURIComponent(listHref(page))}`);
      return;
    }
    setRowError({ id: lead.id, message: result.error.message });
    if (result.error.status === 409 || result.error.status === 404) void load();
  }

  function openLead(event: React.MouseEvent<HTMLTableRowElement>, id: string) {
    // Links and buttons inside the row keep their own behaviour.
    if ((event.target as HTMLElement).closest("a, button")) return;
    if (window.getSelection()?.toString()) return; // the user was selecting text
    const href = `/leads/${id}`;
    if (event.metaKey || event.ctrlKey) {
      window.open(href, "_blank", "noopener");
      return;
    }
    router.push(href);
  }

  const count = status.kind === "ready" ? status.total : null;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="space-y-1">
          <p className="eyebrow text-muted-foreground">Intake</p>
          <h1 className="font-display text-4xl leading-none">
            Leads
            {count !== null && (
              <span className="ml-3 align-middle font-sans text-sm font-normal tracking-normal text-muted-foreground">
                {count} {count === 1 ? "lead" : "leads"}
                {state ? ` · ${stateLabel(state).toLowerCase()}` : ""}
              </span>
            )}
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <StateTabs value={state} counts={counts} />
          <Button variant="outline" size="icon" aria-label="Reload" onClick={() => void load()} disabled={status.kind === "loading"}>
            <RefreshCw className={cn(status.kind === "loading" && "animate-spin")} />
          </Button>
        </div>
      </div>

      {status.kind === "error" && (
        <Alert variant="destructive">
          <AlertTitle>Couldn&apos;t load leads</AlertTitle>
          <AlertDescription>
            <span>{status.error.message}</span>
            <Button variant="outline" size="sm" className="mt-2" onClick={() => void load()}>
              Try again
            </Button>
          </AlertDescription>
        </Alert>
      )}

      <div className="overflow-hidden rounded-xl border border-border bg-card">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <Th>Name</Th>
              <Th>Email</Th>
              <Th>Resume</Th>
              <Th>State</Th>
              <Th>Submitted</Th>
              <Th>Reached out</Th>
              <Th className="text-right">Action</Th>
            </TableRow>
          </TableHeader>
          <TableBody>
            {status.kind === "loading" &&
              Array.from({ length: 4 }).map((_, i) => (
                <TableRow key={i} className="hover:bg-transparent">
                  {Array.from({ length: COLUMNS }).map((_, j) => (
                    <TableCell key={j}>
                      <span className="block h-3.5 w-full max-w-28 animate-pulse rounded-sm bg-muted" />
                    </TableCell>
                  ))}
                </TableRow>
              ))}

            {status.kind === "ready" && status.leads.length === 0 && (
              <TableRow className="hover:bg-transparent">
                <TableCell colSpan={COLUMNS} className="h-32 text-center text-muted-foreground">
                  {page > 1 ? (
                    <>
                      Nothing on this page.{" "}
                      <Link href={listHref(1)} className="underline underline-offset-4">
                        Back to the first page
                      </Link>
                    </>
                  ) : state ? (
                    `No ${stateLabel(state).toLowerCase()} leads.`
                  ) : (
                    "No leads yet. Submissions from the public form appear here."
                  )}
                </TableCell>
              </TableRow>
            )}

            {status.kind === "ready" &&
              status.leads.map((lead) => {
                const done = lead.state === "REACHED_OUT";
                const busy = busyId === lead.id;
                return (
                  <TableRow
                    key={lead.id}
                    className="cursor-pointer align-top focus-within:bg-muted/40"
                    onClick={(e) => openLead(e, lead.id)}
                  >
                    <TableCell className="font-medium">
                      <Link href={`/leads/${lead.id}`} className="underline-offset-4 hover:underline">
                        {lead.first_name} {lead.last_name}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <a href={`mailto:${lead.email}`} className="text-muted-foreground underline-offset-4 hover:text-foreground hover:underline">
                        {lead.email}
                      </a>
                    </TableCell>
                    <TableCell>
                      <span className="inline-flex max-w-56 items-center gap-1">
                        <Link
                          href={`/leads/${lead.id}#resume`}
                          className="truncate underline-offset-4 hover:underline"
                          title={`Preview ${lead.resume_name}`}
                        >
                          {lead.resume_name}
                        </Link>
                        <a
                          href={resumeUrl(lead.id)}
                          target="_blank"
                          rel="noopener noreferrer"
                          aria-label={`Open ${lead.resume_name} in a new tab`}
                          title="Open in new tab"
                          className="rounded-sm p-0.5 text-muted-foreground hover:bg-muted hover:text-foreground"
                        >
                          <ExternalLink className="size-3.5" />
                        </a>
                      </span>
                    </TableCell>
                    <TableCell>
                      <StateBadge state={lead.state} />
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-muted-foreground">
                      <RelativeTime iso={lead.created_at} />
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-muted-foreground">
                      {lead.reached_out_at ? (
                        <span className="flex flex-col gap-0.5">
                          <RelativeTime iso={lead.reached_out_at} />
                          {lead.reached_out_by_email && (
                            <span className="text-xs" title={lead.reached_out_by_email}>
                              by <span className="text-foreground/80">{lead.reached_out_by_email}</span>
                            </span>
                          )}
                        </span>
                      ) : (
                        <span aria-label="not yet">—</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex flex-col items-end gap-1">
                        {!done && (
                          <Button size="sm" disabled={busy} onClick={() => void reachOut(lead)}>
                            {busy && <Loader2 className="animate-spin" data-icon="inline-start" />}
                            Mark reached out
                          </Button>
                        )}
                        {rowError?.id === lead.id && (
                          <span role="alert" className="max-w-52 text-right text-xs text-destructive">
                            {rowError.message}
                          </span>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
          </TableBody>
        </Table>
      </div>

      {status.kind === "ready" && <Pagination page={page} pageSize={PAGE_SIZE} total={status.total} hrefFor={listHref} />}
    </div>
  );
}

function Th({ className, children }: { className?: string; children: React.ReactNode }) {
  return <TableHead className={cn("eyebrow h-10 text-muted-foreground", className)}>{children}</TableHead>;
}
