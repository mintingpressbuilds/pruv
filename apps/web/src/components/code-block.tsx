"use client";

import { useState, useCallback } from "react";

interface Token {
  type: "keyword" | "builtin" | "string" | "comment" | "decorator" | "function" | "number" | "operator" | "variable" | "plain" | "prompt";
  text: string;
}

function tokenize(code: string): Token[] {
  const tokens: Token[] = [];
  const lines = code.split("\n");

  for (let li = 0; li < lines.length; li++) {
    if (li > 0) tokens.push({ type: "plain", text: "\n" });
    const line = lines[li];

    if (line.trimStart().startsWith("#")) {
      tokens.push({ type: "comment", text: line });
      continue;
    }

    if (line.trimStart().startsWith("@")) {
      const match = line.match(/^(\s*)(@\w+(?:\.\w+)*)/);
      if (match) {
        if (match[1]) tokens.push({ type: "plain", text: match[1] });
        tokens.push({ type: "decorator", text: match[2] });
        const rest = line.slice((match[1]?.length || 0) + match[2].length);
        if (rest) tokenizeLine(rest, tokens);
        continue;
      }
    }

    if (line.trimStart().startsWith("$ ")) {
      const indent = line.match(/^(\s*)/)?.[1] || "";
      if (indent) tokens.push({ type: "plain", text: indent });
      tokens.push({ type: "prompt", text: "$ " });
      const rest = line.slice(indent.length + 2);
      tokens.push({ type: "plain", text: rest });
      continue;
    }

    tokenizeLine(line, tokens);
  }
  return tokens;
}

function tokenizeLine(line: string, tokens: Token[]) {
  const keywords = /\b(from|import|def|class|return|await|async|as|if|else|for|in|with|try|except|raise|pass|True|False|None)\b/g;
  const builtins = /\b(print|str|int|list|dict|len|type)\b/g;
  const strings = /("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|f"(?:[^"\\]|\\.)*"|f'(?:[^'\\]|\\.)*')/g;

  const parts: { start: number; end: number; type: Token["type"]; text: string }[] = [];
  let m;

  // Strings first (highest priority)
  while ((m = strings.exec(line)) !== null) {
    parts.push({ start: m.index, end: m.index + m[0].length, type: "string", text: m[0] });
  }

  // Keywords
  while ((m = keywords.exec(line)) !== null) {
    if (!parts.some(p => m!.index >= p.start && m!.index < p.end)) {
      parts.push({ start: m.index, end: m.index + m[0].length, type: "keyword", text: m[0] });
    }
  }

  // Builtins
  while ((m = builtins.exec(line)) !== null) {
    if (!parts.some(p => m!.index >= p.start && m!.index < p.end)) {
      parts.push({ start: m.index, end: m.index + m[0].length, type: "builtin", text: m[0] });
    }
  }

  // Function calls: word followed by (
  const fnCalls = /\b(\w+)\s*\(/g;
  while ((m = fnCalls.exec(line)) !== null) {
    const fnStart = m.index;
    const fnEnd = m.index + m[1].length;
    if (!parts.some(p => fnStart >= p.start && fnStart < p.end)) {
      parts.push({ start: fnStart, end: fnEnd, type: "function", text: m[1] });
    }
  }

  parts.sort((a, b) => a.start - b.start);

  let cursor = 0;
  for (const part of parts) {
    if (part.start > cursor) {
      tokens.push({ type: "plain", text: line.slice(cursor, part.start) });
    }
    if (part.start >= cursor) {
      tokens.push({ type: part.type, text: part.text });
      cursor = part.end;
    }
  }
  if (cursor < line.length) {
    tokens.push({ type: "plain", text: line.slice(cursor) });
  }
}

const TOKEN_CLASSES: Record<Token["type"], string> = {
  keyword: "cb-kw",
  builtin: "cb-fn",
  string: "cb-str",
  comment: "cb-cm",
  decorator: "cb-dec",
  function: "cb-fn",
  number: "cb-num",
  operator: "cb-op",
  variable: "cb-var",
  plain: "",
  prompt: "cb-prompt",
};

export function CodeBlock({ code, label }: { code: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  const tokens = tokenize(code.trim());

  const handleCopy = useCallback(() => {
    const clean = code.trim().replace(/^\$ /gm, "");
    navigator.clipboard.writeText(clean);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }, [code]);

  return (
    <div className="cb">
      {label && <div className="cb-label">{label}</div>}
      <button className="cb-copy" onClick={handleCopy}>
        {copied ? "copied" : "copy"}
      </button>
      <pre className="cb-pre">
        <code>
          {tokens.map((t, i) => {
            const cls = TOKEN_CLASSES[t.type];
            return cls ? (
              <span key={i} className={cls}>{t.text}</span>
            ) : (
              <span key={i}>{t.text}</span>
            );
          })}
        </code>
      </pre>
    </div>
  );
}
