import { z } from "zod";

export const formValuesSchema = z.object({
  project_name: z.string(),
  target_user: z.string(),
  problem: z.string(),
  proposed_solution: z.string(),
  main_risks: z.array(z.string()),
  success_metric: z.string(),
});

export type FormValues = z.infer<typeof formValuesSchema>;
