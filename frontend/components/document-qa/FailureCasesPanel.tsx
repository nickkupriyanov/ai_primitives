"use client";

import type { FailureCaseOut } from "@/app/document-qa/actions";
import { AlertTriangle } from "lucide-react";

interface FailureCasesPanelProps {
  failureCase: FailureCaseOut;
}

export function FailureCasesPanel({ failureCase }: FailureCasesPanelProps) {
  return (
    <div className="rounded-md border border-yellow-500/30 bg-yellow-500/5 p-3">
      <div className="mb-2 flex items-center gap-2 text-sm font-medium text-yellow-700">
        <AlertTriangle className="h-4 w-4" />
        Retrieval Failure Case
      </div>
      <div className="space-y-2 text-xs">
        <div>
          <span className="font-medium">Question:</span> {failureCase.question}
        </div>
        <div>
          <span className="font-medium">Expected:</span> {failureCase.expected_answer}
        </div>
        <div>
          <span className="font-medium">Retrieval Issue:</span> {failureCase.retrieval_issue}
        </div>
      </div>
    </div>
  );
}
