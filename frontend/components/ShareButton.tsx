"use client";

import { useState } from "react";

export default function ShareButton() {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <button
      onClick={handleCopy}
      className="text-xs font-mono text-neutral-600 hover:text-neutral-300 transition-colors border border-neutral-800 rounded px-3 py-1.5 hover:border-neutral-600"
    >
      {copied ? "Copied!" : "Share Report"}
    </button>
  );
}
