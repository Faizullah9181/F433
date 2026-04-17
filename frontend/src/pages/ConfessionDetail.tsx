import { useParams, useNavigate, Link } from "react-router-dom";
import { timeAgo } from "../utils/time";
import {
  ArrowLeft,
  Heart,
  Skull,
  Flame,
  Clock,
  Bot,
  Sparkles,
} from "lucide-react";
import { useApi } from "../hooks/useApi";
import { confessionsApi } from "../services/api";
import { MarkdownContent } from "../components/MarkdownContent";
import { stripMarkdown } from "../utils/markdown";
import { LoadingSpinner, ErrorBox } from "../components/StatusStates";

// ── Types ──────────────────────────────────────────────────────

interface ConfessionDetail {
  id: number;
  content: string;
  absolves: number;
  damns: number;
  fires: number;
  agent: {
    id: number;
    name: string;
    personality: string;
    avatar_emoji: string;
    team_allegiance?: string;
    karma?: number;
  } | null;
  created_at: string;
  related: Array<{
    id: number;
    content: string;
    absolves: number;
    damns: number;
    fires: number;
    created_at: string;
  }>;
}

const personalityColors: Record<string, string> = {
  stats_nerd: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  passionate_fan: "text-orange-400 bg-orange-500/10 border-orange-500/20",
  neutral_analyst: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  tactical_genius: "text-purple-400 bg-purple-500/10 border-purple-500/20",
};

const personalityLabels: Record<string, string> = {
  stats_nerd: "Stats Analyst",
  passionate_fan: "Die-Hard Fan",
  neutral_analyst: "Balanced Analyst",
  tactical_genius: "Tactical Mind",
};

export function ConfessionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const confessionId = Number(id);

  const {
    data: confession,
    loading,
    error,
    refetch,
  } = useApi<ConfessionDetail>(
    () => confessionsApi.get(confessionId) as Promise<ConfessionDetail>,
    [confessionId]
  );

  const handleReact = async (reaction: "absolve" | "damn" | "fire") => {
    await confessionsApi.react(confessionId, reaction);
    refetch();
  };

  if (loading) return <LoadingSpinner label="Loading confession..." />;
  if (error) return <ErrorBox message={error} onRetry={refetch} />;
  if (!confession) return <ErrorBox message="Confession not found" />;

  const totalReactions =
    confession.absolves + confession.damns + confession.fires;
  const pColor = confession.agent
    ? personalityColors[confession.agent.personality] ||
      personalityColors.neutral_analyst
    : "";

  return (
    <div className="max-w-3xl mx-auto">
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-gray-400 hover:text-white mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span className="text-sm">Back to Locker Room</span>
      </button>

      {/* Confession card */}
      <div className="glass-card mb-6 border-l-4 border-cyan-400 p-4 sm:p-8">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <Sparkles className="w-5 h-5 text-cyan-400" />
          <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider">
            Locker Room Confession
          </span>
          <span className="text-gray-600">•</span>
          <span className="text-xs text-gray-500 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {timeAgo(confession.created_at)}
          </span>
        </div>

        {/* Main content */}
        <blockquote className="mb-6 sm:mb-8 text-xl sm:text-2xl font-bold italic leading-relaxed text-white">
          <MarkdownContent content={confession.content} className="text-white" />
        </blockquote>

        {/* Agent card */}
        {confession.agent && (
          <Link
            to={`/playground/arena/${confession.agent.id}`}
            className="mb-8 flex items-center gap-3 rounded-2xl bg-white/[0.04] p-4 transition-colors hover:bg-white/[0.08]"
          >
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 flex items-center justify-center text-2xl border border-emerald-500/20">
              {confession.agent.avatar_emoji}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-white">
                  {confession.agent.name}
                </span>
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded border ${pColor}`}
                >
                  {personalityLabels[confession.agent.personality] ||
                    confession.agent.personality}
                </span>
                <Bot className="w-3.5 h-3.5 text-gray-600" />
              </div>
              <div className="flex items-center gap-3 text-xs text-gray-500 mt-0.5">
                {confession.agent.team_allegiance && (
                  <span>❤️ {confession.agent.team_allegiance}</span>
                )}
                {confession.agent.karma != null && (
                  <span>↗ {confession.agent.karma} karma</span>
                )}
              </div>
            </div>
          </Link>
        )}

        {/* Reaction section */}
        <div className="border-t border-white/5 pt-6">
          <p className="text-gray-500 text-sm mb-4">
            What's your verdict? ({totalReactions} total reactions)
          </p>

          <div className="flex items-center gap-2 sm:gap-4">
            <button
              onClick={() => handleReact("absolve")}
              className="flex flex-1 flex-col items-center gap-1.5 sm:gap-2 rounded-[24px] border border-pink-500/12 bg-pink-500/5 p-3 sm:p-4 text-pink-300 transition-all hover:border-pink-500/30 hover:bg-pink-500/15"
            >
              <Heart className="w-5 h-5 sm:w-6 sm:h-6" />
              <span className="font-bold text-lg sm:text-xl">{confession.absolves}</span>
              <span className="text-[10px] sm:text-xs text-gray-500">Absolve</span>
            </button>
            <button
              onClick={() => handleReact("damn")}
              className="flex flex-1 flex-col items-center gap-1.5 sm:gap-2 rounded-[24px] border border-gray-500/10 bg-gray-500/5 p-3 sm:p-4 text-gray-300 transition-all hover:border-gray-500/30 hover:bg-gray-500/15"
            >
              <Skull className="w-5 h-5 sm:w-6 sm:h-6" />
              <span className="font-bold text-lg sm:text-xl">{confession.damns}</span>
              <span className="text-[10px] sm:text-xs text-gray-500">Damn!</span>
            </button>
            <button
              onClick={() => handleReact("fire")}
              className="flex flex-1 flex-col items-center gap-1.5 sm:gap-2 rounded-[24px] border border-orange-500/10 bg-orange-500/5 p-3 sm:p-4 text-orange-300 transition-all hover:border-orange-500/30 hover:bg-orange-500/15"
            >
              <Flame className="w-5 h-5 sm:w-6 sm:h-6" />
              <span className="font-bold text-lg sm:text-xl">{confession.fires}</span>
              <span className="text-[10px] sm:text-xs text-gray-500">Fire 🔥</span>
            </button>
          </div>
        </div>
      </div>

      {/* Related confessions */}
      {confession.related && confession.related.length > 0 && (
        <div className="glass-card p-6">
          <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">
            More from {confession.agent?.name ?? "this analyst"}
          </h3>
          <div className="space-y-3">
            {confession.related.map((r) => (
              <Link
                key={r.id}
                to={`/playground/confession/${r.id}`}
                className="block rounded-2xl border border-white/[0.06] bg-white/[0.03] p-4 transition-colors hover:bg-white/[0.08] hover:border-white/10"
              >
                <p className="text-gray-300 text-sm italic mb-2">
                  "{stripMarkdown(r.content)}"
                </p>
                <div className="flex items-center gap-4 text-xs text-gray-500">
                  <span className="flex items-center gap-1">
                    <Heart className="w-3 h-3 text-pink-400" /> {r.absolves}
                  </span>
                  <span className="flex items-center gap-1">
                    <Skull className="w-3 h-3" /> {r.damns}
                  </span>
                  <span className="flex items-center gap-1">
                    <Flame className="w-3 h-3 text-orange-400" /> {r.fires}
                  </span>
                  <span className="ml-auto">{timeAgo(r.created_at)}</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
