"use client";

import { useState } from "react";
import {
  AlertCircle,
  ArrowRightLeft,
  Check,
  FileText,
  Layers,
  Sparkles,
  Zap,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface DocumentItem {
  id: number;
  filename: string;
  total_page_count: number;
  total_chunk_count: number;
}

interface ComparisonRow {
  criterion: string;
  document_values: Record<string, string>;
  key_difference: string;
}

interface DocumentHeader {
  document_id: number;
  filename: string;
  detected_type: string;
  total_pages: number;
  total_chunks: number;
}

interface ComparisonResponse {
  documents: DocumentHeader[];
  comparison_matrix: ComparisonRow[];
  shared_topics: string[];
  unique_topics_per_document: Record<string, string[]>;
  synthesis_verdict: string;
}

export function DocumentComparisonView({
  apiBaseUrl,
  documents,
}: {
  apiBaseUrl: string;
  documents: DocumentItem[];
}) {
  const [selectedIds, setSelectedIds] = useState<number[]>(
    documents.slice(0, 2).map((d) => d.id)
  );
  const [isComparing, setIsComparing] = useState(false);
  const [comparisonResult, setComparisonResult] = useState<ComparisonResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const toggleSelectDoc = (id: number) => {
    setSelectedIds((prev) => {
      if (prev.includes(id)) {
        return prev.filter((item) => item !== id);
      }
      if (prev.length >= 4) {
        alert("You can compare up to 4 documents simultaneously.");
        return prev;
      }
      return [...prev, id];
    });
  };

  const handleRunComparison = async () => {
    if (selectedIds.length < 2) {
      setErrorMessage("Please select at least 2 documents to compare.");
      return;
    }
    setIsComparing(true);
    setErrorMessage(null);

    try {
      const response = await fetch(`${apiBaseUrl}/api/documents/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ document_ids: selectedIds }),
      });
      if (!response.ok) {
        throw new Error("Document comparison failed. Check document availability.");
      }
      const data = await response.json();
      setComparisonResult(data);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to compare documents.");
    } finally {
      setIsComparing(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card className="border-border/80 bg-card/60">
        <CardHeader className="pb-3">
          <CardTitle className="text-xl flex items-center gap-2">
            <ArrowRightLeft className="h-5 w-5 text-primary" />
            <span>Structured Document Comparison</span>
          </CardTitle>
          <CardDescription className="text-xs">
            Select 2 to 4 documents from your workspace to run cross-document analysis
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-muted-foreground block mb-2">
              Select Documents to Compare ({selectedIds.length} selected):
            </label>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {documents.map((doc) => {
                const isSelected = selectedIds.includes(doc.id);
                return (
                  <button
                    key={doc.id}
                    type="button"
                    onClick={() => toggleSelectDoc(doc.id)}
                    className={`flex items-center justify-between p-3 rounded-xl border text-xs text-left transition-all ${
                      isSelected
                        ? "bg-primary/10 border-primary text-foreground font-medium shadow-sm"
                        : "border-border/60 hover:bg-muted/30 text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    <div className="flex items-center gap-2.5 truncate">
                      <FileText className={`h-4 w-4 shrink-0 ${isSelected ? "text-primary" : "text-muted-foreground"}`} />
                      <div className="truncate">
                        <p className="font-semibold truncate">{doc.filename}</p>
                        <p className="text-[10px] text-muted-foreground">{doc.total_page_count || 1} pages</p>
                      </div>
                    </div>
                    <div
                      className={`h-4 w-4 rounded-full border flex items-center justify-center shrink-0 ${
                        isSelected ? "bg-primary border-primary text-white" : "border-muted-foreground"
                      }`}
                    >
                      {isSelected && <Check className="h-3 w-3 stroke-[3]" />}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {errorMessage && (
            <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          <Button
            onClick={handleRunComparison}
            disabled={isComparing || selectedIds.length < 2}
            className="gap-2 text-xs"
          >
            <Sparkles className={`h-3.5 w-3.5 ${isComparing ? "animate-spin" : ""}`} />
            <span>{isComparing ? "Analyzing Cross-Document Structures..." : "Compare Selected Documents"}</span>
          </Button>
        </CardContent>
      </Card>

      {comparisonResult && (
        <div className="space-y-6">
          <Card className="border-border/80 bg-gradient-to-br from-card/90 via-card/60 to-primary/5">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Zap className="h-4 w-4 text-primary" />
                <span>Executive Synthesis Verdict</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-xs leading-relaxed text-foreground">
                {comparisonResult.synthesis_verdict}
              </p>

              <div className="space-y-2 pt-2 border-t border-border/50">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Shared Core Themes:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {comparisonResult.shared_topics.map((t) => (
                    <Badge key={t} variant="secondary" className="text-xs bg-primary/10 text-primary">
                      {t}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/80 bg-card/60 overflow-hidden">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Side-by-Side Comparison Matrix</CardTitle>
              <CardDescription className="text-xs">
                Structural breakdown across key dimensions
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b bg-muted/40 font-semibold text-muted-foreground">
                      <th className="p-3 w-44">Criterion</th>
                      {comparisonResult.documents.map((doc) => (
                        <th key={doc.document_id} className="p-3 min-w-[200px]">
                          <div className="font-bold text-foreground truncate">{doc.filename}</div>
                          <div className="text-[10px] text-primary">{doc.detected_type}</div>
                        </th>
                      ))}
                      <th className="p-3 min-w-[220px]">Key Structural Difference</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40">
                    {comparisonResult.comparison_matrix.map((row, idx) => (
                      <tr key={idx} className="hover:bg-muted/20">
                        <td className="p-3 font-semibold text-foreground align-top">
                          {row.criterion}
                        </td>
                        {comparisonResult.documents.map((doc) => (
                          <td key={doc.document_id} className="p-3 text-muted-foreground align-top leading-relaxed">
                            {row.document_values[doc.filename] || "—"}
                          </td>
                        ))}
                        <td className="p-3 font-medium text-primary/90 align-top leading-relaxed bg-primary/5">
                          {row.key_difference}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-4 sm:grid-cols-2">
            {Object.entries(comparisonResult.unique_topics_per_document).map(([filename, topics]) => (
              <Card key={filename} className="border-border/80 bg-card/60 p-4 space-y-2">
                <p className="text-xs font-bold truncate flex items-center gap-1.5 text-foreground">
                  <FileText className="h-3.5 w-3.5 text-primary shrink-0" />
                  <span className="truncate">{filename} Unique Focus:</span>
                </p>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {topics.map((topic) => (
                    <Badge key={topic} variant="outline" className="text-[11px]">
                      {topic}
                    </Badge>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
