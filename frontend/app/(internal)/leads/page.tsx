import type { Metadata } from "next";
import { LeadsTable } from "@/components/leads-table";
import type { LeadState } from "@/lib/api";

export const metadata: Metadata = { title: "Leads" };
export const dynamic = "force-dynamic";

type Props = { searchParams: Promise<{ state?: string | string[]; page?: string | string[] }> };

function first(raw: string | string[] | undefined): string | undefined {
  return Array.isArray(raw) ? raw[0] : raw;
}

function parseState(raw: string | string[] | undefined): LeadState | undefined {
  const v = first(raw);
  return v === "PENDING" || v === "REACHED_OUT" ? v : undefined;
}

function parsePage(raw: string | string[] | undefined): number {
  const n = Number.parseInt(first(raw) ?? "1", 10);
  return Number.isFinite(n) && n >= 1 ? n : 1;
}

export default async function LeadsPage({ searchParams }: Props) {
  const params = await searchParams;
  return (
    <main className="space-y-6">
      <LeadsTable state={parseState(params.state)} page={parsePage(params.page)} />
    </main>
  );
}
