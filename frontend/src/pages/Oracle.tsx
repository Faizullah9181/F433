import { useState } from "react";
import { Link } from "react-router-dom";
import {
  ThumbsUp,
  ThumbsDown,
  Sparkles,
  Loader2,
  Eye,
  Zap,
  Target,
  TrendingUp,
  Activity,
} from "lucide-react";
import { usePaginatedApi } from "../hooks/usePaginatedApi";
import {
  predictionsApi,
  generateApi,
  type PredictionItem,
} from "../services/api";
import {
  LoadingSpinner,
  ErrorBox,
  EmptyState,
  LoadMoreButton,
} from "../components/StatusStates";

/* ── confidence tier ── */
function getConfidenceTier(c: number | undefined) {
  if (c == null) return { label: "UNKNOWN", color: "text-gray-500", ring: "border-gray-500/20", bg: "bg-gray-500/5" };
  if (c >= 85) return { label: "LOCK", color: "text-emerald-400", ring: "border-emerald-400/30", bg: "bg-emerald-400/8" };
  if (c >= 65) return { label: "STRONG", color: "text-cyan-400", ring: "border-cyan-400/25", bg: "bg-cyan-400/6" };
  if (c >= 40) return { label: "HUNCH", color: "text-amber-400", ring: "border-amber-400/25", bg: "bg-amber-400/6" };
  return { label: "WILD", color: "text-rose-400", ring: "border-rose-400/25", bg: "bg-rose-400/6" };
}

function PredictionCard({
  prediction,
  onVote,
  index,
}: {
  prediction: PredictionItem;
  onVote: (id: number, dir: "believe" | "doubt") => void;
  index: number;
}) {
  const totalVotes = prediction.believes + prediction.doubts;
  const believePercent =
    totalVotes > 0 ? (prediction.believes / totalVotes) * 100 : 50;
  const tier = getConfidenceTier(prediction.confidence);
  const isCorrect = prediction.is_correct;

  return (
    <div
      className="oracle-card group"
      style={{ animationDelay: `${index * 60}ms` }}
    >
      {/* Holographic scan line */}
      <div className="oracle-card-scanline" />

      {/* Status corner badge */}
      {isCorrect !== null && (
        <div className={`oracle-card-verdict ${isCorrect ? "oracle-card-verdict--correct" : "oracle-card-verdict--wrong"}`}>
          {isCorrect ? "✓ HIT" : "✗ MISS"}
        </div>
      )}

      {/* Top bar — match teams */}
      <Link to={`/playground/prediction/${prediction.id}`} className="block">
        <div className="flex items-center gap-4 mb-5">
          {/* Home team */}
          <div className="flex items-center gap-2.5 flex-1 min-w-0">
            {prediction.home_logo ? (
              <img src={prediction.home_logo} alt="" className="w-8 h-8 object-contain drop-shadow-[0_0_6px_rgba(6,182,212,0.3)]" />
            ) : (
              <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-xs text-gray-600">H</div>
            )}
            <span className="font-black text-white text-sm uppercase tracking-wide truncate group-hover:text-cyan-300 transition-colors">
              {prediction.home_team}
            </span>
          </div>

          {/* Score prediction — central element */}
          <div className="oracle-score-badge">
            {prediction.predicted_score ? (
              <span className="text-lg font-black tracking-wider">{prediction.predicted_score}</span>
            ) : (
              <span className="text-xs text-gray-500">VS</span>
            )}
          </div>

          {/* Away team */}
          <div className="flex items-center gap-2.5 flex-1 min-w-0 justify-end">
            <span className="font-black text-white text-sm uppercase tracking-wide truncate text-right group-hover:text-cyan-300 transition-colors">
              {prediction.away_team}
            </span>
            {prediction.away_logo ? (
              <img src={prediction.away_logo} alt="" className="w-8 h-8 object-contain drop-shadow-[0_0_6px_rgba(6,182,212,0.3)]" />
            ) : (
              <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-xs text-gray-600">A</div>
            )}
          </div>
        </div>
      </Link>

      {/* Confidence gauge */}
      {prediction.confidence != null && (
        <div className="oracle-confidence-gauge mb-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Target className={`w-3.5 h-3.5 ${tier.color}`} />
              <span className={`text-[10px] font-black uppercase tracking-[0.2em] ${tier.color}`}>
                {tier.label}
              </span>
            </div>
            <span className={`oracle-confidence-number ${tier.color}`}>
              {prediction.confidence}
              <span className="text-[9px] opacity-60">%</span>
            </span>
          </div>
          <div className="oracle-confidence-track">
            <div
              className="oracle-confidence-fill"
              style={{ width: `${prediction.confidence}%` }}
            />
            {/* Tick marks */}
            <div className="oracle-confidence-ticks">
              {[25, 50, 75].map(t => (
                <div key={t} className="oracle-confidence-tick" style={{ left: `${t}%` }} />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Prediction text */}
      <Link to={`/playground/prediction/${prediction.id}`} className="block mb-4">
        <p className="oracle-card-text">
          {prediction.prediction_text}
        </p>
      </Link>

      {/* Agent + League meta */}
      <div className="flex items-center justify-between mb-5">
        <Link
          to={`/playground/arena/${prediction.agent.id}`}
          className="flex items-center gap-2 group/agent"
        >
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-cyan-500/20 to-violet-500/20 border border-white/10 flex items-center justify-center">
            <Zap className="w-3 h-3 text-cyan-400" />
          </div>
          <span className="text-xs font-semibold text-gray-400 group-hover/agent:text-cyan-300 transition-colors">
            {prediction.agent.name}
          </span>
        </Link>
        {prediction.league_name && (
          <span className="text-[10px] uppercase tracking-widest text-gray-600 font-medium">
            {prediction.league_name}
          </span>
        )}
      </div>

      {/* Vote system — crowd trust */}
      <div className="oracle-vote-section">
        {/* Trust bar */}
        <div className="oracle-trust-bar mb-3">
          <div className="oracle-trust-fill" style={{ width: `${believePercent}%` }} />
          <div className="oracle-trust-labels">
            <span className="text-[10px] font-bold text-emerald-400/80">{Math.round(believePercent)}%</span>
            <span className="text-[10px] font-bold text-rose-400/80">{Math.round(100 - believePercent)}%</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onVote(prediction.id, "believe")}
            className="oracle-vote-btn oracle-vote-btn--believe"
          >
            <ThumbsUp className="w-3.5 h-3.5" />
            <span>{prediction.believes}</span>
            <span className="oracle-vote-label">Believe</span>
          </button>
          <button
            onClick={() => onVote(prediction.id, "doubt")}
            className="oracle-vote-btn oracle-vote-btn--doubt"
          >
            <ThumbsDown className="w-3.5 h-3.5" />
            <span>{prediction.doubts}</span>
            <span className="oracle-vote-label">Doubt</span>
          </button>
          <div className="ml-auto flex items-center gap-1.5 text-[10px] text-gray-600">
            <Activity className="w-3 h-3" />
            {totalVotes} votes
          </div>
        </div>
      </div>
    </div>
  );
}

export function Oracle() {
  const [generating, setGenerating] = useState(false);
  const {
    items: predictions,
    loading,
    error,
    refetch,
    hasMore,
    loadMore,
    loadingMore,
    total,
  } = usePaginatedApi((page) => predictionsApi.list(undefined, page), []);

  const handleVote = async (id: number, direction: "believe" | "doubt") => {
    await predictionsApi.vote(id, direction);
    refetch();
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await generateApi.prediction();
      refetch();
    } catch {
      /* ignore - might not have upcoming fixtures */
    } finally {
      setGenerating(false);
    }
  };

  /* Stats from loaded data */
  const avgConf = predictions.length > 0
    ? Math.round(predictions.reduce((s, p) => s + (p.confidence ?? 0), 0) / predictions.length)
    : 0;
  const hitRate = predictions.length > 0
    ? Math.round((predictions.filter(p => p.is_correct === true).length / predictions.filter(p => p.is_correct !== null).length) * 100) || 0
    : 0;

  return (
    <div className="oracle-page">
      <div className="page-head">
        <div className="page-title-wrap">
          <p className="page-kicker">
            <Eye className="w-3.5 h-3.5 inline-block mr-1.5 opacity-60" />
            Forecast room
          </p>
          <h1 className="page-title">Crystal Ball</h1>
          <p className="page-subtitle">
            AI-powered match predictions with crowd consensus. Every call is tracked, every hit recorded.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Stats pills */}
          <div className="oracle-stat-pill">
            <TrendingUp className="w-3.5 h-3.5 text-cyan-400" />
            <div>
              <span className="oracle-stat-value">{total}</span>
              <span className="oracle-stat-label">Predictions</span>
            </div>
          </div>
          <div className="oracle-stat-pill">
            <Target className="w-3.5 h-3.5 text-emerald-400" />
            <div>
              <span className="oracle-stat-value">{avgConf}%</span>
              <span className="oracle-stat-label">Avg Confidence</span>
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={generating}
            className="oracle-generate-btn"
          >
            {generating ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            {generating ? "Channeling…" : "New Vision"}
          </button>
        </div>
      </div>

      {loading && <LoadingSpinner label="Consulting the oracle…" />}
      {error && <ErrorBox message={error} onRetry={refetch} />}
      {!loading && !error && predictions.length === 0 && (
        <EmptyState message="No visions yet. Channel one." />
      )}

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
        {predictions.map((p, i) => (
          <PredictionCard key={p.id} prediction={p} onVote={handleVote} index={i} />
        ))}
      </div>

      {hasMore && (
        <LoadMoreButton
          onClick={loadMore}
          loading={loadingMore}
          current={predictions.length}
          total={total}
        />
      )}
    </div>
  );
}
