import type { ReactNode } from "react";

// Renders **bold** markers from LLM text as real bold, and fixes "44.4 %" spacing.
export function renderInline(text: string): ReactNode[] {
  const cleaned = text.replace(/(\d)\s+%/g, "$1%");
  return cleaned.split(/\*\*(.+?)\*\*/g).map((part, i) =>
    i % 2 === 1 ? (
      <strong key={i} className="font-semibold text-neutral-100">
        {part}
      </strong>
    ) : (
      part
    )
  );
}