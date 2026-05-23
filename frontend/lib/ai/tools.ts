import { z } from "zod";
import {
  summarizeTextArgsSchema,
  classifyPriorityArgsSchema,
  draftQuestionsArgsSchema,
  summarizeTextResultSchema,
  classifyPriorityResultSchema,
  draftQuestionsResultSchema,
} from "@/lib/validators/toolSchema";

export const toolDefinitions = [
  {
    type: "function" as const,
    function: {
      name: "summarize_text",
      description: "Summarize a piece of text into a shorter version.",
      parameters: {
        type: "object",
        properties: { text: { type: "string", description: "The text to summarize" } },
        required: ["text"],
      },
    },
  },
  {
    type: "function" as const,
    function: {
      name: "classify_priority",
      description: "Classify the priority level of a given text or task description.",
      parameters: {
        type: "object",
        properties: { text: { type: "string", description: "The text to classify" } },
        required: ["text"],
      },
    },
  },
  {
    type: "function" as const,
    function: {
      name: "draft_follow_up_questions",
      description: "Draft follow-up questions based on provided context.",
      parameters: {
        type: "object",
        properties: { context: { type: "string", description: "The context to generate questions from" } },
        required: ["context"],
      },
    },
  },
];

export async function executeTool(name: string, args: unknown) {
  switch (name) {
    case "summarize_text": {
      const { text } = summarizeTextArgsSchema.parse(args);
      const summary = text.length > 80 ? text.slice(0, 80) + "..." : text;
      return summarizeTextResultSchema.parse({ summary });
    }
    case "classify_priority": {
      const { text } = classifyPriorityArgsSchema.parse(args);
      const priority = text.length > 100 ? "high" : text.length > 50 ? "medium" : "low";
      return classifyPriorityResultSchema.parse({
        priority,
        reason: "Based on text length heuristic.",
      });
    }
    case "draft_follow_up_questions": {
      const { context } = draftQuestionsArgsSchema.parse(args);
      return draftQuestionsResultSchema.parse({
        questions: [
          "What is the budget?",
          "What is the timeline?",
          "Who are the stakeholders?",
        ],
      });
    }
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}
