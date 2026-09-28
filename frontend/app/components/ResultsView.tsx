"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { motion, animate } from "framer-motion";
import type { FullAnalysisResult } from "../lib/api";
import { renderInline } from "../lib/format";

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.1 } },
};

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

function scoreColor(score: number) {
  if (score >= 70) return "text-emerald-400";
  if (score >= 40) return "text-amber-400";
  return "text-rose-400";
}

// Backend returns lowercase skills; recover the original casing for display.
function buildDisplayName(result: FullAnalysisResult) {
  const map = new Map<string, string>();
  [...result.role.required_skills, ...result.resume.skills].forEach((s) => {
    const key = s.trim().toLowerCase();
    if (!map.has(key)) map.set(key, s.trim());
  });
  return (skill: string) => map.get(skill.toLowerCase()) ?? skill;
}

function ScoreRing({ score }: { score: number }) {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const [shown, setShown] = useState(0);

  useEffect(() => {
    const controls = animate(0, score, {
      duration: 1.2,
      ease: "easeOut",
      onUpdate: (v) => setShown(Math.round(v * 10) / 10),
    });
    return () => controls.stop();
  }, [score]);

  return (
    <div className={`relative w-32 h-32 shrink-0 ${scoreColor(score)}`}>
      <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
        <circle cx="60" cy="60" r={radius} fill="none" strokeWidth="10" className="stroke-neutral-800" />
        <motion.circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          strokeWidth="10"
          strokeLinecap="round"
          stroke="currentColor"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: circumference * (1 - score / 100) }}
          transition={{ duration: 1.2, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold">{shown}%</span>
        <span className="text-xs text-neutral-400">match</span>
      </div>
    </div>
  );
}

function Chip({ label, tone }: { label: string; tone: "good" | "gap" }) {
  const styles =
    tone === "good"
      ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/30"
      : "bg-rose-500/10 text-rose-300 border-rose-500/30";
  return (
    <span className={`inline-block px-3 py-1 rounded-full text-xs md:text-sm border ${styles}`}>
      {label}
    </span>
  );
}

function Card({
  title,
  children,
  className = "",
}: {
  title?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <motion.section
      variants={item}
      className={`bg-neutral-900 rounded-2xl p-5 md:p-6 shadow-xl ${className}`}
    >
      {title && <h2 className="text-base md:text-lg font-semibold mb-3">{title}</h2>}
      {children}
    </motion.section>
  );
}

export default function ResultsView({
  result,
  onReset,
}: {
  result: FullAnalysisResult;
  onReset: () => void;
}) {
  const name = buildDisplayName(result);

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="grid gap-6 lg:grid-cols-[340px_1fr] items-start"
    >
      {/* Left: pinned summary */}
      <div className="space-y-4 lg:sticky lg:top-8">
        <Card>
          <div className="flex flex-col items-center gap-4 text-center">
            <ScoreRing score={result.match_percentage} />
            <div>
              <p className="text-xs uppercase tracking-wide text-neutral-400">Target role</p>
              <h2 className="text-xl font-bold">{result.role.role_title}</h2>
            </div>
            <p className="text-sm text-neutral-300 leading-relaxed text-left">
              {renderInline(result.match_analysis)}
            </p>
          </div>
        </Card>
        <motion.button
          variants={item}
          whileTap={{ scale: 0.97 }}
          onClick={onReset}
          className="w-full py-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 font-medium transition-colors"
        >
          Analyze another resume
        </motion.button>
      </div>

      {/* Right: details */}
      <div className="space-y-6">
        <div className="grid gap-6 md:grid-cols-2 items-start">
          <Card title="Skills you have">
            <div className="flex flex-wrap gap-2">
              {result.matched_skills.length > 0 ? (
                result.matched_skills.map((s) => <Chip key={s} label={name(s)} tone="good" />)
              ) : (
                <p className="text-sm text-neutral-400">No matching skills found.</p>
              )}
            </div>
          </Card>
          <Card title="Skills to add">
            <div className="flex flex-wrap gap-2">
              {result.missing_skills.length > 0 ? (
                result.missing_skills.map((s) => <Chip key={s} label={name(s)} tone="gap" />)
              ) : (
                <p className="text-sm text-neutral-400">No gaps found. Nice work.</p>
              )}
            </div>
          </Card>
        </div>

        {result.suggestions.length > 0 && (
          <Card title="How to improve">
            <ul className="space-y-4">
              {result.suggestions.map((s) => (
                <li key={s.missing_skill} className="border-l-2 border-indigo-500/50 pl-4">
                  <p className="text-sm font-semibold text-indigo-300 mb-1">
                    {name(s.missing_skill)}
                  </p>
                  <p className="text-sm md:text-base text-neutral-300 leading-relaxed">
                    {renderInline(s.suggestion)}
                  </p>
                </li>
              ))}
            </ul>
          </Card>
        )}

        <Card className="border border-indigo-500/30 bg-indigo-500/5">
          <p className="text-xs uppercase tracking-wide text-indigo-300 mb-1">Overall advice</p>
          <p className="text-sm md:text-base text-neutral-200 leading-relaxed">
            {renderInline(result.overall_advice)}
          </p>
        </Card>

        <Card title="Your resume at a glance">
          <p className="text-sm md:text-base text-neutral-300 leading-relaxed">
            {renderInline(result.resume.candidate_summary)}
          </p>
        </Card>
      </div>
    </motion.div>
  );
}