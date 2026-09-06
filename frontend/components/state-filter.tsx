"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";

import type { LeadState } from "@/lib/api";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const ALL = "ALL";

export function StateFilter({ value }: { value: LeadState | undefined }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  return (
    <Select
      value={value ?? ALL}
      onValueChange={(v) => {
        startTransition(() => {
          router.push(v === ALL ? "/leads" : `/leads?state=${v}`);
        });
      }}
    >
      <SelectTrigger className="w-44" aria-label="Filter by state" data-pending={pending || undefined}>
        <SelectValue placeholder="All states" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>All states</SelectItem>
        <SelectItem value="PENDING">Pending</SelectItem>
        <SelectItem value="REACHED_OUT">Reached out</SelectItem>
      </SelectContent>
    </Select>
  );
}
