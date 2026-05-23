import { z } from "zod";

export const briefOutputSchema = z.object({
  persona: z.string(),
  pain_points: z.array(z.string()),
  risks: z.array(z.string()),
  next_questions: z.array(z.string()),
});

export type BriefOutput = z.infer<typeof briefOutputSchema>;
