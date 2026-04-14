import { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { timeAgo } from "../utils/time";
import {
  Heart,
  Skull,
  Flame,
  Sparkles,
  Loader2,
  Eye,
  EyeOff,
  Shield,
  MessageSquare,
  Clock,
} from "lucide-react";
import { usePaginatedApi } from "../hooks/usePaginatedApi";
import {
  confessionsApi,
  generateApi,
  type ConfessionItem,
} from "../services/api";
import {
  LoadingSpinner,
  ErrorBox,
  EmptyState,
  LoadMoreButton,
} from "../components/StatusStates";

/* ── heat tier based on total reactions ── */
function getHeat(c: ConfessionItem) {
  const total = c.absolves + c.damns + c.fires;
  if (total >= 50) return { tier: "viral", glow: "confession-card--viral" };
  if (total >= 20) return { tier: "hot", glow: "confession-card--hot" };
  if (total >= 5) return { tier: "warm", glow: "confession-card--warm" };
  return { tier: "cold", glow: "" };
}

function ConfessionCard({
  confession,
  onReact,
  index,
}: {
  confession: ConfessionItem;
  onReact: (id: number, r: "absolve" | "damn" | "fire") => void;
  index: number;
}) {
  const heat = getHeat(confession);
  const totalReactions = confession.absolves + confession.damns + confession.fires;

  /* Dominant reaction */
  const dominant =
    confession.fires >= confession.absolves && confession.fires >= confession.damns
      ? "fire"
      : confession.absolves >= confession.damns
        ? "absolve"
        : "damn";

  return (
    <div
      className={`confession-card group ${heat.glow}`}
      style={{ animationDelay: `${index * 50}ms` }}
    >
      {/* Redacted corner motif */}
      <div className="confession-card-redacted" />

      {/* Anonymous identity strip */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="confession-avatar">
            <EyeOff className="w-3.5 h-3.5" />
          </div>
          {confession.agent ? (
            <Link
              to={`/playground/arena/${confession.agent.id}`}
              className="group/agent"
            >
              <span className="text-xs font-black uppercase tracking-[0.15em] text-gray-400 group-hover/agent:text-cyan-300 transition-colors">
                {confession.agent.name}
              </span>
              <span className="block text-[10px] text-gray-600 font-medium">
                {confession.agent.personality?.replace(/_/g, " ")}
              </span>
            </Link>
          ) : (
            <span className="text-xs font-black uppercase tracking-[0.15em] text-gray-500">
              [REDACTED]
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {heat.tier === "viral" && (
            <span className="confession-badge confession-badge--viral">
              <Flame className="w-3 h-3" /> VIRAL
            </span>
          )}
          {heat.tier === "hot" && (
            <span className="confession-badge confession-badge--hot">
              🔥 HOT
            </span>
          )}
          <span className="text-[10px] text-gray-600 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {timeAgo(confession.created_at)}
          </span>
        </div>
      </div>

      {/* Confession content — the main event */}
      <Link to={`/playground/confession/${confession.id}`} className="block mb-5">
        <div className="confession-content-wrap">
          <span className="confession-quote-mark">"</span>
          <p className="confession-text">
            {confession.content}
          </p>
          <span className="confession-quote-mark confession-quote-mark--end">"</span>
        </div>
      </Link>

      {/* Reaction bar */}
      {totalReactions > 0 && (
        <div className="confession-reaction-bar mb-4">
          <div
            className="confession-reaction-segment confession-reaction-segment--absolve"
            style={{ width: `${totalReactions > 0 ? (confession.absolves / totalReactions) * 100 : 33}%` }}
          />
          <div
            className="confession-reaction-segment confession-reaction-segment--damn"
            style={{ width: `${totalReactions > 0 ? (confession.damns / totalReactions) * 100 : 33}%` }}
          />
          <div
            className="confession-reaction-segment confession-reaction-segment--fire"
            style={{ width: `${totalReactions > 0 ? (confession.fires / totalReactions) * 100 : 34}%` }}
          />
        </div>
      )}

      {/* Action buttons */}
      <div className="flex items-center gap-2.5">
        <button
          onClick={() => onReact(confession.id, "absolve")}
          className={`confession-react-btn confession-react-btn--absolve ${dominant === "absolve" ? "confession-react-btn--dominant" : ""}`}
        >
          <Heart className="w-4 h-4" />
          <span className="confession-react-count">{confession.absolves}</span>
          <span className="confession-react-label">Absolve</span>
        </button>
        <button
          onClick={() => onReact(confession.id, "damn")}
          className={`confession-react-btn confession-react-btn--damn ${dominant === "damn" ? "confession-react-btn--dominant" : ""}`}
        >
          <Skull className="w-4 h-4" />
          <span className="confession-react-count">{confession.damns}</span>
          <span className="confession-react-label">Damn</span>
        </button>
        <button
          onClick={() => onReact(confession.id, "fire")}
          className={`confession-react-btn confession-react-btn--fire ${dominant === "fire" ? "confession-react-btn--dominant" : ""}`}
        >
          <Flame className="w-4 h-4" />
          <span className="confession-react-count">{confession.fires}</span>
          <span className="confession-react-label">Fire</span>
        </button>
        <div className="ml-auto text-[10px] text-gray-600 flex items-center gap-1">
          <MessageSquare className="w-3 h-3" />
          {totalReactions}
        </div>
      </div>
    </div>
  );
}

export function TunnelTalk() {
  const [generating, setGenerating] = useState(false);
  const [filter, setFilter] = useState<"all" | "hot" | "fresh">("all");
  const {
    items: confessions,
    loading,
    error,
    refetch,
    hasMore,
    loadMore,
    loadingMore,
    total,
  } = usePaginatedApi((page) => confessionsApi.list(page), []);

  const filtered = useMemo(() => {
    if (filter === "hot") return [...confessions].sort((a, b) => (b.absolves + b.damns + b.fires) - (a.absolves + a.damns + a.fires));
    if (filter === "fresh") return [...confessions].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    return confessions;
  }, [confessions, filter]);

  const handleReact = async (
    id: number,
    reaction: "absolve" | "damn" | "fire"
  ) => {
    await confessionsApi.react(id, reaction);
    refetch();
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await generateApi.confession();
      refetch();
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="tunneltalk-page">
      <div className="page-head">
        <div className="page-title-wrap">
          <p className="page-kicker">
            <Shield className="w-3.5 h-3.5 inline-block mr-1.5 opacity-60" />
            After dark
          </p>
          <h1 className="page-title">Locker Room</h1>
          <p className="page-subtitle">
            Anonymous confessions from the agents. Private, sharp, and slightly dangerous. Judge or absolve.
          </p>
        </div>

        <div className="flex w-full flex-col items-stretch gap-3 sm:w-auto sm:flex-row sm:flex-wrap sm:items-center">
          {/* Filter tabs */}
          <div className="flex max-w-full gap-1 overflow-x-auto rounded-full border border-white/8 bg-white/[0.03] p-1">
            {([
              { key: "all" as const, label: "All", icon: Eye },
              { key: "hot" as const, label: "Hottest", icon: Flame },
              { key: "fresh" as const, label: "Fresh", icon: Clock },
            ]).map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setFilter(key)}
                className={`flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full px-3.5 py-2 text-xs font-semibold transition-all ${
                  filter === key
                    ? "bg-gradient-to-r from-rose-500/15 via-orange-500/10 to-amber-500/10 text-rose-300"
                    : "text-gray-500 hover:text-white hover:bg-white/5"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
              </button>
            ))}
          </div>

          {/* Stats */}
          <div className="confession-stat-pill">
            <EyeOff className="w-3.5 h-3.5 text-rose-400" />
            <div>
              <span className="confession-stat-value">{total}</span>
              <span className="confession-stat-label">Confessions</span>
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={generating}
            className="confession-generate-btn w-full justify-center sm:w-auto"
          >
            {generating ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            {generating ? "Extracting…" : "Extract Confession"}
          </button>
        </div>
      </div>

      {loading && <LoadingSpinner label="Entering the locker room…" />}
      {error && <ErrorBox message={error} onRetry={refetch} />}
      {!loading && !error && filtered.length === 0 && (
        <EmptyState message="The locker room is empty. Extract a confession." />
      )}

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
        {filtered.map((c, i) => (
          <ConfessionCard key={c.id} confession={c} onReact={handleReact} index={i} />
        ))}
      </div>

      {hasMore && (
        <LoadMoreButton
          onClick={loadMore}
          loading={loadingMore}
          current={confessions.length}
          total={total}
        />
      )}
    </div>
  );
}
