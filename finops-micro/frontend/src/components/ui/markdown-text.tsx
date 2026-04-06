"use client";

import type { ReactNode } from "react";

type MarkdownTextProps = {
  content: string;
  className?: string;
};

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const tokenRegex = /(`[^`]+`|\*\*[^*]+\*\*)/g;
  let lastIndex = 0;
  let partIndex = 0;

  for (const match of text.matchAll(tokenRegex)) {
    const token = match[0];
    const tokenIndex = match.index ?? 0;
    if (tokenIndex > lastIndex) {
      nodes.push(text.slice(lastIndex, tokenIndex));
    }

    if (token.startsWith("`")) {
      nodes.push(
        <code key={`${keyPrefix}-code-${partIndex}`} className="rounded bg-slate-100 px-1 py-0.5 font-mono text-[0.85em] text-slate-800">
          {token.slice(1, -1)}
        </code>,
      );
    } else if (token.startsWith("**")) {
      nodes.push(
        <strong key={`${keyPrefix}-strong-${partIndex}`} className="font-semibold text-slate-900">
          {token.slice(2, -2)}
        </strong>,
      );
    }

    lastIndex = tokenIndex + token.length;
    partIndex += 1;
  }

  if (lastIndex < text.length) {
    nodes.push(text.slice(lastIndex));
  }
  return nodes;
}

export function MarkdownText({ content, className }: MarkdownTextProps) {
  const lines = content.split(/\r?\n/);
  const blocks: ReactNode[] = [];

  for (let i = 0; i < lines.length; i += 1) {
    const raw = lines[i] ?? "";
    const line = raw.trim();
    if (!line) {
      continue;
    }

    if (line.startsWith("### ")) {
      blocks.push(
        <h4 key={`h3-${i}`} className="mt-2 text-sm font-semibold text-slate-900">
          {renderInline(line.slice(4), `h3-${i}`)}
        </h4>,
      );
      continue;
    }

    if (line.startsWith("## ")) {
      blocks.push(
        <h3 key={`h2-${i}`} className="mt-2 text-base font-semibold text-slate-900">
          {renderInline(line.slice(3), `h2-${i}`)}
        </h3>,
      );
      continue;
    }

    if (line.startsWith("# ")) {
      blocks.push(
        <h2 key={`h1-${i}`} className="mt-2 text-lg font-semibold text-slate-900">
          {renderInline(line.slice(2), `h1-${i}`)}
        </h2>,
      );
      continue;
    }

    if (line.startsWith("- ")) {
      const items: ReactNode[] = [];
      let cursor = i;
      while (cursor < lines.length) {
        const current = (lines[cursor] ?? "").trim();
        if (!current.startsWith("- ")) {
          break;
        }
        items.push(
          <li key={`li-${cursor}`} className="leading-relaxed text-slate-800">
            {renderInline(current.slice(2), `li-${cursor}`)}
          </li>,
        );
        cursor += 1;
      }
      blocks.push(
        <ul key={`ul-${i}`} className="list-disc space-y-1 pl-5">
          {items}
        </ul>,
      );
      i = cursor - 1;
      continue;
    }

    blocks.push(
      <p key={`p-${i}`} className="leading-relaxed text-slate-800">
        {renderInline(line, `p-${i}`)}
      </p>,
    );
  }

  return <div className={className ?? "space-y-2"}>{blocks}</div>;
}
