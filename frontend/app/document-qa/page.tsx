"use client";

import { useState, useCallback, useEffect } from "react";
import {
  uploadDocument,
  queryDocument,
  getSources,
  deleteSource,
  loadDemoScenario,
  type SourceOut,
  type QuestionResponse,
} from "./actions";
import type { DocumentQAStatus } from "@/types/ai";
import { DemoScenarios } from "@/components/document-qa/DemoScenarios";
import { DocumentUploader } from "@/components/document-qa/DocumentUploader";
import { SourcesList } from "@/components/document-qa/SourcesList";
import { QuestionInput } from "@/components/document-qa/QuestionInput";
import { AnswerCard } from "@/components/document-qa/AnswerCard";
import { ErrorState } from "@/components/ai/ErrorState";
import { Separator } from "@/components/ui/separator";

type Tab = "demo" | "upload";

export default function DocumentQAPage() {
  const [activeTab, setActiveTab] = useState<Tab>("demo");
  const [sources, setSources] = useState<SourceOut[]>([]);
  const [status, setStatus] = useState<DocumentQAStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<QuestionResponse | null>(null);
  const [loadedScenario, setLoadedScenario] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    queueMicrotask(() => {
      getSources().then(setSources).catch(() => {});
    });
  }, []);

  const handleLoadScenario = useCallback(async (scenarioId: string) => {
    setStatus("loading");
    setError(null);
    setResponse(null);
    setLoadedScenario(scenarioId);

    try {
      const newSources = await loadDemoScenario(scenarioId);
      setSources((prev) => [...prev, ...newSources]);
      setStatus("success");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load scenario");
      setStatus("error");
      setLoadedScenario(null);
    }
  }, []);

  const handleQuestion = useCallback(async (question: string) => {
    setStatus("loading");
    setError(null);
    setResponse(null);

    try {
      const sourceIds = sources.length > 0 ? sources.map((s) => s.id) : undefined;
      const result = await queryDocument(question, 5, sourceIds);
      setResponse(result);
      setStatus("success");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to query documents");
      setStatus("error");
    }
  }, [sources]);

  const handleUpload = useCallback(async (filename: string, content: string, contentType: string) => {
    setStatus("loading");
    setError(null);

    try {
      const source = await uploadDocument(filename, content, contentType);
      setSources((prev) => [...prev, source]);
      setStatus("success");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload document");
      setStatus("error");
    }
  }, []);

  const handleDelete = useCallback(async (id: string) => {
    setDeletingId(id);
    try {
      await deleteSource(id);
      setSources((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete source");
    } finally {
      setDeletingId(null);
    }
  }, []);

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="mb-6 space-y-1">
        <h1 className="text-2xl font-bold">Document QA</h1>
        <p className="text-muted-foreground">
          Upload documents and ask questions. Answers come with citations and source tracking.
        </p>
      </div>

      <div className="mb-6 flex gap-1 border-b">
        <button
          onClick={() => setActiveTab("demo")}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "demo"
              ? "border-foreground text-foreground"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Demo Scenarios
        </button>
        <button
          onClick={() => setActiveTab("upload")}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "upload"
              ? "border-foreground text-foreground"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          My Documents
        </button>
      </div>

      {activeTab === "demo" && (
        <div className="space-y-6">
          <DemoScenarios
            onLoad={handleLoadScenario}
            onQuestionClick={handleQuestion}
            loadedScenario={loadedScenario}
            loading={status === "loading"}
          />
        </div>
      )}

      {activeTab === "upload" && (
        <div className="space-y-6">
          <DocumentUploader
            onUpload={handleUpload}
            disabled={status === "loading"}
          />

          <Separator />

          <SourcesList
            sources={sources}
            onDelete={handleDelete}
            deleting={deletingId}
          />

          <QuestionInput
            onSubmit={handleQuestion}
            disabled={sources.length === 0}
            loading={status === "loading"}
          />
        </div>
      )}

      {status === "error" && (
        <div className="mt-6">
          <ErrorState
            message={error ?? "Something went wrong"}
            onRetry={() => {
              setStatus("idle");
              setError(null);
            }}
          />
        </div>
      )}

      {response && (
        <div className="mt-6">
          <AnswerCard response={response} />
        </div>
      )}
    </div>
  );
}
