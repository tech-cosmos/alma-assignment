import type { LeadState } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

export function StateBadge({ state }: { state: LeadState }) {
  return state === "REACHED_OUT" ? (
    <Badge className="bg-success text-success-foreground">Reached out</Badge>
  ) : (
    <Badge variant="outline" className="border-brass/60 bg-brass/10 text-brass-foreground">
      Pending
    </Badge>
  );
}
