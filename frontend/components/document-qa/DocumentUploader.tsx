"use client";

import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2, FileText } from "lucide-react";

interface DocumentUploaderProps {
  onUpload: (filename: string, content: string, contentType: string) => Promise<void>;
  disabled: boolean;
}

export function DocumentUploader({ onUpload, disabled }: DocumentUploaderProps) {
  const [textContent, setTextContent] = useState("");
  const [textFilename, setTextFilename] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const ext = file.name.split(".").pop()?.toLowerCase();
    const typeMap: Record<string, string> = {
      md: "text/markdown",
      txt: "text/plain",
      pdf: "application/pdf",
    };
    const contentType = typeMap[ext ?? ""] ?? "text/plain";

    setUploading(true);
    try {
      let content: string;
      if (contentType === "application/pdf") {
        content = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve((reader.result as string).split(",")[1]);
          reader.onerror = () => reject(new Error("Failed to read PDF file"));
          reader.readAsDataURL(file);
        });
      } else {
        content = await file.text();
      }
      await onUpload(file.name, content, contentType);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handlePasteUpload = async () => {
    if (!textContent.trim() || !textFilename.trim()) return;
    setUploading(true);
    try {
      await onUpload(textFilename, textContent, "text/plain");
      setTextContent("");
      setTextFilename("");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>Upload File (.md, .txt, .pdf)</Label>
        <div className="flex items-center gap-2">
          <Input
            ref={fileInputRef}
            type="file"
            accept=".md,.txt,.pdf"
            onChange={handleFileUpload}
            disabled={disabled || uploading}
            className="flex-1"
          />
          {uploading && <Loader2 className="h-4 w-4 animate-spin" />}
        </div>
      </div>

      <div className="space-y-2">
        <Label>Or paste text</Label>
        <Input
          placeholder="Document filename..."
          value={textFilename}
          onChange={(e) => setTextFilename(e.target.value)}
          disabled={disabled || uploading}
        />
        <Textarea
          placeholder="Paste document text here..."
          value={textContent}
          onChange={(e) => setTextContent(e.target.value)}
          rows={4}
          disabled={disabled || uploading}
        />
        <Button
          variant="outline"
          size="sm"
          onClick={handlePasteUpload}
          disabled={!textContent.trim() || !textFilename.trim() || disabled || uploading}
        >
          {uploading ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <FileText className="mr-2 h-4 w-4" />
          )}
          Add Document
        </Button>
      </div>
    </div>
  );
}
