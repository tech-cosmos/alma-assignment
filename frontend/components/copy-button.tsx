"use client";

import { useEffect, useState } from "react";
import { Check, Copy } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Props = {
  /** Text placed on the clipboard. */
  value: string;
  /** Accessible name, e.g. "Copy email". */
  label: string;
  /** Optional visible label; without it the button is icon-only. */
  children?: React.ReactNode;
  size?: "icon-xs" | "icon-sm" | "sm" | "xs";
  className?: string;
};

/** Writes `value` to the clipboard and flashes a check mark for a moment. */
export function CopyButton({ value, label, children, size, className }: Props) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) return;
    const id = window.setTimeout(() => setCopied(false), 1600);
    return () => window.clearTimeout(id);
  }, [copied]);

  const iconOnly = children === undefined;
  return (
    <Button
      type="button"
      variant="ghost"
      size={size ?? (iconOnly ? "icon-xs" : "sm")}
      aria-label={copied ? "Copied" : label}
      title={copied ? "Copied" : label}
      className={cn(copied ? "text-success" : "text-muted-foreground hover:text-foreground", className)}
      onClick={async (e) => {
        e.stopPropagation();
        try {
          await navigator.clipboard.writeText(value);
          setCopied(true);
        } catch {
          // Clipboard access can be denied (insecure context); leave the button as-is.
        }
      }}
    >
      {copied ? <Check data-icon={iconOnly ? undefined : "inline-start"} /> : <Copy data-icon={iconOnly ? undefined : "inline-start"} />}
      {children === undefined ? null : copied ? "Copied" : children}
    </Button>
  );
}
