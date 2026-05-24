"use server";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

function extractErrorMessage(data: unknown, status: number): string {
  if (data && typeof data === "object" && "error" in data) {
    const err = (data as { error?: { code?: string; message?: string } }).error;
    if (err?.message) {
      const prefix = err.code ? `[${err.code}] ` : "";
      return `${prefix}${err.message}`;
    }
  }
  return `Request failed with status ${status}`;
}

export interface SourceOut {
  id: string;
  filename: string;
  content_type: string;
  chunk_count: number;
  created_at: string;
}

export interface CitationOut {
  source_id: string;
  source_filename: string;
  chunk_position: number;
  chunk_text: string;
}

export interface FailureCaseOut {
  question: string;
  expected_answer: string;
  actual_answer: string;
  retrieval_issue: string;
}

export interface QuestionResponse {
  question: string;
  answer: string;
  citations: CitationOut[];
  latency_ms: number;
  failure_case: FailureCaseOut | null;
}

export async function uploadDocument(
  filename: string,
  content: string,
  contentType: string = "text/plain",
): Promise<SourceOut> {
  const res = await fetch(`${BACKEND_URL}/documents/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      filename,
      content_type: contentType,
      content,
    }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(extractErrorMessage(data, res.status));
  }

  return res.json();
}

export async function queryDocument(
  question: string,
  topK: number = 5,
): Promise<QuestionResponse> {
  const res = await fetch(`${BACKEND_URL}/documents/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, top_k: topK }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(extractErrorMessage(data, res.status));
  }

  return res.json();
}

export async function getSources(): Promise<SourceOut[]> {
  const res = await fetch(`${BACKEND_URL}/documents/sources`);

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(extractErrorMessage(data, res.status));
  }

  return res.json();
}

export async function deleteSource(sourceId: string): Promise<void> {
  const res = await fetch(`${BACKEND_URL}/documents/sources/${sourceId}`, {
    method: "DELETE",
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(extractErrorMessage(data, res.status));
  }
}

export async function loadDemoScenario(
  scenario: string,
): Promise<SourceOut[]> {
  const res = await fetch(`${BACKEND_URL}/documents/demo/${scenario}`, {
    method: "POST",
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(extractErrorMessage(data, res.status));
  }

  return res.json();
}
