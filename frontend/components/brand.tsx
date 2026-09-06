import Link from "next/link";
import { cn } from "@/lib/utils";

/** Wordmark used across the public form, login, and internal header. */
export function Brand({ className, href = "/" }: { className?: string; href?: string }) {
  return (
    <Link href={href} className={cn("inline-flex items-baseline gap-2 no-underline", className)}>
      <span aria-hidden className="inline-block size-2.5 translate-y-[-1px] rotate-45 bg-brass" />
      <span className="font-display text-xl leading-none tracking-tight">Alma</span>
      <span className="eyebrow translate-y-[-1px] text-current/70">Immigration</span>
    </Link>
  );
}
