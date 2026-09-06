import type { Metadata } from "next";
import { LeadsTable } from "@/components/leads-table";
import type { LeadState } from "@/lib/api";

export const metadata: Metadata = { title: "Leads" };
export const dynamic = "force-dynamic";

type Props = { searchParams: Promise<{ state?: string | string[] }> };

function parseState(raw: string | string[] | undefined): LeadState | undefined {
  const v = Array.isArray(raw) ? raw[0] : raw;
  return v === "PENDING" || v === "REACHED_OUT" ? v : undefined;
}

export default async function LeadsPage({ searchParams }: Props) {
  const state = parseState((await searchParams).state);
  return (
    <main className="space-y-6">
      <LeadsTable state={state} />
    </main>
  );
}
