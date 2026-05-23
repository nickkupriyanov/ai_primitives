"use server";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

interface ToolPlanResult {
  toolName: string;
  args: unknown;
  requiresApproval: boolean;
}

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

export async function requestToolCall(input: string): Promise<ToolPlanResult> {
  const res = await fetch(`${BACKEND_URL}/tools/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(extractErrorMessage(data, res.status));
  }

  const json = await res.json();
  return {
    toolName: json.tool_name,
    args: json.arguments,
    requiresApproval: json.requires_approval,
  };
}

export async function executeApprovedTool(
  toolName: string,
  args: unknown,
): Promise<unknown> {
  const res = await fetch(`${BACKEND_URL}/tools/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      tool_name: toolName,
      arguments: args,
      approved: true,
    }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(extractErrorMessage(data, res.status));
  }

  const json = await res.json();
  return json.result;
}
