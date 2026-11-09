"use client";

import dynamic from "next/dynamic";
import { Card, CardHeader, CardContent } from "@/components/ui/card";

function ChartSkeleton() {
  return (
    <Card className="col-span-1 lg:col-span-2 animate-pulse">
      <CardHeader className="space-y-2">
        <div className="h-6 w-48 bg-muted rounded-md" />
        <div className="h-4 w-72 bg-muted/60 rounded-md" />
      </CardHeader>
      <CardContent>
        <div className="h-64 flex items-end gap-4 pt-8">
          {[40, 65, 80, 70, 95, 50, 45].map((h, i) => (
            <div key={i} className="flex-1 flex flex-col items-center gap-2">
              <div
                style={{ height: `${h}%` }}
                className="w-full max-w-[42px] bg-muted/70 rounded-t-md"
              />
              <div className="h-3 w-6 bg-muted/50 rounded" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export const DynamicAnalyticsChart = dynamic(
  () => import("./analytics-chart").then((mod) => mod.AnalyticsChart),
  {
    ssr: false,
    loading: () => <ChartSkeleton />,
  }
);
