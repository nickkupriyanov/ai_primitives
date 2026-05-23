"use client";

import { useState, useCallback } from "react";
import { briefOutputSchema, type BriefOutput } from "@/lib/validators/briefSchema";
import { RequestStatus } from "@/types/ai";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { JsonPreview } from "@/components/ai/JsonPreview";
import { ErrorState } from "@/components/ai/ErrorState";
import { RetryButton } from "@/components/ai/RetryButton";
import {
  Loader2,
  Send,
  CheckCircle2,
  Tags,
  AlertTriangle,
  HelpCircle,
} from "lucide-react";

const backendUrl =
  process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";

function getApiErrorMessage(data: unknown, status: number) {
  if (data && typeof data === "object" && "error" in data) {
    const { error } = data as {
      error?: string | { message?: string };
    };

    if (typeof error === "string") return error;
    if (error?.message) return error.message;
  }

  return `Request failed with status ${status}`;
}

export default function BriefParserPage() {
  const [briefText, setBriefText] = useState("");
  const [status, setStatus] = useState<RequestStatus>("idle");
  const [parsedResult, setParsedResult] = useState<BriefOutput | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = useCallback(async () => {
    if (!briefText.trim()) return;

    setStatus("loading");
    setParsedResult(null);
    setValidationError(null);

    try {
      const res = await fetch(`${backendUrl}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: 'include',
        body: JSON.stringify({ text: briefText, language: "ru" }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(getApiErrorMessage(data, res.status));
      }

      const json = await res.json();
      const validated = briefOutputSchema.parse(json);
      setParsedResult(validated);
      setStatus("success");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to parse response";
      setValidationError(message);
      setStatus("error");
    }
  }, [briefText]);

  const handleRetry = useCallback(() => {
    handleSubmit();
  }, [handleSubmit]);

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="mb-6 space-y-1">
        <h1 className="text-2xl font-bold">Brief Parser</h1>
        <p className="text-muted-foreground">
          Paste a product description or business idea. The model returns structured JSON.
        </p>
      </div>

      <div className="space-y-4">
        <Textarea
          placeholder="Describe your product or business idea..."
          value={briefText}
          onChange={(e) => setBriefText(e.target.value)}
          rows={6}
          disabled={status === "loading"}
        />

        <div className="flex items-center gap-2">
          <Button
            onClick={handleSubmit}
            disabled={!briefText.trim() || status === "loading"}
          >
            {status === "loading" ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Send className="mr-2 h-4 w-4" />
            )}
            {status === "loading" ? "Analyzing..." : "Parse Brief"}
          </Button>

          {(status === "error" || status === "success") && (
            <RetryButton onRetry={handleRetry} />
          )}
        </div>
      </div>

      {status === "error" && (
        <div className="mt-6 space-y-4">
          <ErrorState
            message={
              validationError ?? "The model returned invalid output. Please retry or simplify your input."
            }
            onRetry={handleRetry}
          />
        </div>
      )}

      {status === "success" && parsedResult && (
        <div className="mt-6 space-y-6">
          <Card className="border-green-500/30 bg-green-500/5">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                <CardTitle className="text-base">Validation passed</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                The model output matches the expected schema.
              </p>
            </CardContent>
          </Card>

          <div className="space-y-4">
            <h2 className="text-lg font-semibold">Parsed Result</h2>

            <div className="grid gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2">
                    <Tags className="h-4 w-4 text-primary" />
                    <CardTitle className="text-sm">Topics</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="list-disc pl-4 text-sm space-y-1">
                    {parsedResult.topics.map((topic, i) => (
                      <li key={i}>{topic}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-primary" />
                    <CardTitle className="text-sm">Pain Points</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="list-disc pl-4 text-sm space-y-1">
                    {parsedResult.pain_points.map((point, i) => (
                      <li key={i}>{point}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-primary" />
                    <CardTitle className="text-sm">Risks</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="list-disc pl-4 text-sm space-y-1">
                    {parsedResult.risks.map((risk, i) => (
                      <li key={i}>{risk}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2">
                    <HelpCircle className="h-4 w-4 text-primary" />
                    <CardTitle className="text-sm">Next Questions</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="list-disc pl-4 text-sm space-y-1">
                    {parsedResult.next_questions.map((q, i) => (
                      <li key={i}>{q}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </div>
          </div>

          <Separator />

          <div>
            <h2 className="mb-2 text-lg font-semibold">Raw JSON</h2>
            <JsonPreview data={parsedResult} />
          </div>
        </div>
      )}
    </div>
  );
}
