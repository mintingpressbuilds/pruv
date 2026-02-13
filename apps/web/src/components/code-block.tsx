"use client";

import { useState } from "react";

interface CodeBlockProps {
  code: string;
  language?: string;
  filename?: string;
  showLineNumbers?: boolean;
}

export function CodeBlock({
  code,
  language = "python",
  filename,
  showLineNumbers = false,
}: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lines = code.split("\n");

  return (
    <div className="relative group rounded-xl overflow-hidden border border-zinc-800 bg-zinc-950">
      {/* Header */}
      {(filename || language) && (
        <div className="flex items-center justify-between px-4 py-2 bg-zinc-900/80 border-b border-zinc-800">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-zinc-700" />
              <div className="w-3 h-3 rounded-full bg-zinc-700" />
              <div className="w-3 h-3 rounded-full bg-zinc-700" />
            </div>
            {filename && (
              <span className="text-xs text-zinc-500 font-mono ml-2">
                {filename}
              </span>
            )}
          </div>
          <button
            onClick={handleCopy}
            className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors font-mono opacity-0 group-hover:opacity-100"
          >
            {copied ? "copied!" : "copy"}
          </button>
        </div>
      )}

      {/* Code */}
      <div className="overflow-x-auto">
        <pre className="p-4 text-sm leading-relaxed">
          <code className={`language-${language}`}>
            {lines.map((line, i) => (
              <div key={i} className="flex">
                {showLineNumbers && (
                  <span className="select-none text-zinc-600 text-right w-8 pr-4 flex-shrink-0">
                    {i + 1}
                  </span>
                )}
                <span className="flex-1">
                  {highlightSyntax(line, language)}
                </span>
              </div>
            ))}
          </code>
        </pre>
      </div>
    </div>
  );
}

function highlightSyntax(line: string, language: string): React.ReactNode {
  if (language === "bash" || language === "shell") {
    if (line.startsWith("$") || line.startsWith("#")) {
      return (
        <>
          <span className="text-zinc-500">{line[0]} </span>
          <span className="text-emerald-400">{line.slice(2)}</span>
        </>
      );
    }
    return <span className="text-emerald-300">{line}</span>;
  }

  if (language === "python") {
    return highlightPython(line);
  }

  return <span className="text-zinc-300">{line}</span>;
}

function highlightPython(line: string): React.ReactNode {
  const keywords =
    /\b(from|import|def|class|return|if|elif|else|for|while|with|as|try|except|finally|raise|yield|async|await|True|False|None)\b/g;
  const strings = /(["'])(?:(?=(\\?))\2.)*?\1/g;
  const comments = /(#.*)$/g;
  const decorators = /(@\w+)/g;
  const functions = /\b(\w+)\(/g;

  const parts: { start: number; end: number; className: string }[] = [];

  let match;

  // Comments first (highest priority)
  const commentRegex = new RegExp(comments);
  while ((match = commentRegex.exec(line)) !== null) {
    parts.push({
      start: match.index,
      end: match.index + match[0].length,
      className: "text-zinc-500 italic",
    });
  }

  // Strings
  const stringRegex = new RegExp(strings);
  while ((match = stringRegex.exec(line)) !== null) {
    parts.push({
      start: match.index,
      end: match.index + match[0].length,
      className: "text-amber-300",
    });
  }

  // Decorators
  const decoRegex = new RegExp(decorators);
  while ((match = decoRegex.exec(line)) !== null) {
    parts.push({
      start: match.index,
      end: match.index + match[0].length,
      className: "text-purple-400",
    });
  }

  // Keywords
  const kwRegex = new RegExp(keywords);
  while ((match = kwRegex.exec(line)) !== null) {
    parts.push({
      start: match.index,
      end: match.index + match[0].length,
      className: "text-pink-400",
    });
  }

  // Functions
  const fnRegex = new RegExp(functions);
  while ((match = fnRegex.exec(line)) !== null) {
    parts.push({
      start: match.index,
      end: match.index + match[1].length,
      className: "text-blue-400",
    });
  }

  if (parts.length === 0) {
    return <span className="text-zinc-300">{line}</span>;
  }

  // Sort by start position and remove overlaps
  parts.sort((a, b) => a.start - b.start);
  const merged: typeof parts = [];
  for (const part of parts) {
    if (merged.length === 0 || part.start >= merged[merged.length - 1].end) {
      merged.push(part);
    }
  }

  const result: React.ReactNode[] = [];
  let lastEnd = 0;

  for (const part of merged) {
    if (part.start > lastEnd) {
      result.push(
        <span key={`plain-${lastEnd}`} className="text-zinc-300">
          {line.slice(lastEnd, part.start)}
        </span>
      );
    }
    result.push(
      <span key={`hl-${part.start}`} className={part.className}>
        {line.slice(part.start, part.end)}
      </span>
    );
    lastEnd = part.end;
  }

  if (lastEnd < line.length) {
    result.push(
      <span key={`plain-${lastEnd}`} className="text-zinc-300">
        {line.slice(lastEnd)}
      </span>
    );
  }

  return <>{result}</>;
}
