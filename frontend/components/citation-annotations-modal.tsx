"use client";

import { useEffect, useState } from "react";
import {
  Bookmark,
  Check,
  ExternalLink,
  Highlighter,
  MessageSquare,
  StickyNote,
  Trash2,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface SourceItem {
  chunk_id: number;
  document_filename: string;
  source_page_number: number;
  similarity_percentage: number;
  chunk_text_content: string;
}

interface UserAnnotation {
  id: number;
  document_id: number;
  chunk_id: number | null;
  highlighted_text: string;
  annotation_note: string | null;
  color_code: string;
  source_page_number: number | null;
  created_at: string;
}

const COLOR_OPTIONS = [
  { name: "yellow", bg: "bg-yellow-200 dark:bg-yellow-900/50", border: "border-yellow-400" },
  { name: "emerald", bg: "bg-emerald-200 dark:bg-emerald-900/50", border: "border-emerald-400" },
  { name: "sky", bg: "bg-sky-200 dark:bg-sky-900/50", border: "border-sky-400" },
  { name: "purple", bg: "bg-purple-200 dark:bg-purple-900/50", border: "border-purple-400" },
  { name: "pink", bg: "bg-pink-200 dark:bg-pink-900/50", border: "border-pink-400" },
];

export function CitationAnnotationsModal({
  apiBaseUrl,
  sourceChunk,
  onClose,
}: {
  apiBaseUrl: string;
  sourceChunk: SourceItem | null;
  onClose: () => void;
}) {
  const [annotations, setAnnotations] = useState<UserAnnotation[]>([]);
  const [selectedText, setSelectedText] = useState("");
  const [annotationNote, setAnnotationNote] = useState("");
  const [selectedColor, setSelectedColor] = useState("yellow");
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (!sourceChunk) return;
    const fetchChunkAnnotations = async () => {
      try {
        const res = await fetch(`${apiBaseUrl}/api/annotations/chunk/${sourceChunk.chunk_id}`, {
          credentials: "include",
        });
        if (res.ok) {
          const list = await res.json();
          setAnnotations(list);
        }
      } catch {}
    };
    fetchChunkAnnotations();
  }, [sourceChunk, apiBaseUrl]);

  if (!sourceChunk) return null;

  const handleCreateAnnotation = async () => {
    const textToHighlight = selectedText.trim() || sourceChunk.chunk_text_content.slice(0, 100);
    setIsSaving(true);
    try {
      const res = await fetch(`${apiBaseUrl}/api/annotations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          document_id: 1, // Fallback if chunk document id isn't populated directly
          chunk_id: sourceChunk.chunk_id,
          highlighted_text: textToHighlight,
          annotation_note: annotationNote.trim() || null,
          color_code: selectedColor,
          source_page_number: sourceChunk.source_page_number,
        }),
      });
      if (res.ok) {
        const created = await res.json();
        setAnnotations((prev) => [created, ...prev]);
        setSelectedText("");
        setAnnotationNote("");
      }
    } catch (err) {
      alert("Failed to save highlight: " + String(err));
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteAnnotation = async (id: number) => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/annotations/${id}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (res.ok) {
        setAnnotations((prev) => prev.filter((a) => a.id !== id));
      }
    } catch {}
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-2xl border border-border bg-card p-6 shadow-2xl space-y-5 animate-in fade-in-50 zoom-in-95">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 text-muted-foreground hover:text-foreground p-1 rounded-lg hover:bg-muted"
        >
          <X className="h-4 w-4" />
        </button>

        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-3">
          <div className="flex items-center gap-2">
            <span className="font-bold text-sm">{sourceChunk.document_filename}</span>
            <Badge variant="outline" className="text-xs font-mono">
              Page {sourceChunk.source_page_number || 1}
            </Badge>
          </div>
          <Badge variant="secondary" className="text-xs font-mono bg-emerald-500/10 text-emerald-600">
            {sourceChunk.similarity_percentage}% Vector Match
          </Badge>
        </div>

        <div className="space-y-2">
          <label className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
            <ExternalLink className="h-3.5 w-3.5 text-primary" />
            Source Excerpt (Select text to highlight):
          </label>
          <div
            onMouseUp={() => {
              const sel = window.getSelection()?.toString();
              if (sel && sel.trim().length > 3) {
                setSelectedText(sel.trim());
              }
            }}
            className="p-4 rounded-xl border border-border/80 bg-muted/20 text-xs leading-relaxed font-mono whitespace-pre-wrap select-text max-h-56 overflow-y-auto"
          >
            {sourceChunk.chunk_text_content}
          </div>
        </div>

        <div className="p-4 rounded-xl border border-border/60 bg-muted/10 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold flex items-center gap-1.5 text-foreground">
              <Highlighter className="h-3.5 w-3.5 text-amber-500" />
              <span>Create Highlight &amp; Sticky Note</span>
            </span>
            <div className="flex items-center gap-1.5">
              {COLOR_OPTIONS.map((c) => (
                <button
                  key={c.name}
                  type="button"
                  onClick={() => setSelectedColor(c.name)}
                  className={`h-5 w-5 rounded-full border-2 transition-transform ${c.bg} ${
                    selectedColor === c.name ? "scale-125 border-foreground" : "border-transparent"
                  }`}
                  title={c.name}
                />
              ))}
            </div>
          </div>

          {selectedText && (
            <div className="p-2 rounded-lg bg-card border text-[11px] text-muted-foreground truncate">
              Selected: <b className="text-foreground italic">"{selectedText.slice(0, 70)}..."</b>
            </div>
          )}

          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Add an optional sticky note / observation..."
              value={annotationNote}
              onChange={(e) => setAnnotationNote(e.target.value)}
              className="flex-1 text-xs rounded-lg border border-border bg-background px-3 py-1.5 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
            <Button
              size="sm"
              onClick={handleCreateAnnotation}
              disabled={isSaving}
              className="text-xs h-8 px-3 gap-1.5 shrink-0"
            >
              <StickyNote className="h-3.5 w-3.5" />
              <span>Save Note</span>
            </Button>
          </div>
        </div>

        {annotations.length > 0 && (
          <div className="space-y-2 pt-2">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Saved Annotations ({annotations.length})
            </h4>
            <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
              {annotations.map((ann) => (
                <div
                  key={ann.id}
                  className="flex items-start justify-between gap-3 p-3 rounded-lg border border-border/60 bg-card text-xs"
                >
                  <div className="space-y-1 min-w-0">
                    <p className="font-semibold text-foreground italic">"{ann.highlighted_text}"</p>
                    {ann.annotation_note && (
                      <p className="text-muted-foreground flex items-center gap-1">
                        <MessageSquare className="h-3 w-3 text-primary shrink-0" />
                        <span>{ann.annotation_note}</span>
                      </p>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => handleDeleteAnnotation(ann.id)}
                    className="text-muted-foreground hover:text-destructive p-1 rounded shrink-0"
                    title="Delete annotation"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex justify-end pt-2 border-t border-border/60">
          <Button size="sm" onClick={onClose} className="text-xs h-8 px-4">
            Close Inspector
          </Button>
        </div>
      </div>
    </div>
  );
}
