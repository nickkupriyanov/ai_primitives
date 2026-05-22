"use client";

interface StreamingMessageProps {
  text: string;
  isStreaming: boolean;
}

export function StreamingMessage({ text, isStreaming }: StreamingMessageProps) {
  return (
    <div className="whitespace-pre-wrap text-sm leading-relaxed">
      {text}
      {isStreaming && (
        <span className="inline-block w-2 h-4 ml-0.5 bg-foreground animate-pulse align-text-bottom" />
      )}
    </div>
  );
}
