"use client";

interface JsonPreviewProps {
  data: unknown;
  className?: string;
}

export function JsonPreview({ data, className }: JsonPreviewProps) {
  return (
    <pre
      className={`rounded-md bg-zinc-950 p-4 overflow-x-auto text-sm font-mono text-zinc-50 ${className || ""}`}
    >
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}
