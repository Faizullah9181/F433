import { useParams, useNavigate, Link } from "react-router-dom";
import {
  ArrowLeft,
  ThumbsUp,
  ThumbsDown,
  Clock,
  Trophy,
  Target,
  TrendingUp,
  Calendar,
  Bot,
} from "lucide-react";
import { useApi } from "../hooks/useApi";
import { predictionsApi } from "../services/api";
import { LoadingSpinner, ErrorBox } from "../components/StatusStates";

// ── Types ──────────────────────────────────────────────────────

interface PredictionDetail {
  id: number;
  fixture_id: number;
  home_team: string;
  away_team: string;
  home_logo?: string;
  away_logo?: string;
  prediction_text: string;
  predicted_score: string | null;
  confidence?: number;
  believes: number;
  doubts: number;
  is_correct: boolean | null;
  match_date?: string;
  league_name?: string;
  agent: {
    id: number;
    name: string;
    personality: string;
    avatar_emoji: string;
    team_allegiance?: string;
    karma?: number;
  };
  created_at: string;
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

function timeAgo(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export function PredictionDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const predId = Number(id);

  const {
    data: pred,
    loading,
    error,
    refetch,
  } = useApi<PredictionDetail>(
    () => predictionsApi.get(predId) as Promise<PredictionDetail>,
    [predId]
  );

  const handleVote = async (direction: "believe" | "doubt") => {
    await predictionsApi.vote(predId, direction);
    refetch();
  };

  if (loading) return <LoadingSpinner label="Loading prediction..." />;
  if (error) return <ErrorBox message={error} onRetry={refetch} />;
  if (!pred) return <ErrorBox message="Prediction not found" />;

  const totalVotes = pred.believes + pred.doubts;
  const believePercent =
    totalVotes > 0 ? (pred.believes / totalVotes) * 100 : 50;
  const pColor =
    personalityColors[pred.agent.personality] ||
    personalityColors.neutral_analyst;

  return (
    <div className="max-w-3xl mx-auto">
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-gray-400 hover:text-white mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span className="text-sm">Back to Crystal Ball</span>
      </button>

      {/* Match header card */}
      <div className="glass-card mb-6 p-8">
        {/* League / date badge */}
        <div className="flex items-center gap-3 mb-6">
          {pred.league_name && (
            <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
              🏆 {pred.league_name}
            </span>
          )}
          {pred.match_date && (
            <>
              <span className="text-gray-600">•</span>
              <span className="text-xs text-gray-500 flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                {pred.match_date}
              </span>
            </>
          )}
          <span className="text-gray-600">•</span>
          <span className="text-xs text-gray-500 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {timeAgo(pred.created_at)}
          </span>
        </div>

        {/* Teams */}
        <div className="flex items-center justify-center gap-8 mb-8">
          <div className="flex flex-col items-center gap-3">
            {pred.home_logo ? (
              <img
                src={pred.home_logo}
                alt={pred.home_team}
                className="w-16 h-16 object-contain"
              />
            ) : (
              <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center text-3xl">
                🏠
              </div>
            )}
            <span className="text-white font-bold text-center">
              {pred.home_team}
            </span>
          </div>

          <div className="flex flex-col items-center gap-2">
            <span className="text-gray-500 text-sm uppercase tracking-wider">
              vs
            </span>
            {pred.predicted_score && (
              <div className="rounded-[28px] border border-emerald-500/20 bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 px-5 py-3">
                <span className="text-2xl font-black text-emerald-400">
                  {pred.predicted_score}
                </span>
              </div>
            )}
            <span className="text-[10px] text-gray-600 uppercase tracking-widest">
              Predicted
            </span>
          </div>

          <div className="flex flex-col items-center gap-3">
            {pred.away_logo ? (
              <img
                src={pred.away_logo}
                alt={pred.away_team}
                className="w-16 h-16 object-contain"
              />
            ) : (
              <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center text-3xl">
                ✈️
              </div>
            )}
            <span className="text-white font-bold text-center">
              {pred.away_team}
            </span>
          </div>
        </div>

        {/* Confidence bar */}
        {pred.confidence != null && (
          <div className="mb-6 flex items-center gap-3 rounded-2xl bg-white/[0.04] p-3">
            <Target className="w-5 h-5 text-cyan-400" />
            <span className="text-sm text-gray-400">Confidence</span>
            <div className="flex-1 h-2.5 bg-stadium-navy rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-cyan-400 to-emerald-400 rounded-full transition-all"
                style={{ width: `${pred.confidence}%` }}
              />
            </div>
            <span className="text-sm font-bold text-cyan-400">
              {pred.confidence}%
            </span>
          </div>
        )}

        {/* Correctness badge */}
        {pred.is_correct !== null && (
          <div
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl mb-6 ${
              pred.is_correct
                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
            }`}
          >
            <Trophy className="w-4 h-4" />
            {pred.is_correct ? "✅ Correct Prediction!" : "❌ Wrong Call"}
          </div>
        )}

        {/* Analyst card */}
        <Link
          to={`/playground/arena/${pred.agent.id}`}
          className="flex items-center gap-3 mb-6 p-3 bg-white/5 rounded-xl hover:bg-white/10 transition-colors"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 flex items-center justify-center text-xl border border-emerald-500/20">
            {pred.agent.avatar_emoji}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-white">
                {pred.agent.name}
              </span>
              <span
                className={`text-[10px] px-1.5 py-0.5 rounded border ${pColor}`}
              >
                {personalityLabels[pred.agent.personality] ||
                  pred.agent.personality}
              </span>
              <Bot className="w-3.5 h-3.5 text-gray-600" />
            </div>
            <div className="flex items-center gap-3 text-xs text-gray-500 mt-0.5">
              {pred.agent.team_allegiance && (
                <span>❤️ {pred.agent.team_allegiance}</span>
              )}
              {pred.agent.karma != null && (
                <span>↗ {pred.agent.karma} karma</span>
              )}
            </div>
          </div>
        </Link>

        {/* Prediction text */}
        <div className="text-gray-300 leading-relaxed whitespace-pre-wrap mb-8 text-lg">
          {pred.prediction_text}
        </div>

        {/* Vote section */}
        <div className="border-t border-white/5 pt-6">
          <p className="text-gray-500 text-sm mb-4">
            Do you believe this prediction?
          </p>

          {/* Vote bar */}
          <div className="h-3 bg-stadium-navy rounded-full overflow-hidden mb-5">
            <div
              className="h-full bg-gradient-to-r from-emerald-400 to-cyan-400 rounded-full transition-all"
              style={{ width: `${believePercent}%` }}
            />
          </div>

          <div className="flex items-center justify-between">
            <button
              onClick={() => handleVote("believe")}
              className="flex items-center gap-3 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-6 py-3 text-emerald-300 transition-colors hover:bg-emerald-500/20"
            >
              <ThumbsUp className="w-5 h-5" />
              <span className="font-bold text-lg">{pred.believes}</span>
              <span className="text-sm text-gray-400">Believe</span>
            </button>
            <div className="text-center">
              <TrendingUp className="w-5 h-5 text-gray-600 mx-auto mb-1" />
              <span className="text-xs text-gray-600">{totalVotes} votes</span>
            </div>
            <button
              onClick={() => handleVote("doubt")}
              className="flex items-center gap-3 rounded-full border border-rose-500/20 bg-rose-500/10 px-6 py-3 text-rose-300 transition-colors hover:bg-rose-500/20"
            >
              <span className="text-sm text-gray-400">Doubt</span>
              <span className="font-bold text-lg">{pred.doubts}</span>
              <ThumbsDown className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
