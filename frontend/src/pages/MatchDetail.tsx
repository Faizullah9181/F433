import { useParams, Link } from "react-router-dom";
import { useState } from "react";
import { formatDateTime } from "../utils/time";
import {
  ArrowLeft,
  Clock,
  MapPin,
  User,
  AlertCircle,
  Shirt,
  BarChart3,
  Activity,
  Users,
  Target,
  RefreshCw,
} from "lucide-react";
import { useApi } from "../hooks/useApi";
import {
  footballApi,
  type FixtureItem,
  type MatchEvent,
  type MatchLineup,
  type PlayerStatItem,
} from "../services/api";
import { LoadingSpinner, ErrorBox, EmptyState } from "../components/StatusStates";
import { ErrorBoundary } from "../components/ErrorBoundary";

/* ── helpers ──────────────────────────────────────── */

function statusColor(short: string) {
  if (["1H", "2H", "ET", "P", "BT", "LIVE"].includes(short))
    return "text-sky-300 bg-sky-500/[0.18] border-sky-500/[0.28]";
  if (["HT"].includes(short))
    return "text-cyan-400 bg-cyan-500/20 border-cyan-500/30";
  if (["FT", "AET", "PEN"].includes(short))
    return "text-gray-400 bg-gray-500/10 border-gray-500/20";
  return "text-amber-400 bg-amber-500/20 border-amber-500/30";
}

function eventIcon(type: string, detail: string) {
  if (type === "Goal") return detail.includes("Penalty") ? "🎯" : detail.includes("Own") ? "🔴" : "⚽";
  if (type === "Card") return detail.includes("Red") ? "🟥" : "🟨";
  if (type === "subst") return "🔄";
  if (type === "Var") return "📺";
  return "📋";
}

type DetailTab = "summary" | "stats" | "lineups" | "players";

/* ── Match Header ──────────────────────────────────── */

function MatchHeader({ fixture }: { fixture: FixtureItem }) {
  const st = fixture.fixture.status;
  const home = fixture.teams.home;
  const away = fixture.teams.away;
  const isLive = ["1H", "2H", "ET", "P", "BT", "LIVE"].includes(st.short);

  return (
    <div className="glass-card p-6 md:p-8 relative overflow-hidden">
      {/* Gradient bg */}
      <div className="absolute inset-0 bg-gradient-to-r from-sky-600/8 via-transparent to-violet-600/8" />
      <div className="relative">
        {/* League info */}
        <div className="flex items-center gap-3 mb-6 justify-center">
          {fixture.league.logo && (
            <img src={fixture.league.logo} alt="" className="w-6 h-6 object-contain" />
          )}
          <span className="text-sm text-gray-400 font-medium">{fixture.league.name}</span>
          {fixture.league.round && (
            <>
              <span className="text-gray-600">·</span>
              <span className="text-xs text-gray-500">{fixture.league.round}</span>
            </>
          )}
        </div>

        {/* Teams & Score */}
        <div className="flex items-center justify-center gap-4 md:gap-8">
          {/* Home */}
          <div className="flex-1 text-center">
            {home.logo && (
              <img src={home.logo} alt="" className="w-16 h-16 md:w-20 md:h-20 object-contain mx-auto mb-3" />
            )}
            <h2 className={`text-lg md:text-xl font-bold ${home.winner === true ? "text-white" : home.winner === false ? "text-gray-500" : "text-gray-200"}`}>
              {home.name}
            </h2>
          </div>

          {/* Score */}
          <div className="text-center shrink-0">
            <div className="px-8 py-5 bg-[#0a0f1a] rounded-2xl border border-white/5 mb-3">
              <span className={`text-4xl md:text-5xl font-black tracking-wider ${isLive ? "text-sky-300" : "text-white"}`}>
                {fixture.goals.home ?? "-"}
              </span>
              <span className="text-gray-600 mx-3 text-2xl font-bold">:</span>
              <span className={`text-4xl md:text-5xl font-black tracking-wider ${isLive ? "text-sky-300" : "text-white"}`}>
                {fixture.goals.away ?? "-"}
              </span>
            </div>
            <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold border ${statusColor(st.short)}
              ${isLive ? "animate-pulse" : ""}`}>
              {isLive && <span className="w-1.5 h-1.5 rounded-full bg-sky-300 animate-pulse" />}
              {st.long}
              {st.elapsed != null && ` · ${st.elapsed}'`}
            </span>
          </div>

          {/* Away */}
          <div className="flex-1 text-center">
            {away.logo && (
              <img src={away.logo} alt="" className="w-16 h-16 md:w-20 md:h-20 object-contain mx-auto mb-3" />
            )}
            <h2 className={`text-lg md:text-xl font-bold ${away.winner === true ? "text-white" : away.winner === false ? "text-gray-500" : "text-gray-200"}`}>
              {away.name}
            </h2>
          </div>
        </div>

        {/* Half-time, extra scores */}
        {fixture.score && (
          <div className="flex items-center justify-center gap-4 mt-4 text-xs text-gray-500">
            {fixture.score.halftime?.home != null && (
              <span>HT: {fixture.score.halftime.home} - {fixture.score.halftime.away}</span>
            )}
            {fixture.score.extratime?.home != null && (
              <span>ET: {fixture.score.extratime.home} - {fixture.score.extratime.away}</span>
            )}
            {fixture.score.penalty?.home != null && (
              <span>Pen: {fixture.score.penalty.home} - {fixture.score.penalty.away}</span>
            )}
          </div>
        )}

        {/* Meta */}
        <div className="flex items-center justify-center gap-6 mt-5 text-xs text-gray-500">
          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" />
            {formatDateTime(fixture.fixture.date)}
          </div>
          {fixture.fixture.venue?.name && (
            <div className="flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5" />
              {fixture.fixture.venue.name}{fixture.fixture.venue.city && `, ${fixture.fixture.venue.city}`}
            </div>
          )}
          {fixture.fixture.referee && (
            <div className="flex items-center gap-1.5">
              <User className="w-3.5 h-3.5" />
              {fixture.fixture.referee}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── Events Timeline ───────────────────────────────── */

function EventsTimeline({ events, fixture }: { events: MatchEvent[]; fixture: FixtureItem }) {
  if (!events || events.length === 0) {
    return <EmptyState message="No match events yet." />;
  }

  const homeId = fixture.teams.home.id;

  return (
    <div className="space-y-1">
      {events.map((e, i) => {
        const isHome = e.team.id === homeId;
        return (
          <div key={i} className={`flex items-center gap-3 p-3 rounded-xl hover:bg-white/[0.02] transition-colors
            ${isHome ? "" : "flex-row-reverse text-right"}`}>
            {/* Time */}
            <span className="text-xs font-bold text-gray-500 w-10 shrink-0 text-center">
              {e.time.elapsed}'
              {e.time.extra ? `+${e.time.extra}` : ""}
            </span>
            {/* Icon */}
            <span className="text-lg shrink-0">{eventIcon(e.type, e.detail)}</span>
            {/* Info */}
            <div className="flex-1 min-w-0">
              <p className="text-sm text-white font-semibold truncate">
                {e.player?.name || "Unknown"}
              </p>
              <p className="text-[11px] text-gray-500 truncate">
                {e.type === "subst"
                  ? `↗ ${e.assist?.name || "—"}`
                  : e.assist?.name
                    ? `Assist: ${e.assist.name}`
                    : e.detail}
              </p>
            </div>
            {/* Team logo */}
            {e.team.logo && (
              <img src={e.team.logo} alt="" className="w-5 h-5 object-contain shrink-0 opacity-40" />
            )}
          </div>
        );
      })}
    </div>
  );
}

/* ── Match Statistics ──────────────────────────────── */

function StatBar({ label, home, away }: { label: string; home: number | string | null; away: number | string | null }) {
  const h = typeof home === "string" ? parseFloat(home) || 0 : (home ?? 0);
  const a = typeof away === "string" ? parseFloat(away) || 0 : (away ?? 0);
  const total = h + a || 1;
  const hPct = Math.round((h / total) * 100);
  const aPct = 100 - hPct;

  return (
    <div className="py-2.5">
      <div className="flex items-center justify-between mb-1.5">
        <span className={`text-sm font-bold ${h > a ? "text-white" : "text-gray-400"}`}>
          {home ?? 0}
        </span>
        <span className="text-[11px] text-gray-500 uppercase tracking-wider">{label}</span>
        <span className={`text-sm font-bold ${a > h ? "text-white" : "text-gray-400"}`}>
          {away ?? 0}
        </span>
      </div>
      <div className="flex gap-1 h-1.5 rounded-full overflow-hidden">
        <div className="rounded-full bg-sky-500/60 transition-all duration-500" style={{ width: `${hPct}%` }} />
        <div className="rounded-full bg-cyan-500/60 transition-all duration-500" style={{ width: `${aPct}%` }} />
      </div>
    </div>
  );
}

function MatchStatsView({ fixtureId }: { fixtureId: number }) {
  const { data, loading, error } = useApi(() => footballApi.fixtureStats(fixtureId), [fixtureId]);

  if (loading) return <LoadingSpinner label="Loading statistics..." />;
  if (error) return <div className="text-gray-500 text-sm text-center py-6"><AlertCircle className="w-5 h-5 mx-auto mb-2 text-rose-400" />Unable to load statistics</div>;
  if (!data || data.length < 2) return <EmptyState message="No statistics available." />;

  const homeStats = data[0];
  const awayStats = data[1];

  // merge stats by type
  const statMap = new Map<string, { home: number | string | null; away: number | string | null }>();
  for (const s of homeStats.statistics) {
    statMap.set(s.type, { home: s.value, away: null });
  }
  for (const s of awayStats.statistics) {
    const entry = statMap.get(s.type) || { home: null, away: null };
    entry.away = s.value;
    statMap.set(s.type, entry);
  }

  return (
    <div className="glass-card p-5">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          {homeStats.team.logo && <img src={homeStats.team.logo} alt="" className="w-5 h-5 object-contain" />}
          <span className="text-xs text-gray-400 font-medium">{homeStats.team.name}</span>
        </div>
        <BarChart3 className="w-4 h-4 text-gray-600" />
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400 font-medium">{awayStats.team.name}</span>
          {awayStats.team.logo && <img src={awayStats.team.logo} alt="" className="w-5 h-5 object-contain" />}
        </div>
      </div>
      <div className="space-y-1">
        {Array.from(statMap.entries()).map(([type, vals]) => (
          <StatBar key={type} label={type} home={vals.home} away={vals.away} />
        ))}
      </div>
    </div>
  );
}

/* ── Lineups ───────────────────────────────────────── */

function LineupsView({ fixtureId }: { fixtureId: number }) {
  const { data, loading, error } = useApi(() => footballApi.fixtureLineups(fixtureId), [fixtureId]);

  if (loading) return <LoadingSpinner label="Loading lineups..." />;
  if (error) return <div className="text-gray-500 text-sm text-center py-6"><AlertCircle className="w-5 h-5 mx-auto mb-2 text-rose-400" />Unable to load lineups</div>;
  if (!data || data.length === 0) return <EmptyState message="No lineup data available." />;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {data.map((lineup: MatchLineup) => (
        <div key={lineup.team.id} className="glass-card overflow-hidden">
          {/* Team header */}
          <div className="p-4 border-b border-white/5 flex items-center gap-3">
            {lineup.team.logo && <img src={lineup.team.logo} alt="" className="w-6 h-6 object-contain" />}
            <div className="flex-1">
              <span className="text-sm font-bold text-white">{lineup.team.name}</span>
              {lineup.formation && (
                <span className="ml-2 rounded-lg bg-sky-500/10 px-2 py-0.5 text-xs text-sky-300">
                  {lineup.formation}
                </span>
              )}
            </div>
            {lineup.coach?.name && (
              <div className="flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-gray-500" />
                <span className="text-[11px] text-gray-400">{lineup.coach.name}</span>
              </div>
            )}
          </div>

          {/* Starting XI */}
          <div className="p-4">
            <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold mb-3">Starting XI</p>
            <div className="space-y-1">
              {lineup.startXI?.map((p, i) => (
                <div key={i} className="flex items-center gap-2 py-1.5 px-2 rounded-lg hover:bg-white/[0.02]">
                  <span className="w-6 h-6 rounded-lg bg-white/5 flex items-center justify-center text-[10px] font-bold text-gray-400 shrink-0">
                    {p.player.number}
                  </span>
                  <span className="text-sm text-gray-200 flex-1 truncate">{p.player.name}</span>
                  <span className="text-[10px] text-gray-600 uppercase">{p.player.pos}</span>
                </div>
              ))}
            </div>

            {/* Subs */}
            {lineup.substitutes && lineup.substitutes.length > 0 && (
              <>
                <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold mt-5 mb-3">Substitutes</p>
                <div className="space-y-1">
                  {lineup.substitutes.map((p, i) => (
                    <div key={i} className="flex items-center gap-2 py-1 px-2 rounded-lg hover:bg-white/[0.02]">
                      <span className="w-6 h-6 rounded-lg bg-white/5 flex items-center justify-center text-[10px] font-bold text-gray-500 shrink-0">
                        {p.player.number}
                      </span>
                      <span className="text-sm text-gray-400 flex-1 truncate">{p.player.name}</span>
                      <span className="text-[10px] text-gray-600 uppercase">{p.player.pos}</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Player Stats ──────────────────────────────────── */

function PlayerStatsView({ fixtureId }: { fixtureId: number }) {
  const { data, loading, error } = useApi(() => footballApi.fixturePlayerStats(fixtureId), [fixtureId]);

  if (loading) return <LoadingSpinner label="Loading player stats..." />;
  if (error) return <div className="text-gray-500 text-sm text-center py-6"><AlertCircle className="w-5 h-5 mx-auto mb-2 text-rose-400" />Unable to load player stats</div>;
  if (!data || data.length === 0) return <EmptyState message="No player statistics available." />;

  // data from API-Football player-stats comes grouped by team
  // Each entry has: player + statistics array with per-team stats
  // We need to handle the nested structure
  const allPlayers: Array<{
    player: PlayerStatItem["player"];
    stat: PlayerStatItem["statistics"][0];
  }> = [];

  for (const ps of data) {
    if (ps.statistics && ps.statistics.length > 0) {
      allPlayers.push({ player: ps.player, stat: ps.statistics[0] });
    }
  }

  // Sort by rating desc
  allPlayers.sort((a, b) => {
    const ra = parseFloat(a.stat.games?.rating || "0");
    const rb = parseFloat(b.stat.games?.rating || "0");
    return rb - ra;
  });

  return (
    <div className="glass-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 text-[10px] uppercase tracking-wider border-b border-white/5">
              <th className="p-3 text-left">Player</th>
              <th className="p-3 text-center">Rating</th>
              <th className="p-3 text-center">Min</th>
              <th className="p-3 text-center">G</th>
              <th className="p-3 text-center">A</th>
              <th className="p-3 text-center">Shots</th>
              <th className="p-3 text-center">Pass%</th>
              <th className="p-3 text-center">Tackles</th>
              <th className="p-3 text-center hidden md:table-cell">Dribbles</th>
              <th className="p-3 text-center hidden md:table-cell">Cards</th>
            </tr>
          </thead>
          <tbody>
            {allPlayers.slice(0, 30).map((p, i) => {
              const rating = parseFloat(p.stat.games?.rating || "0");
              const ratingColor = rating >= 8 ? "text-sky-300 bg-sky-500/20"
                : rating >= 7 ? "text-cyan-400 bg-cyan-500/20"
                : rating >= 6 ? "text-amber-400 bg-amber-500/20"
                : "text-rose-400 bg-rose-500/20";

              return (
                <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      {p.stat.team?.logo && (
                        <img src={p.stat.team.logo} alt="" className="w-4 h-4 object-contain opacity-40" />
                      )}
                      <span className="text-gray-200 font-medium truncate max-w-[140px]">{p.player.name}</span>
                      {p.stat.games?.position && (
                        <span className="text-[9px] text-gray-600 uppercase">{p.stat.games.position.slice(0, 1)}</span>
                      )}
                    </div>
                  </td>
                  <td className="p-3 text-center">
                    {p.stat.games?.rating ? (
                      <span className={`px-2 py-0.5 rounded-lg text-xs font-bold ${ratingColor}`}>
                        {parseFloat(p.stat.games.rating).toFixed(1)}
                      </span>
                    ) : "-"}
                  </td>
                  <td className="p-3 text-center text-gray-400">{p.stat.games?.minutes ?? "-"}</td>
                  <td className="p-3 text-center">
                    <span className={p.stat.goals?.total ? "font-bold text-sky-300" : "text-gray-600"}>
                      {p.stat.goals?.total ?? 0}
                    </span>
                  </td>
                  <td className="p-3 text-center">
                    <span className={p.stat.goals?.assists ? "text-cyan-400 font-bold" : "text-gray-600"}>
                      {p.stat.goals?.assists ?? 0}
                    </span>
                  </td>
                  <td className="p-3 text-center text-gray-400">
                    {p.stat.shots?.on ?? 0}/{p.stat.shots?.total ?? 0}
                  </td>
                  <td className="p-3 text-center text-gray-400">{p.stat.passes?.accuracy ?? "-"}</td>
                  <td className="p-3 text-center text-gray-400">{p.stat.tackles?.total ?? 0}</td>
                  <td className="p-3 text-center text-gray-400 hidden md:table-cell">
                    {p.stat.dribbles?.success ?? 0}/{p.stat.dribbles?.attempts ?? 0}
                  </td>
                  <td className="p-3 text-center hidden md:table-cell">
                    {(p.stat.cards?.yellow ?? 0) > 0 && <span className="text-amber-400 mr-1">🟨{p.stat.cards.yellow}</span>}
                    {(p.stat.cards?.red ?? 0) > 0 && <span className="text-rose-400">🟥{p.stat.cards.red}</span>}
                    {(p.stat.cards?.yellow ?? 0) === 0 && (p.stat.cards?.red ?? 0) === 0 && <span className="text-gray-600">-</span>}
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

/* ═══════════════════════════════════════════════════
   MAIN: MatchDetail page
   ═══════════════════════════════════════════════════ */

export function MatchDetail() {
  const { id } = useParams<{ id: string }>();
  const fixtureId = parseInt(id || "0", 10);
  const [tab, setTab] = useState<DetailTab>("summary");

  const { data: fixture, loading, error, refetch } = useApi(
    () => footballApi.fixtureDetail(fixtureId),
    [fixtureId],
  );

  const { data: events } = useApi(
    () => footballApi.fixtureEvents(fixtureId),
    [fixtureId],
  );

  const isLive = fixture
    ? ["1H", "2H", "ET", "P", "BT", "LIVE"].includes(fixture.fixture.status.short)
    : false;

  const detailTabs: { key: DetailTab; label: string; icon: typeof Activity }[] = [
    { key: "summary", label: "Summary", icon: Activity },
    { key: "stats", label: "Statistics", icon: BarChart3 },
    { key: "lineups", label: "Lineups", icon: Shirt },
    { key: "players", label: "Player Stats", icon: Users },
  ];

  if (loading) {
    return (
      <div>
        <Link to="/playground/matchday" className="inline-flex items-center gap-2 text-gray-500 hover:text-white mb-6 transition-colors text-sm font-medium">
          <ArrowLeft className="w-4 h-4" /> Back to Matchday
        </Link>
        <LoadingSpinner label="Loading match details..." />
      </div>
    );
  }

  if (error || !fixture) {
    return (
      <div>
        <Link to="/playground/matchday" className="inline-flex items-center gap-2 text-gray-500 hover:text-white mb-6 transition-colors text-sm font-medium">
          <ArrowLeft className="w-4 h-4" /> Back to Matchday
        </Link>
        <ErrorBox message={error || "Match not found."} onRetry={refetch} />
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div>
        {/* Back + refresh */}
        <div className="flex items-center justify-between mb-6">
          <Link to="/playground/matchday" className="inline-flex items-center gap-2 text-sm font-medium text-gray-500 transition-colors hover:text-white">
            <ArrowLeft className="w-4 h-4" /> Back to Matchday
          </Link>
          {isLive && (
            <button onClick={refetch}
              className="poster-action-ghost min-h-[2.5rem] px-4 text-xs text-sky-300">
              <RefreshCw className="w-3.5 h-3.5" /> Refresh
            </button>
          )}
        </div>

        {/* Match header */}
        <MatchHeader fixture={fixture} />

        {/* Tab nav */}
        <div className="mt-6 mb-6 flex w-fit gap-1 rounded-full border border-white/8 bg-white/5 p-1">
          {detailTabs.map(({ key, label, icon: Icon }) => (
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
        {tab === "summary" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Events */}
            <div className="glass-card p-5">
              <div className="flex items-center gap-2 mb-4">
                <Activity className="w-4 h-4 text-sky-300" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Match Events</h3>
              </div>
              <EventsTimeline events={events || []} fixture={fixture} />
            </div>

            {/* Quick stats + match info */}
            <div className="space-y-4">
              {/* Score breakdown */}
              <div className="glass-card p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Target className="w-4 h-4 text-cyan-400" />
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">Match Info</h3>
                </div>
                <div className="space-y-3 text-sm">
                  <div className="flex items-center justify-between py-2 border-b border-white/5">
                    <span className="text-gray-500">Status</span>
                    <span className={`px-2 py-0.5 rounded-lg text-xs font-bold border ${statusColor(fixture.fixture.status.short)}`}>
                      {fixture.fixture.status.long}
                    </span>
                  </div>
                  <div className="flex items-center justify-between py-2 border-b border-white/5">
                    <span className="text-gray-500">Kick-off</span>
                    <span className="text-gray-200">{formatDateTime(fixture.fixture.date)}</span>
                  </div>
                  {fixture.fixture.venue?.name && (
                    <div className="flex items-center justify-between py-2 border-b border-white/5">
                      <span className="text-gray-500">Venue</span>
                      <span className="text-gray-200">{fixture.fixture.venue.name}</span>
                    </div>
                  )}
                  {fixture.fixture.referee && (
                    <div className="flex items-center justify-between py-2 border-b border-white/5">
                      <span className="text-gray-500">Referee</span>
                      <span className="text-gray-200">{fixture.fixture.referee}</span>
                    </div>
                  )}
                  {fixture.score?.halftime?.home != null && (
                    <div className="flex items-center justify-between py-2 border-b border-white/5">
                      <span className="text-gray-500">Half-time</span>
                      <span className="text-gray-200">{fixture.score.halftime.home} - {fixture.score.halftime.away}</span>
                    </div>
                  )}
                  {fixture.score?.fulltime?.home != null && (
                    <div className="flex items-center justify-between py-2">
                      <span className="text-gray-500">Full-time</span>
                      <span className="text-gray-200">{fixture.score.fulltime.home} - {fixture.score.fulltime.away}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Goal scorers */}
              {events && events.filter(e => e.type === "Goal").length > 0 && (
                <div className="glass-card p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <span className="text-lg">⚽</span>
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider">Goals</h3>
                  </div>
                  <div className="space-y-2">
                    {events.filter(e => e.type === "Goal").map((g, i) => (
                      <div key={i} className="flex items-center gap-3 p-2 rounded-lg bg-white/[0.02]">
                        <span className="text-xs font-bold text-gray-500 w-8">{g.time.elapsed}'</span>
                        <span className="text-lg">{eventIcon(g.type, g.detail)}</span>
                        <div className="flex-1">
                          <span className="text-sm text-white font-semibold">{g.player?.name}</span>
                          {g.assist?.name && (
                            <span className="text-[11px] text-gray-500 ml-2">({g.assist.name})</span>
                          )}
                        </div>
                        {g.team.logo && <img src={g.team.logo} alt="" className="w-5 h-5 object-contain opacity-50" />}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {tab === "stats" && <MatchStatsView fixtureId={fixtureId} />}
        {tab === "lineups" && <LineupsView fixtureId={fixtureId} />}
        {tab === "players" && <PlayerStatsView fixtureId={fixtureId} />}
      </div>
    </ErrorBoundary>
  );
}
