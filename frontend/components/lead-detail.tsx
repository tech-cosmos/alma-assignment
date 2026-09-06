"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Check, Loader2 } from "lucide-react";

import { type ApiFailure, type LeadDetail as LeadDetailData, type LeadNote, getLead, logout, markReachedOut } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { CopyButton } from "@/components/copy-button";
import { LeadTimeline } from "@/components/lead-timeline";
import { NoteComposer } from "@/components/note-composer";
import { RelativeTime } from "@/components/relative-time";
import { ResumeViewer } from "@/components/resume-viewer";
import { StateBadge } from "@/components/state-badge";

type Status =
  | { kind: "loading" }
  | { kind: "missing" }
  | { kind: "error"; error: ApiFailure }
  | { kind: "ready"; lead: LeadDetailData };

export function LeadDetail({ id }: { id: string }) {
  const router = useRouter();
  const [status, setStatus] = useState<Status>({ kind: "loading" });
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(
    async (options: { quiet?: boolean } = {}) => {
      if (!options.quiet) setStatus({ kind: "loading" });
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
    },
    [id, router],
  );

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
      // Show the new state immediately, then pull the history entry the server just wrote.
      setStatus({ kind: "ready", lead: { ...status.lead, ...result.data } });
      void load({ quiet: true });
      return;
    }
    if (result.error.status === 401) {
      await logout();
      router.replace(`/login?next=${encodeURIComponent(`/leads/${id}`)}`);
      return;
    }
    setActionError(result.error.message);
    if (result.error.status === 409 || result.error.status === 404) void load({ quiet: true });
  }

  function noteAdded(note: LeadNote) {
    // The server returned the stored row, so append it directly; no reload needed.
    setStatus((current) => (current.kind === "ready" ? { kind: "ready", lead: { ...current.lead, notes: [...current.lead.notes, note] } } : current));
  }

  async function noteFailed(error: ApiFailure) {
    if (error.status === 401) {
      await logout();
      router.replace(`/login?next=${encodeURIComponent(`/leads/${id}`)}`);
      return;
    }
    setActionError(error.message);
    if (error.status === 404) void load({ quiet: true });
  }

  return (
    <div className="space-y-6">
      <Link href="/leads" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground underline-offset-4 hover:underline">
        <ArrowLeft className="size-4" />
        All leads
      </Link>

      {status.kind === "loading" && (
        <div className="space-y-6" aria-busy="true" aria-label="Loading lead">
          <span className="block h-10 w-72 animate-pulse rounded-sm bg-muted" />
          <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
            <span className="block h-64 animate-pulse rounded-xl bg-muted" />
            <span className="block h-[32rem] animate-pulse rounded-xl bg-muted" />
          </div>
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

      {status.kind === "ready" && (
        <LeadView lead={status.lead} busy={busy} error={actionError} onReachOut={reachOut} onNoteAdded={noteAdded} onNoteFailed={noteFailed} />
      )}
    </div>
  );
}

type LeadViewProps = {
  lead: LeadDetailData;
  busy: boolean;
  error: string | null;
  onReachOut: () => void;
  onNoteAdded: (note: LeadNote) => void;
  onNoteFailed: (error: ApiFailure) => void;
};

function LeadView({ lead, busy, error, onReachOut, onNoteAdded, onNoteFailed }: LeadViewProps) {
  const done = lead.state === "REACHED_OUT";
  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="space-y-2">
          <p className="eyebrow text-muted-foreground">Lead</p>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="font-display text-4xl leading-none">
              {lead.first_name} {lead.last_name}
            </h1>
            <StateBadge state={lead.state} />
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          {done ? (
            <p className="inline-flex items-center gap-1.5 text-sm text-muted-foreground">
              <Check className="size-4 text-success" />
              Reached out <RelativeTime iso={lead.reached_out_at ?? lead.updated_at} />
              {lead.reached_out_by_email && (
                <>
                  {" "}
                  by <span className="text-foreground/80">{lead.reached_out_by_email}</span>
                </>
              )}
            </p>
          ) : (
            <Button disabled={busy} onClick={onReachOut}>
              {busy && <Loader2 className="animate-spin" data-icon="inline-start" />}
              Mark reached out
            </Button>
          )}
          {error && (
            <span role="alert" className="text-xs text-destructive">
              {error}
            </span>
          )}
        </div>
      </div>

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        <div className="space-y-6">
          <Card title="Contact">
            <dl className="divide-y divide-border">
              <Row label="Email">
                <span className="flex items-center gap-1">
                  <a href={`mailto:${lead.email}`} className="truncate underline-offset-4 hover:underline">
                    {lead.email}
                  </a>
                  <CopyButton value={lead.email} label="Copy email" />
                </span>
              </Row>
              <Row label="Submitted">
                <RelativeTime iso={lead.created_at} />
                <span className="ml-2 text-xs text-muted-foreground">{formatDateTime(lead.created_at)}</span>
              </Row>
              <Row label="Reached out">
                {lead.reached_out_at ? (
                  <>
                    <RelativeTime iso={lead.reached_out_at} />
                    <span className="ml-2 text-xs text-muted-foreground">{formatDateTime(lead.reached_out_at)}</span>
                    {lead.reached_out_by_email && (
                      <span className="block text-xs text-muted-foreground">
                        by <span className="text-foreground/80">{lead.reached_out_by_email}</span>
                      </span>
                    )}
                  </>
                ) : (
                  <span className="text-muted-foreground">Not yet</span>
                )}
              </Row>
              <Row label="Lead id">
                <span className="flex items-center gap-1">
                  <code className="truncate font-mono text-xs">{lead.id}</code>
                  <CopyButton value={lead.id} label="Copy lead id" />
                </span>
              </Row>
            </dl>
          </Card>

          <Card title="History">
            <div className="border-b border-border px-5 py-4">
              <NoteComposer leadId={lead.id} onAdded={onNoteAdded} onFailure={onNoteFailed} />
            </div>
            <div className="px-5 py-4">
              <LeadTimeline events={lead.events} notes={lead.notes} />
            </div>
          </Card>
        </div>

        <ResumeViewer lead={lead} />
      </div>
    </section>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section aria-label={title} className="rounded-xl border border-border bg-card">
      <h2 className="eyebrow border-b border-border px-5 py-2.5 font-sans text-muted-foreground">{title}</h2>
      {children}
    </section>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-1 px-5 py-3 sm:grid-cols-[7rem_1fr] sm:gap-4">
      <dt className="eyebrow self-center text-muted-foreground">{label}</dt>
      <dd className="min-w-0 text-sm">{children}</dd>
    </div>
  );
}
