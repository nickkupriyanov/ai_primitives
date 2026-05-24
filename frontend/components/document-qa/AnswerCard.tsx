"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CitationBadge } from "./CitationBadge";
import { FailureCasesPanel } from "./FailureCasesPanel";
import type { QuestionResponse } from "@/app/document-qa/actions";

interface AnswerCardProps {
  response: QuestionResponse;
}

export function AnswerCard({ response }: AnswerCardProps) {
  return (
    <Card className="border-blue-500/30">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Answer
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm leading-relaxed whitespace-pre-wrap">
          {response.answer}
        </p>

        {response.citations.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-medium text-muted-foreground uppercase">
              Sources
            </p>
            <div className="flex flex-wrap gap-1">
              {response.citations.map((c, i) => (
                <CitationBadge key={`${c.source_id}-${c.chunk_position}-${i}`} citation={c} />
              ))}
            </div>
          </div>
        )}

        <p className="text-xs text-muted-foreground">
          {response.latency_ms}ms
        </p>

        {response.failure_case && (
          <FailureCasesPanel failureCase={response.failure_case} />
        )}
      </CardContent>
    </Card>
  );
}
