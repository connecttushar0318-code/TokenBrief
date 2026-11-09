"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  BookOpen,
  Bot,
  Check,
  Copy,
  ExternalLink,
  FileCheck2,
  FileText,
  Headphones,
  Home,
  Layers,
  LogOut,
  Search,
  Send,
  Sparkles,
  Trash2,
  User as UserIcon,
  Volume2,
  VolumeX,
  X,
} from "lucide-react";
import { DynamicAnalyticsChart } from "@/components/dynamic-analytics-chart";
import { DocumentUploadCard } from "@/components/document-upload-card";
import { MetricsCards } from "@/components/metrics-cards";
import { ThemeToggle } from "@/components/theme-toggle";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

interface SourceItem {
  chunk_id: number;
  document_filename: string;
  source_page_number: number;
  similarity_percentage: number;
  chunk_text_content: string;
}

interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  text: string;
  cacheHit?: boolean;
  sources?: SourceItem[];
  timestamp: string;
}

interface DocumentItem {
  id: number;
  filename: string;
  file_size_bytes: number;
  total_page_count: number;
  total_chunk_count: number;
  created_at: string;
}

interface SummaryData {
  document_id: number;
  filename: string;
  executive_summary: string;
  key_takeaways: string[];
  topics: string[];
}

interface ChatSuggestion {
  label: string;
  query: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const CHAT_SUGGESTIONS: ChatSuggestion[] = [
  { label: "⚡ Skill-Gap & ATS Audit", query: "Run a Skill-Gap & ATS Audit comparing the resume against the curriculum/data mining syllabus. Highlight matched skills, missing technical topics, and ATS bullet rewrites." },
  { label: "📝 Exam Prep / Viva Mode", query: "Generate 5 technical interview / exam prep questions strictly grounded in this document with answers and page citations." },
  { label: "👤 Resume Executive Profile", query: "What is this resume all about?" },
  { label: "🔬 WEKA & Data Mining Notes", query: "What is WEKA tool used for and what are the main experiments in DM File.pdf?" },
  { label: "💡 What should I know?", query: "What are the most useful things to know from my documents?" },
  { label: "🗂️ Compare my files", query: "What themes and skills are shared across my documents?" },
];

function getDocumentType(filename: string) {
  const extension = filename.split(".").pop()?.trim().toUpperCase();
  return extension || "FILE";
}

export default function DashboardPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);
  const [activeSummary, setActiveSummary] = useState<SummaryData | null>(null);
  const [summarizingDocId, setSummarizingDocId] = useState<number | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState("tushar");
  const [expandedSourceChunk, setExpandedSourceChunk] = useState<SourceItem | null>(null);
  const [chatSessionId, setChatSessionId] = useState<string | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [latencyMs, setLatencyMs] = useState(420);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleToggleAudioBrief = () => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      alert("Speech synthesis is not supported in this browser.");
      return;
    }
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }
    const lastAssistantMsg = [...messages].reverse().find((m) => m.sender === "assistant")?.text;
    const textToSpeak =
      lastAssistantMsg ||
      activeSummary?.executive_summary ||
      "Welcome to TokenBrief AI. Upload or select a document to listen to an executive summary or ask questions.";
    const cleanSpeechText = textToSpeak
      .replace(/[#*`_~]/g, "")
      .replace(/\(Source:[^)]+\)/gi, "")
      .replace(/\[Excerpt[^\]]+\]/gi, "");
    const utterance = new SpeechSynthesisUtterance(cleanSpeechText);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const fetchCurrentUser = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/me`, { credentials: "include" });
      if (response.ok) {
        const data = await response.json();
        setCurrentUser(data.username || "tushar");
      }
    } catch {}
  };

  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/documents`, { credentials: "include" });
      if (response.ok) {
        setDocuments(await response.json());
      }
    } catch {}
  };

  useEffect(() => {
    fetchCurrentUser();
    fetchDocuments();
  }, []);

  const handleAskQuestion = async (queryText?: string) => {
    const questionToAsk = queryText || inputQuery;
    if (!questionToAsk.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: "usr_" + Date.now(),
      sender: "user",
      text: questionToAsk.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((previous) => [...previous, userMsg]);
    setInputQuery("");
    setIsLoading(true);
    const requestStartTime = Date.now();

    try {
      const response = await fetch(`${API_BASE_URL}/api/qa/quick-chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          message_text: questionToAsk.trim(),
          document_id: selectedDocId,
          session_id: chatSessionId || undefined,
        }),
      });

      setLatencyMs(Date.now() - requestStartTime);

      if (!response.ok) {
        throw new Error("We could not find an answer right now.");
      }

      const data = await response.json();
      if (data.session_id) {
        setChatSessionId(data.session_id);
      }
      const assistantMsg: ChatMessage = {
        id: "ast_" + Date.now(),
        sender: "assistant",
        text: data.answer || "No response received.",
        cacheHit: Boolean(data.cache_hit),
        sources: data.sources || [],
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((previous) => [...previous, assistantMsg]);
    } catch (error: any) {
      setMessages((previous) => [
        ...previous,
        {
          id: "err_" + Date.now(),
          sender: "assistant",
          text: error.message || "An error occurred while answering your question.",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSummarizeDoc = async (docId: number) => {
    if (summarizingDocId !== null) return;

    setSummarizingDocId(docId);
    setActiveSummary(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/documents/${docId}/summary`, {
        method: "POST",
        credentials: "include",
      });
      if (!response.ok) throw new Error("Summary generation failed");
      setActiveSummary(await response.json());
    } catch (error: any) {
      alert("Failed to create a summary: " + error.message);
    } finally {
      setSummarizingDocId(null);
    }
  };

  const handleDeleteDoc = async (docId: number, event: React.MouseEvent) => {
    event.stopPropagation();
    if (!confirm("Are you sure you want to delete this document?")) return;
    try {
      const response = await fetch(`${API_BASE_URL}/api/documents/${docId}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (response.ok) {
        if (selectedDocId === docId) setSelectedDocId(null);
        if (activeSummary?.document_id === docId) setActiveSummary(null);
        fetchDocuments();
      }
    } catch (error: any) {
      alert("Failed to delete document: " + error.message);
    }
  };

  const handleSignOut = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
    } catch {}
    router.push("/login");
  };

  const handleCopyAnswer = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="page-surface min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-40 border-b border-border/80 bg-background/85 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
          <Link href="/" className="flex min-w-0 items-center gap-2.5 group" aria-label="TokenBrief home">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-primary via-indigo-500 to-purple-500 text-xs font-black text-white shadow-sm shadow-primary/25 transition-transform group-hover:scale-105">
              <span className="tracking-tighter">TB</span>
            </div>
            <div className="min-w-0">
              <p className="text-base font-extrabold tracking-tight">
                Token<span className="text-primary">Brief</span>
              </p>
              <p className="hidden text-[11px] text-muted-foreground sm:block">AI Document Workspace</p>
            </div>
          </Link>

          <div className="flex items-center gap-2 sm:gap-3">
            <div className="hidden items-center gap-2 text-sm sm:flex">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-[11px] font-bold text-primary">
                {currentUser.slice(0, 1).toUpperCase()}
              </div>
              <span className="max-w-28 truncate text-xs font-medium text-muted-foreground">{currentUser}</span>
            </div>
            <Button
              variant={isSpeaking ? "default" : "outline"}
              size="sm"
              onClick={handleToggleAudioBrief}
              className={`gap-1.5 text-xs h-8 px-2.5 ${isSpeaking ? "bg-amber-600 hover:bg-amber-700 text-white animate-pulse" : ""}`}
              title={isSpeaking ? "Stop audio briefing" : "Listen to audio brief"}
            >
              {isSpeaking ? <VolumeX className="h-3.5 w-3.5" /> : <Headphones className="h-3.5 w-3.5 text-primary" />}
              <span className="hidden sm:inline">{isSpeaking ? "Stop Brief" : "Audio Brief"}</span>
            </Button>
            <Link href="/">
              <Button variant="ghost" size="sm" className="text-xs h-8 px-2.5 gap-1.5 hidden sm:inline-flex">
                <Home className="h-3.5 w-3.5" />
                <span>Home</span>
              </Button>
            </Link>
            <ThemeToggle />
            <Button
              variant="outline"
              size="sm"
              onClick={handleSignOut}
              className="gap-1.5 text-xs h-8 px-2.5"
              title="Sign out"
            >
              <LogOut className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Sign out</span>
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl space-y-6 px-4 py-8 sm:px-6 sm:py-10">
        <section className="flex flex-col justify-between gap-5 border-b border-border/80 pb-7 sm:flex-row sm:items-end">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary">Workspace</p>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">Work with your documents</h1>
            <p className="mt-2 max-w-xl text-sm leading-6 text-muted-foreground">
              Add a file, ask a question, and check the source behind each answer.
            </p>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <FileText className="h-4 w-4 text-primary" />
            <span>{documents.length} {documents.length === 1 ? "document" : "documents"} in your library</span>
          </div>
        </section>

        <MetricsCards
          data={{
            totalDocuments: documents.length,
            averageLatencyMs: latencyMs,
            securityStatus: "Active",
          }}
        />

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_21rem]">
          <div className="space-y-6">
            <Card className="flex h-[640px] min-h-[560px] flex-col">
              <CardHeader className="gap-3 border-b border-border/75 pb-4 sm:flex-row sm:items-start sm:justify-between sm:space-y-0">
                <div>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Bot className="h-4 w-4 text-primary" />
                    Ask a question
                  </CardTitle>
                  <CardDescription className="mt-1 text-xs">
                    Answers are based on the documents in your library.
                  </CardDescription>
                </div>

                <div className="flex items-center gap-2">
                  <label className="sr-only" htmlFor="document-filter">Choose a document</label>
                  <select
                    id="document-filter"
                    value={selectedDocId ?? ""}
                    onChange={(event) => {
                      setSelectedDocId(event.target.value ? Number(event.target.value) : null);
                      setChatSessionId(null);
                    }}
                    className="h-8 max-w-48 rounded-lg border border-input bg-background px-2.5 text-xs text-foreground outline-none transition-colors focus:ring-2 focus:ring-ring"
                  >
                    <option value="">All documents</option>
                    {documents.map((document) => (
                      <option key={document.id} value={document.id}>
                        {document.filename.length > 25 ? document.filename.slice(0, 25) + "…" : document.filename}
                      </option>
                    ))}
                  </select>
                  {messages.length > 0 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setMessages([]);
                        setChatSessionId(null);
                      }}
                      className="text-muted-foreground"
                    >
                      Clear
                    </Button>
                  )}
                </div>
              </CardHeader>

              <CardContent className="flex-1 overflow-y-auto p-4 sm:p-5">
                {messages.length === 0 ? (
                  <div className="flex h-full flex-col items-center justify-center px-3 text-center">
                    <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
                      <Bot className="h-5 w-5" />
                    </div>
                    <h2 className="mt-4 text-sm font-semibold">Start with a question</h2>
                    <p className="mt-1 max-w-sm text-sm leading-6 text-muted-foreground">
                      {documents.length > 0
                        ? "Choose a prompt below or write a question in your own words."
                        : "Add a document from the panel on the right, then come back here to ask about it."}
                    </p>

                    <div className="mt-6 grid w-full max-w-xl grid-cols-1 gap-2 text-left sm:grid-cols-2">
                      {CHAT_SUGGESTIONS.map((suggestion) => (
                        <button
                          key={suggestion.query}
                          type="button"
                          onClick={() => handleAskQuestion(suggestion.query)}
                          className="rounded-lg border border-border bg-card px-3 py-3 text-left text-sm transition-colors hover:border-primary/40 hover:bg-primary/[0.03]"
                        >
                          {suggestion.label}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-5">
                    {messages.map((message) => (
                      <div
                        key={message.id}
                        className={"flex gap-3 " + (message.sender === "user" ? "justify-end" : "justify-start")}
                      >
                        {message.sender === "assistant" && (
                          <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                            <Bot className="h-4 w-4" />
                          </div>
                        )}

                        <div
                          className={
                            "max-w-[86%] rounded-2xl px-4 py-3 text-sm " +
                            (message.sender === "user"
                              ? "rounded-tr-sm bg-primary text-primary-foreground"
                              : "rounded-tl-sm border border-border bg-muted/35")
                          }
                        >
                          <div
                            className={
                              "mb-2 flex items-center justify-between gap-3 text-[11px] " +
                              (message.sender === "user" ? "text-primary-foreground/70" : "text-muted-foreground")
                            }
                          >
                            <span className="font-semibold text-primary">{message.sender === "user" ? "You" : "TokenBrief AI"}</span>
                            <div className="flex items-center gap-2">
                              <span>{message.timestamp}</span>
                              {message.sender === "assistant" && (
                                <button
                                  type="button"
                                  onClick={() => handleCopyAnswer(message.text, message.id)}
                                  className="rounded p-0.5 hover:bg-background/60"
                                  aria-label="Copy answer"
                                  title="Copy answer"
                                >
                                  {copiedId === message.id ? (
                                    <Check className="h-3.5 w-3.5 text-emerald-500" />
                                  ) : (
                                    <Copy className="h-3.5 w-3.5" />
                                  )}
                                </button>
                              )}
                            </div>
                          </div>

                          <div className="whitespace-pre-wrap leading-6">{message.text}</div>

                          {message.sources && message.sources.length > 0 && (
                            <div className="mt-3 border-t border-border/70 pt-3">
                              <div className="mb-2 flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground">
                                <BookOpen className="h-3.5 w-3.5" />
                                Sources
                              </div>
                              <div className="flex flex-wrap gap-1.5">
                                {message.sources.map((source, index) => (
                                  <button
                                    key={source.chunk_id + "-" + index}
                                    type="button"
                                    onClick={() => setExpandedSourceChunk(source)}
                                    className="inline-flex max-w-full items-center gap-1.5 rounded-md border border-border bg-background/70 px-2 py-1 text-[11px] text-foreground transition-colors hover:border-primary/40"
                                  >
                                    <FileText className="h-3 w-3 shrink-0 text-primary" />
                                    <span className="max-w-36 truncate">{source.document_filename}</span>
                                    <span className="text-muted-foreground">p. {source.source_page_number || 1}</span>
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>

                        {message.sender === "user" && (
                          <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                            <UserIcon className="h-4 w-4" />
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {isLoading && (
                  <div className="mt-5 flex items-center gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <Bot className="h-4 w-4" />
                    </div>
                    <div className="rounded-xl border border-border bg-muted/30 px-3 py-2 text-sm text-muted-foreground">
                      Looking through your documents…
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </CardContent>

              <CardFooter className="border-t border-border/75 bg-muted/20 p-3 sm:p-4">
                <form
                  onSubmit={(event) => {
                    event.preventDefault();
                    handleAskQuestion();
                  }}
                  className="flex w-full gap-2"
                >
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder={selectedDocId ? "Ask about the selected document…" : "Ask about your documents…"}
                      value={inputQuery}
                      onChange={(event) => setInputQuery(event.target.value)}
                      className="h-10 pl-9 text-sm"
                      disabled={isLoading}
                    />
                  </div>
                  <Button type="submit" disabled={isLoading || !inputQuery.trim()} className="h-10 gap-1.5 px-4">
                    <Send className="h-3.5 w-3.5" />
                    <span className="hidden sm:inline">Ask</span>
                  </Button>
                </form>
              </CardFooter>
            </Card>

            <DynamicAnalyticsChart />
          </div>

          <aside className="space-y-5">
            <DocumentUploadCard onUploadSuccess={fetchDocuments} />

            <Card>
              <CardHeader className="gap-3 border-b border-border/75 pb-4 sm:flex-row sm:items-start sm:justify-between sm:space-y-0">
                <div>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Layers className="h-4 w-4 text-primary" />
                    Your documents
                  </CardTitle>
                  <CardDescription className="mt-1 text-xs">
                    Select a file to focus your questions.
                  </CardDescription>
                </div>
                <Badge variant="secondary">{documents.length}</Badge>
              </CardHeader>

              <CardContent className="max-h-[390px] space-y-2 overflow-y-auto p-3">
                {documents.length === 0 ? (
                  <div className="px-3 py-7 text-center">
                    <p className="text-sm font-medium">No documents yet</p>
                    <p className="mt-1 text-xs leading-5 text-muted-foreground">Add a file above to build your library.</p>
                  </div>
                ) : (
                  documents.map((document) => {
                    const isSelected = selectedDocId === document.id;
                    return (
                      <div
                        key={document.id}
                        onClick={() => {
                          setSelectedDocId(isSelected ? null : document.id);
                          setChatSessionId(null);
                        }}
                        className={
                          "flex cursor-pointer items-center gap-2 rounded-xl border p-3 transition-colors " +
                          (isSelected
                            ? "border-primary/50 bg-primary/[0.06]"
                            : "border-border bg-card hover:bg-muted/45")
                        }
                      >
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted text-primary">
                          <FileText className="h-4 w-4" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium">{document.filename}</p>
                          <p className="mt-0.5 text-[11px] text-muted-foreground">
                            {getDocumentType(document.filename)} · {document.total_page_count} {document.total_page_count === 1 ? "page" : "pages"} · {(document.file_size_bytes / 1024).toFixed(1)} KB
                          </p>
                        </div>

                        <div className="flex shrink-0 items-center gap-0.5">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={(event) => {
                              event.stopPropagation();
                              handleSummarizeDoc(document.id);
                            }}
                            disabled={summarizingDocId !== null}
                            className="h-7 px-2 text-[11px]"
                          >
                            {summarizingDocId === document.id ? "…" : "Summary"}
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={(event) => handleDeleteDoc(document.id, event)}
                            className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive"
                            aria-label={"Delete " + document.filename}
                            title={"Delete " + document.filename}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </div>
                    );
                  })
                )}
              </CardContent>
            </Card>

            {activeSummary && (
              <Card>
                <CardHeader className="flex-row items-start justify-between gap-3 border-b border-border/75 pb-4">
                  <div className="min-w-0">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <FileCheck2 className="h-4 w-4 text-primary" />
                      Document summary
                    </CardTitle>
                    <CardDescription className="mt-1 truncate text-xs">{activeSummary.filename}</CardDescription>
                  </div>
                  <button
                    type="button"
                    onClick={() => setActiveSummary(null)}
                    className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
                    aria-label="Close summary"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </CardHeader>
                <CardContent className="space-y-4 p-4 text-sm">
                  <div>
                    <h3 className="font-medium">Overview</h3>
                    <p className="mt-1.5 leading-6 text-muted-foreground">{activeSummary.executive_summary}</p>
                  </div>
                  <div>
                    <h3 className="font-medium">Key points</h3>
                    <ul className="mt-1.5 space-y-1.5 pl-4 text-muted-foreground">
                      {activeSummary.key_takeaways.map((point, index) => (
                        <li key={index} className="list-disc leading-5">{point}</li>
                      ))}
                    </ul>
                  </div>
                  {activeSummary.topics.length > 0 && (
                    <div>
                      <h3 className="font-medium">Topics</h3>
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {activeSummary.topics.map((topic, index) => (
                          <Badge key={topic + "-" + index} variant="outline" className="text-[11px]">
                            {topic}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </aside>
        </div>
      </main>

      {expandedSourceChunk && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm animate-in fade-in duration-200">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="source-excerpt-title"
            className="w-full max-w-xl rounded-2xl border border-primary/20 bg-card p-6 shadow-2xl"
          >
            <div className="flex items-start justify-between gap-4 border-b border-border/80 pb-4">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="flex h-6 w-6 items-center justify-center rounded-md bg-primary/10 text-primary">
                    <FileText className="h-3.5 w-3.5" />
                  </span>
                  <h2 id="source-excerpt-title" className="text-base font-semibold tracking-tight">
                    Citation Inspector
                  </h2>
                </div>
                <p className="mt-1 truncate text-xs font-medium text-primary">
                  {expandedSourceChunk.document_filename}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setExpandedSourceChunk(null)}
                className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                aria-label="Close source excerpt"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
              <Badge variant="secondary" className="font-mono text-[11px] bg-primary/10 text-primary border-primary/20">
                Page {expandedSourceChunk.source_page_number || 1}
              </Badge>
              <Badge variant="outline" className="text-[11px]">
                Grounding Match {expandedSourceChunk.similarity_percentage}%
              </Badge>
              <span className="text-[11px] text-muted-foreground">
                Verified against workspace index
              </span>
            </div>

            <div className="mt-4 rounded-xl border border-border bg-muted/40 p-4 text-xs sm:text-sm leading-relaxed max-h-72 overflow-y-auto">
              <div className="whitespace-pre-wrap font-sans text-foreground/90 selection:bg-amber-300 selection:text-amber-950">
                {expandedSourceChunk.chunk_text_content.replace(/\[Document:[^\]]+\]\n?/g, "")}
              </div>
            </div>

            <div className="mt-5 flex items-center justify-between gap-3 border-t border-border/70 pt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  const targetDoc = documents.find((d) => d.filename === expandedSourceChunk.document_filename);
                  if (targetDoc) {
                    handleSummarizeDoc(targetDoc.id);
                  }
                  setExpandedSourceChunk(null);
                }}
                className="gap-1.5 text-xs"
              >
                <Sparkles className="h-3.5 w-3.5 text-primary" />
                <span>Summarize Full File</span>
              </Button>
              <Button size="sm" onClick={() => setExpandedSourceChunk(null)} className="text-xs px-4">
                Done
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
