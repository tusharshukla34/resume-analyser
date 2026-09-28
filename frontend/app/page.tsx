"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { analyzeResume, FullAnalysisResult } from "./lib/api";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [roleTitle, setRoleTitle] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [result, setResult] = useState<FullAnalysisResult | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !roleTitle.trim()) return;

    setStatus("loading");
    setErrorMessage("");

    try {
      const data = await analyzeResume(file, roleTitle.trim());
      setResult(data);
      setStatus("success");
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Something went wrong.");
      setStatus("error");
    }
  };

  const handleReset = () => {
    setFile(null);
    setRoleTitle("");
    setResult(null);
    setStatus("idle");
  };

  return (
    <main className="min-h-screen bg-neutral-950 text-neutral-100 px-4 py-8 md:py-16">
      <div className="max-w-2xl mx-auto">
        <motion.h1
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-2xl md:text-4xl font-bold text-center mb-2"
        >
          AI Resume Analyzer
        </motion.h1>
        <p className="text-center text-neutral-400 mb-8 text-sm md:text-base">
          Upload your resume and target role to get an instant analysis
        </p>

        <AnimatePresence mode="wait">
          {status !== "success" && (
            <motion.form
              key="form"
              onSubmit={handleSubmit}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="bg-neutral-900 rounded-2xl p-5 md:p-8 shadow-xl space-y-5"
            >
              <div>
                <label className="block text-sm font-medium mb-2">Resume (PDF)</label>
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="block w-full text-sm text-neutral-300 file:mr-4 file:py-2 file:px-4
                             file:rounded-lg file:border-0 file:bg-indigo-600 file:text-white
                             file:cursor-pointer hover:file:bg-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Target Job Role</label>
                <input
                  type="text"
                  value={roleTitle}
                  onChange={(e) => setRoleTitle(e.target.value)}
                  placeholder="e.g., Data Analyst"
                  className="w-full rounded-lg bg-neutral-800 border border-neutral-700 px-4 py-2.5
                             text-sm md:text-base focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              {status === "error" && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-red-400 text-sm"
                >
                  {errorMessage}
                </motion.p>
              )}

              <motion.button
                whileTap={{ scale: 0.97 }}
                type="submit"
                disabled={!file || !roleTitle.trim() || status === "loading"}
                className="w-full py-3 rounded-lg bg-indigo-600 hover:bg-indigo-500
                           disabled:bg-neutral-700 disabled:cursor-not-allowed
                           font-medium transition-colors"
              >
                {status === "loading" ? "Analyzing..." : "Analyze Resume"}
              </motion.button>
            </motion.form>
          )}
        </AnimatePresence>

        {status === "success" && result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-neutral-900 rounded-2xl p-5 md:p-8 shadow-xl"
          >
            <p className="mb-4">Analysis complete! (Results UI coming in the next step)</p>
            <button
              onClick={handleReset}
              className="text-sm text-indigo-400 hover:text-indigo-300"
            >
              Analyze another resume
            </button>
          </motion.div>
        )}
      </div>
    </main>
  );
}