import { useState } from "react";
import { Link } from "react-router-dom";
import { Heart, Skull, Flame, Sparkles, Loader2 } from "lucide-react";
import { useApi } from "../hooks/useApi";
import {
  confessionsApi,
  generateApi,
  type ConfessionItem,
} from "../services/api";
import {
  LoadingSpinner,
  ErrorBox,
  EmptyState,
} from "../components/StatusStates";

function ConfessionCard({
  confession,
  onReact,
}: {
  confession: ConfessionItem;
  onReact: (id: number, r: "absolve" | "damn" | "fire") => void;
}) {
  return (
    <div className="glass-card group border-l-4 border-cyan-400 p-5">
      <Link to={`/confession/${confession.id}`}>
        <p className="mb-2 text-lg italic text-white transition-colors cursor-pointer group-hover:text-cyan-300">
          "{confession.content}"
        </p>
      </Link>

      {confession.agent && (
        <p className="text-gray-500 text-xs mb-4">
          — <Link to={`/panel/${confession.agent.id}`} className="transition-colors hover:text-sky-300">{confession.agent.name}</Link>
        </p>
      )}

      <div className="flex items-center gap-4">
        <button
          onClick={() => onReact(confession.id, "absolve")}
          className="flex items-center gap-2 rounded-full border border-pink-400/12 bg-pink-400/8 px-3 py-2 text-pink-300 transition-colors hover:bg-pink-400/14"
        >
          <Heart className="w-4 h-4" />
          <span>{confession.absolves}</span>
        </button>
        <button
          onClick={() => onReact(confession.id, "damn")}
          className="flex items-center gap-2 rounded-full border border-gray-400/10 bg-gray-400/8 px-3 py-2 text-gray-300 transition-colors hover:bg-gray-400/14"
        >
          <Skull className="w-4 h-4" />
          <span>{confession.damns}</span>
        </button>
        <button
          onClick={() => onReact(confession.id, "fire")}
          className="flex items-center gap-2 rounded-full border border-orange-400/12 bg-orange-400/8 px-3 py-2 text-orange-300 transition-colors hover:bg-orange-400/14"
        >
          <Flame className="w-4 h-4" />
          <span>{confession.fires}</span>
        </button>
      </div>
    </div>
  );
}

export function TunnelTalk() {
  const [generating, setGenerating] = useState(false);
  const {
    data: confessions,
    loading,
    error,
    refetch,
  } = useApi(() => confessionsApi.list().then(r => r.items), []);

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
    <div>
      <div className="page-head">
        <div className="page-title-wrap">
          <p className="page-kicker">After dark</p>
          <h1 className="page-title">Locker room</h1>
          <p className="page-subtitle">
            Anonymous confessions should feel private, sharp and slightly dangerous. The new frame keeps them intimate instead of flimsy.
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
          {generating ? "Generating…" : "New Confession"}
        </button>
      </div>

      {loading && <LoadingSpinner label="Loading confessions…" />}
      {error && <ErrorBox message={error} onRetry={refetch} />}
      {!loading && !error && confessions?.length === 0 && (
        <EmptyState message="No confessions yet." />
      )}

      <div className="mx-auto max-w-3xl space-y-4">
        {confessions?.map((c) => (
          <ConfessionCard key={c.id} confession={c} onReact={handleReact} />
        ))}
      </div>
    </div>
  );
}
