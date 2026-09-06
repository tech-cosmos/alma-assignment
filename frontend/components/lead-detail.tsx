"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Check, ExternalLink, Loader2 } from "lucide-react";

import { type ApiFailure, type Lead, getLead, logout, markReachedOut, resumeUrl } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { StateBadge } from "@/components/state-badge";

type Status =
  | { kind: "loading" }
  | { kind: "missing" }
  | { kind: "error"; error: ApiFailure }
  | { kind: "ready"; lead: Lead };

export function LeadDetail({ id }: { id: string }) {
  const router = useRouter();
  const [status, setStatus] = useState<Status>({ kind: "loading" });
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setStatus({ kind: "loading" });
    const result = await getLead(id);
    if (result.ok) {
      setStatus({ kind: "ready", lead: result.data });
      return;
    }
    if (result.error.status === 401) {
      await logout();
      router.replace(`/login?next=${encodeURIComponent(`/leads/${id}`)}`);
      return;
    }
    // 404 from the API and 422 for a malformed UUID both mean "no such lead".
    if (result.error.status === 404 || result.error.status === 422) {
      setStatus({ kind: "missing" });
      return;
    }
    setStatus({ kind: "error", error: result.error });
  }, [id, router]);

  useEffect(() => {
    void load();
  }, [load]);

  async function reachOut() {
    if (status.kind !== "ready") return;
    setActionError(null);
    setBusy(true);
    const result = await markReachedOut(status.lead.id);
    setBusy(false);
    if (result.ok) {
      setStatus({ kind: "ready", lead: result.data });
      return;
    }
    if (result.error.status === 401) {
      await logout();
      router.replace(`/login?next=${encodeURIComponent(`/leads/${id}`)}`);
      return;
    }
    setActionError(result.error.message);
    if (result.error.status === 409 || result.error.status === 404) void load();
  }

  return (
    <div className="space-y-6">
      <Link href="/leads" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground underline-offset-4 hover:underline">
        <ArrowLeft className="size-4" />
        All leads
      </Link>

      {status.kind === "loading" && (
        <div className="space-y-3" aria-busy="true" aria-label="Loading lead">
          <span className="block h-8 w-64 animate-pulse rounded-sm bg-muted" />
          <span className="block h-40 w-full max-w-2xl animate-pulse rounded-xl bg-muted" />
        </div>
      )}

      {status.kind === "missing" && (
        <Alert>
          <AlertTitle>Lead not found</AlertTitle>
          <AlertDescription>
            <span>
              No lead exists with id <code className="font-mono text-xs">{id}</code>. It may have been removed, or the link may be incomplete.
            </span>
            <Button asChild variant="outline" size="sm" className="mt-2">
              <Link href="/leads">Back to all leads</Link>
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {status.kind === "error" && (
        <Alert variant="destructive">
          <AlertTitle>Couldn&apos;t load this lead</AlertTitle>
          <AlertDescription>
            <span>{status.error.message}</span>
            <Button variant="outline" size="sm" className="mt-2" onClick={() => void load()}>
              Try again
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {status.kind === "ready" && <LeadCard lead={status.lead} busy={busy} error={actionError} onReachOut={reachOut} />}
    </div>
  );
}

function LeadCard({ lead, busy, error, onReachOut }: { lead: Lead; busy: boolean; error: string | null; onReachOut: () => void }) {
  const done = lead.state === "REACHED_OUT";
  return (
    <section className="max-w-3xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-1">
          <p className="eyebrow text-muted-foreground">Lead</p>
          <h1 className="font-display text-4xl leading-none">
            {lead.first_name} {lead.last_name}
          </h1>
        </div>
        <StateBadge state={lead.state} />
      </div>

      <div className="rounded-xl border border-border bg-card">
        <dl className="divide-y divide-border">
          <Row label="First name">{lead.first_name}</Row>
          <Row label="Last name">{lead.last_name}</Row>
          <Row label="Email">
            <a href={`mailto:${lead.email}`} className="underline-offset-4 hover:underline">
              {lead.email}
            </a>
          </Row>
          <Row label="Resume">
            <a
              href={resumeUrl(lead.id)}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 underline-offset-4 hover:underline"
              title={lead.resume_type}
            >
              <span className="truncate">{lead.resume_name}</span>
              <ExternalLink className="size-3.5 shrink-0 text-muted-foreground" />
            </a>
          </Row>
          <Row label="Submitted">{formatDateTime(lead.created_at)}</Row>
          <Row label="Reached out">{lead.reached_out_at ? formatDateTime(lead.reached_out_at) : <span className="text-muted-foreground">Not yet</span>}</Row>
          <Row label="Lead id">
            <code className="font-mono text-xs">{lead.id}</code>
          </Row>
        </dl>
      </div>

      <div className="flex flex-col items-start gap-2">
        <Button variant={done ? "secondary" : "default"} disabled={done || busy} aria-disabled={done} onClick={onReachOut}>
          {busy ? <Loader2 className="animate-spin" data-icon="inline-start" /> : done ? <Check data-icon="inline-start" /> : null}
          {done ? "Reached out" : "Mark reached out"}
        </Button>
        {error && (
          <span role="alert" className="text-xs text-destructive">
            {error}
          </span>
        )}
      </div>
    </section>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-1 px-5 py-3.5 sm:grid-cols-[10rem_1fr] sm:gap-6">
      <dt className="eyebrow self-center text-muted-foreground">{label}</dt>
      <dd className="min-w-0 text-sm">{children}</dd>
    </div>
  );
}
