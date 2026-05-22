"use client";

import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface RetryButtonProps {
  onRetry: () => void;
  label?: string;
}

export function RetryButton({ onRetry, label = "Retry" }: RetryButtonProps) {
  return (
    <Button variant="outline" onClick={onRetry} className="gap-2">
      <RefreshCw className="h-4 w-4" />
      {label}
    </Button>
  );
}
