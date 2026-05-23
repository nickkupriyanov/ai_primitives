"use client";

import { useState, useCallback, useEffect } from "react";
import { formValuesSchema, type FormValues } from "@/lib/validators/formSchema";
import { RequestStatus } from "@/types/ai";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Label } from "@/components/ui/label";
import { ApprovalCard } from "@/components/ai/ApprovalCard";
import { ErrorState } from "@/components/ai/ErrorState";
import { RetryButton } from "@/components/ai/RetryButton";
import { Loader2, Save, Plus, X, Lightbulb } from "lucide-react";

const backendUrl =
  process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

const emptyForm: FormValues = {
  project_name: "",
  target_user: "",
  problem: "",
  proposed_solution: "",
  main_risks: [""],
  success_metric: "",
};

function isEmptyValue(value: unknown): boolean {
  if (typeof value === "string") return value.trim() === "";
  if (Array.isArray(value)) {
    return (
      value.length === 0 ||
      value.every((v) => typeof v === "string" && v.trim() === "")
    );
  }
  return false;
}

function getApiErrorMessage(data: unknown, status: number) {
  if (data && typeof data === "object" && "error" in data) {
    const { error } = data as {
      error?: string | { message?: string };
    };

    if (typeof error === "string") return error;
    if (error?.message) return error.message;
  }

  return `Request failed with status ${status}`;
}

export default function FormAssistantPage() {
  const [context, setContext] = useState("");
  const [currentValues, setCurrentValues] = useState<FormValues>(emptyForm);
  const [suggestedValues, setSuggestedValues] = useState<FormValues | null>(null);
  const [status, setStatus] = useState<RequestStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [showApproval, setShowApproval] = useState(false);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    queueMicrotask(() => {
      try {
        const saved = localStorage.getItem("form-assistant-values");
        if (saved) {
          const parsed = JSON.parse(saved);
          const validated = formValuesSchema.partial().parse(parsed);
          setCurrentValues((prev) => ({ ...prev, ...validated }));
        }
      } catch {
        // ignore invalid saved data
      }
    });
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!context.trim()) return;

    setStatus("loading");
    setSuggestedValues(null);
    setError(null);
    setShowApproval(false);
    setSavedMessage(null);

    try {
      const res = await fetch(`${backendUrl}/form-assistant`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ context }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(getApiErrorMessage(data, res.status));
      }

      const json = await res.json();
      const validated = formValuesSchema.parse(json);
      setSuggestedValues(validated);
      setShowApproval(true);
      setStatus("success");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to process suggestion";
      setError(message);
      setStatus("error");
    }
  }, [context]);

  const handleApprove = useCallback(() => {
    if (!suggestedValues) return;
    setCurrentValues(suggestedValues);
    setShowApproval(false);
  }, [suggestedValues]);

  const handleReject = useCallback(() => {
    setShowApproval(false);
    setSuggestedValues(null);
  }, []);

  const handleSave = useCallback(() => {
    localStorage.setItem("form-assistant-values", JSON.stringify(currentValues));
    setSavedMessage("Saved to localStorage");
    setTimeout(() => setSavedMessage(null), 3000);
  }, [currentValues]);

  const updateField = useCallback(
    <K extends keyof FormValues>(field: K, value: FormValues[K]) => {
      setCurrentValues((prev) => ({ ...prev, [field]: value }));
    },
    []
  );

  const addRisk = useCallback(() => {
    setCurrentValues((prev) => ({
      ...prev,
      main_risks: [...prev.main_risks, ""],
    }));
  }, []);

  const removeRisk = useCallback((index: number) => {
    setCurrentValues((prev) => ({
      ...prev,
      main_risks: prev.main_risks.filter((_, i) => i !== index),
    }));
  }, []);

  const updateRisk = useCallback((index: number, value: string) => {
    setCurrentValues((prev) => ({
      ...prev,
      main_risks: prev.main_risks.map((r, i) => (i === index ? value : r)),
    }));
  }, []);

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="mb-6 space-y-1">
        <h1 className="text-2xl font-bold">AI Form Assistant</h1>
        <p className="text-muted-foreground">
          Describe your project and let AI suggest form values. You must approve before anything is applied.
        </p>
      </div>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Project Description</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              placeholder="Describe your project, target audience, and goals..."
              value={context}
              onChange={(e) => setContext(e.target.value)}
              rows={4}
              disabled={status === "loading"}
            />
            <div className="flex items-center gap-2">
              <Button
                onClick={handleSubmit}
                disabled={!context.trim() || status === "loading"}
              >
                {status === "loading" ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Lightbulb className="mr-2 h-4 w-4" />
                )}
                {status === "loading" ? "Thinking..." : "Help me fill this form"}
              </Button>
              {(status === "error" || status === "success") && !showApproval && (
                <RetryButton onRetry={handleSubmit} />
              )}
            </div>
          </CardContent>
        </Card>

        {status === "error" && (
          <div className="space-y-4">
            <ErrorState
              message={error ?? "The model returned invalid output. Please retry or simplify your input."}
              onRetry={handleSubmit}
            />
          </div>
        )}

        {showApproval && suggestedValues && (
          <ApprovalCard
            title="Review AI Suggestions"
            onApprove={handleApprove}
            onCancel={handleReject}
          >
            <div className="space-y-3 text-sm">
              {(
                [
                  ["Project Name", suggestedValues.project_name],
                  ["Target User", suggestedValues.target_user],
                  ["Problem", suggestedValues.problem],
                  ["Proposed Solution", suggestedValues.proposed_solution],
                  ["Success Metric", suggestedValues.success_metric],
                ] as const
              ).map(([label, value]) => (
                <div key={label}>
                  <span className="text-muted-foreground">{label}:</span>{" "}
                  <span className={isEmptyValue(currentValues[label.toLowerCase().replace(/ /g, "_") as keyof FormValues]) ? "font-medium" : ""}>
                    {value}
                  </span>
                </div>
              ))}
              <div>
                <span className="text-muted-foreground">Main Risks:</span>
                <ul className="mt-1 list-disc pl-4">
                  {suggestedValues.main_risks.map((risk, i) => (
                    <li key={i}>{risk}</li>
                  ))}
                </ul>
              </div>
            </div>
          </ApprovalCard>
        )}

        <Separator />

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Project Form</h2>
            <Button variant="outline" size="sm" onClick={handleSave}>
              <Save className="mr-2 h-4 w-4" />
              Save
            </Button>
          </div>
          {savedMessage && (
            <p className="text-sm text-green-600">{savedMessage}</p>
          )}

          <div className="grid gap-4">
            <div className="space-y-2">
              <Label htmlFor="project_name">Project Name</Label>
              <Input
                id="project_name"
                value={currentValues.project_name}
                onChange={(e) => updateField("project_name", e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="target_user">Target User</Label>
              <Input
                id="target_user"
                value={currentValues.target_user}
                onChange={(e) => updateField("target_user", e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="problem">Problem</Label>
              <Textarea
                id="problem"
                value={currentValues.problem}
                onChange={(e) => updateField("problem", e.target.value)}
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="proposed_solution">Proposed Solution</Label>
              <Textarea
                id="proposed_solution"
                value={currentValues.proposed_solution}
                onChange={(e) => updateField("proposed_solution", e.target.value)}
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label>Main Risks</Label>
              <div className="space-y-2">
                {currentValues.main_risks.map((risk, index) => (
                  <div key={index} className="flex gap-2">
                    <Input
                      value={risk}
                      onChange={(e) => updateRisk(index, e.target.value)}
                      placeholder={`Risk ${index + 1}`}
                    />
                    {currentValues.main_risks.length > 1 && (
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => removeRisk(index)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                ))}
                <Button variant="outline" size="sm" onClick={addRisk}>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Risk
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="success_metric">Success Metric</Label>
              <Input
                id="success_metric"
                value={currentValues.success_metric}
                onChange={(e) => updateField("success_metric", e.target.value)}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
