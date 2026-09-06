import type { Metadata } from "next";
import { LeadDetail } from "@/components/lead-detail";

export const metadata: Metadata = { title: "Lead" };
export const dynamic = "force-dynamic";

type Props = { params: Promise<{ id: string }> };

/** Target of the link in the attorney notification email: PUBLIC_WEB_URL/leads/{id}. */
export default async function LeadPage({ params }: Props) {
  const { id } = await params;
  return (
    <main className="space-y-6">
      <LeadDetail id={id} />
    </main>
  );
}
