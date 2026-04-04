import { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import {
  Radio,
  Clock,
  RefreshCw,
  Calendar,
  Zap,
  ChevronDown,
  ChevronRight,
  MapPin,
  Filter,
  Globe,
  Trophy,
  X,
  Star,
  Search,
} from "lucide-react";
import { useApi } from "../hooks/useApi";
import { footballApi, type FixtureItem } from "../services/api";
import {
  LoadingSpinner,
  ErrorBox,
  EmptyState,
} from "../components/StatusStates";

type Tab = "live" | "today" | "upcoming";

/* ── Priority league IDs — Top European leagues pinned first ── */

const TOP_LEAGUE_IDS = new Set([
  // 🏆 UEFA
  2,   // Champions League
  3,   // Europa League
  848, // Conference League
  // 🏴󠁧󠁢󠁥󠁮󠁧󠁿 England
  39,  // Premier League
  40,  // Championship
  41,  // League One
  45,  // FA Cup
  48,  // League Cup
  // 🇪🇸 Spain
  140, // La Liga
  141, // Segunda Division
  143, // Copa del Rey
  // 🇮🇹 Italy
  135, // Serie A
  136, // Serie B
  137, // Coppa Italia
  // 🇩🇪 Germany
  78,  // Bundesliga
  79,  // 2. Bundesliga
  81,  // DFB Pokal
  // 🇫🇷 France
  61,  // Ligue 1
  62,  // Ligue 2
  66,  // Coupe de France
  // 🇵🇹 Portugal
  94,  // Primeira Liga
  // 🇳🇱 Netherlands
  88,  // Eredivisie
  // 🇹🇷 Turkey
  203, // Super Lig
  // 🌍 International
  1,   // World Cup
  4,   // Euro Championship
  5,   // UEFA Nations League
  9,   // Copa America
  10,  // Friendlies
  15,  // FIFA Club World Cup
]);

/** Ordered priority — lower = shown first */
const LEAGUE_PRIORITY: Record<number, number> = {
  2: 1, 3: 2, 848: 3,                          // UEFA
  39: 10, 40: 11, 41: 12, 45: 13, 48: 14,      // England
  140: 20, 141: 21, 143: 22,                    // Spain
  135: 30, 136: 31, 137: 32,                    // Italy
  78: 40, 79: 41, 81: 42,                       // Germany
  61: 50, 62: 51, 66: 52,                       // France
  94: 60, 88: 65, 203: 70,                      // Portugal, NL, Turkey
  1: 5, 4: 6, 5: 7, 9: 8, 10: 9, 15: 4,        // International
};

/** Quick-filter chips for the top leagues */
const TOP_LEAGUE_CHIPS: { id: number; label: string; icon: string }[] = [
  { id: 2,   label: "UCL",        icon: "🏆" },
  { id: 3,   label: "UEL",        icon: "🏆" },
  { id: 39,  label: "PL",         icon: "🏴󠁧󠁢󠁥󠁮󠁧󠁿" },
  { id: 140, label: "La Liga",    icon: "🇪🇸" },
  { id: 135, label: "Serie A",    icon: "🇮🇹" },
  { id: 78,  label: "Bundesliga", icon: "🇩🇪" },
  { id: 61,  label: "Ligue 1",    icon: "🇫🇷" },
  { id: 94,  label: "Primeira",   icon: "🇵🇹" },
  { id: 88,  label: "Eredivisie", icon: "🇳🇱" },
  { id: 5,   label: "Nations Lg", icon: "🌍" },
];

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

function formatTime(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" });
}

type LeagueGroup = { league: FixtureItem["league"]; fixtures: FixtureItem[] };

/** Group fixtures by league, sort by priority (top European first), then alphabetical */
function groupByLeague(fixtures: FixtureItem[]): LeagueGroup[] {
  const map = new Map<number, LeagueGroup>();
  for (const f of fixtures) {
    const key = f.league.id;
    if (!map.has(key)) {
      map.set(key, { league: f.league, fixtures: [] });
    }
    map.get(key)!.fixtures.push(f);
  }
  return Array.from(map.values()).sort((a, b) => {
    const pa = LEAGUE_PRIORITY[a.league.id] ?? 999;
    const pb = LEAGUE_PRIORITY[b.league.id] ?? 999;
    if (pa !== pb) return pa - pb;
    // Same priority tier → alphabetical
    return a.league.name.localeCompare(b.league.name);
  });
}

/** Extract unique countries from fixtures */
function extractCountries(fixtures: FixtureItem[]): string[] {
  const countries = new Set<string>();
  for (const f of fixtures) {
    if (f.league.country) countries.add(f.league.country);
  }
  return Array.from(countries).sort();
}

/** Extract unique leagues from fixtures */
function extractLeagues(fixtures: FixtureItem[]): { id: number; name: string; country?: string }[] {
  const map = new Map<number, { id: number; name: string; country?: string }>();
  for (const f of fixtures) {
    if (!map.has(f.league.id)) {
      map.set(f.league.id, { id: f.league.id, name: f.league.name, country: f.league.country });
    }
  }
  return Array.from(map.values()).sort((a, b) => {
    const pa = LEAGUE_PRIORITY[a.id] ?? 999;
    const pb = LEAGUE_PRIORITY[b.id] ?? 999;
    if (pa !== pb) return pa - pb;
    return a.name.localeCompare(b.name);
  });
}

/* ── Fixture card (clickable) ──────────────────────── */

function FixtureRow({ fixture }: { fixture: FixtureItem }) {
  const st = fixture.fixture.status;
  const home = fixture.teams.home;
  const away = fixture.teams.away;
  const isLive = ["1H", "2H", "ET", "P", "BT", "LIVE"].includes(st.short);
  const isFinished = ["FT", "AET", "PEN"].includes(st.short);
  const isScheduled = ["NS", "TBD", "PST"].includes(st.short);

  return (
    <Link
      to={`/match/${fixture.fixture.id}`}
      className={`block p-4 rounded-xl border transition-all duration-200 group
        hover:bg-white/[0.03] hover:border-sky-500/20 cursor-pointer
        ${isLive ? "bg-sky-500/[0.03] border-sky-500/[0.15]" : "bg-[#0a0f1a]/40 border-white/5"}`}
    >
      <div className="flex items-center gap-3">
        {/* Status / Time column */}
        <div className="w-16 shrink-0 text-center">
          {isLive ? (
            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-bold border ${statusColor(st.short)}`}>
              <span className="w-1.5 h-1.5 rounded-full bg-sky-300 animate-pulse" />
              {st.elapsed}'
            </span>
          ) : isFinished ? (
            <span className="text-xs font-bold text-gray-500 bg-white/5 px-2 py-1 rounded-lg">FT</span>
          ) : isScheduled ? (
            <span className="text-xs text-gray-500">{formatTime(fixture.fixture.date)}</span>
          ) : (
            <span className={`px-2 py-1 rounded-lg text-xs font-bold border ${statusColor(st.short)}`}>{st.short}</span>
          )}
        </div>

        {/* Teams & Score */}
        <div className="flex-1 min-w-0">
          {/* Home */}
          <div className="flex items-center gap-3 mb-1.5">
            <div className="flex items-center gap-2 flex-1 min-w-0">
              {home.logo && <img src={home.logo} alt="" className="w-5 h-5 object-contain" />}
              <span className={`text-sm font-semibold truncate
                ${home.winner === true ? "text-white" : home.winner === false ? "text-gray-500" : "text-gray-200"}`}>
                {home.name}
              </span>
            </div>
            <span className={`text-sm font-bold w-6 text-right
              ${home.winner === true ? "text-white" : "text-gray-400"}`}>
              {fixture.goals.home ?? "-"}
            </span>
          </div>
          {/* Away */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 flex-1 min-w-0">
              {away.logo && <img src={away.logo} alt="" className="w-5 h-5 object-contain" />}
              <span className={`text-sm font-semibold truncate
                ${away.winner === true ? "text-white" : away.winner === false ? "text-gray-500" : "text-gray-200"}`}>
                {away.name}
              </span>
            </div>
            <span className={`text-sm font-bold w-6 text-right
              ${away.winner === true ? "text-white" : "text-gray-400"}`}>
              {fixture.goals.away ?? "-"}
            </span>
          </div>
        </div>

        {/* Arrow */}
        <ChevronRight className="w-4 h-4 shrink-0 text-gray-600 transition-colors group-hover:text-sky-300" />
      </div>

      {/* Venue */}
      {fixture.fixture.venue?.name && (
        <div className="mt-2 ml-[76px] flex items-center gap-1.5">
          <MapPin className="w-3 h-3 text-gray-600" />
          <span className="text-[11px] text-gray-600 truncate">
            {fixture.fixture.venue.name}
          </span>
        </div>
      )}
    </Link>
  );
}

/* ── League group (collapsible) ────────────────────── */

function LeagueGroupCard({ league, fixtures, isTopLeague }: {
  league: FixtureItem["league"];
  fixtures: FixtureItem[];
  isTopLeague: boolean;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const liveCount = fixtures.filter(f => ["1H", "2H", "ET", "P", "BT", "LIVE"].includes(f.fixture.status.short)).length;

  return (
    <div className={`glass-card overflow-hidden ${isTopLeague ? "ring-1 ring-white/[0.04]" : ""}`}>
      {/* League header */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="w-full flex items-center gap-3 p-4 hover:bg-white/[0.02] transition-colors"
      >
        {league.logo && <img src={league.logo} alt="" className="w-6 h-6 object-contain" />}
        <div className="flex-1 text-left min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-white truncate">{league.name}</span>
            {isTopLeague && <Star className="w-3 h-3 text-amber-400 fill-amber-400 shrink-0" />}
            {league.country && (
              <span className="text-[11px] text-gray-500">{league.country}</span>
            )}
            {league.flag && <img src={league.flag} alt="" className="w-4 h-3 object-contain" />}
          </div>
          {league.round && (
            <span className="text-[11px] text-gray-600">{league.round}</span>
          )}
        </div>
        {liveCount > 0 && (
          <span className="flex items-center gap-1 rounded-full border border-sky-500/20 bg-sky-500/[0.15] px-2 py-0.5 text-[10px] font-bold text-sky-300">
            <span className="w-1.5 h-1.5 rounded-full bg-sky-300 animate-pulse" />
            {liveCount} LIVE
          </span>
        )}
        <span className="text-xs text-gray-600 font-medium">{fixtures.length}</span>
        <ChevronDown className={`w-4 h-4 text-gray-500 transition-transform ${collapsed ? "-rotate-90" : ""}`} />
      </button>

      {/* Fixtures */}
      {!collapsed && (
        <div className="px-3 pb-3 space-y-1">
          {fixtures.map(f => (
            <FixtureRow key={f.fixture.id} fixture={f} />
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Filter bar ────────────────────────────────────── */

type FilterMode = "all" | "top" | "country" | "league";

function FilterBar({
  fixtures,
  filterMode,
  setFilterMode,
  selectedCountry,
  setSelectedCountry,
  selectedLeagueId,
  setSelectedLeagueId,
  searchQuery,
  setSearchQuery,
}: {
  fixtures: FixtureItem[];
  filterMode: FilterMode;
  setFilterMode: (m: FilterMode) => void;
  selectedCountry: string | null;
  setSelectedCountry: (c: string | null) => void;
  selectedLeagueId: number | null;
  setSelectedLeagueId: (id: number | null) => void;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
}) {
  const countries = useMemo(() => extractCountries(fixtures), [fixtures]);
  const leagues = useMemo(() => extractLeagues(fixtures), [fixtures]);

  const filterModes: { key: FilterMode; label: string; icon: typeof Globe }[] = [
    { key: "all", label: "All", icon: Globe },
    { key: "top", label: "Top Leagues", icon: Star },
    { key: "country", label: "By Nation", icon: Globe },
    { key: "league", label: "By League", icon: Trophy },
  ];

  const hasActiveFilter = filterMode !== "all" || selectedCountry || selectedLeagueId || searchQuery;

  return (
    <div className="mb-6 space-y-4">
      {/* Filter mode buttons */}
      <div className="flex flex-wrap items-center gap-2">
        <Filter className="w-4 h-4 text-gray-600 shrink-0" />
        {filterModes.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => {
              setFilterMode(key);
              setSelectedCountry(null);
              setSelectedLeagueId(null);
            }}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all
              ${filterMode === key
                ? "bg-gradient-to-r from-sky-500/[0.18] via-violet-500/[0.14] to-amber-400/[0.14] text-sky-200 border border-sky-500/20"
                : "text-gray-500 hover:text-white bg-white/5 hover:bg-white/10 border border-transparent"
              }`}
          >
            <Icon className="w-3.5 h-3.5" />
            {label}
          </button>
        ))}

        {/* Search */}
        <div className="ml-auto flex items-center gap-2 rounded-xl border border-white/8 bg-white/5 px-3 py-2 
          transition-colors focus-within:border-sky-500/30">
          <Search className="w-3.5 h-3.5 text-gray-600" />
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search team..."
            className="bg-transparent text-sm text-white placeholder-gray-600 outline-none w-32 lg:w-48"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery("")} className="text-gray-500 hover:text-white">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Clear all */}
        {hasActiveFilter && (
          <button
            onClick={() => { setFilterMode("all"); setSelectedCountry(null); setSelectedLeagueId(null); setSearchQuery(""); }}
            className="flex items-center gap-1 px-3 py-2 rounded-xl text-xs font-medium text-rose-400 
              bg-rose-500/10 hover:bg-rose-500/20 transition-colors"
          >
            <X className="w-3 h-3" /> Clear
          </button>
        )}
      </div>

      {/* Country selector dropdown */}
      {filterMode === "country" && (
        <div className="flex flex-wrap gap-2">
          {countries.map(c => (
            <button
              key={c}
              onClick={() => setSelectedCountry(selectedCountry === c ? null : c)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all border
                ${selectedCountry === c
                  ? "bg-sky-500/[0.18] text-sky-200 border-sky-500/[0.24]"
                  : "text-gray-400 bg-white/5 border-white/5 hover:text-white hover:bg-white/10"
                }`}
            >
              {c}
            </button>
          ))}
        </div>
      )}

      {/* League selector dropdown */}
      {filterMode === "league" && (
        <div className="flex flex-wrap gap-2">
          {leagues.map(l => (
            <button
              key={l.id}
              onClick={() => setSelectedLeagueId(selectedLeagueId === l.id ? null : l.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all border
                ${selectedLeagueId === l.id
                  ? "bg-sky-500/[0.18] text-sky-200 border-sky-500/[0.24]"
                  : "text-gray-400 bg-white/5 border-white/5 hover:text-white hover:bg-white/10"
                }`}
            >
              {l.name}
              {l.country && <span className="text-gray-600 ml-1">({l.country})</span>}
            </button>
          ))}
        </div>
      )}

      {/* Top league quick chips (shown by default above the results) */}
      {filterMode === "all" && !selectedCountry && !selectedLeagueId && !searchQuery && (
        <div className="flex flex-wrap gap-1.5">
          {TOP_LEAGUE_CHIPS.map(chip => {
            const hasMatches = fixtures.some(f => f.league.id === chip.id);
            return (
              <button
                key={chip.id}
                onClick={() => {
                  setFilterMode("league");
                  setSelectedLeagueId(chip.id);
                }}
                disabled={!hasMatches}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-[11px] font-bold transition-all border
                  ${hasMatches
                    ? "text-gray-300 bg-white/5 border-white/5 hover:border-sky-500/[0.24] hover:text-sky-300 hover:bg-sky-500/10"
                    : "text-gray-700 bg-white/[0.02] border-transparent cursor-not-allowed"
                  }`}
              >
                <span>{chip.icon}</span>
                {chip.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ── Main Matchday page ────────────────────────────── */

export function Matchday() {
  const [tab, setTab] = useState<Tab>("today");
  const [filterMode, setFilterMode] = useState<FilterMode>("all");
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);
  const [selectedLeagueId, setSelectedLeagueId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const fetcher = (): Promise<FixtureItem[]> => {
    switch (tab) {
      case "live":
        return footballApi.live().then(r => r.fixtures);
      case "today": {
        const today = new Date().toISOString().slice(0, 10);
        return footballApi.fixtures({ date: today }).then(r => r.fixtures);
      }
      case "upcoming":
        return footballApi.fixtures({ next_count: 50 }).then(r => r.fixtures);
    }
  };

  const { data: fixtures, loading, error, refetch } = useApi(fetcher, [tab]);

  /* ── apply filters ── */
  const filtered = useMemo(() => {
    if (!fixtures) return [];
    let list = fixtures;

    // Top leagues only
    if (filterMode === "top") {
      list = list.filter(f => TOP_LEAGUE_IDS.has(f.league.id));
    }

    // Country filter
    if (filterMode === "country" && selectedCountry) {
      list = list.filter(f => f.league.country === selectedCountry);
    }

    // League filter
    if (filterMode === "league" && selectedLeagueId) {
      list = list.filter(f => f.league.id === selectedLeagueId);
    }

    // Search by team name
    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase();
      list = list.filter(f =>
        f.teams.home.name.toLowerCase().includes(q) ||
        f.teams.away.name.toLowerCase().includes(q) ||
        f.league.name.toLowerCase().includes(q)
      );
    }

    return list;
  }, [fixtures, filterMode, selectedCountry, selectedLeagueId, searchQuery]);

  const grouped = useMemo(() => groupByLeague(filtered), [filtered]);

  const tabs: { key: Tab; label: string; icon: typeof Radio }[] = [
    { key: "live", label: "Live Now", icon: Radio },
    { key: "today", label: "Today", icon: Calendar },
    { key: "upcoming", label: "Upcoming", icon: Clock },
  ];

  const liveTotal = fixtures?.filter(f =>
    ["1H", "2H", "ET", "P", "BT", "LIVE"].includes(f.fixture.status.short)
  ).length ?? 0;

  return (
    <div>
      <div className="page-head">
        <div className="page-title-wrap">
          <p className="page-kicker">Live board</p>
          <h1 className="page-title">Matchday</h1>
          <p className="page-subtitle">
            Fixtures, league priority and live states now sit inside the same high-contrast board instead of a loose utility page.
          </p>
        </div>

        <button onClick={refetch} disabled={loading}
          className="poster-action-ghost disabled:opacity-50">
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          <span className="hidden sm:inline">Refresh</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="mb-6 flex w-fit gap-2 rounded-full border border-white/10 bg-white/5 p-1">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button key={key} onClick={() => setTab(key)}
            className={`flex items-center gap-2 rounded-full px-5 py-3 font-semibold text-sm 
              transition-all duration-200 ${
                tab === key
                  ? "bg-gradient-to-r from-sky-500/[0.18] via-violet-500/[0.14] to-amber-400/[0.14] text-sky-200"
                  : "text-gray-500 hover:text-white hover:bg-white/5"
              }`}>
            <Icon className={`w-4 h-4 ${tab === key && key === "live" ? "animate-pulse" : ""}`} />
            {label}
            {key === "live" && liveTotal > 0 && (
              <span className="flex items-center gap-1 rounded-full bg-sky-500/[0.18] px-1.5 py-0.5 text-[10px] font-bold text-sky-200">
                {liveTotal}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Filters (only when we have data) */}
      {!loading && fixtures && fixtures.length > 0 && (
        <FilterBar
          fixtures={fixtures}
          filterMode={filterMode}
          setFilterMode={setFilterMode}
          selectedCountry={selectedCountry}
          setSelectedCountry={setSelectedCountry}
          selectedLeagueId={selectedLeagueId}
          setSelectedLeagueId={setSelectedLeagueId}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
        />
      )}

      {/* Summary bar */}
      {!loading && fixtures && fixtures.length > 0 && (
        <div className="flex items-center gap-4 mb-6 px-1">
          <span className="text-xs text-gray-500">
            {grouped.length} league{grouped.length !== 1 ? "s" : ""} · {filtered.length} match{filtered.length !== 1 ? "es" : ""}
            {filtered.length !== fixtures.length && (
              <span className="text-gray-600"> of {fixtures.length} total</span>
            )}
          </span>
          {liveTotal > 0 && (
            <span className="flex items-center gap-1.5 text-xs text-sky-300">
              <span className="w-1.5 h-1.5 rounded-full bg-sky-300 animate-pulse" />
              {liveTotal} live
            </span>
          )}
        </div>
      )}

      {/* Content */}
      {loading && <LoadingSpinner label="Fetching fixtures…" />}
      {error && <ErrorBox message={error} onRetry={refetch} />}
      {!loading && !error && fixtures?.length === 0 && (
        <EmptyState message={
          tab === "live"
            ? "No live matches right now. Check back soon!"
            : tab === "today"
              ? "No matches scheduled today."
              : "No upcoming fixtures found."
        } />
      )}
      {!loading && !error && fixtures && fixtures.length > 0 && filtered.length === 0 && (
        <EmptyState message="No matches found with current filters. Try adjusting your search." />
      )}

      {/* League groups */}
      <div className="space-y-4">
        {grouped.map(g => (
          <LeagueGroupCard
            key={`${g.league.id}-${g.league.name}`}
            league={g.league}
            fixtures={g.fixtures}
            isTopLeague={TOP_LEAGUE_IDS.has(g.league.id)}
          />
        ))}
      </div>
    </div>
  );
}
