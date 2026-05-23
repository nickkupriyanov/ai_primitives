import { z } from "zod";

export const summarizeTextArgsSchema = z.object({ text: z.string() });
export const classifyPriorityArgsSchema = z.object({ text: z.string() });
export const draftQuestionsArgsSchema = z.object({ context: z.string() });

export const summarizeTextResultSchema = z.object({ summary: z.string() });
export const classifyPriorityResultSchema = z.object({
  priority: z.enum(["low", "medium", "high"]),
  reason: z.string(),
});
export const draftQuestionsResultSchema = z.object({
  questions: z.array(z.string()),
});
