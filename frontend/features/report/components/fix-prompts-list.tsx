"use client";

import { useState } from "react";

import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import type { FixPrompt } from "@/shared/types/report";

interface FixPromptsListProps {
  prompts: FixPrompt[];
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={async () => {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
    >
      {copied ? "Copied" : "Copy"}
    </Button>
  );
}

export function FixPromptsList({ prompts }: FixPromptsListProps) {
  if (prompts.length === 0) {
    return (
      <div className="neon-card p-6">
        <p className="text-sm text-white/40">
          No anti-patterns detected and no fallback signal available for this repo.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {prompts.map((p, i) => (
        <div key={`${p.type}-${i}`} className="neon-card p-4">
          <div className="mb-2 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="border-magenta/40 text-magenta">
                {p.type}
              </Badge>
              {p.fallback && (
                <Badge variant="outline" className="text-xs text-white/40">
                  Generic — Python-only detection
                </Badge>
              )}
              <span className="font-mono text-xs text-white/35">{p.location}</span>
            </div>
            <CopyButton text={p.prompt} />
          </div>
          <pre className="overflow-x-auto rounded-md bg-white/5 p-3 text-xs whitespace-pre-wrap text-white/70">
            {p.prompt}
          </pre>
          {p.fallback && (
            <p className="mt-2 text-xs text-white/35">
              No language-specific anti-pattern was detected — this prompt is built from
              general structural metrics instead.
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
