"use client";

import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";

type Props = {
  /** 1-based current page. */
  page: number;
  pageSize: number;
  total: number;
  hrefFor: (page: number) => string;
};

/** "Showing 1–50 of 132" with previous/next links. Renders nothing when everything fits on one page. */
export function Pagination({ page, pageSize, total, hrefFor }: Props) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  if (total <= pageSize && page === 1) return null;

  const first = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const last = Math.min(page * pageSize, total);
  const hasPrev = page > 1;
  const hasNext = page < pages;

  return (
    <nav aria-label="Pagination" className="flex flex-wrap items-center justify-between gap-3 text-sm text-muted-foreground">
      <p>
        {total === 0 ? (
          "Nothing on this page."
        ) : (
          <>
            Showing <span className="tabular-nums text-foreground">{first}</span>–<span className="tabular-nums text-foreground">{last}</span> of{" "}
            <span className="tabular-nums text-foreground">{total}</span>
          </>
        )}
      </p>
      <div className="flex items-center gap-1">
        <PageLink href={hrefFor(page - 1)} disabled={!hasPrev} label="Previous page">
          <ChevronLeft /> Previous
        </PageLink>
        <span className="px-2 tabular-nums">
          Page {page} of {pages}
        </span>
        <PageLink href={hrefFor(page + 1)} disabled={!hasNext} label="Next page">
          Next <ChevronRight />
        </PageLink>
      </div>
    </nav>
  );
}

function PageLink({ href, disabled, label, children }: { href: string; disabled: boolean; label: string; children: React.ReactNode }) {
  if (disabled) {
    return (
      <Button variant="outline" size="sm" disabled aria-label={label}>
        {children}
      </Button>
    );
  }
  return (
    <Button asChild variant="outline" size="sm">
      <Link href={href} aria-label={label} className="no-underline">
        {children}
      </Link>
    </Button>
  );
}
