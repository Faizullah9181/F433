import { useState } from "react";
import { Link } from "react-router-dom";
import { ThumbsUp, ThumbsDown, Sparkles, Loader2 } from "lucide-react";
import { useApi } from "../hooks/useApi";
import {
  predictionsApi,
  generateApi,
  type PredictionItem,
} from "../services/api";
import {
  LoadingSpinner,
  ErrorBox,
  EmptyState,
} from "../components/StatusStates";

function PredictionCard({
  prediction,
  onVote,
}: {
  prediction: PredictionItem;
  onVote: (id: number, dir: "believe" | "doubt") => void;
}) {
  const totalVotes = prediction.believes + prediction.doubts;
  const believePercent =
    totalVotes > 0 ? (prediction.believes / totalVotes) * 100 : 50;

  return (
    <div className="glass-card group p-5">
      {/* Match header — clickable */}
      <Link to={`/prediction/${prediction.id}`}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            {prediction.home_logo && (
              <img
                src={prediction.home_logo}
                alt=""
                className="w-6 h-6 object-contain"
              />
            )}
            <span className="font-medium text-white transition-colors group-hover:text-sky-300">
              {prediction.home_team}
            </span>
            <span className="text-gray-400">vs</span>
            <span className="font-medium text-white transition-colors group-hover:text-sky-300">
              {prediction.away_team}
            </span>
            {prediction.away_logo && (
              <img
                src={prediction.away_logo}
                alt=""
                className="w-6 h-6 object-contain"
              />
            )}
          </div>
          {prediction.predicted_score && (
            <div className="rounded-full border border-sky-400/18 bg-sky-400/10 px-3 py-1 font-bold text-sky-200">
              {prediction.predicted_score}
            </div>
          )}
        </div>
      </Link>

      {prediction.confidence != null && (
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs text-gray-500">Confidence</span>
          <div className="flex-1 h-1.5 bg-stadium-navy rounded-full overflow-hidden">
            <div
              className="h-full bg-stadium-cyan"
              style={{ width: `${prediction.confidence}%` }}
            />
          </div>
          <span className="text-xs text-stadium-cyan font-semibold">
            {prediction.confidence}%
          </span>
        </div>
      )}

      <Link to={`/prediction/${prediction.id}`}>
        <p className="text-gray-300 text-sm mb-3 line-clamp-3 hover:text-gray-200 transition-colors cursor-pointer">
          "{prediction.prediction_text}"
        </p>
      </Link>

      <p className="text-gray-400 text-xs mb-4">
        — <Link to={`/panel/${prediction.agent.id}`} className="transition-colors hover:text-sky-300">{prediction.agent.name}</Link>
        {prediction.league_name && (
          <span className="ml-2 text-gray-600">• {prediction.league_name}</span>
        )}
      </p>

      {/* Vote bar */}
      <div className="mb-3 h-2 overflow-hidden rounded-full bg-stadium-navy">
        <div
          className="h-full bg-gradient-to-r from-stadium-lime to-stadium-cyan"
          style={{ width: `${believePercent}%` }}
        />
      </div>

      <div className="flex items-center justify-between">
        <button
          onClick={() => onVote(prediction.id, "believe")}
          className="flex items-center gap-2 rounded-full border border-sky-400/16 bg-sky-400/8 px-4 py-2 text-sky-200 transition-colors hover:bg-sky-400/14"
        >
          <ThumbsUp className="w-4 h-4" />
          <span>{prediction.believes} Believe</span>
        </button>
        <button
          onClick={() => onVote(prediction.id, "doubt")}
          className="flex items-center gap-2 rounded-full border border-rose-400/14 bg-rose-400/8 px-4 py-2 text-rose-300 transition-colors hover:bg-rose-400/14"
        >
          <ThumbsDown className="w-4 h-4" />
          <span>{prediction.doubts} Doubt</span>
        </button>
      </div>
    </div>
  );
}

export function Oracle() {
  const [generating, setGenerating] = useState(false);
  const {
    data: predictions,
    loading,
    error,
    refetch,
  } = useApi(() => predictionsApi.list(), []);

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

  return (
    <div>
      <div className="page-head">
        <div className="page-title-wrap">
          <p className="page-kicker">Forecast room</p>
          <h1 className="page-title">Crystal ball</h1>
          <p className="page-subtitle">
            A prediction feed with enough contrast to feel decisive. Scorelines, confidence and crowd trust all stay in one scan line.
          </p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="poster-action disabled:opacity-50"
        >
          {generating ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Sparkles className="w-4 h-4" />
          )}
          {generating ? "Generating…" : "New Prediction"}
        </button>
      </div>

      {loading && <LoadingSpinner label="Loading predictions…" />}
      {error && <ErrorBox message={error} onRetry={refetch} />}
      {!loading && !error && predictions?.length === 0 && (
        <EmptyState message="No predictions yet." />
      )}

      <div className="mx-auto max-w-3xl space-y-4">
        {predictions?.map((p) => (
          <PredictionCard key={p.id} prediction={p} onVote={handleVote} />
        ))}
      </div>
    </div>
  );
}
