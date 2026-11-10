import Link from "next/link";
import { ArrowRight, Check, FileText, MessageSquare, Search, ShieldCheck } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { DinoRangerLogo } from "@/components/dino-ranger-logo";

const steps = [
  {
    number: "01",
    title: "Add your files",
    description: "Upload a PDF, text file, or Markdown document.",
    icon: FileText,
  },
  {
    number: "02",
    title: "Ask a focused question",
    description: "Use everyday language to explore what is in your documents.",
    icon: MessageSquare,
  },
  {
    number: "03",
    title: "Review the source",
    description: "Open the relevant excerpt whenever you need more context.",
    icon: Search,
  },
];

export default function HomePage() {
  return (
    <div className="page-surface min-h-screen bg-background text-foreground">
      <header className="border-b border-border/80 bg-background/75 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5 sm:px-6">
          <Link href="/" className="flex items-center gap-2.5 group" aria-label="TokenBrief home">
            <DinoRangerLogo size={36} className="group-hover:rotate-3" />
            <span className="text-lg font-extrabold tracking-tight">
              Token<span className="text-primary">Brief</span>
            </span>
          </Link>

          <div className="flex items-center gap-2 sm:gap-3">
            <ThemeToggle />
            <Link href="/login">
              <Button variant="ghost" size="sm" className="hidden sm:inline-flex">
                Sign in
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button size="sm" className="gap-1.5">
                Open workspace
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-5 pb-16 pt-14 sm:px-6 sm:pt-20">
        <section className="grid items-center gap-12 lg:grid-cols-[1.05fr_0.95fr] lg:gap-16">
          <div>
            <p className="mb-4 text-xs font-semibold uppercase tracking-[0.16em] text-primary">
              Document workspace
            </p>
            <h1 className="max-w-2xl text-4xl font-semibold tracking-tight sm:text-5xl lg:text-[3.35rem] lg:leading-[1.08]">
              Find answers in your documents, without losing the context.
            </h1>
            <p className="mt-6 max-w-xl text-base leading-7 text-muted-foreground sm:text-lg">
              Keep files in one place, ask clear questions, and follow every answer back to the source.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link href="/dashboard">
                <Button size="lg" className="gap-2">
                  Start working
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/login">
                <Button size="lg" variant="outline">
                  Sign in
                </Button>
              </Link>
            </div>

            <p className="mt-6 flex items-center gap-2 text-sm text-muted-foreground">
              <ShieldCheck className="h-4 w-4 text-primary" />
              Your workspace is available after you sign in.
            </p>
          </div>

          <div className="rounded-2xl border border-border bg-card p-5 shadow-[0_12px_36px_rgba(15,23,42,0.06)] sm:p-6">
            <div className="flex items-center justify-between border-b border-border pb-4">
              <div>
                <p className="text-sm font-semibold">A simple workflow</p>
                <p className="mt-1 text-xs text-muted-foreground">From file to source-backed answer.</p>
              </div>
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <FileText className="h-4 w-4" />
              </div>
            </div>

            <div className="divide-y divide-border/80">
              {steps.map(({ number, title, description, icon: Icon }) => (
                <div key={number} className="flex gap-4 py-5 last:pb-1">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted text-primary">
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-baseline justify-between gap-3">
                      <h2 className="text-sm font-semibold">{title}</h2>
                      <span className="text-[11px] font-medium text-muted-foreground">{number}</span>
                    </div>
                    <p className="mt-1 text-sm leading-6 text-muted-foreground">{description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mt-20 border-t border-border pt-10 sm:mt-24 sm:pt-12">
          <div className="mb-7 max-w-xl">
            <h2 className="text-2xl font-semibold tracking-tight">Built around the work you need to do.</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              No extra dashboards to decode—just the files, questions, and source details that matter.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {[
              ["Keep a clear library", "See your uploaded documents and focus a question on one file when needed."],
              ["Ask in plain language", "Start with a suggested question or write your own in the workspace."],
              ["Check the evidence", "Open the source excerpt behind an answer before you rely on it."],
            ].map(([title, description]) => (
              <div key={title} className="rounded-xl border border-border bg-card/60 p-5">
                <Check className="h-4 w-4 text-primary" />
                <h3 className="mt-4 text-sm font-semibold">{title}</h3>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{description}</p>
              </div>
            ))}
          </div>
        </section>
      </main>

      <footer className="border-t border-border/80 py-6 text-center text-xs text-muted-foreground">
        TokenBrief · Smart Document Intelligence & Workspace
      </footer>
    </div>
  );
}
