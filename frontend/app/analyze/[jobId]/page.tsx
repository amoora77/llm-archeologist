"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";

const STATUS_LABELS: Record<string, string> = {
  cloning: "Cloning repository",
  extracting: "Extracting git history",
  processing: "Processing commits",
  analyzing: "Analyzing with AI",
  complete: "Report ready",
  error: "Analysis failed",
};

const FUN_FACTS = [
  "git was created by Linus Torvalds in 2005 — it took him two weeks.",
  "The average developer spends 13% of their time resolving merge conflicts.",
  "The word 'bug' in computing traces back to 1947 and an actual moth found in a relay.",
  "In most repos, 10% of contributors make 90% of the commits.",
  "The longest commit message on record was over 2,000 words long.",
  "git blame was originally called git annotate.",
  "The first open-source commit message ever written was 'Initial revision' by Linus Torvalds.",
];

const PROGRESS_STEPS = ["cloning", "extracting", "processing", "analyzing", "complete"];

export default function AnalyzePage() {
  const params = useParams<{ jobId: string }>();
  const router = useRouter();

  const [events, setEvents] = useState<{ status: string; message: string }[]>([]);
  const [currentStatus, setCurrentStatus] = useState("cloning");
  const [error, setError] = useState("");
  const [factIdx, setFactIdx] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setFactIdx((i) => (i + 1) % FUN_FACTS.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const es = new EventSource(`/api/analyze/${params.jobId}/stream`);

    es.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.status === "heartbeat") return;

      setCurrentStatus(data.status);

      if (data.message) {
        setEvents((prev) => [...prev, { status: data.status, message: data.message }]);
      }

      if (data.status === "complete") {
        es.close();
        setTimeout(() => router.push(`/report/${data.report_id}`), 600);
      }

      if (data.status === "error") {
        es.close();
        setError(data.message ?? "Analysis failed");
      }
    };

    es.onerror = () => {
      es.close();
      setError("Lost connection to server. Please try again.");
    };

    return () => es.close();
  }, [params.jobId, router]);

  const stepIdx = PROGRESS_STEPS.indexOf(currentStatus);
  const progressPct = Math.round(((stepIdx + 1) / PROGRESS_STEPS.length) * 100);

  if (error) {
    return (
      <main className="min-h-screen flex items-center justify-center px-6">
        <div className="text-center">
          <p className="text-neutral-600 font-mono text-xs uppercase tracking-widest mb-4">
            Analysis failed
          </p>
          <p className="text-red-400 font-mono text-sm mb-8 max-w-sm">{error}</p>
          <button
            onClick={() => router.push("/")}
            className="border border-neutral-800 text-white px-6 py-3 rounded-lg text-sm hover:bg-neutral-900 transition-colors"
          >
            ← Try again
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6">
      <div className="w-full max-w-lg">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12 text-center"
        >
          <p className="text-xs font-mono tracking-[0.35em] text-neutral-600 uppercase mb-8">
            Code Archeologist
          </p>
          <h1 className="text-4xl font-bold text-white mb-3">
            {STATUS_LABELS[currentStatus] ?? "Working…"}
          </h1>
          <p className="text-neutral-600 text-sm font-mono">
            {events.at(-1)?.message ?? "Initializing…"}
          </p>
        </motion.div>

        {/* Progress bar */}
        <div className="relative h-px bg-neutral-900 rounded-full mb-12 overflow-hidden">
          <motion.div
            className="absolute inset-y-0 left-0 bg-neutral-400 rounded-full"
            initial={{ width: "0%" }}
            animate={{ width: `${progressPct}%` }}
            transition={{ duration: 0.7, ease: "easeOut" }}
          />
        </div>

        {/* Event log */}
        <div className="space-y-2 mb-12 min-h-[100px]">
          <AnimatePresence initial={false}>
            {events.slice(-6).map((event, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: i === events.slice(-6).length - 1 ? 0.9 : 0.35 }}
                className="flex items-start gap-3"
              >
                <span className="text-neutral-700 font-mono text-xs mt-0.5 shrink-0">›</span>
                <span className="text-neutral-500 font-mono text-xs leading-relaxed">
                  {event.message}
                </span>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Fun fact */}
        <div className="border border-neutral-900 rounded-lg p-5">
          <p className="text-neutral-700 text-xs font-mono uppercase tracking-widest mb-3">
            Did you know
          </p>
          <AnimatePresence mode="wait">
            <motion.p
              key={factIdx}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4 }}
              className="text-neutral-500 text-sm leading-relaxed"
            >
              {FUN_FACTS[factIdx]}
            </motion.p>
          </AnimatePresence>
        </div>
      </div>
    </main>
  );
}
