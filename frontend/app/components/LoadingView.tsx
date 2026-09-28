"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

const STAGES = [
  "Reading your resume",
  "Understanding the target role",
  "Matching your skills",
  "Writing suggestions",
];

export default function LoadingView() {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    const id = setInterval(
      () => setStage((s) => Math.min(s + 1, STAGES.length - 1)),
      4000
    );
    return () => clearInterval(id);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-neutral-900 rounded-2xl p-8 shadow-xl max-w-md mx-auto"
    >
      <div className="flex justify-center mb-6">
        <motion.div
          className="w-12 h-12 rounded-full border-4 border-neutral-700 border-t-indigo-500"
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
        />
      </div>
      <ul className="space-y-3">
        {STAGES.map((label, i) => (
          <li
            key={label}
            className={`flex items-center gap-3 text-sm transition-colors ${
              i < stage
                ? "text-emerald-400"
                : i === stage
                ? "text-neutral-100"
                : "text-neutral-600"
            }`}
          >
            <span className="w-4 text-center">{i < stage ? "✓" : i === stage ? "•" : ""}</span>
            {label}
          </li>
        ))}
      </ul>
      <p className="text-xs text-neutral-500 text-center mt-6">
        This usually takes 10 to 20 seconds
      </p>
    </motion.div>
  );
}