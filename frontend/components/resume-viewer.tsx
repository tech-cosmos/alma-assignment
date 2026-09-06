"use client";

import { useState } from "react";
import { Download, ExternalLink, FileText, Loader2 } from "lucide-react";

import { type Lead, resumeUrl } from "@/lib/api";
import { resumeKind, resumeKindLabel } from "@/lib/format";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CopyButton } from "@/components/copy-button";

type Props = { lead: Pick<Lead, "id" | "resume_name" | "resume_type"> };

/**
 * Shows a PDF right on the page; other formats get a download card because browsers cannot
 * render Word documents. The toolbar always offers the shareable link, a new-tab view, and a
 * forced download.
 */
export function ResumeViewer({ lead }: Props) {
  const kind = resumeKind(lead.resume_type);
  const label = resumeKindLabel(kind);
  const viewUrl = resumeUrl(lead.id);
  const downloadUrl = resumeUrl(lead.id, { download: true });
  const [loaded, setLoaded] = useState(false);

  return (
    <section id="resume" aria-label="Resume" className="scroll-mt-20 overflow-hidden rounded-xl border border-border bg-card">
      <header className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-b border-border px-4 py-2.5">
        <div className="flex min-w-0 items-center gap-2">
          <FileText className="size-4 shrink-0 text-muted-foreground" />
          <span className="truncate text-sm font-medium" title={lead.resume_name}>
            {lead.resume_name}
          </span>
          <Badge variant="outline" className="shrink-0 text-[0.65rem] tracking-wider">
            {label}
          </Badge>
        </div>
        <div className="flex items-center gap-0.5">
          <Button asChild variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
            <a href={viewUrl} target="_blank" rel="noopener noreferrer" className="no-underline">
              <ExternalLink data-icon="inline-start" /> Open in new tab
            </a>
          </Button>
          <Button asChild variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
            <a href={downloadUrl} className="no-underline">
              <Download data-icon="inline-start" /> Download
            </a>
          </Button>
          <CopyButton value={viewUrl} label="Copy resume link">
            Copy link
          </CopyButton>
        </div>
      </header>

      {kind === "pdf" ? (
        <div className="relative bg-muted/40">
          {!loaded && (
            <div className="absolute inset-0 flex items-center justify-center gap-2 text-sm text-muted-foreground" aria-hidden>
              <Loader2 className="size-4 animate-spin" /> Loading preview
            </div>
          )}
          {/* <object> (not <iframe>) so a browser without a PDF viewer renders the fallback below. */}
          <object
            data={`${viewUrl}#view=FitH`}
            type="application/pdf"
            aria-label={`Resume preview: ${lead.resume_name}`}
            className="relative block h-[70vh] min-h-[32rem] w-full"
            onLoad={() => setLoaded(true)}
          >
            <Fallback name={lead.resume_name} downloadUrl={downloadUrl} viewUrl={viewUrl}>
              This browser can&apos;t display PDFs inline. Open it in a new tab or download it instead.
            </Fallback>
          </object>
        </div>
      ) : (
        <Fallback name={lead.resume_name} downloadUrl={downloadUrl}>
          {kind === "other" ? "This file type" : "Word documents"} can&apos;t be previewed in the browser. Download it to open in Word or
          Pages.
        </Fallback>
      )}
    </section>
  );
}

function Fallback({
  name,
  downloadUrl,
  viewUrl,
  children,
}: {
  name: string;
  downloadUrl: string;
  viewUrl?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="relative flex h-full flex-col items-center justify-center gap-3 bg-card px-6 py-14 text-center">
      <span className="flex size-12 items-center justify-center rounded-lg bg-muted text-muted-foreground">
        <FileText className="size-6" />
      </span>
      <p className="text-sm font-medium">{name}</p>
      <p className="max-w-sm text-sm leading-relaxed text-muted-foreground">{children}</p>
      <div className="flex flex-wrap items-center justify-center gap-2">
        {viewUrl && (
          <Button asChild variant="outline">
            <a href={viewUrl} target="_blank" rel="noopener noreferrer" className="no-underline">
              <ExternalLink data-icon="inline-start" /> Open in new tab
            </a>
          </Button>
        )}
        <Button asChild>
          <a href={downloadUrl} className="no-underline">
            <Download data-icon="inline-start" /> Download
          </a>
        </Button>
      </div>
    </div>
  );
}
