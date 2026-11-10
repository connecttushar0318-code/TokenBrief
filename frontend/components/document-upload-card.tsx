"use client";

import { useState } from "react";
import { AlertCircle, CheckCircle2, FileText, Upload } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { documentUploadSchema } from "@/lib/validations";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function DocumentUploadCard({ onUploadSuccess }: { onUploadSuccess?: () => void }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleFilesProcess = async (files: File[]) => {
    if (!files.length || isUploading) return;

    setStatusMessage(null);
    const validFiles: File[] = [];
    const validationErrors: string[] = [];

    files.forEach((file) => {
      const validation = documentUploadSchema.safeParse({ file });
      if (validation.success) {
        validFiles.push(file);
      } else {
        validationErrors.push(`${file.name}: ${validation.error.errors[0]?.message || "This file could not be added."}`);
      }
    });

    if (!validFiles.length) {
      setStatusMessage({
        type: "error",
        text: validationErrors[0] || "These files could not be added.",
      });
      return;
    }

    setIsUploading(true);
    let uploadedCount = 0;
    const uploadErrors = [...validationErrors];

    try {
      for (let index = 0; index < validFiles.length; index += 1) {
        const file = validFiles[index];
        setSelectedFileName(
          validFiles.length === 1 ? file.name : `${file.name} (${index + 1}/${validFiles.length})`
        );
        const formData = new FormData();
        formData.append("uploaded_file", file);

        try {
          const headers: Record<string, string> = {};
          if (typeof window !== "undefined") {
            const token = localStorage.getItem("access_token");
            if (token) headers["Authorization"] = `Bearer ${token}`;
          }
          const response = await fetch(`${API_BASE_URL}/api/documents/upload`, {
            method: "POST",
            headers,
            body: formData,
            credentials: "include",
          });

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || "The server could not add this file.");
          }

          await response.json();
          uploadedCount += 1;
        } catch (err: any) {
          uploadErrors.push(`${file.name}: ${err.message || "The file could not be uploaded."}`);
        }
      }

      if (uploadedCount > 0) {
        const noun = uploadedCount === 1 ? "document" : "documents";
        const problemNote = uploadErrors.length ? ` ${uploadErrors.length} file${uploadErrors.length === 1 ? " was" : "s were"} skipped.` : "";
        setStatusMessage({
          type: "success",
          text: `Added ${uploadedCount} ${noun}.${problemNote}`,
        });
        onUploadSuccess?.();
      } else {
        setStatusMessage({
          type: "error",
          text: uploadErrors[0] || "The files could not be uploaded.",
        });
      }
    } finally {
      setSelectedFileName(null);
      setIsUploading(false);
    }
  };

  const handleFileInput = (files: FileList | null) => {
    void handleFilesProcess(Array.from(files || []));
  };

  const handleFileDrop = (files: FileList | null) => {
    void handleFilesProcess(Array.from(files || []));
  };

  const fileInputId = "file-upload-input";
  const selectFiles = () => document.getElementById(fileInputId)?.click();

  return (
    <Card>
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-base">
          <Upload className="h-4 w-4 text-primary" />
          Add a document
        </CardTitle>
        <CardDescription className="text-xs">
          Upload PDFs, text files, or Markdown files to start asking questions.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-3">
        <div
          role="button"
          tabIndex={0}
          onDragOver={(event) => {
            event.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setIsDragging(false);
            handleFileDrop(event.dataTransfer.files);
          }}
          onClick={selectFiles}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              selectFiles();
            }
          }}
          className={`rounded-xl border border-dashed p-6 text-center transition-colors ${
            isDragging
              ? "border-primary bg-primary/10"
              : "border-border bg-muted/25 hover:border-primary/50 hover:bg-muted/50"
          }`}
        >
          <input
            id={fileInputId}
            type="file"
            accept=".pdf,.txt,.md"
            multiple
            className="hidden"
            onChange={(event) => {
              handleFileInput(event.target.files);
              event.currentTarget.value = "";
            }}
          />

          <div className="flex flex-col items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-background text-primary shadow-sm">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-medium">
                {isUploading ? `Adding ${selectedFileName || "file"}…` : "Drop files here"}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                {isUploading ? "Files are processed one at a time. This may take a moment." : "or choose one or more files from your computer"}
              </p>
            </div>
          </div>
        </div>

        <p className="px-1 text-xs text-muted-foreground">PDF, TXT, or MD · up to 15 MB per file</p>

        {statusMessage && (
          <div
            className={`flex items-start gap-2 rounded-lg border p-3 text-xs leading-relaxed ${
              statusMessage.type === "success"
                ? "border-emerald-500/25 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400"
                : "border-destructive/25 bg-destructive/10 text-destructive"
            }`}
          >
            {statusMessage.type === "success" ? (
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
            ) : (
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            )}
            <span>{statusMessage.text}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
