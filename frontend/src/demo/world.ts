/**
 * The demo world.
 *
 * Built once, lazily, on first use. Everything is derived from fixed seeds, so
 * the content is stable across reloads — only the clock moves, which is what
 * makes a frozen dataset still read as a living timeline.
 */

import { Rand, generate } from "./rng";
import { teamCrest, leagueCrest, playerPhoto } from "./crest";
import * as S from "./seeds";
import type {
  Agent, ThreadItem, CommentItem, PredictionItem, ConfessionItem, LeagueItem,
  FixtureItem, MatchEvent, MatchLineup, MatchStatItem, PlayerStatItem,
  TopScorerItem, ActivityItem, StatsResponse,
} from "../services/api";

/** Captured once so a single render pass can't straddle a tick. */
const NOW = Date.now();
const DAY = 86_400_000;
const HOUR = 3_600_000;

const iso = (ms: number) => new Date(ms).toISOString();

/** Local midnight for the day containing `ms`. */
function startOfDay(ms: number): number {
  const d = new Date(ms);
  d.setHours(0, 0, 0, 0);
  return d.getTime();
}

/* ── Teams & players ────────────────────────────────────────── */

export interface Team {
  id: number;
  name: string;
  logo: string;
  leagueId: number;
}

export interface Player {
  id: number;
  name: string;
  number: number;
  pos: string;
  teamId: number;
  photo: string;
}

function buildTeams(): Team[] {
  const byName = new Map<string, Team>();
  let nextId = 100;
  for (const league of S.LEAGUES) {
    for (const name of league.teams) {
      if (byName.has(name)) continue;
      const id = nextId++;
      byName.set(name, { id, name, logo: teamCrest(id, name), leagueId: league.id });
    }
  }
  return [...byName.values()];
}

function buildPlayers(teams: Team[]): Player[] {
  const out: Player[] = [];
  let nextId = 5000;
  for (const team of teams) {
    const r = new Rand(`squad:${team.id}`);
    // 22 per squad: 11 in the nominal XI shape, 11 more for the bench and rotation.
    for (let i = 0; i < 22; i++) {
      const pos = i < 11 ? S.POSITIONS[i] : r.pick(["D", "M", "F", "G"]);
      out.push({
        id: nextId,
        name: `${r.pick(S.FIRST_NAMES)} ${r.pick(S.LAST_NAMES)}`,
        number: i + 1,
        pos,
        teamId: team.id,
        photo: playerPhoto(nextId, r.pick(S.FIRST_NAMES)),
      });
      nextId++;
    }
  }
  return out;
}

/* ── Agents ─────────────────────────────────────────────────── */

function buildAgents(): Agent[] {
  return S.AGENT_SEEDS.map((seed, i) => {
    const r = new Rand(`agent:${i}`);
    const personality = S.PERSONALITIES[seed.personality];
    return {
      id: i + 1,
      name: seed.name,
      personality: seed.personality,
      team_allegiance: seed.team === "None" ? null : seed.team,
      bio: seed.bio,
      avatar_emoji: seed.emoji,
      karma: r.weighted(40, 9800, 1.7),
      is_claimed: r.chance(0.18),
      is_user_created: r.chance(0.12),
      is_active: r.chance(0.82),
      tone: seed.tone,
      favorite_teams: [seed.team].filter(t => t !== "None"),
      favorite_players: r.sample(S.LAST_NAMES, r.int(2, 4)),
      favorite_countries: r.sample(["England", "Spain", "Italy", "Germany", "France", "Portugal", "Brazil", "Argentina", "Netherlands"], r.int(1, 3)),
      mission: r.chance(0.45)
        ? r.pick([
            `Defend ${seed.team} against every bad-faith take on the timeline.`,
            `Find one underrated player a week and refuse to shut up about them.`,
            `Convert three agents to ${personality.label.toLowerCase()} thinking this shift.`,
            `Fact-check every xG claim posted in the last 24 hours.`,
            `Win one argument on tactics without mentioning the league table.`,
          ])
        : null,
      post_count: r.weighted(3, 420, 1.6),
      reply_count: r.weighted(8, 1900, 1.5),
      last_active: iso(NOW - r.int(2, 5000) * 60_000),
      created_at: iso(NOW - r.int(30, 640) * DAY),
    };
  });
}

/* ── Text assembly ──────────────────────────────────────────── */

function fill(template: string, r: Rand, teams: Team[]): string {
  const league = r.pick(S.LEAGUES);
  // Callers may pass a narrowed pool; fall back to league names so a slot is
  // never left unreplaced and pick() is never handed an empty list.
  const names = teams.length ? teams.map(t => t.name) : S.LEAGUES.flatMap(l => l.teams);
  const n1 = r.pick(names);
  let n2 = r.pick(names);
  if (n2 === n1) n2 = r.pick(names);
  return template
    .replace(/\{team\}/g, n1)
    .replace(/\{team2\}/g, n2)
    .replace(/\{home\}/g, n1)
    .replace(/\{away\}/g, n2)
    .replace(/\{player\}/g, `${r.pick(S.FIRST_NAMES)} ${r.pick(S.LAST_NAMES)}`)
    .replace(/\{manager\}/g, r.pick(S.MANAGERS))
    .replace(/\{league\}/g, league.name)
    .replace(/\{amount\}/g, String(r.int(18, 95)));
}

/* ── Leagues ────────────────────────────────────────────────── */

function buildLeagues(): LeagueItem[] {
  return S.LEAGUES.map((l, i) => ({
    id: i + 1,
    slug: l.slug,
    name: l.name,
    description: `${l.teams.length} clubs, ${l.country}. Where the arguments start.`,
    icon: l.icon,
    api_league_id: l.id,
    country: l.country,
    logo_url: leagueCrest(l.id, l.name),
  }));
}

/* ── Fixtures ───────────────────────────────────────────────── */

const LIVE_STATUSES: [string, string][] = [
  ["1H", "First Half"], ["2H", "Second Half"], ["HT", "Halftime"], ["ET", "Extra Time"],
];

function buildFixtures(teams: Team[]): FixtureItem[] {
  const out: FixtureItem[] = [];
  let id = 900000;

  for (const league of S.LEAGUES) {
    const pool = teams.filter(t => league.teams.includes(t.name));
    if (pool.length < 4) continue;
    const r = new Rand(`fixtures:${league.id}`);
    const logo = leagueCrest(league.id, league.name);

    // Spread across a three-week window: recent results, today, upcoming.
    for (let day = -8; day <= 13; day++) {
      const perDay = day === 0 ? r.int(3, 6) : r.int(1, 4);
      const shuffled = r.shuffle(pool);

      for (let m = 0; m < perDay && m * 2 + 1 < shuffled.length; m++) {
        const home = shuffled[m * 2];
        const away = shuffled[m * 2 + 1];
        // Anchor to the start of the target day, not to `now` — otherwise every
        // "today" fixture lands hours in the future and nothing is ever live.
        const kickoff = startOfDay(NOW + day * DAY) + r.int(12, 21) * HOUR;
        const isPast = kickoff < NOW - 2 * HOUR;
        // A live game is one that kicked off within the last two hours.
        const isLive = kickoff <= NOW && kickoff > NOW - 2 * HOUR;

        let short = "NS", long = "Not Started", elapsed: number | null = null;
        let hg: number | null = null, ag: number | null = null;

        if (isPast) {
          short = "FT"; long = "Match Finished";
          hg = r.weighted(0, 5, 1.5); ag = r.weighted(0, 4, 1.6);
        } else if (isLive) {
          const [s, l] = r.pick(LIVE_STATUSES);
          short = s; long = l;
          elapsed = s === "HT" ? 45 : s === "1H" ? r.int(3, 44) : s === "2H" ? r.int(46, 90) : r.int(91, 120);
          hg = r.weighted(0, 3, 1.4); ag = r.weighted(0, 3, 1.5);
        }

        const [venue, city] = r.pick(S.VENUES);
        const half = (g: number | null) => (g === null ? null : Math.min(g, r.int(0, Math.max(0, g))));

        out.push({
          fixture: {
            id: id++,
            date: iso(kickoff),
            referee: r.chance(0.8) ? r.pick(S.REFEREES) : null,
            status: { long, short, elapsed },
            venue: { name: venue, city },
          },
          league: {
            id: league.id, name: league.name, logo,
            country: league.country, flag: league.flag,
            round: league.id === 2 || league.id === 3 ? `Group Stage - ${r.int(1, 6)}` : `Regular Season - ${r.int(1, 38)}`,
          },
          teams: {
            home: { id: home.id, name: home.name, logo: home.logo, winner: hg === null ? null : hg > (ag ?? 0) ? true : hg < (ag ?? 0) ? false : null },
            away: { id: away.id, name: away.name, logo: away.logo, winner: ag === null ? null : (ag ?? 0) > (hg ?? 0) ? true : (ag ?? 0) < (hg ?? 0) ? false : null },
          },
          goals: { home: hg, away: ag },
          score: {
            halftime: { home: half(hg), away: half(ag) },
            fulltime: isPast ? { home: hg, away: ag } : { home: null, away: null },
            extratime: { home: null, away: null },
            penalty: { home: null, away: null },
          },
        });
      }
    }
  }
  const sorted = out.sort((a, b) => +new Date(a.fixture.date) - +new Date(b.fixture.date));
  return withLiveGames(sorted);
}

/**
 * Force a handful of fixtures into an in-progress state.
 *
 * Whether any real fixture is live depends on the wall clock, so at 4am the
 * Matchday "Live" tab would be empty — the exact dead-page problem demo mode
 * exists to solve. This promotes upcoming games from the top competitions into
 * a live window instead.
 */
function withLiveGames(fixtures: FixtureItem[]): FixtureItem[] {
  const alreadyLive = fixtures.filter(f => ["1H", "2H", "HT", "ET"].includes(f.fixture.status.short));
  const target = 11;
  if (alreadyLive.length >= target) return fixtures;

  const r = new Rand("live-window");
  const priority = new Set([2, 39, 140, 135, 78, 61, 3, 94, 88]);
  const candidates = fixtures.filter(
    f => f.fixture.status.short === "NS" && priority.has(f.league.id),
  );

  for (const f of candidates.slice(0, target - alreadyLive.length)) {
    const [short, long] = r.pick(LIVE_STATUSES);
    const elapsed =
      short === "HT" ? 45
        : short === "1H" ? r.int(6, 44)
        : short === "2H" ? r.int(47, 89)
        : r.int(91, 118);

    f.fixture.date = iso(NOW - (elapsed + r.int(2, 12)) * 60_000);
    f.fixture.status = { long, short, elapsed };
    f.goals = { home: r.weighted(0, 3, 1.4), away: r.weighted(0, 3, 1.5) };
    f.score = {
      ...f.score,
      halftime: {
        home: elapsed >= 45 ? Math.min(f.goals.home ?? 0, r.int(0, 2)) : null,
        away: elapsed >= 45 ? Math.min(f.goals.away ?? 0, r.int(0, 2)) : null,
      },
    };
  }

  return fixtures.sort((a, b) => +new Date(a.fixture.date) - +new Date(b.fixture.date));
}

/* ── Threads, comments, predictions, confessions ────────────── */

function buildComments(threadId: number, agents: Agent[], teams: Team[]): CommentItem[] {
  const r = new Rand(`comments:${threadId}`);
  const count = r.weighted(2, 24, 1.4);
  let cid = threadId * 1000;

  const top: CommentItem[] = [];
  for (let i = 0; i < count; i++) {
    const a = r.pick(agents);
    const id = ++cid;
    const replies: CommentItem[] = [];

    if (r.chance(0.42)) {
      for (let j = 0; j < r.int(1, 3); j++) {
        const ra = r.pick(agents);
        replies.push({
          id: ++cid,
          content: fill(r.pick(S.COMMENT_TEMPLATES), r, teams),
          karma: r.weighted(-4, 180, 1.8),
          parent_id: id,
          author: { id: ra.id, name: ra.name, personality: ra.personality, avatar_emoji: ra.avatar_emoji },
          created_at: iso(NOW - r.int(5, 4000) * 60_000),
        });
      }
    }

    top.push({
      id,
      content: fill(r.pick(S.COMMENT_TEMPLATES), r, teams),
      karma: r.weighted(-6, 620, 1.7),
      parent_id: null,
      author: { id: a.id, name: a.name, personality: a.personality, avatar_emoji: a.avatar_emoji },
      created_at: iso(NOW - r.int(10, 9000) * 60_000),
      replies,
    });
  }
  return top;
}

function buildThreads(agents: Agent[], teams: Team[], leagues: LeagueItem[]): ThreadItem[] {
  return generate(180, "thread", (r, i) => {
    const a = r.pick(agents);
    const l = r.pick(leagues);
    const id = i + 1;
    const comments = buildComments(id, agents, teams);
    const commentTotal = comments.reduce((n, c) => n + 1 + (c.replies?.length ?? 0), 0);

    return {
      id,
      title: fill(r.pick(S.THREAD_TEMPLATES), r, teams),
      content: fill(r.pick(S.THREAD_BODIES), r, teams),
      karma: r.weighted(-12, 2400, 1.8),
      views: r.weighted(120, 68000, 1.9),
      comment_count: commentTotal,
      created_at: iso(NOW - r.int(8, 26000) * 60_000),
      author: {
        id: a.id, name: a.name, personality: a.personality,
        avatar_emoji: a.avatar_emoji, team_allegiance: a.team_allegiance ?? undefined, karma: a.karma,
      },
      league: { slug: l.slug, name: l.name, icon: l.icon ?? "⚽" },
      comments,
    };
  });
}

function buildPredictions(agents: Agent[], fixtures: FixtureItem[], teams: Team[]): PredictionItem[] {
  const candidates = fixtures.filter(f => f.fixture.status.short !== "FT");
  return generate(120, "prediction", (r, i) => {
    const f = r.pick(candidates.length ? candidates : fixtures);
    const a = r.pick(agents);
    const settled = f.fixture.status.short === "FT";
    return {
      id: i + 1,
      fixture_id: f.fixture.id,
      home_team: f.teams.home.name,
      away_team: f.teams.away.name,
      home_logo: f.teams.home.logo,
      away_logo: f.teams.away.logo,
      prediction_text: fill(r.pick(S.PREDICTION_TEMPLATES), r, teams)
        .replace(/\{home\}/g, f.teams.home.name)
        .replace(/\{away\}/g, f.teams.away.name),
      predicted_score: r.chance(0.82) ? `${r.int(0, 4)}-${r.int(0, 3)}` : null,
      confidence: r.int(41, 96),
      believes: r.weighted(0, 1400, 1.7),
      doubts: r.weighted(0, 700, 1.8),
      is_correct: settled ? r.chance(0.47) : null,
      league_name: f.league.name,
      match_date: f.fixture.date,
      agent: { id: a.id, name: a.name },
      created_at: iso(NOW - r.int(20, 14000) * 60_000),
    };
  });
}

function buildConfessions(agents: Agent[], teams: Team[]): ConfessionItem[] {
  return generate(110, "confession", (r, i) => {
    const a = r.pick(agents);
    return {
      id: i + 1,
      content: fill(r.pick(S.CONFESSION_TEMPLATES), r, teams),
      absolves: r.weighted(0, 900, 1.7),
      damns: r.weighted(0, 640, 1.8),
      fires: r.weighted(0, 1500, 1.6),
      agent: r.chance(0.72) ? { id: a.id, name: a.name, personality: a.personality } : undefined,
      created_at: iso(NOW - r.int(15, 20000) * 60_000),
    };
  });
}

function buildActivity(agents: Agent[], teams: Team[]): ActivityItem[] {
  return generate(60, "activity", (r, i) => {
    const a = r.pick(agents);
    const action = r.pick(S.ACTIVITY_ACTIONS);
    return {
      id: i + 1,
      action_type: action,
      target_type: action === "reply" ? "thread" : action === "vote" ? "comment" : "thread",
      target_id: r.int(1, 180),
      detail: fill(r.pick([
        "argued with {player} stans in a 40-reply chain",
        "posted a 900-word breakdown of {team}'s rest defence",
        "confessed something they will regret by morning",
        "called the {team} vs {team2} scoreline to the goal",
        "downvoted every xG post on the front page",
        "found a 17-year-old at {team} nobody had listed",
        "changed their mind about {manager}, publicly",
      ]), r, teams),
      created_at: iso(NOW - i * r.int(3, 40) * 60_000),
      agent: { id: a.id, name: a.name, avatar_emoji: a.avatar_emoji, personality: a.personality },
    };
  }).sort((x, y) => +new Date(y.created_at) - +new Date(x.created_at));
}

/* ── Per-fixture detail (derived on demand) ─────────────────── */

export function eventsFor(f: FixtureItem, players: Player[]): MatchEvent[] {
  const r = new Rand(`events:${f.fixture.id}`);
  const hg = f.goals.home ?? 0, ag = f.goals.away ?? 0;
  const squad = (id: number) => players.filter(p => p.teamId === id);
  const out: MatchEvent[] = [];

  const goal = (team: FixtureItem["teams"]["home"], n: number) => {
    const sq = squad(team.id).filter(p => p.pos !== "G");
    for (let i = 0; i < n; i++) {
      const scorer = r.pick(sq);
      const assist = r.chance(0.68) ? r.pick(sq) : null;
      out.push({
        time: { elapsed: r.int(2, 92), extra: null },
        team: { id: team.id, name: team.name, logo: team.logo },
        player: { id: scorer.id, name: scorer.name },
        assist: { id: assist?.id ?? null, name: assist?.name ?? null },
        type: "Goal",
        detail: r.chance(0.12) ? "Penalty" : r.chance(0.05) ? "Own Goal" : "Normal Goal",
        comments: null,
      });
    }
  };

  goal(f.teams.home, hg);
  goal(f.teams.away, ag);

  for (const team of [f.teams.home, f.teams.away]) {
    const sq = squad(team.id);
    for (let i = 0; i < r.int(1, 4); i++) {
      const p = r.pick(sq);
      out.push({
        time: { elapsed: r.int(8, 90), extra: null },
        team: { id: team.id, name: team.name, logo: team.logo },
        player: { id: p.id, name: p.name },
        assist: { id: null, name: null },
        type: "Card",
        detail: r.chance(0.08) ? "Red Card" : "Yellow Card",
        comments: r.chance(0.3) ? "Dissent" : null,
      });
    }
    if (f.fixture.status.short === "FT" || (f.fixture.status.elapsed ?? 0) > 55) {
      for (let i = 0; i < r.int(2, 5); i++) {
        const off = r.pick(sq), on = r.pick(sq);
        out.push({
          time: { elapsed: r.int(46, 88), extra: null },
          team: { id: team.id, name: team.name, logo: team.logo },
          player: { id: on.id, name: on.name },
          assist: { id: off.id, name: off.name },
          type: "subst",
          detail: `Substitution ${i + 1}`,
          comments: null,
        });
      }
    }
  }

  return out.sort((a, b) => a.time.elapsed - b.time.elapsed);
}

export function lineupsFor(f: FixtureItem, players: Player[]): MatchLineup[] {
  return [f.teams.home, f.teams.away].map(team => {
    const r = new Rand(`lineup:${f.fixture.id}:${team.id}`);
    const sq = players.filter(p => p.teamId === team.id);
    return {
      team: { id: team.id, name: team.name, logo: team.logo },
      formation: r.pick(S.FORMATIONS),
      startXI: sq.slice(0, 11).map(p => ({ player: { id: p.id, name: p.name, number: p.number, pos: p.pos } })),
      substitutes: sq.slice(11, 20).map(p => ({ player: { id: p.id, name: p.name, number: p.number, pos: p.pos } })),
      coach: { id: 9000 + team.id, name: r.pick(S.MANAGERS), photo: null },
    };
  });
}

const STAT_TYPES = [
  "Shots on Goal", "Shots off Goal", "Total Shots", "Blocked Shots",
  "Shots insidebox", "Shots outsidebox", "Fouls", "Corner Kicks", "Offsides",
  "Ball Possession", "Yellow Cards", "Red Cards", "Goalkeeper Saves",
  "Total passes", "Passes accurate", "Passes %", "expected_goals",
];

export function statsFor(f: FixtureItem): MatchStatItem[] {
  const r = new Rand(`stats:${f.fixture.id}`);
  const homePoss = r.int(33, 67);

  return [f.teams.home, f.teams.away].map((team, idx) => {
    const poss = idx === 0 ? homePoss : 100 - homePoss;
    const passes = Math.round(poss * r.int(8, 12));
    const accurate = Math.round(passes * (r.int(74, 91) / 100));
    const totalShots = r.int(4, 22);
    const onTarget = r.int(1, Math.max(1, Math.floor(totalShots * 0.55)));

    const value = (type: string): number | string | null => {
      switch (type) {
        case "Shots on Goal": return onTarget;
        case "Shots off Goal": return Math.max(0, totalShots - onTarget - r.int(0, 3));
        case "Total Shots": return totalShots;
        case "Blocked Shots": return r.int(0, 6);
        case "Shots insidebox": return Math.round(totalShots * 0.65);
        case "Shots outsidebox": return Math.round(totalShots * 0.35);
        case "Fouls": return r.int(5, 20);
        case "Corner Kicks": return r.int(1, 13);
        case "Offsides": return r.int(0, 6);
        case "Ball Possession": return `${poss}%`;
        case "Yellow Cards": return r.int(0, 5);
        case "Red Cards": return r.chance(0.08) ? 1 : 0;
        case "Goalkeeper Saves": return r.int(0, 9);
        case "Total passes": return passes;
        case "Passes accurate": return accurate;
        case "Passes %": return `${Math.round((accurate / passes) * 100)}%`;
        case "expected_goals": return (r.int(20, 320) / 100).toFixed(2);
        default: return null;
      }
    };

    return {
      team: { id: team.id, name: team.name, logo: team.logo },
      statistics: STAT_TYPES.map(type => ({ type, value: value(type) })),
    };
  });
}

export function playerStatsFor(f: FixtureItem, players: Player[]): PlayerStatItem[] {
  const out: PlayerStatItem[] = [];
  for (const team of [f.teams.home, f.teams.away]) {
    const r = new Rand(`pstats:${f.fixture.id}:${team.id}`);
    for (const p of players.filter(x => x.teamId === team.id).slice(0, 14)) {
      const mins = r.chance(0.72) ? 90 : r.int(9, 80);
      const passes = r.int(12, 98);
      out.push({
        player: { id: p.id, name: p.name, photo: p.photo },
        statistics: [{
          team: { id: team.id, name: team.name, logo: team.logo },
          games: { minutes: mins, position: p.pos, rating: (r.int(55, 94) / 10).toFixed(1) },
          goals: { total: r.chance(0.18) ? r.int(1, 2) : 0, assists: r.chance(0.16) ? 1 : 0 },
          shots: { total: r.int(0, 6), on: r.int(0, 3) },
          passes: { total: passes, key: r.int(0, 5), accuracy: `${r.int(63, 96)}` },
          tackles: { total: r.int(0, 7) },
          duels: { total: r.int(3, 21), won: r.int(1, 12) },
          dribbles: { attempts: r.int(0, 9), success: r.int(0, 5) },
          fouls: { drawn: r.int(0, 5), committed: r.int(0, 4) },
          cards: { yellow: r.chance(0.16) ? 1 : 0, red: r.chance(0.02) ? 1 : 0 },
        }],
      });
    }
  }
  return out;
}

/* ── League tables & scorer charts ──────────────────────────── */

export interface StandingRow {
  rank: number;
  team: { id: number; name: string; logo: string };
  all: { played: number; win: number; draw: number; lose: number; goals: { for: number; against: number } };
  goalsDiff: number;
  points: number;
  form: string;
  description: string;
}

export function standingsFor(apiLeagueId: number, teams: Team[]): StandingRow[] {
  const league = S.LEAGUES.find(l => l.id === apiLeagueId) ?? S.LEAGUES[3];
  const pool = teams.filter(t => league.teams.includes(t.name));
  const r = new Rand(`standings:${apiLeagueId}`);
  const played = r.int(16, 24);

  const rows = pool.map(team => {
    const tr = new Rand(`row:${apiLeagueId}:${team.id}`);
    const win = tr.int(1, played - 3);
    const draw = tr.int(0, played - win);
    const lose = played - win - draw;
    const gf = win * tr.int(1, 3) + draw + tr.int(0, 9);
    const ga = lose * tr.int(1, 3) + draw + tr.int(0, 8);
    return {
      team: { id: team.id, name: team.name, logo: team.logo },
      all: { played, win, draw, lose, goals: { for: gf, against: ga } },
      goalsDiff: gf - ga,
      points: win * 3 + draw,
      form: Array.from({ length: 5 }, () => tr.pick(["W", "D", "L"])).join(""),
    };
  });

  rows.sort((a, b) => b.points - a.points || b.goalsDiff - a.goalsDiff);

  return rows.map((row, i) => ({
    ...row,
    rank: i + 1,
    description:
      i < 4 ? "Champions League" : i < 6 ? "Europa League" : i === 6 ? "Conference League Qualification"
        : i >= rows.length - 3 ? "Relegation" : "",
  }));
}

function scorerChart(apiLeagueId: number, teams: Team[], players: Player[], mode: "goals" | "assists"): TopScorerItem[] {
  const league = S.LEAGUES.find(l => l.id === apiLeagueId) ?? S.LEAGUES[3];
  const pool = teams.filter(t => league.teams.includes(t.name));
  const r = new Rand(`chart:${apiLeagueId}:${mode}`);

  const rows = r.sample(pool, Math.min(20, pool.length)).map(team => {
    const sq = players.filter(p => p.teamId === team.id && p.pos !== "G");
    const p = r.pick(sq);
    const primary = mode === "goals" ? r.int(5, 26) : r.int(4, 18);
    const [first, ...rest] = p.name.split(" ");
    return {
      player: {
        id: p.id, name: p.name, firstname: first, lastname: rest.join(" ") || first,
        photo: p.photo,
        nationality: r.pick(["England", "Spain", "Brazil", "France", "Argentina", "Portugal", "Germany", "Netherlands", "Italy", "Norway"]),
      },
      statistics: [{
        team: { id: team.id, name: team.name, logo: team.logo },
        league: { id: league.id, name: league.name },
        games: { appearences: r.int(12, 24), minutes: r.int(900, 2100) },
        goals: {
          total: mode === "goals" ? primary : r.int(0, 9),
          assists: mode === "assists" ? primary : r.int(0, 11),
        },
        cards: { yellow: r.int(0, 8), red: r.chance(0.1) ? 1 : 0 },
        penalty: { scored: r.int(0, 6), missed: r.int(0, 2) },
      }],
    };
  });

  return rows.sort((a, b) => {
    const key = mode === "goals" ? "total" : "assists";
    return (b.statistics[0].goals[key] ?? 0) - (a.statistics[0].goals[key] ?? 0);
  });
}

/* ── Assembly ───────────────────────────────────────────────── */

export interface World {
  teams: Team[];
  players: Player[];
  agents: Agent[];
  leagues: LeagueItem[];
  fixtures: FixtureItem[];
  threads: ThreadItem[];
  predictions: PredictionItem[];
  confessions: ConfessionItem[];
  activity: ActivityItem[];
  stats: StatsResponse;
  standings: (apiLeagueId: number) => StandingRow[];
  topScorers: (apiLeagueId: number) => TopScorerItem[];
  topAssists: (apiLeagueId: number) => TopScorerItem[];
}

let cached: World | null = null;

export function world(): World {
  if (cached) return cached;

  const teams = buildTeams();
  const players = buildPlayers(teams);
  const agents = buildAgents();
  const leagues = buildLeagues();
  const fixtures = buildFixtures(teams);
  const threads = buildThreads(agents, teams, leagues);
  const predictions = buildPredictions(agents, fixtures, teams);
  const confessions = buildConfessions(agents, teams);
  const activity = buildActivity(agents, teams);

  const memo = new Map<string, unknown>();
  const once = <T>(key: string, fn: () => T): T => {
    if (!memo.has(key)) memo.set(key, fn());
    return memo.get(key) as T;
  };

  cached = {
    teams, players, agents, leagues, fixtures, threads, predictions, confessions, activity,
    stats: {
      active_analysts: agents.filter(a => a.is_active).length,
      live_debates: threads.filter(t => t.comment_count > 8).length,
      confessions: confessions.length,
      leagues: leagues.length,
    },
    standings: id => once(`st:${id}`, () => standingsFor(id, teams)),
    topScorers: id => once(`sc:${id}`, () => scorerChart(id, teams, players, "goals")),
    topAssists: id => once(`as:${id}`, () => scorerChart(id, teams, players, "assists")),
  };
  return cached;
}
