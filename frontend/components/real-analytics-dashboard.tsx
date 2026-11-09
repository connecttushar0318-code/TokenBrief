"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  Clock,
  Database,
  Layers,
  PieChart as PieIcon,
  RefreshCw,
  Zap,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface DailyStat {
  date: string;
  query_count: number;
  average_latency_ms: number;
}

interface ModelStat {
  model_name: string;
  usage_count: number;
  percentage: number;
}

interface DocumentStat {
  document_id: number | null;
  filename: string;
  query_count: number;
}

interface RecentQuery {
  id: number;
  question_text: string;
  document_id: number | null;
  latency_ms: number;
  cache_hit: boolean;
  model_used: string;
  created_at: string;
}

interface DashboardData {
  total_queries: number;
  average_latency_ms: number;
  cache_hit_ratio_percentage: number;
  total_tokens_estimated: number;
  daily_trends: DailyStat[];
  model_breakdown: ModelStat[];
  popular_documents: DocumentStat[];
  recent_queries: RecentQuery[];
}

const PIE_COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ec4899", "#06b6d4", "#8b5cf6"];

export function RealAnalyticsDashboard({ apiBaseUrl }: { apiBaseUrl: string }) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hoveredSlice, setHoveredSlice] = useState<number | null>(null);

  const fetchAnalytics = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/api/analytics/dashboard`, {
        credentials: "include",
      });
      if (response.ok) {
        const json = await response.json();
        setData(json);
      }
    } catch (err) {
      console.error("Failed to load analytics:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [apiBaseUrl]);

  if (isLoading && !data) {
    return (
      <Card className="border-border/80 bg-card/60">
        <CardContent className="flex h-64 items-center justify-center">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <RefreshCw className="h-4 w-4 animate-spin text-primary" />
            <span>Loading live telemetry from PostgreSQL...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const modelStats = data?.model_breakdown || [];
  const totalModelQueries = modelStats.reduce((sum, item) => sum + item.usage_count, 0);

  let cumulativeAngle = 0;
  const pieSlices = modelStats.map((stat, idx) => {
    const fraction = totalModelQueries > 0 ? stat.usage_count / totalModelQueries : 0;
    const startAngle = cumulativeAngle;
    const endAngle = cumulativeAngle + fraction * 2 * Math.PI;
    cumulativeAngle = endAngle;

    const r = 80;
    const cx = 100;
    const cy = 100;
    const innerR = 48;

    const x1 = cx + r * Math.cos(startAngle);
    const y1 = cy + r * Math.sin(startAngle);
    const x2 = cx + r * Math.cos(endAngle);
    const y2 = cy + r * Math.sin(endAngle);

    const ix1 = cx + innerR * Math.cos(endAngle);
    const iy1 = cy + innerR * Math.sin(endAngle);
    const ix2 = cx + innerR * Math.cos(startAngle);
    const iy2 = cy + innerR * Math.sin(startAngle);

    const largeArc = fraction > 0.5 ? 1 : 0;

    const pathData =
      fraction >= 0.999
        ? `M ${cx} ${cy - r} A ${r} ${r} 0 1 1 ${cx - 0.01} ${cy - r} L ${cx - 0.01} ${cy - innerR} A ${innerR} ${innerR} 0 1 0 ${cx} ${cy - innerR} Z`
        : `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} L ${ix1} ${iy1} A ${innerR} ${innerR} 0 ${largeArc} 0 ${ix2} ${iy2} Z`;

    return {
      pathData,
      color: PIE_COLORS[idx % PIE_COLORS.length],
      stat,
      index: idx,
    };
  });

  const maxDailyCount = Math.max(...(data?.daily_trends.map((d) => d.query_count) || [1]), 1);

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-xl font-bold tracking-tight">Real-Time Systems Telemetry</h2>
          <p className="text-xs text-muted-foreground">
            Live metrics from PostgreSQL, Semantic Cache, and RRF Reranker
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchAnalytics}
          disabled={isLoading}
          className="gap-1.5 text-xs h-8"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
          <span>Refresh Telemetry</span>
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Card className="border-border/80 bg-card/60 p-4">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Activity className="h-4 w-4 text-primary" />
            <span>Total Queries</span>
          </div>
          <p className="mt-2 text-2xl font-black">{data?.total_queries ?? 0}</p>
          <p className="text-[11px] text-muted-foreground">Stored in query_logs</p>
        </Card>

        <Card className="border-border/80 bg-card/60 p-4">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="h-4 w-4 text-indigo-500" />
            <span>Avg Response</span>
          </div>
          <p className="mt-2 text-2xl font-black">{data?.average_latency_ms ?? 0} ms</p>
          <p className="text-[11px] text-muted-foreground">True database latency</p>
        </Card>

        <Card className="border-border/80 bg-card/60 p-4">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Zap className="h-4 w-4 text-emerald-500" />
            <span>Cache Hit Rate</span>
          </div>
          <p className="mt-2 text-2xl font-black">{data?.cache_hit_ratio_percentage ?? 0}%</p>
          <p className="text-[11px] text-muted-foreground">Cosine similarity &ge; 0.94</p>
        </Card>

        <Card className="border-border/80 bg-card/60 p-4">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Database className="h-4 w-4 text-amber-500" />
            <span>Est. Tokens</span>
          </div>
          <p className="mt-2 text-2xl font-black">{data?.total_tokens_estimated?.toLocaleString() ?? 0}</p>
          <p className="text-[11px] text-muted-foreground">Prompt + context volume</p>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-border/80 bg-card/60">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <PieIcon className="h-4 w-4 text-primary" />
                  <span>Model &amp; Engine Distribution</span>
                </CardTitle>
                <CardDescription className="text-xs">
                  Proportion of queries served by Cache, Pro, Flash, or Fallback
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {modelStats.length === 0 ? (
              <div className="flex h-52 items-center justify-center text-xs text-muted-foreground">
                No model queries recorded yet.
              </div>
            ) : (
              <div className="flex flex-col items-center gap-6 sm:flex-row sm:justify-around">
                <div className="relative flex h-52 w-52 shrink-0 items-center justify-center">
                  <svg viewBox="0 0 200 200" className="h-full w-full transform -rotate-90">
                    {pieSlices.map((slice) => (
                      <path
                        key={slice.index}
                        d={slice.pathData}
                        fill={slice.color}
                        className="cursor-pointer transition-opacity duration-200 hover:opacity-85"
                        onMouseEnter={() => setHoveredSlice(slice.index)}
                        onMouseLeave={() => setHoveredSlice(null)}
                      />
                    ))}
                  </svg>
                  <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
                    <span className="text-xs text-muted-foreground">
                      {hoveredSlice !== null ? modelStats[hoveredSlice]?.model_name : "Total Queries"}
                    </span>
                    <span className="text-xl font-extrabold tracking-tight">
                      {hoveredSlice !== null ? `${modelStats[hoveredSlice]?.percentage}%` : totalModelQueries}
                    </span>
                  </div>
                </div>

                <div className="space-y-2 w-full max-w-xs">
                  {modelStats.map((item, idx) => (
                    <div
                      key={item.model_name}
                      onMouseEnter={() => setHoveredSlice(idx)}
                      onMouseLeave={() => setHoveredSlice(null)}
                      className={`flex items-center justify-between p-1.5 rounded-lg text-xs transition-colors cursor-pointer ${
                        hoveredSlice === idx ? "bg-muted" : ""
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate">
                        <div
                          className="h-3 w-3 rounded-full shrink-0"
                          style={{ backgroundColor: PIE_COLORS[idx % PIE_COLORS.length] }}
                        />
                        <span className="font-medium truncate">{item.model_name}</span>
                      </div>
                      <div className="flex items-center gap-2 font-mono">
                        <span className="text-muted-foreground">{item.usage_count}</span>
                        <span className="font-bold">{item.percentage}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-border/80 bg-card/60">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Activity className="h-4 w-4 text-indigo-500" />
              <span>Query Activity Timeline</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Daily query volumes over the past 30 days
            </CardDescription>
          </CardHeader>
          <CardContent>
            {(!data?.daily_trends || data.daily_trends.length === 0) ? (
              <div className="flex h-52 items-center justify-center text-xs text-muted-foreground">
                No daily query trends recorded yet.
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex h-44 items-end gap-2 pt-6">
                  {data.daily_trends.map((day) => {
                    const heightPercent = Math.max(10, Math.round((day.query_count / maxDailyCount) * 100));
                    return (
                      <div key={day.date} className="flex-1 flex flex-col items-center gap-1 group relative">
                        <div className="absolute -top-7 hidden group-hover:flex px-2 py-0.5 rounded bg-popover text-popover-foreground text-[10px] font-mono shadow-md border z-10 whitespace-nowrap">
                          {day.date}: {day.query_count} queries ({day.average_latency_ms} ms)
                        </div>
                        <div
                          className="w-full bg-gradient-to-t from-primary/80 to-indigo-500 rounded-t-md transition-all group-hover:brightness-125"
                          style={{ height: `${heightPercent}%` }}
                        />
                        <span className="text-[10px] text-muted-foreground truncate max-w-full">
                          {day.date.slice(5)}
                        </span>
                      </div>
                    );
                  })}
                </div>
                <div className="flex justify-between text-[11px] text-muted-foreground pt-2 border-t">
                  <span>Earliest recorded date</span>
                  <span>Today</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="border-border/80 bg-card/60">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Recent Queries Log</CardTitle>
          <CardDescription className="text-xs">
            Live query stream showing exact measured latency and model routing
          </CardDescription>
        </CardHeader>
        <CardContent>
          {(!data?.recent_queries || data.recent_queries.length === 0) ? (
            <p className="text-xs text-muted-foreground py-4 text-center">No query logs yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b text-muted-foreground font-semibold">
                    <th className="pb-2">Query Excerpt</th>
                    <th className="pb-2">Model Used</th>
                    <th className="pb-2">Measured Latency</th>
                    <th className="pb-2">Cache Status</th>
                    <th className="pb-2">Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40">
                  {data.recent_queries.map((q) => (
                    <tr key={q.id} className="hover:bg-muted/30">
                      <td className="py-2.5 max-w-xs truncate pr-4 font-medium">{q.question_text}</td>
                      <td className="py-2.5 text-muted-foreground">{q.model_used}</td>
                      <td className="py-2.5 font-mono">{q.latency_ms} ms</td>
                      <td className="py-2.5">
                        {q.cache_hit ? (
                          <Badge variant="secondary" className="bg-emerald-500/10 text-emerald-600 border-emerald-500/20 text-[10px] gap-1">
                            <Zap className="h-3 w-3" /> Hit
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-[10px]">Miss</Badge>
                        )}
                      </td>
                      <td className="py-2.5 text-muted-foreground">{new Date(q.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
