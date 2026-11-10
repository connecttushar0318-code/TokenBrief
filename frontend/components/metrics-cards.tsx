import { Bot, Clock, Layers, ShieldCheck, Zap } from "lucide-react";

interface MetricsData {
  totalDocuments: number;
  totalPages?: number;
  averageLatencyMs: number;
  securityStatus: string;
  activeEngine?: string;
}

export function MetricsCards({ data }: { data: MetricsData }) {
  const items = [
    {
      title: "TOTAL UPLOADED DOCUMENTS",
      value: `${data.totalDocuments} ${data.totalDocuments === 1 ? "File" : "Files"}`,
      badge: "Library",
      detail: `${data.totalPages || data.totalDocuments * 8} Pages indexed`,
      icon: Layers,
      color: "text-indigo-500 bg-indigo-500/10 border-indigo-500/20",
    },
    {
      title: "AI REASONING ENGINE",
      value: data.activeEngine || "Gemini 2.5 Pro",
      badge: "Unified RAG",
      detail: "Full-digest synthesis",
      icon: Bot,
      color: "text-amber-500 bg-amber-500/10 border-amber-500/20",
    },
    {
      title: "AVERAGE RESPONSE TIME",
      value: `${data.averageLatencyMs} ms`,
      badge: "Real-time",
      detail: "Sub-second hybrid lookup",
      icon: Zap,
      color: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20",
    },
    {
      title: "ZERO-LEAK SECURITY",
      value: data.securityStatus || "Active",
      badge: "Isolated",
      detail: "Neon DB SSL pgvector",
      icon: ShieldCheck,
      color: "text-purple-500 bg-purple-500/10 border-purple-500/20",
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <div
            key={item.title}
            className="group relative overflow-hidden rounded-2xl border border-border/80 bg-card/60 p-4 backdrop-blur-sm transition-all duration-200 hover:border-primary/40 hover:bg-card/90 hover:shadow-md"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                {item.title}
              </span>
              <div className={`flex h-7 w-7 items-center justify-center rounded-lg border ${item.color}`}>
                <Icon className="h-3.5 w-3.5" />
              </div>
            </div>

            <div className="mt-2.5 flex items-baseline gap-2">
              <span className="text-xl font-extrabold tracking-tight text-foreground">
                {item.value}
              </span>
            </div>

            <div className="mt-1 flex items-center justify-between text-[11px] text-muted-foreground">
              <span>{item.detail}</span>
              <span className="rounded-full bg-muted/60 px-1.5 py-0.5 text-[9px] font-semibold text-muted-foreground group-hover:text-foreground">
                {item.badge}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
