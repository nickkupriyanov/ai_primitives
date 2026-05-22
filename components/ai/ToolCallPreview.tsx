"use client";

import { JsonPreview } from "./JsonPreview";
import { Badge } from "@/components/ui/badge";

interface ToolCallPreviewProps {
  toolName: string;
  args: Record<string, unknown>;
}

export function ToolCallPreview({ toolName, args }: ToolCallPreviewProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Tool:</span>
        <Badge variant="secondary">{toolName}</Badge>
      </div>
      <div>
        <span className="text-sm text-muted-foreground">Arguments:</span>
        <JsonPreview data={args} className="mt-1" />
      </div>
    </div>
  );
}
