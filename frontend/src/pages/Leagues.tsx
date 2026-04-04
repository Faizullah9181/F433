import { Link } from "react-router-dom";
import { ArrowRight, Trophy, Users, ChevronRight } from "lucide-react";
import { useApi } from "../hooks/useApi";
import { leaguesApi, type LeagueItem } from "../services/api";
import {
  LoadingSpinner,
  ErrorBox,
  EmptyState,
} from "../components/StatusStates";

// League gradient presets
const LEAGUE_GRADIENTS: Record<string, string> = {
  premier_league: "from-purple-600 to-blue-600",
  la_liga: "from-red-500 to-yellow-500",
  serie_a: "from-green-600 to-blue-500",
  bundesliga: "from-red-600 to-gray-900",
  ligue_1: "from-blue-600 to-red-500",
  champions_league: "from-blue-700 to-purple-600",
};

function LeagueCard({ league }: { league: LeagueItem }) {
  const gradient =
    LEAGUE_GRADIENTS[league.slug] || "from-sky-600 to-violet-600";

  return (
    <Link
      to={`/leagues/${league.slug.replace(/_/g, "-")}`}
      className="glass-card group relative overflow-hidden p-6"
    >
      {/* Gradient overlay on hover */}
      <div
        className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-0 
        group-hover:opacity-10 transition-opacity duration-500`}
      />

      <div className="relative flex items-center gap-5">
        {/* League icon */}
        <div className="league-icon shrink-0">
          <span>{league.icon || "⚽"}</span>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h3 className="mb-1 text-[1.35rem] font-black text-white transition-colors group-hover:text-sky-300">
            {league.name}
          </h3>
          <p className="text-sm text-gray-500 line-clamp-1">
            {league.description || "Join the debate"}
          </p>
        </div>

        {/* Arrow */}
        <div className="shrink-0 flex h-11 w-11 items-center justify-center rounded-2xl bg-white/5 text-gray-500 transition-all duration-300 group-hover:translate-x-1 group-hover:bg-sky-500/20 group-hover:text-sky-300">
          <ChevronRight className="w-5 h-5" />
        </div>
      </div>

      {/* Stats footer */}
      <div className="relative mt-5 flex items-center gap-6 border-t border-white/5 pt-4">
        <div className="flex items-center gap-2 text-sm">
          <Users className="w-4 h-4 text-cyan-400" />
          <span className="text-gray-400">12.5k members</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <Trophy className="w-4 h-4 text-amber-400" />
          <span className="text-gray-400">Season 25/26</span>
        </div>
      </div>
    </Link>
  );
}

export function Leagues() {
  const {
    data: leagues,
    loading,
    error,
    refetch,
  } = useApi(() => leaguesApi.list(), []);

  return (
    <div>
      <div className="page-head">
        <div className="page-title-wrap">
          <p className="page-kicker">Competition map</p>
          <h1 className="page-title">Leagues</h1>
          <p className="page-subtitle">
            Every competition gets the same sharper visual frame, so the badge, the standings and the community all feel connected.
          </p>
        </div>
        <div className="poster-metric min-w-[9rem]">
          <span className="poster-metric-label">Loaded</span>
          <strong className="poster-metric-value text-white">{leagues?.length ?? 0}</strong>
        </div>
      </div>

      {loading && <LoadingSpinner label="Loading leagues…" />}
      {error && <ErrorBox message={error} onRetry={refetch} />}
      {!loading && !error && leagues?.length === 0 && (
        <EmptyState message="No leagues found." />
      )}

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
        {leagues?.map((league) => (
          <LeagueCard key={league.id} league={league} />
        ))}
      </div>
    </div>
  );
}
