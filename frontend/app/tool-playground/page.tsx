"use client";

import { useState, useCallback } from "react";
import { requestToolCall, executeApprovedTool } from "./actions";
import { ToolCallStatus } from "@/types/ai";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ToolCallPreview } from "@/components/ai/ToolCallPreview";
import { ApprovalCard } from "@/components/ai/ApprovalCard";
import { JsonPreview } from "@/components/ai/JsonPreview";
import { ErrorState } from "@/components/ai/ErrorState";
import { RetryButton } from "@/components/ai/RetryButton";
import { Loader2, Send, XCircle, CheckCircle2 } from "lucide-react";

export default function ToolPlaygroundPage() {
  const [inputText, setInputText] = useState("");
  const [toolCall, setToolCall] = useState<{ name: string; args: unknown } | null>(null);
  const [toolResult, setToolResult] = useState<unknown | null>(null);
  const [status, setStatus] = useState<ToolCallStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  const handleSend = useCallback(async () => {
    if (!inputText.trim()) return;

    setStatus("loading");
    setToolCall(null);
    setToolResult(null);
    setError(null);

    try {
      const result = await requestToolCall(inputText);
      setToolCall({ name: result.toolName, args: result.args });
      setStatus("pending_approval");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to request tool";
      setError(message);
      setStatus("error");
    }
  }, [inputText]);

  const handleExecute = useCallback(async () => {
    if (!toolCall) return;

    setStatus("executing");
    try {
      const result = await executeApprovedTool(toolCall.name, toolCall.args);
      setToolResult(result);
      setStatus("success");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Tool execution failed";
      setError(message);
      setStatus("error");
    }
  }, [toolCall]);

  const handleCancel = useCallback(() => {
    setToolCall(null);
    setStatus("cancelled");
  }, []);

  const handleRetry = useCallback(() => {
    handleSend();
  }, [handleSend]);

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="mb-6 space-y-1">
        <h1 className="text-2xl font-bold">Tool Calling Playground</h1>
        <p className="text-muted-foreground">
          See how the model chooses tools. Preview arguments and approve execution before any side effects.
        </p>
      </div>

      <div className="space-y-4">
        <Textarea
          placeholder="Describe what you want the model to do (e.g., 'Summarize this text: ...' or 'Classify priority of: ...')"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          rows={4}
          disabled={status === "loading" || status === "executing"}
        />

        <div className="flex items-center gap-2">
          <Button
            onClick={handleSend}
            disabled={!inputText.trim() || status === "loading" || status === "executing"}
          >
            {status === "loading" ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Send className="mr-2 h-4 w-4" />
            )}
            {status === "loading" ? "Thinking..." : "Send to model"}
          </Button>

          {(status === "error" || status === "cancelled") && (
            <RetryButton onRetry={handleRetry} />
          )}
        </div>
      </div>

      {status === "pending_approval" && toolCall && (
        <div className="mt-6">
          <ApprovalCard
            title={`Approve tool: ${toolCall.name}`}
            onApprove={handleExecute}
            onCancel={handleCancel}
          >
            <ToolCallPreview
              toolName={toolCall.name}
              args={toolCall.args as Record<string, unknown>}
            />
          </ApprovalCard>
        </div>
      )}

      {status === "executing" && (
        <div className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Executing tool...
              </CardTitle>
            </CardHeader>
          </Card>
        </div>
      )}

      {status === "success" && toolResult !== null && (
        <div className="mt-6 space-y-4">
          <Card className="border-green-500/30 bg-green-500/5">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                <CardTitle className="text-base">Tool executed successfully</CardTitle>
              </div>
            </CardHeader>
          </Card>
          <div>
            <h2 className="mb-2 text-lg font-semibold">Result</h2>
            <JsonPreview data={toolResult} />
          </div>
        </div>
      )}

      {status === "cancelled" && (
        <div className="mt-6">
          <Card className="border-muted">
            <CardHeader>
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <XCircle className="h-4 w-4 text-muted-foreground" />
                Tool execution cancelled
              </CardTitle>
            </CardHeader>
          </Card>
        </div>
      )}

      {status === "error" && (
        <div className="mt-6 space-y-4">
          <ErrorState
            message={error ?? "Something went wrong"}
            onRetry={handleRetry}
          />
        </div>
      )}
    </div>
  );
}
