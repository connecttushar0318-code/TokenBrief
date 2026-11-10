"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowRightLeft,
  BarChart3,
  BookOpen,
  Bot,
  Calendar,
  Check,
  ChevronRight,
  Copy,
  Download,
  ExternalLink,
  FileCheck2,
  FileText,
  Headphones,
  Home,
  Layers,
  LayoutDashboard,
  LogOut,
  Network,
  Search,
  Send,
  Settings,
  Sliders,
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
import { RealAnalyticsDashboard } from "@/components/real-analytics-dashboard";
import { InteractiveQuizStudio } from "@/components/interactive-quiz-studio";
import { DocumentComparisonView } from "@/components/document-comparison-view";
import { KnowledgeGraphVisualizer } from "@/components/knowledge-graph-visualizer";
import { UserProfileModal } from "@/components/user-profile-modal";
import { CitationAnnotationsModal } from "@/components/citation-annotations-modal";
import { DinoRangerLogo } from "@/components/dino-ranger-logo";
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

const getAuthHeaders = (extraHeaders: Record<string, string> = {}): Record<string, string> => {
  const headers: Record<string, string> = { ...extraHeaders };
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }
  return headers;
};

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

function getFormattedDate() {
  try {
    return new Intl.DateTimeFormat("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
    }).format(new Date());
  } catch {
    return "Today";
  }
}

function getDynamicSuggestions(selectedDocId: number | null, documents: DocumentItem[]): ChatSuggestion[] {
  const selectedDoc = documents.find((d) => d.id === selectedDocId);

  if (selectedDoc) {
    const name = selectedDoc.filename.toLowerCase();

    // 1. Resume / CV / Career Profile
    if (name.includes("resume") || name.includes("cv") || name.includes("profile") || name.includes("bio")) {
      return [
        {
          label: "⚡ ATS & Skill-Gap Audit",
          query: `Analyze ${selectedDoc.filename} for ATS compatibility. Highlight core technical skills, identify missing keywords, and suggest high-impact bullet improvements.`,
        },
        {
          label: "👤 Executive Profile & Experience",
          query: `Provide a concise executive overview of the candidate's career trajectory, key roles, and major technical achievements in ${selectedDoc.filename}.`,
        },
        {
          label: "🎯 Targeted Interview Questions",
          query: `Generate 5 technical interview questions based strictly on the projects, tools, and experience listed in ${selectedDoc.filename}.`,
        },
        {
          label: "💼 Role & Seniority Fit",
          query: `Based on the demonstrated experience and technologies in ${selectedDoc.filename}, what roles and seniority levels is this candidate best suited for?`,
        },
        {
          label: "💡 Top Strengths & Growth Areas",
          query: `Summarize the top 3 standout technical strengths and 3 recommended growth areas based on ${selectedDoc.filename}.`,
        },
        {
          label: "📝 Action Verbs & Impact Review",
          query: `Evaluate the project descriptions in ${selectedDoc.filename}: highlight strong action verbs and suggest quantified metrics where descriptions could be stronger.`,
        },
      ];
    }

    // 2. Syllabus / Coursework / Exam Notes / Lab Manual
    if (
      name.includes("syllabus") ||
      name.includes("notes") ||
      name.includes("curriculum") ||
      name.includes("course") ||
      name.includes("exam") ||
      name.includes("unit") ||
      name.includes("lab") ||
      name.includes("dm") ||
      name.includes("file")
    ) {
      return [
        {
          label: "📝 Exam Prep & Viva Mode",
          query: `Generate 5 challenging exam prep / viva questions with comprehensive answers grounded strictly in ${selectedDoc.filename}.`,
        },
        {
          label: "💡 Core Concepts & Terminology",
          query: `Explain the fundamental concepts, algorithms, and key terminology introduced in ${selectedDoc.filename} in clear, simple terms.`,
        },
        {
          label: "🔬 Methodologies & Practical Tools",
          query: `Summarize the practical experiments, tools, and step-by-step methodologies covered in ${selectedDoc.filename}.`,
        },
        {
          label: "📌 High-Yield Revision Sheet",
          query: `Provide a high-yield study sheet summarizing the most critical rules, formulas, and concepts for quick revision from ${selectedDoc.filename}.`,
        },
        {
          label: "⚠️ Common Pitfalls & Edge Cases",
          query: `What are the common misunderstandings, pitfalls, or edge cases discussed in ${selectedDoc.filename}?`,
        },
        {
          label: "🔍 Step-by-Step Practice Scenario",
          query: `Create 2 conceptual practice scenarios or problems based on ${selectedDoc.filename} with complete step-by-step solutions.`,
        },
      ];
    }

    // 3. Research Paper / Technical Report / Study
    if (
      name.includes("paper") ||
      name.includes("report") ||
      name.includes("research") ||
      name.includes("thesis") ||
      name.includes("analysis") ||
      name.includes("study")
    ) {
      return [
        {
          label: "📌 Executive Summary & Findings",
          query: `Summarize the core hypothesis, research methodology, key findings, and final conclusions of ${selectedDoc.filename}.`,
        },
        {
          label: "📊 Empirical Metrics & Results",
          query: `Extract the principal quantitative metrics, experimental benchmarks, and datasets reported in ${selectedDoc.filename}.`,
        },
        {
          label: "💡 Novel Contributions",
          query: `What novel techniques or primary contributions does ${selectedDoc.filename} present compared to existing prior work?`,
        },
        {
          label: "⚠️ Limitations & Future Work",
          query: `What constraints, assumptions, and directions for future research are identified in ${selectedDoc.filename}?`,
        },
        {
          label: "🔍 Methodology Breakdown",
          query: `Detail the experimental design and procedural workflow utilized in ${selectedDoc.filename}.`,
        },
        {
          label: "🎯 Key Actionable Takeaways",
          query: `Provide 4 high-impact bullet points outlining the practical takeaways and significance of ${selectedDoc.filename}.`,
        },
      ];
    }

    // 4. Universal Document Prompts (works for any PDF/Doc)
    return [
      {
        label: "📌 Comprehensive Executive Summary",
        query: `Provide a comprehensive executive summary of ${selectedDoc.filename}, covering its main goals, core topics, and conclusions.`,
      },
      {
        label: "🎯 Key Takeaways & Action Items",
        query: `What are the primary takeaways, action items, and crucial decisions outlined in ${selectedDoc.filename}?`,
      },
      {
        label: "💡 Critical Concepts & Definitions",
        query: `Identify and explain the key concepts, frameworks, and definitions essential to understanding ${selectedDoc.filename}.`,
      },
      {
        label: "📝 5 Grounded Practice Questions",
        query: `Generate 5 insightful review or interview questions strictly grounded in ${selectedDoc.filename} with answers and page references.`,
      },
      {
        label: "⚠️ Risks, Limits & Caveats",
        query: `What risks, challenges, limitations, or caveats are highlighted in ${selectedDoc.filename}?`,
      },
      {
        label: "🔍 Key Facts & Data Points",
        query: `Extract the most important statistics, factual highlights, and specific data points presented in ${selectedDoc.filename}.`,
      },
    ];
  }

  // Cross-Document Prompts (When "All documents" is selected)
  if (documents.length > 1) {
    return [
      {
        label: "🗂️ Cross-Document Synthesis",
        query: "Synthesize the main themes, findings, and commonalities across all uploaded documents in my workspace.",
      },
      {
        label: "⚖️ Compare & Contrast",
        query: "Compare and contrast the key methodologies, topics, and conclusions between the different documents in my library.",
      },
      {
        label: "💡 Shared Insights & Connections",
        query: "What concepts, skills, or arguments are shared between the uploaded files, and where do they differ?",
      },
      {
        label: "📌 Complete Workspace Overview",
        query: "Give me a high-level executive overview of everything in my library and how each document complements the others.",
      },
      {
        label: "📝 Multi-Doc Knowledge Check",
        query: "Generate 5 comprehensive questions testing key knowledge from across all documents in this workspace.",
      },
      {
        label: "🎯 Actionable Roadmap",
        query: "Based on all documents uploaded in my library, what are the primary recommendations and next steps?",
      },
    ];
  }

  // Single document in library without specific selection
  if (documents.length === 1) {
    const singleDoc = documents[0];
    return [
      {
        label: "📌 Executive Summary",
        query: `Summarize the main goals, key findings, and conclusions of ${singleDoc.filename}.`,
      },
      {
        label: "🎯 Key Takeaways",
        query: `What are the most important actionable takeaways from ${singleDoc.filename}?`,
      },
      {
        label: "💡 Core Concepts & Terms",
        query: `Explain the fundamental concepts and key definitions in ${singleDoc.filename}.`,
      },
      {
        label: "📝 5 Review Questions",
        query: `Generate 5 review questions with answers based on ${singleDoc.filename}.`,
      },
      {
        label: "⚠️ Critical Caveats & Limits",
        query: `What limitations or important caveats are mentioned in ${singleDoc.filename}?`,
      },
      {
        label: "🔍 Highlights & Data Points",
        query: `What are the standout data points and facts in ${singleDoc.filename}?`,
      },
    ];
  }

  // Empty library prompts
  return [
    {
      label: "💡 What can TokenBrief do?",
      query: "What types of documents can I upload to TokenBrief, and what features are available?",
    },
    {
      label: "🚀 How does Neural RAG work?",
      query: "Explain how TokenBrief uses verified citations and full-file digests to prevent AI hallucinations.",
    },
  ];
}

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
  const [activeTab, setActiveTab] = useState<"workspace" | "quiz" | "compare" | "graph" | "analytics">("workspace");
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isExportingPdf, setIsExportingPdf] = useState(false);
  const [userData, setUserData] = useState<any>(null);
  const [currentUser, setCurrentUser] = useState("tushar");
  const [expandedSourceChunk, setExpandedSourceChunk] = useState<SourceItem | null>(null);
  const [chatSessionId, setChatSessionId] = useState<string | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [latencyMs, setLatencyMs] = useState(420);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleExportPdf = async () => {
    if (isExportingPdf) return;
    setIsExportingPdf(true);
    try {
      const formattedMessages = messages.map((m) => ({
        sender_role: m.sender,
        message_text: m.text,
      }));
      const res = await fetch(`${API_BASE_URL}/api/export/pdf`, {
        method: "POST",
        headers: getAuthHeaders({ "Content-Type": "application/json" }),
        credentials: "include",
        body: JSON.stringify({
          session_title: "TokenBrief Intelligence Report",
          document_ids: selectedDocId ? [selectedDocId] : documents.map((d) => d.id),
          messages: formattedMessages.length > 0 ? formattedMessages : [
            { sender_role: "assistant", message_text: activeSummary?.executive_summary || "Document workspace analysis." }
          ],
        }),
      });
      if (!res.ok) throw new Error("PDF report generation failed.");
      const blob = await res.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = `TokenBrief_Report_${Date.now()}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(blobUrl);
    } catch (err: any) {
      alert("Export failed: " + err.message);
    } finally {
      setIsExportingPdf(false);
    }
  };

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
      const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
        headers: getAuthHeaders(),
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setCurrentUser(data.username || "tushar");
        setUserData(data);
      } else if (response.status === 401) {
        document.cookie = "access_token=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT";
        localStorage.removeItem("access_token");
        window.location.href = "/login";
      }
    } catch {}
  };

  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/documents`, {
        headers: getAuthHeaders(),
        credentials: "include",
      });
      if (response.ok) {
        setDocuments(await response.json());
      }
    } catch {}
  };

  useEffect(() => {
    try {
      const savedUser = localStorage.getItem("tokenbrief_user");
      if (savedUser) {
        const parsed = JSON.parse(savedUser);
        if (parsed.username) setCurrentUser(parsed.username);
      }
    } catch {}
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
        headers: getAuthHeaders({ "Content-Type": "application/json" }),
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
        headers: getAuthHeaders(),
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
        headers: getAuthHeaders(),
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
        headers: getAuthHeaders(),
        credentials: "include",
      });
    } catch {}
    document.cookie = "access_token=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    localStorage.removeItem("access_token");
    localStorage.removeItem("tokenbrief_user");
    window.location.href = "/login";
  };

  const handleCopyAnswer = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const totalPages = documents.reduce((acc, d) => acc + (d.total_page_count || 1), 0);
  const formattedUser = currentUser ? (currentUser.charAt(0).toUpperCase() + currentUser.slice(1)) : "User";

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col md:flex-row">
      {/* 1. Left Sidebar Navigation (Desktop - Retentrix Style) */}
      <aside className="hidden md:flex w-64 fixed inset-y-0 left-0 z-30 flex-col justify-between border-r border-border/70 bg-card/60 backdrop-blur-md">
        <div>
          {/* Logo & Brand Header */}
          <div className="p-4 border-b border-border/70">
            <Link href="/" className="flex items-center gap-3 group" aria-label="TokenBrief home">
              <DinoRangerLogo size={36} className="group-hover:rotate-6 transition-transform" />
              <div className="min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="text-base font-extrabold tracking-tight">
                    Token<span className="text-primary">Brief</span>
                  </span>
                </div>
                <p className="text-[10px] uppercase font-bold tracking-wider text-muted-foreground">
                  AI Workspace
                </p>
              </div>
            </Link>
          </div>

          {/* Navigation Module Menu */}
          <div className="px-3 py-4 space-y-1">
            <p className="px-3 pb-2 text-[10px] font-bold tracking-wider uppercase text-muted-foreground/70">
              Dashboard Modules
            </p>

            <button
              type="button"
              onClick={() => setActiveTab("workspace")}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "workspace"
                  ? "bg-primary text-primary-foreground shadow-sm shadow-primary/20"
                  : "text-muted-foreground hover:bg-muted/70 hover:text-foreground"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <LayoutDashboard className="h-4 w-4" />
                <span>Workspace & Chat</span>
              </div>
              {documents.length > 0 && (
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold ${
                    activeTab === "workspace"
                      ? "bg-primary-foreground/20 text-primary-foreground"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {documents.length}
                </span>
              )}
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("quiz")}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "quiz"
                  ? "bg-primary text-primary-foreground shadow-sm shadow-primary/20"
                  : "text-muted-foreground hover:bg-muted/70 hover:text-foreground"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Sliders className="h-4 w-4" />
                <span>Quiz Studio</span>
              </div>
              <span
                className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider ${
                  activeTab === "quiz"
                    ? "bg-primary-foreground/20 text-primary-foreground"
                    : "bg-primary/10 text-primary"
                }`}
              >
                New
              </span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("compare")}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "compare"
                  ? "bg-primary text-primary-foreground shadow-sm shadow-primary/20"
                  : "text-muted-foreground hover:bg-muted/70 hover:text-foreground"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <ArrowRightLeft className="h-4 w-4" />
                <span>Compare Docs</span>
              </div>
              <span
                className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider ${
                  activeTab === "compare"
                    ? "bg-primary-foreground/20 text-primary-foreground"
                    : "bg-primary/10 text-primary"
                }`}
              >
                New
              </span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("graph")}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "graph"
                  ? "bg-primary text-primary-foreground shadow-sm shadow-primary/20"
                  : "text-muted-foreground hover:bg-muted/70 hover:text-foreground"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Network className="h-4 w-4" />
                <span>Knowledge Graph</span>
              </div>
              <span
                className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider ${
                  activeTab === "graph"
                    ? "bg-primary-foreground/20 text-primary-foreground"
                    : "bg-primary/10 text-primary"
                }`}
              >
                New
              </span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("analytics")}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "analytics"
                  ? "bg-primary text-primary-foreground shadow-sm shadow-primary/20"
                  : "text-muted-foreground hover:bg-muted/70 hover:text-foreground"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <BarChart3 className="h-4 w-4" />
                <span>Real Analytics</span>
              </div>
              <span className="flex items-center gap-1 text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Live
              </span>
            </button>
          </div>
        </div>

        {/* Bottom Sidebar Settings & User Profile (Retentrix style) */}
        <div className="p-3 border-t border-border/70 space-y-1.5">
          <button
            type="button"
            onClick={() => setIsProfileOpen(true)}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium text-muted-foreground hover:bg-muted/70 hover:text-foreground transition-colors"
          >
            <Settings className="h-4 w-4" />
            <span>Settings & Profile</span>
          </button>

          <div className="flex items-center justify-between rounded-xl bg-muted/40 p-2.5 border border-border/50">
            <button
              type="button"
              onClick={() => setIsProfileOpen(true)}
              className="flex items-center gap-2.5 min-w-0 text-left group"
            >
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/15 text-xs font-extrabold text-primary">
                {currentUser.slice(0, 1).toUpperCase()}
              </div>
              <div className="min-w-0">
                <p className="truncate text-xs font-semibold text-foreground group-hover:text-primary">
                  {formattedUser}
                </p>
                <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Admin</p>
              </div>
            </button>
            <button
              type="button"
              onClick={handleSignOut}
              className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-destructive transition-colors"
              title="Sign out"
              aria-label="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* 2. Main Canvas (Offset by sidebar width md:pl-64) */}
      <div className="flex flex-col flex-1 min-h-screen md:pl-64 bg-background">
        {/* Retentrix Top Header */}
        <header className="sticky top-0 z-20 border-b border-border/70 bg-background/85 backdrop-blur-md px-4 sm:px-8 py-3.5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                  {getGreeting()}, {formattedUser} 👋
                </h1>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/10 px-2.5 py-0.5 text-[11px] font-semibold text-primary">
                  <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
                  Live Document Intelligence
                </span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                Real-time document knowledge base & AI synthesis • {getFormattedDate()}
              </p>
            </div>

            {/* Top Right Action Buttons */}
            <div className="flex items-center gap-2 sm:gap-2.5">
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportPdf}
                disabled={isExportingPdf}
                className="gap-1.5 text-xs h-8 px-2.5"
                title="Export workspace session as branded PDF"
              >
                <Download className="h-3.5 w-3.5 text-primary" />
                <span className="hidden sm:inline">{isExportingPdf ? "Exporting…" : "Export PDF"}</span>
              </Button>

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
                <Button variant="ghost" size="sm" className="text-xs h-8 px-2.5 gap-1.5 hidden lg:inline-flex">
                  <Home className="h-3.5 w-3.5" />
                  <span>Home</span>
                </Button>
              </Link>

              <ThemeToggle />

              <button
                type="button"
                onClick={() => setIsProfileOpen(true)}
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-xs font-bold text-primary hover:ring-2 hover:ring-primary/40 transition-all"
                title="Edit Profile"
              >
                {currentUser.slice(0, 1).toUpperCase()}
              </button>
            </div>
          </div>

          {/* Mobile Tab Selector (Visible only on screens < md) */}
          <div className="flex md:hidden items-center gap-1.5 overflow-x-auto pt-3 border-t border-border/50 mt-3 no-scrollbar">
            <Button
              variant={activeTab === "workspace" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab("workspace")}
              className="h-7 text-[11px] px-2.5 shrink-0"
            >
              <LayoutDashboard className="h-3 w-3 mr-1" />
              Workspace
            </Button>
            <Button
              variant={activeTab === "quiz" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab("quiz")}
              className="h-7 text-[11px] px-2.5 shrink-0"
            >
              <Sliders className="h-3 w-3 mr-1" />
              Quiz
            </Button>
            <Button
              variant={activeTab === "compare" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab("compare")}
              className="h-7 text-[11px] px-2.5 shrink-0"
            >
              <ArrowRightLeft className="h-3 w-3 mr-1" />
              Compare
            </Button>
            <Button
              variant={activeTab === "graph" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab("graph")}
              className="h-7 text-[11px] px-2.5 shrink-0"
            >
              <Network className="h-3 w-3 mr-1" />
              Graph
            </Button>
            <Button
              variant={activeTab === "analytics" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab("analytics")}
              className="h-7 text-[11px] px-2.5 shrink-0"
            >
              <BarChart3 className="h-3 w-3 mr-1" />
              Analytics
            </Button>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 p-4 sm:p-8 space-y-6 max-w-7xl w-full mx-auto">
          {activeTab === "workspace" && (
            <>
              {/* 4 Retentrix-Style KPI Metrics Cards */}
              <MetricsCards
                data={{
                  totalDocuments: documents.length,
                  totalPages,
                  averageLatencyMs: latencyMs,
                  securityStatus: "Zero-Leak",
                  activeEngine: "Gemini Pro AI",
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

                    <div className="mt-6 grid w-full max-w-2xl grid-cols-1 gap-2.5 text-left sm:grid-cols-2">
                      {getDynamicSuggestions(selectedDocId, documents).map((suggestion) => (
                        <button
                          key={suggestion.label + suggestion.query}
                          type="button"
                          onClick={() => handleAskQuestion(suggestion.query)}
                          className="group relative flex flex-col justify-between rounded-xl border border-border/70 bg-card/60 p-3.5 text-left transition-all duration-150 hover:border-primary/50 hover:bg-primary/[0.04] hover:shadow-sm"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-xs font-semibold text-foreground group-hover:text-primary">
                              {suggestion.label}
                            </span>
                            <ChevronRight className="h-3 w-3 text-muted-foreground/60 transition-transform group-hover:translate-x-0.5 group-hover:text-primary" />
                          </div>
                          <p className="mt-1 line-clamp-2 text-[11px] leading-relaxed text-muted-foreground">
                            {suggestion.query}
                          </p>
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
          </>
        )}

        {activeTab === "quiz" && (
          <InteractiveQuizStudio
            apiBaseUrl={API_BASE_URL}
            documents={documents}
            initialDocId={selectedDocId}
          />
        )}

        {activeTab === "compare" && (
          <DocumentComparisonView
            apiBaseUrl={API_BASE_URL}
            documents={documents}
          />
        )}

        {activeTab === "graph" && (
          <KnowledgeGraphVisualizer
            apiBaseUrl={API_BASE_URL}
            documents={documents}
            initialDocId={selectedDocId}
          />
        )}

        {activeTab === "analytics" && (
          <RealAnalyticsDashboard
            apiBaseUrl={API_BASE_URL}
          />
        )}
      </main>
      </div>

      {expandedSourceChunk && (
        <CitationAnnotationsModal
          apiBaseUrl={API_BASE_URL}
          sourceChunk={expandedSourceChunk}
          onClose={() => setExpandedSourceChunk(null)}
        />
      )}

      <UserProfileModal
        isOpen={isProfileOpen}
        onClose={() => setIsProfileOpen(false)}
        currentUser={currentUser}
        emailAddress={userData?.email || `${currentUser}@tokenbrief.ai`}
        role={userData?.role || "Member"}
        createdAt={userData?.created_at}
        totalDocuments={documents.length}
      />
    </div>
  );
}
