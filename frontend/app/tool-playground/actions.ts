"use server";

import { openai } from "@/lib/ai/client";
import { AI_CONFIG } from "@/lib/ai/config";
import { toolPlaygroundPrompt } from "@/lib/ai/prompts";
import { toolDefinitions, executeTool } from "@/lib/ai/tools";

interface ToolCallRequest {
  toolName: string;
  args: unknown;
}

export async function requestToolCall(input: string): Promise<ToolCallRequest> {
  try {
    const response = await openai.chat.completions.create({
      model: AI_CONFIG.model,
      messages: [
        { role: "system", content: toolPlaygroundPrompt },
        { role: "user", content: input },
      ],
      tools: toolDefinitions,
      tool_choice: "auto",
    });

    const message = response.choices[0]?.message;
    const toolCalls = message?.tool_calls;

    if (!toolCalls || toolCalls.length === 0) {
      throw new Error("The model did not choose a tool. Try a more specific prompt.");
    }

    const call = toolCalls[0];
    const fn = (call as { function: { name: string; arguments: string } }).function;
    let args: unknown;
    try {
      args = JSON.parse(fn.arguments);
    } catch {
      throw new Error("The model returned invalid tool arguments.");
    }

    return { toolName: fn.name, args };
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    throw new Error(`Tool request failed: ${message}`);
  }
}

export async function executeApprovedTool(toolName: string, args: unknown) {
  try {
    const result = await executeTool(toolName, args);
    return result;
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    throw new Error(`Tool execution failed: ${message}`);
  }
}
