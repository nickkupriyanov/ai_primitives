"use client";

import { Button } from "@/components/ui/button";
import { Loader2, Trash2, FileText } from "lucide-react";
import type { SourceOut } from "@/app/document-qa/actions";

interface SourcesListProps {
  sources: SourceOut[];
  onDelete: (id: string) => void;
  deleting: string | null;
}

export function SourcesList({ sources, onDelete, deleting }: SourcesListProps) {
  if (sources.length === 0) return null;

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium">Ingested Documents</h3>
      <div className="space-y-1">
        {sources.map((s) => (
          <div
            key={s.id}
            className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
          >
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <span>{s.filename}</span>
              <span className="text-xs text-muted-foreground">
                ({s.chunk_count} chunks)
              </span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => onDelete(s.id)}
              disabled={deleting === s.id}
            >
              {deleting === s.id ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4 text-muted-foreground" />
              )}
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
