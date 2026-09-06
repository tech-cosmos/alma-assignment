"use client";

import { useEffect, useState } from "react";

import { me } from "@/lib/api";
import { initialsFromEmail } from "@/lib/format";
import { LogoutButton } from "@/components/logout-button";

/** Header slot: who is signed in (so "by <email>" in lead history is recognisable) plus sign out. */
export function UserMenu() {
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    void me().then((result) => {
      if (alive && result.ok) setEmail(result.data.email);
    });
    return () => {
      alive = false;
    };
  }, []);

  return (
    <div className="flex items-center gap-3">
      {email && (
        <span className="hidden items-center gap-2 text-sm text-muted-foreground sm:inline-flex" title={`Signed in as ${email}`}>
          <span
            aria-hidden
            className="flex size-6 items-center justify-center rounded-full bg-ink font-display text-[0.65rem] font-semibold text-ink-foreground"
          >
            {initialsFromEmail(email)}
          </span>
          <span className="max-w-56 truncate">{email}</span>
        </span>
      )}
      <LogoutButton />
    </div>
  );
}
