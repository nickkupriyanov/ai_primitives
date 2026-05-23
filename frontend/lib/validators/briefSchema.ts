import { z } from "zod";

export const briefOutputSchema = z.object({
  topics: z.array(z.string()),
  pain_points: z.array(z.string()),
  risks: z.array(z.string()),
  next_questions: z.array(z.string()),
  meta: z.object({
    model: z.string().nullable().optional(),
    latency_ms: z.number().nullable().optional(),
  }),
});

export type BriefOutput = z.infer<typeof briefOutputSchema>;
