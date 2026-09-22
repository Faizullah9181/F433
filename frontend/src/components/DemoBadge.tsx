import { useEffect, useState } from "react";
import { FlaskConical, X } from "lucide-react";
import { isDemoActive, onDemoChange } from "../demo";

/**
 * Marks the session as running on generated data.
 *
 * The backend is off, so every figure on screen — fixtures, tables, scorers —
 * is simulated. Saying so plainly matters: without it the site presents
 * invented scorelines as live results.
 */
export function DemoBadge() {
  const [active, setActive] = useState(isDemoActive());
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => onDemoChange(setActive), []);

  if (!active || dismissed) return null;

  return (
    <div className="pointer-events-none fixed bottom-4 left-1/2 z-50 w-[min(92vw,30rem)] -translate-x-1/2 px-2">
      <div className="pointer-events-auto flex items-start gap-3 rounded-2xl border border-amber-400/25 bg-[#0b1120]/95 px-4 py-3 shadow-2xl backdrop-blur">
        <FlaskConical className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
        <p className="flex-1 text-xs leading-5 text-gray-400">
          <span className="font-semibold text-amber-300">Demo data.</span>{" "}
          The live backend is offline, so fixtures, tables and agent activity on
          this page are simulated — not real results.
        </p>
        <button
          onClick={() => setDismissed(true)}
          aria-label="Dismiss demo notice"
          className="rounded-lg p-1 text-gray-600 transition-colors hover:bg-white/5 hover:text-gray-300"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
