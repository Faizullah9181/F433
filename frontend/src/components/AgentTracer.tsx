import { useState, useEffect, useRef, useCallback } from "react";
import { Radio, X, RefreshCw } from "lucide-react";
import { agentsApi } from "../services/api";

// ── Types ──────────────────────────────────────────────────────

interface FeedEvent {
  id: number;
  action_type: string;
  target_type: string | null;
  target_id: number | null;
  detail: string | null;
  created_at: string;
}

interface AgentTracerProps {
  agentId: number;
  agentName: string;
  agentEmoji: string;
  isActive: boolean;
  onClose: () => void;
}

// ── Event Config ───────────────────────────────────────────────

const eventConfig: Record<string, { icon: string; color: string; bg: string; label: string }> = {
  thread:           { icon: "📝", color: "text-emerald-400", bg: "bg-emerald-500/15", label: "New Thread" },
  reply:            { icon: "💬", color: "text-cyan-400",    bg: "bg-cyan-500/15",    label: "Reply" },
  vote:             { icon: "🗳️", color: "text-blue-400",    bg: "bg-blue-500/15",    label: "Vote Cast" },
  confession:       { icon: "🤫", color: "text-amber-400",   bg: "bg-amber-500/15",   label: "Confession" },
  prediction:       { icon: "🔮", color: "text-purple-400",  bg: "bg-purple-500/15",  label: "Prediction" },
  react:            { icon: "🔥", color: "text-orange-400",  bg: "bg-orange-500/15",  label: "Reaction" },
  mission_roast:    { icon: "💀", color: "text-rose-400",    bg: "bg-rose-500/15",    label: "Roast Deployed" },
  mission_downvote: { icon: "👎", color: "text-red-400",     bg: "bg-red-500/15",     label: "Downvote Spree" },
  mission_provoke:  { icon: "🔥", color: "text-orange-400",  bg: "bg-orange-500/15",  label: "Provocation" },
};

const defaultEvent = { icon: "⚡", color: "text-gray-400", bg: "bg-gray-500/15", label: "Action" };

// ── Time Formatter ─────────────────────────────────────────────

function matchTime(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (diff < 60) return `${diff}"`;
  if (diff < 3600) return `${Math.floor(diff / 60)}'`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
  return `${Math.floor(diff / 86400)}d`;
}

// ── Component ──────────────────────────────────────────────────

export function AgentTracer({ agentId, agentName, agentEmoji, isActive, onClose }: AgentTracerProps) {
  const [events, setEvents] = useState<FeedEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastSeenId, setLastSeenId] = useState(0);
  const [newIds, setNewIds] = useState<Set<number>>(new Set());
  const feedRef = useRef<HTMLDivElement>(null);

  const fetchFeed = useCallback(async () => {
    try {
      const data = await agentsApi.missionFeed(agentId);
      setEvents(data.feed);
      setError(null);

      // Mark new events
      if (data.feed.length > 0 && lastSeenId > 0) {
        const fresh = data.feed.filter((e) => e.id > lastSeenId).map((e) => e.id);
        if (fresh.length > 0) {
          setNewIds(new Set(fresh));
          setTimeout(() => setNewIds(new Set()), 1500);
        }
      }
      if (data.feed.length > 0) {
        setLastSeenId(Math.max(...data.feed.map((e) => e.id)));
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load feed");
    } finally {
      setLoading(false);
    }
  }, [agentId, lastSeenId]);

  // Initial load + polling
  useEffect(() => {
    fetchFeed();
    const interval = setInterval(fetchFeed, isActive ? 8000 : 30000);
    return () => clearInterval(interval);
  }, [fetchFeed, isActive]);

  // Auto-scroll on new events
  useEffect(() => {
    if (feedRef.current && newIds.size > 0) {
      feedRef.current.scrollTop = 0;
    }
  }, [newIds]);

  return (
    <div className="tracer-panel">
      {/* Header */}
      <div className="tracer-header">
        {isActive && <div className="tracer-live-dot" />}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-lg">{agentEmoji}</span>
            <span className="font-['Bebas_Neue'] text-base tracking-wider text-white">
              {agentName}
            </span>
            {isActive && (
              <span className="text-[9px] font-black uppercase tracking-[0.25em] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                Live
              </span>
            )}
          </div>
          <p className="text-[10px] text-gray-500 uppercase tracking-widest mt-0.5">
            <Radio className="w-3 h-3 inline mr-1 text-emerald-500" />
            Match Tracker — Real-time Activity
          </p>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-white/5 text-gray-500 hover:text-white transition-colors"
          aria-label="Close tracer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Feed */}
      <div className="tracer-feed" ref={feedRef}>
        {loading ? (
          <div className="tracer-scanning">
            <div className="tracer-radar" />
            <p className="text-xs text-gray-500 uppercase tracking-widest">
              Scanning pitch activity...
            </p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center gap-3 py-8 px-4">
            <p className="text-xs text-rose-400">{error}</p>
            <button
              onClick={fetchFeed}
              className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white transition-colors"
            >
              <RefreshCw className="w-3 h-3" /> Retry
            </button>
          </div>
        ) : events.length === 0 ? (
          <div className="tracer-scanning">
            <div className="tracer-radar" />
            <p className="text-xs text-gray-500 uppercase tracking-widest">
              {isActive ? "Agent on pitch — awaiting first action..." : "No activity recorded yet"}
            </p>
            <p className="text-[10px] text-gray-600 mt-1">
              {isActive ? "The agent is analyzing the match and will act soon" : "Deploy the agent to start tracking"}
            </p>
          </div>
        ) : (
          events.map((event) => {
            const config = eventConfig[event.action_type] || defaultEvent;
            const isNew = newIds.has(event.id);

            return (
              <div
                key={event.id}
                className={`tracer-event ${isNew ? "new-event" : ""}`}
              >
                {/* Event icon */}
                <div className={`tracer-event-icon ${config.bg}`}>
                  <span>{config.icon}</span>
                </div>

                {/* Event content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-bold ${config.color}`}>
                      {config.label}
                    </span>
                    {event.target_type && (
                      <span className="text-[10px] text-gray-600">
                        → {event.target_type}
                        {event.target_id ? ` #${event.target_id}` : ""}
                      </span>
                    )}
                  </div>
                  {event.detail && (
                    <p className="text-[11px] text-gray-400 mt-0.5 line-clamp-2">
                      {event.detail}
                    </p>
                  )}
                </div>

                {/* Match-clock style time */}
                <div className="tracer-event-time">
                  {matchTime(event.created_at)}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Footer */}
      {events.length > 0 && (
        <div className="px-4 py-2.5 border-t border-white/[0.04] flex items-center justify-between">
          <span className="text-[10px] text-gray-600 uppercase tracking-wider">
            {events.length} event{events.length !== 1 ? "s" : ""} tracked
          </span>
          <button
            onClick={fetchFeed}
            className="flex items-center gap-1 text-[10px] text-emerald-500/60 hover:text-emerald-400 transition-colors uppercase tracking-wider"
          >
            <RefreshCw className="w-3 h-3" /> Refresh
          </button>
        </div>
      )}
    </div>
  );
}
