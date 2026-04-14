import { useParams, Link } from "react-router-dom";
import { useState } from "react";
import {
  ArrowLeft,
  Trophy,
  TrendingUp,
  Users,
  AlertCircle,
  Target,
  Award,
  Calendar,
  ChevronRight,
} from "lucide-react";
import { useApi } from "../hooks/useApi";
import {
  footballApi,
  threadsApi,
  type ThreadItem,
  type FixtureItem,
  type TopScorerItem,
} from "../services/api";
import {
  LoadingSpinner,
  ErrorBox,
  EmptyState,
  LoadMoreButton,
} from "../components/StatusStates";
import { usePaginatedApi } from "../hooks/usePaginatedApi";
import { ErrorBoundary } from "../components/ErrorBoundary";

/* ── League config ────────────────────────────────── */

const LEAGUE_ID_MAP: Record<string, number> = {
  premier_league: 39,
  la_liga: 140,
  serie_a: 135,
  bundesliga: 78,
  ligue_1: 61,
  champions_league: 2,
  general: 39,
};

const LEAGUE_INFO: Record<string, { name: string; icon: string; gradient: string }> = {
  premier_league: { name: "Premier League", icon: "🏴󠁧󠁢󠁥󠁮󠁧󠁿", gradient: "from-purple-600 via-blue-600 to-purple-600" },
  la_liga:        { name: "La Liga",        icon: "🇪🇸", gradient: "from-red-500 via-yellow-500 to-red-500" },
  serie_a:        { name: "Serie A",        icon: "🇮🇹", gradient: "from-green-600 via-white to-red-500" },
  bundesliga:     { name: "Bundesliga",     icon: "🇩🇪", gradient: "from-black via-red-600 to-yellow-400" },
  ligue_1:        { name: "Ligue 1",        icon: "🇫🇷", gradient: "from-blue-600 via-white to-red-500" },
  champions_league:{ name: "Champions League",icon: "🏆", gradient: "from-blue-700 via-purple-600 to-blue-600" },
  general:        { name: "General Football",icon: "⚽", gradient: "from-emerald-500 via-cyan-500 to-emerald-500" },
};

function normalizeSlug(slug: string | undefined): string {
  if (!slug) return "general";
  return slug.replace(/-/g, "_");
}

type LeagueTab = "standings" | "scorers" | "assists" | "fixtures";

/* ── Standings Table ───────────────────────────────── */

interface StandingTeam {
  rank: number;
  team: { id: number; name: string; logo?: string };
  all: { played: number; win: number; draw: number; lose: number; goals: { for: number; against: number } };
  goalsDiff: number;
  points: number;
  form?: string;
  description?: string;
}

function StandingsTable({ leagueId }: { leagueId: number }) {
  const { data, loading, error } = useApi(() => footballApi.standings(leagueId), [leagueId]);

  if (loading) return <LoadingSpinner label="Loading standings..." />;
  if (error) return <div className="glass-card p-6 text-center"><AlertCircle className="w-5 h-5 mx-auto mb-2 text-rose-400" /><span className="text-gray-400 text-sm">Unable to load standings</span></div>;

  let standings: StandingTeam[] = [];
  try {
    const raw = data?.standings;
    if (Array.isArray(raw) && raw.length > 0) standings = raw as StandingTeam[];
  } catch (e) { console.error(e); }

  if (standings.length === 0) return <EmptyState message="No standings data available." />;

  return (
    <div className="glass-card overflow-hidden">
      <div className="p-5 border-b border-white/5 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center">
          <Trophy className="w-5 h-5 text-amber-400" />
        </div>
        <h3 className="text-lg font-bold text-white">Standings</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 text-[10px] uppercase tracking-wider border-b border-white/5">
              <th className="p-4 text-left w-10">#</th>
              <th className="p-4 text-left">Team</th>
              <th className="p-4 text-center">P</th>
              <th className="p-4 text-center">W</th>
              <th className="p-4 text-center">D</th>
              <th className="p-4 text-center">L</th>
              <th className="p-4 text-center hidden md:table-cell">GF</th>
              <th className="p-4 text-center hidden md:table-cell">GA</th>
              <th className="p-4 text-center">GD</th>
              <th className="p-4 text-center">Pts</th>
              <th className="p-4 text-center hidden lg:table-cell">Form</th>
            </tr>
          </thead>
          <tbody>
            {standings.map((team, idx) => {
              const desc = team.description?.toLowerCase() || "";
              const rowBorder = desc.includes("champions") ? "border-l-2 border-l-emerald-500"
                : desc.includes("europa") || desc.includes("conference") ? "border-l-2 border-l-cyan-500"
                : desc.includes("relegation") ? "border-l-2 border-l-rose-500"
                : "";

              return (
                <tr key={team?.team?.id || idx}
                  className={`border-b border-white/5 hover:bg-white/[0.03] transition-colors ${rowBorder}`}>
                  <td className="p-4">
                    <span className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold
                      ${idx < 4 ? "bg-emerald-500/20 text-emerald-400"
                        : idx >= standings.length - 3 ? "bg-rose-500/15 text-rose-400"
                        : "bg-white/5 text-gray-400"}`}>
                      {team?.rank ?? idx + 1}
                    </span>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      {team?.team?.logo && <img src={team.team.logo} alt="" className="w-6 h-6 object-contain" />}
                      <span className="text-white font-medium">{team?.team?.name ?? "Unknown"}</span>
                    </div>
                  </td>
                  <td className="p-4 text-center text-gray-400">{team?.all?.played ?? "-"}</td>
                  <td className="p-4 text-center text-emerald-400 font-medium">{team?.all?.win ?? "-"}</td>
                  <td className="p-4 text-center text-gray-400">{team?.all?.draw ?? "-"}</td>
                  <td className="p-4 text-center text-rose-400">{team?.all?.lose ?? "-"}</td>
                  <td className="p-4 text-center text-gray-400 hidden md:table-cell">{team?.all?.goals?.for ?? "-"}</td>
                  <td className="p-4 text-center text-gray-400 hidden md:table-cell">{team?.all?.goals?.against ?? "-"}</td>
                  <td className="p-4 text-center text-gray-300 font-medium">
                    {team?.goalsDiff != null ? (team.goalsDiff > 0 ? `+${team.goalsDiff}` : team.goalsDiff) : "-"}
                  </td>
                  <td className="p-4 text-center">
                    <span className="font-bold text-white bg-emerald-500/20 px-3 py-1 rounded-lg">
                      {team?.points ?? "-"}
                    </span>
                  </td>
                  <td className="p-4 text-center hidden lg:table-cell">
                    {team?.form ? (
                      <div className="flex items-center gap-0.5 justify-center">
                        {team.form.split("").slice(-5).map((c, fi) => (
                          <span key={fi} className={`w-5 h-5 rounded text-[9px] font-bold flex items-center justify-center
                            ${c === "W" ? "bg-emerald-500/30 text-emerald-400"
                              : c === "D" ? "bg-amber-500/30 text-amber-400"
                              : "bg-rose-500/30 text-rose-400"}`}>
                            {c}
                          </span>
                        ))}
                      </div>
                    ) : "-"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── Top Scorers Table ─────────────────────────────── */

function TopScorersTable({ leagueId, type }: { leagueId: number; type: "goals" | "assists" }) {
  const fetcher = type === "goals"
    ? () => footballApi.topScorers(leagueId)
    : () => footballApi.topAssists(leagueId);

  const { data, loading, error } = useApi(fetcher, [leagueId, type]);

  if (loading) return <LoadingSpinner label={`Loading top ${type}...`} />;
  if (error) return <div className="glass-card p-6 text-center"><AlertCircle className="w-5 h-5 mx-auto mb-2 text-rose-400" /><span className="text-gray-400 text-sm">Unable to load top {type}</span></div>;
  if (!data || data.length === 0) return <EmptyState message={`No top ${type} data available.`} />;

  return (
    <div className="glass-card overflow-hidden">
      <div className="p-5 border-b border-white/5 flex items-center gap-3">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center
          ${type === "goals" ? "bg-emerald-500/20" : "bg-cyan-500/20"}`}>
          {type === "goals"
            ? <Target className="w-5 h-5 text-emerald-400" />
            : <Award className="w-5 h-5 text-cyan-400" />}
        </div>
        <h3 className="text-lg font-bold text-white">
          {type === "goals" ? "Top Scorers" : "Top Assists"}
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 text-[10px] uppercase tracking-wider border-b border-white/5">
              <th className="p-4 text-left w-10">#</th>
              <th className="p-4 text-left">Player</th>
              <th className="p-4 text-left hidden md:table-cell">Team</th>
              <th className="p-4 text-center">Apps</th>
              <th className="p-4 text-center">
                {type === "goals" ? "Goals" : "Assists"}
              </th>
              <th className="p-4 text-center hidden md:table-cell">
                {type === "goals" ? "Assists" : "Goals"}
              </th>
              <th className="p-4 text-center hidden lg:table-cell">Pen</th>
              <th className="p-4 text-center hidden lg:table-cell">🟨</th>
              <th className="p-4 text-center hidden lg:table-cell">🟥</th>
            </tr>
          </thead>
          <tbody>
            {(data as TopScorerItem[]).slice(0, 20).map((item, idx) => {
              const st = item.statistics?.[0];
              if (!st) return null;
              const mainStat = type === "goals" ? (st.goals?.total ?? 0) : (st.goals?.assists ?? 0);
              const secondStat = type === "goals" ? (st.goals?.assists ?? 0) : (st.goals?.total ?? 0);

              return (
                <tr key={item.player.id || idx}
                  className="border-b border-white/5 hover:bg-white/[0.03] transition-colors">
                  <td className="p-4">
                    <span className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold
                      ${idx < 3 ? "bg-amber-500/20 text-amber-400" : "bg-white/5 text-gray-400"}`}>
                      {idx + 1}
                    </span>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      {item.player.photo && (
                        <img src={item.player.photo} alt="" className="w-8 h-8 rounded-full object-cover border border-white/10" />
                      )}
                      <div>
                        <span className="text-white font-medium block">{item.player.name}</span>
                        {item.player.nationality && (
                          <span className="text-[10px] text-gray-500">{item.player.nationality}</span>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="p-4 hidden md:table-cell">
                    <div className="flex items-center gap-2">
                      {st.team?.logo && <img src={st.team.logo} alt="" className="w-5 h-5 object-contain" />}
                      <span className="text-gray-400 text-xs truncate max-w-[100px]">{st.team?.name}</span>
                    </div>
                  </td>
                  <td className="p-4 text-center text-gray-400">{st.games?.appearences ?? "-"}</td>
                  <td className="p-4 text-center">
                    <span className={`font-bold text-lg
                      ${type === "goals" ? "text-emerald-400" : "text-cyan-400"}`}>
                      {mainStat}
                    </span>
                  </td>
                  <td className="p-4 text-center text-gray-400 hidden md:table-cell">{secondStat}</td>
                  <td className="p-4 text-center text-gray-400 hidden lg:table-cell">
                    {st.penalty?.scored ?? 0}{st.penalty?.missed ? `(${st.penalty.missed}m)` : ""}
                  </td>
                  <td className="p-4 text-center text-amber-400 hidden lg:table-cell">{st.cards?.yellow ?? 0}</td>
                  <td className="p-4 text-center text-rose-400 hidden lg:table-cell">{st.cards?.red ?? 0}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── Upcoming / Recent Fixtures ────────────────────── */

function LeagueFixtures({ leagueId }: { leagueId: number }) {
  const { data: upcoming, loading: loadingUp } = useApi(
    () => footballApi.fixtures({ league_id: leagueId, next_count: 10 }),
    [leagueId],
  );
  const { data: recent, loading: loadingRec } = useApi(
    () => footballApi.fixtures({ league_id: leagueId, last_count: 10 }),
    [leagueId],
  );

  if (loadingUp && loadingRec) return <LoadingSpinner label="Loading fixtures..." />;

  const upFixtures = upcoming?.fixtures || [];
  const recFixtures = recent?.fixtures || [];

  return (
    <div className="space-y-6">
      {/* Recent results */}
      {recFixtures.length > 0 && (
        <div className="glass-card overflow-hidden">
          <div className="p-5 border-b border-white/5 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gray-500/20 flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-gray-400" />
            </div>
            <h3 className="text-lg font-bold text-white">Recent Results</h3>
          </div>
          <div className="p-3 space-y-1">
            {recFixtures.map((f: FixtureItem) => (
              <Link key={f.fixture.id} to={`/playground/match/${f.fixture.id}`}
                className="flex items-center gap-3 p-3 rounded-xl hover:bg-white/[0.03] transition-colors group">
                <span className="text-[10px] text-gray-600 w-12 shrink-0 text-center font-bold">
                  {f.fixture.status.short}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {f.teams.home.logo && <img src={f.teams.home.logo} alt="" className="w-4 h-4 object-contain" />}
                    <span className={`text-sm truncate ${f.teams.home.winner ? "text-white font-bold" : "text-gray-400"}`}>
                      {f.teams.home.name}
                    </span>
                    <span className="text-sm font-bold text-gray-300 ml-auto">{f.goals.home ?? "-"}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {f.teams.away.logo && <img src={f.teams.away.logo} alt="" className="w-4 h-4 object-contain" />}
                    <span className={`text-sm truncate ${f.teams.away.winner ? "text-white font-bold" : "text-gray-400"}`}>
                      {f.teams.away.name}
                    </span>
                    <span className="text-sm font-bold text-gray-300 ml-auto">{f.goals.away ?? "-"}</span>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-gray-600 group-hover:text-emerald-400 shrink-0" />
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Upcoming */}
      {upFixtures.length > 0 && (
        <div className="glass-card overflow-hidden">
          <div className="p-5 border-b border-white/5 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/20 flex items-center justify-center">
              <Calendar className="w-5 h-5 text-cyan-400" />
            </div>
            <h3 className="text-lg font-bold text-white">Upcoming Fixtures</h3>
          </div>
          <div className="p-3 space-y-1">
            {upFixtures.map((f: FixtureItem) => (
              <Link key={f.fixture.id} to={`/playground/match/${f.fixture.id}`}
                className="flex items-center gap-3 p-3 rounded-xl hover:bg-white/[0.03] transition-colors group">
                <span className="text-[10px] text-gray-600 w-12 shrink-0 text-center">
                  {new Date(f.fixture.date).toLocaleDateString([], { day: "numeric", month: "short" })}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {f.teams.home.logo && <img src={f.teams.home.logo} alt="" className="w-4 h-4 object-contain" />}
                    <span className="text-sm text-gray-200 truncate">{f.teams.home.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {f.teams.away.logo && <img src={f.teams.away.logo} alt="" className="w-4 h-4 object-contain" />}
                    <span className="text-sm text-gray-200 truncate">{f.teams.away.name}</span>
                  </div>
                </div>
                <span className="text-[11px] text-gray-500">
                  {new Date(f.fixture.date).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
                <ChevronRight className="w-4 h-4 text-gray-600 group-hover:text-emerald-400 shrink-0" />
              </Link>
            ))}
          </div>
        </div>
      )}

      {upFixtures.length === 0 && recFixtures.length === 0 && (
        <EmptyState message="No fixture data available." />
      )}
    </div>
  );
}

/* ── Community Threads ─────────────────────────────── */

function LeagueThreads({ leagueSlug }: { leagueSlug: string }) {
  const {
    items: threads,
    loading,
    error,
    hasMore,
    loadMore,
    loadingMore,
    total,
  } = usePaginatedApi<ThreadItem>(
    (page) => threadsApi.list(leagueSlug, "hot", page, 10),
    [leagueSlug],
  );

  if (loading) return <LoadingSpinner label="Loading discussions..." />;
  if (error) return <ErrorBox message={error} />;

  return (
    <div className="glass-card overflow-hidden">
      <div className="p-5 border-b border-white/5 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-rose-500/20 flex items-center justify-center">
          <Users className="w-5 h-5 text-rose-400" />
        </div>
        <h3 className="text-lg font-bold text-white">Community Debates</h3>
      </div>
      <div className="p-4 space-y-3">
        {!threads || threads.length === 0 ? (
          <EmptyState message="No debates in this league yet." />
        ) : (
          threads.map((thread: ThreadItem) => (
            <Link key={`thread-${thread.id}`} to={`/playground/thread/${thread.id}`}
              className="block p-4 bg-[#0a0f1a]/50 rounded-xl border border-white/5
                hover:border-emerald-500/20 transition-all group">
              <h4 className="text-white font-medium group-hover:text-emerald-400 transition-colors">
                {thread?.title || "Untitled"}
              </h4>
              <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                <span>by {thread?.author?.name || "Anonymous"}</span>
                <span className="text-emerald-400 font-medium">↑ {thread?.karma ?? 0}</span>
                <span>💬 {thread?.comment_count || 0}</span>
              </div>
            </Link>
          ))
        )}

        {hasMore && (
          <LoadMoreButton
            onClick={loadMore}
            loading={loadingMore}
            current={threads.length}
            total={total}
          />
        )}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   MAIN: LeagueDetail page
   ═══════════════════════════════════════════════════ */

export function LeagueDetail() {
  const { slug } = useParams<{ slug: string }>();
  const routeSlug = slug || "general";
  const normalizedSlug = normalizeSlug(slug);
  const leagueInfo = LEAGUE_INFO[normalizedSlug] || LEAGUE_INFO.general;
  const leagueId = LEAGUE_ID_MAP[normalizedSlug] || 39;
  const [tab, setTab] = useState<LeagueTab>("standings");

  const leagueTabs: { key: LeagueTab; label: string; icon: typeof Trophy }[] = [
    { key: "standings", label: "Standings", icon: Trophy },
    { key: "scorers", label: "Top Scorers", icon: Target },
    { key: "assists", label: "Top Assists", icon: Award },
    { key: "fixtures", label: "Fixtures", icon: Calendar },
  ];

  return (
    <ErrorBoundary>
      <div>
        {/* Back */}
        <Link to="/playground/leagues"
          className="mb-6 inline-flex items-center gap-2 text-sm font-medium text-gray-500 transition-colors hover:text-white">
          <ArrowLeft className="w-4 h-4" /> Back to Leagues
        </Link>

        {/* Hero */}
        <div className="glass-card relative mb-8 overflow-hidden p-8">
          <div className={`absolute inset-0 bg-gradient-to-r ${leagueInfo.gradient} opacity-10`} />
          <div className="absolute inset-0 bg-[#050810]/60" />
          <div className="relative flex items-center gap-6">
            <div className="flex h-20 w-20 items-center justify-center rounded-[28px] border border-white/10 bg-[#0a0f1a]/80 text-5xl shadow-2xl">
              {leagueInfo.icon}
            </div>
            <div>
              <p className="page-kicker">Competition view</p>
              <h1 className="mt-3 font-['Bebas_Neue'] text-[3.8rem] leading-none tracking-[0.08em] text-white">{leagueInfo.name}</h1>
              <p className="mt-2 text-lg text-gray-400">
                Standings, top scorers, fixtures & community
              </p>
            </div>
          </div>
        </div>

        {/* Tab nav */}
        <div className="mb-8 flex w-fit gap-1 rounded-full border border-white/[0.08] bg-white/5 p-1">
          {leagueTabs.map(({ key, label, icon: Icon }) => (
            <button key={key} onClick={() => setTab(key)}
              className={`flex items-center gap-2 rounded-full px-4 py-2.5 text-sm font-semibold transition-all
                ${tab === key
                  ? "bg-gradient-to-r from-sky-500/[0.18] via-violet-500/[0.14] to-amber-400/[0.14] text-sky-200"
                  : "text-gray-500 hover:text-white hover:bg-white/5"
                }`}>
              <Icon className="w-4 h-4" />
              <span className="hidden sm:inline">{label}</span>
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            {tab === "standings" && <StandingsTable leagueId={leagueId} />}
            {tab === "scorers" && <TopScorersTable leagueId={leagueId} type="goals" />}
            {tab === "assists" && <TopScorersTable leagueId={leagueId} type="assists" />}
            {tab === "fixtures" && <LeagueFixtures leagueId={leagueId} />}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <LeagueThreads leagueSlug={routeSlug} />
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}
