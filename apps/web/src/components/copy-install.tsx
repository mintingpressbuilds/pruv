"use client";

import { useState, useCallback } from "react";

export function CopyInstall() {
  const [copied, setCopied] = useState(false);
  const cmd = "pip install pruv";

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(cmd);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }, []);

  return (
    <div className="big-install" onClick={handleCopy}>
      <span className="big-install-prompt">$</span>
      <span className="big-install-cmd">{cmd}</span>
      <span className="big-install-copy">{copied ? "copied" : "copy"}</span>
    </div>
  );
}
