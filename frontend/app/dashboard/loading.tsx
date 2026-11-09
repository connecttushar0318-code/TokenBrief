export default function DashboardLoading() {
  return (
    <div className="min-h-screen bg-background p-6 space-y-6 animate-pulse">
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div className="h-8 w-48 bg-muted rounded-lg" />
        <div className="h-8 w-24 bg-muted rounded-full" />
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-28 bg-muted rounded-xl" />
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 h-80 bg-muted rounded-xl" />
        <div className="h-80 bg-muted rounded-xl" />
      </div>
    </div>
  );
}
