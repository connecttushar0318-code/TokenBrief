import { Clock, FileText, ShieldCheck } from "lucide-react";

interface MetricsData {
  totalDocuments: number;
  averageLatencyMs: number;
  securityStatus: string;
}

export function MetricsCards({ data }: { data: MetricsData }) {
  const items = [
    {
      label: "Documents",
      value: data.totalDocuments,
      detail: "ready to search",
      icon: FileText,
    },
    {
      label: "Average response",
      value: `${data.averageLatencyMs} ms`,
      detail: "for recent questions",
      icon: Clock,
    },
    {
      label: "Workspace access",
      value: data.securityStatus,
      detail: "signed-in session",
      icon: ShieldCheck,
    },
  ];

  return (
    <dl className="grid gap-3 sm:grid-cols-3">
      {items.map(({ label, value, detail, icon: Icon }) => (
        <div
          key={label}
          className="flex items-center gap-3 rounded-xl border border-border/80 bg-card/70 px-4 py-3"
        >
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Icon className="h-4 w-4" />
          </div>
          <div className="min-w-0">
            <dt className="text-xs text-muted-foreground">{label}</dt>
            <dd className="mt-0.5 text-sm font-semibold tracking-tight">{value}</dd>
            <p className="text-[11px] text-muted-foreground">{detail}</p>
          </div>
        </div>
      ))}
    </dl>
  );
}
