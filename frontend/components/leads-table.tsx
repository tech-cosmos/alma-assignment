"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Check, ExternalLink, Loader2, RefreshCw } from "lucide-react";

import { type ApiFailure, type Lead, type LeadState, listLeads, logout, markReachedOut, resumeUrl } from "@/lib/api";
import { formatDateTime, stateLabel } from "@/lib/format";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { StateFilter } from "@/components/state-filter";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 100;

type Status =
  | { kind: "loading" }
  | { kind: "error"; error: ApiFailure }
  | { kind: "ready"; leads: Lead[]; total: number };

export function LeadsTable({ state }: { state: LeadState | undefined }) {
  const router = useRouter();
  const [status, setStatus] = useState<Status>({ kind: "loading" });
  const [rowError, setRowError] = useState<{ id: string; message: string } | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setStatus({ kind: "loading" });
    const result = await listLeads({ state, limit: PAGE_SIZE });
    if (!result.ok) {
      if (result.error.status === 401) {
        // Stale or missing session: clear the cookie so middleware stops letting us through, then bounce.
        await logout();
        router.replace(`/login?next=${encodeURIComponent(state ? `/leads?state=${state}` : "/leads")}`);
        return;
      }
      setStatus({ kind: "error", error: result.error });
      return;
    }
    setStatus({ kind: "ready", leads: result.data.items, total: result.data.total });
  }, [state, router]);

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
      return;
    }
    if (result.error.status === 401) {
      await logout();
      router.replace("/login?next=/leads");
      return;
    }
    setRowError({ id: lead.id, message: result.error.message });
    if (result.error.status === 409 || result.error.status === 404) void load();
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
          <StateFilter value={state} />
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
              <Th>First name</Th>
              <Th>Last name</Th>
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
                  {Array.from({ length: 8 }).map((_, j) => (
                    <TableCell key={j}>
                      <span className="block h-3.5 w-full max-w-28 animate-pulse rounded-sm bg-muted" />
                    </TableCell>
                  ))}
                </TableRow>
              ))}

            {status.kind === "ready" && status.leads.length === 0 && (
              <TableRow className="hover:bg-transparent">
                <TableCell colSpan={8} className="h-32 text-center text-muted-foreground">
                  {state ? `No ${stateLabel(state).toLowerCase()} leads.` : "No leads yet. Submissions from the public form appear here."}
                </TableCell>
              </TableRow>
            )}

            {status.kind === "ready" &&
              status.leads.map((lead) => {
                const done = lead.state === "REACHED_OUT";
                const busy = busyId === lead.id;
                return (
                  <TableRow key={lead.id} className="align-top">
                    <TableCell className="font-medium">{lead.first_name}</TableCell>
                    <TableCell className="font-medium">{lead.last_name}</TableCell>
                    <TableCell>
                      <a href={`mailto:${lead.email}`} className="underline-offset-4 hover:underline">
                        {lead.email}
                      </a>
                    </TableCell>
                    <TableCell>
                      <a
                        href={resumeUrl(lead.id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex max-w-56 items-center gap-1.5 underline-offset-4 hover:underline"
                        title={`${lead.resume_name} (${lead.resume_type})`}
                      >
                        <span className="truncate">{lead.resume_name}</span>
                        <ExternalLink className="size-3.5 shrink-0 text-muted-foreground" />
                      </a>
                    </TableCell>
                    <TableCell>
                      <StateBadge state={lead.state} />
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-muted-foreground">{formatDateTime(lead.created_at)}</TableCell>
                    <TableCell className="whitespace-nowrap text-muted-foreground">
                      {lead.reached_out_at ? formatDateTime(lead.reached_out_at) : <span aria-label="not yet">—</span>}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex flex-col items-end gap-1">
                        <Button
                          size="sm"
                          variant={done ? "secondary" : "default"}
                          disabled={done || busy}
                          aria-disabled={done}
                          onClick={() => void reachOut(lead)}
                        >
                          {busy ? (
                            <Loader2 className="animate-spin" data-icon="inline-start" />
                          ) : done ? (
                            <Check data-icon="inline-start" />
                          ) : null}
                          {done ? "Reached out" : "Mark reached out"}
                        </Button>
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
    </div>
  );
}

function Th({ className, children }: { className?: string; children: React.ReactNode }) {
  return <TableHead className={cn("eyebrow h-10 text-muted-foreground", className)}>{children}</TableHead>;
}

function StateBadge({ state }: { state: LeadState }) {
  return state === "REACHED_OUT" ? (
    <Badge className="bg-success text-success-foreground">Reached out</Badge>
  ) : (
    <Badge variant="outline" className="border-brass/60 bg-brass/10 text-brass-foreground">
      Pending
    </Badge>
  );
}
