"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { FileText } from "lucide-react";
import type { CitationOut } from "@/app/document-qa/actions";

interface CitationBadgeProps {
  citation: CitationOut;
}

export function CitationBadge({ citation }: CitationBadgeProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="inline-block">
      <Badge
        variant="secondary"
        className="cursor-pointer gap-1"
        onClick={() => setExpanded(!expanded)}
      >
        <FileText className="h-3 w-3" />
        {citation.source_filename} [chunk {citation.chunk_position}]
      </Badge>
      {expanded && (
        <div className="mt-1 rounded-md border bg-muted/50 p-2 text-xs text-muted-foreground max-w-md">
          {citation.chunk_text}
        </div>
      )}
    </div>
  );
}
