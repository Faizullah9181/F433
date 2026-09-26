import { useEffect, useState } from "react";
import { FlaskConical, X } from "lucide-react";
import { isDemoActive, onDemoChange } from "../demo";

/**
 * Marks the session as running on generated data.
 *
 * The backend is off, so every figure on screen — fixtures, tables, scorers —
 * is simulated. Saying so plainly matters: without it the site presents
 * invented scorelines as live results.
 *
 * Anchored bottom-RIGHT and self-collapsing. Centred, it covered the "Load
 * More" button that sits at the bottom of every paginated feed.
 */
export function DemoBadge() {
  const [active, setActive] = useState(isDemoActive());
  const [dismissed, setDismissed] = useState(false);
  const [expanded, setExpanded] = useState(true);

  useEffect(() => onDemoChange(setActive), []);

  // Say it properly once, then shrink out of the way.
  useEffect(() => {
    if (!active) return;
    const t = setTimeout(() => setExpanded(false), 7000);
    return () => clearTimeout(t);
  }, [active]);

  if (!active || dismissed) return null;

  if (!expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        title="This site is showing generated demo data"
        className="fixed bottom-4 right-4 z-40 flex items-center gap-1.5 rounded-full border border-amber-400/25 bg-[#0b1120]/90 px-3 py-1.5 text-[11px] font-medium text-amber-300/90 shadow-lg backdrop-blur transition-colors hover:border-amber-400/50 hover:text-amber-200"
      >
        <FlaskConical className="h-3 w-3" />
        Demo data
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 z-40 w-[min(calc(100vw-2rem),22rem)]">
      <div className="flex items-start gap-2.5 rounded-xl border border-amber-400/25 bg-[#0b1120]/95 p-3 shadow-2xl backdrop-blur">
        <FlaskConical className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-400" />
        <p className="flex-1 text-[11px] leading-[1.6] text-gray-400">
          <span className="font-semibold text-amber-300">Demo data.</span>{" "}
          The live backend is offline. Fixtures, tables and agent activity here
          are simulated — not real results.
        </p>
        <button
          onClick={() => setDismissed(true)}
          aria-label="Dismiss demo notice"
          className="-mr-0.5 -mt-0.5 rounded-md p-1 text-gray-600 transition-colors hover:bg-white/5 hover:text-gray-300"
        >
          <X className="h-3 w-3" />
        </button>
      </div>
    </div>
  );
}
