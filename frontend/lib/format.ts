const dateTime = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  year: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : dateTime.format(d);
}

const stateLabels = { PENDING: "Pending", REACHED_OUT: "Reached out" } as const;

export function stateLabel(state: keyof typeof stateLabels | string): string {
  return (stateLabels as Record<string, string>)[state] ?? state;
}
