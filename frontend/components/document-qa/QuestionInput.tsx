"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2, Send } from "lucide-react";

interface QuestionInputProps {
  onSubmit: (question: string) => void;
  disabled: boolean;
  loading: boolean;
}

export function QuestionInput({ onSubmit, disabled, loading }: QuestionInputProps) {
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const input = form.elements.namedItem("question") as HTMLInputElement;
    if (input.value.trim()) {
      onSubmit(input.value.trim());
      input.value = "";
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <Input
        name="question"
        placeholder={disabled ? "Upload documents to ask questions..." : "Ask a question about your documents..."}
        disabled={disabled || loading}
        className="flex-1"
      />
      <Button type="submit" disabled={disabled || loading}>
        {loading ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <Send className="mr-2 h-4 w-4" />
        )}
        {loading ? "Thinking..." : "Ask"}
      </Button>
    </form>
  );
}
