"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface DataPoint {
  day: string;
  queries: number;
  cacheHits: number;
  latencyMs: number;
}

const mockData: DataPoint[] = [
  { day: "Mon", queries: 145, cacheHits: 98, latencyMs: 12 },
  { day: "Tue", queries: 232, cacheHits: 180, latencyMs: 9 },
  { day: "Wed", queries: 310, cacheHits: 245, latencyMs: 8 },
  { day: "Thu", queries: 290, cacheHits: 215, latencyMs: 11 },
  { day: "Fri", queries: 420, cacheHits: 350, latencyMs: 6 },
  { day: "Sat", queries: 210, cacheHits: 170, latencyMs: 7 },
  { day: "Sun", queries: 185, cacheHits: 140, latencyMs: 8 },
];

const metricLabels = {
  queries: "Questions",
  cacheHits: "Quick replies",
  latencyMs: "Response time",
} as const;

export function AnalyticsChart() {
  const [activeMetric, setActiveMetric] = useState<keyof typeof metricLabels>("queries");
  const [hoveredPoint, setHoveredPoint] = useState<DataPoint | null>(null);
  const maxValue = Math.max(...mockData.map((datum) => datum[activeMetric]));

  return (
    <Card>
      <CardHeader className="gap-4 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
        <div>
          <CardTitle className="text-base">Activity</CardTitle>
          <CardDescription className="mt-1 text-xs">A seven-day view of your workspace.</CardDescription>
        </div>

        <div className="inline-flex w-fit rounded-lg border border-border bg-muted/40 p-1">
          {(Object.keys(metricLabels) as Array<keyof typeof metricLabels>).map((metric) => (
            <button
              key={metric}
              type="button"
              onClick={() => setActiveMetric(metric)}
              className={`rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors ${
                activeMetric === metric
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {metricLabels[metric]}
            </button>
          ))}
        </div>
      </CardHeader>

      <CardContent>
        <div className="relative pt-5">
          {hoveredPoint && (
            <div className="absolute right-0 top-0 rounded-md border border-border bg-card px-2.5 py-1 text-xs shadow-sm">
              <span className="font-medium">{hoveredPoint.day}</span>
              <span className="ml-2 text-muted-foreground">
                {activeMetric === "latencyMs"
                  ? `${hoveredPoint.latencyMs} ms`
                  : activeMetric === "cacheHits"
                    ? `${hoveredPoint.cacheHits} replies`
                    : `${hoveredPoint.queries} questions`}
              </span>
            </div>
          )}

          <div className="flex h-56 items-end gap-3 px-1 pb-1 pt-8 sm:gap-5">
            {mockData.map((datum) => {
              const heightPercent = Math.max((datum[activeMetric] / maxValue) * 100, 8);
              return (
                <div
                  key={datum.day}
                  onMouseEnter={() => setHoveredPoint(datum)}
                  onMouseLeave={() => setHoveredPoint(null)}
                  className="group flex flex-1 cursor-pointer flex-col items-center gap-2"
                >
                  <div className="flex h-44 w-full items-end justify-center">
                    <div
                      style={{ height: `${heightPercent}%` }}
                      className={`w-full max-w-10 rounded-t-md transition-opacity group-hover:opacity-100 ${
                        activeMetric === "latencyMs"
                          ? "bg-emerald-500/75 opacity-65"
                          : activeMetric === "cacheHits"
                            ? "bg-sky-500/75 opacity-65"
                            : "bg-primary/75 opacity-65"
                      }`}
                    />
                  </div>
                  <span className="text-xs text-muted-foreground group-hover:text-foreground">{datum.day}</span>
                </div>
              );
            })}
          </div>

          <div className="mt-4 border-t border-border/70 pt-3 text-xs text-muted-foreground">
            Last 7 days
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
