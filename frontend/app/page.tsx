"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";

const EXAMPLE_REPOS = [
  {
    name: "facebook/react",
    url: "https://github.com/facebook/react",
    description: "The UI library that changed everything",
  },
  {
    name: "tiangolo/fastapi",
    url: "https://github.com/tiangolo/fastapi",
    description: "Born fast, stayed fast",
  },
  {
    name: "django/django",
    url: "https://github.com/django/django",
    description: "20 years of web history",
  },
];

export default function HomePage() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  async function handleAnalyze() {
    const trimmed = url.trim();
    if (!trimmed) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: trimmed }),
      });
      if (!res.ok) throw new Error("Failed to start analysis");
      const { job_id } = await res.json();
      router.push(`/analyze/${job_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-2xl"
      >
        {/* Header */}
        <div className="mb-14 text-center">
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="text-xs font-mono tracking-[0.35em] text-neutral-600 uppercase mb-8"
          >
            Code Archeologist
          </motion.p>
          <motion.h1
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.5 }}
            className="text-5xl sm:text-6xl font-bold text-white tracking-tight leading-[1.1] mb-5"
          >
            Uncover the history
            <br />
            <span className="text-neutral-600">buried in your git log.</span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.35 }}
            className="text-neutral-500 text-lg leading-relaxed"
          >
            Paste any public GitHub URL. Get a magazine-style narrative about
            how your codebase was born, evolved, and became what it is today.
          </motion.p>
        </div>

        {/* Input */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.45 }}
        >
          <div className="flex gap-3 items-stretch">
            <div className="flex-1 flex items-center border border-neutral-800 rounded-lg bg-neutral-900/40 px-4 gap-3 focus-within:border-neutral-600 transition-colors">
              <span className="text-neutral-700 font-mono text-sm select-none shrink-0">
                $
              </span>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
                placeholder="https://github.com/owner/repo"
                className="flex-1 bg-transparent text-white font-mono text-sm py-4 outline-none placeholder:text-neutral-700 min-w-0"
                disabled={loading}
                autoFocus
              />
            </div>
            <button
              onClick={handleAnalyze}
              disabled={loading || !url.trim()}
              className="px-6 py-4 bg-white text-black font-semibold text-sm rounded-lg hover:bg-neutral-100 disabled:opacity-30 disabled:cursor-not-allowed transition-all shrink-0"
            >
              {loading ? "Starting…" : "Analyze"}
            </button>
          </div>
          <AnimatePresence>
            {error && (
              <motion.p
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mt-3 text-red-400 text-sm font-mono"
              >
                {error}
              </motion.p>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Example repos */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-16"
        >
          <p className="text-neutral-700 text-xs font-mono uppercase tracking-widest mb-4 text-center">
            Try an example
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {EXAMPLE_REPOS.map((repo) => (
              <button
                key={repo.url}
                onClick={() => setUrl(repo.url)}
                className="text-left border border-neutral-800/80 rounded-lg p-4 hover:border-neutral-700 hover:bg-neutral-900/40 transition-all group"
              >
                <p className="text-neutral-300 font-mono text-sm group-hover:text-white transition-colors">
                  {repo.name}
                </p>
                <p className="text-neutral-600 text-xs mt-1 leading-snug">
                  {repo.description}
                </p>
              </button>
            ))}
          </div>
        </motion.div>
      </motion.div>
    </main>
  );
}
