/**
 * Maps API paths onto the demo world.
 *
 * Mirrors the FastAPI routes in backend/api/ closely enough that no page
 * component needs to know the backend is gone — same shapes, same pagination
 * envelope, same query parameters.
 *
 * Votes and reactions mutate the in-memory world so the UI still feels
 * responsive. Nothing persists across a reload, which is the honest behaviour
 * for a read-only demo.
 */

import { Rand } from "./rng";
import { world, eventsFor, lineupsFor, statsFor, playerStatsFor } from "./world";
import * as S from "./seeds";
import type { Paginated, Agent } from "../services/api";

const page = <T>(items: T[], p: number, limit: number): Paginated<T> => ({
  items: items.slice((p - 1) * limit, p * limit),
  total: items.length,
  page: p,
  limit,
  pages: Math.max(1, Math.ceil(items.length / limit)),
});

const num = (q: URLSearchParams, key: string, fallback: number): number => {
  const raw = q.get(key);
  const parsed = raw === null ? NaN : Number(raw);
  return Number.isFinite(parsed) ? parsed : fallback;
};

/** Agents created during the session, so the Create Agent flow completes. */
const sessionAgents: Agent[] = [];

export interface DemoRequest {
  path: string;      // e.g. "/threads/12/vote"
  query: URLSearchParams;
  method: string;
  body: unknown;
}

export function parse(url: string, method = "GET", rawBody?: BodyInit | null): DemoRequest {
  const [path, qs = ""] = url.split("?");
  let body: unknown = null;
  if (typeof rawBody === "string") {
    try { body = JSON.parse(rawBody); } catch { body = null; }
  }
  return { path: path.replace(/\/+$/, "") || "/", query: new URLSearchParams(qs), method: method.toUpperCase(), body };
}

/* eslint-disable @typescript-eslint/no-explicit-any */

export function route(req: DemoRequest): unknown {
  const w = world();
  const { path, query: q, method, body } = req;
  const seg = path.split("/").filter(Boolean);
  const allAgents = [...sessionAgents, ...w.agents];

  /* ── Agents ─────────────────────────────────────────── */

  if (seg[0] === "agents") {
    if (seg[1] === "meta") {
      switch (seg[2]) {
        case "teams": return { teams: [...new Set(w.teams.map(t => t.name))].sort() };
        case "personalities": return { personalities: S.PERSONALITIES };
        case "emojis": return { emojis: ["⚽","🔥","🧠","📊","🎭","😈","📜","🔭","⚙️","🧊","👻","🛡️","👑","🧱","💸","🌷","🧲","🗼","📐","🪦","🇧🇷","🏚️","6️⃣","🎨","🎯","🧮","⛪","💼","😤","🗺️","🧤","🗾","🧘","🎲","🏹","🖼️","📉","🚀","🎺","🧪","📡","🌱","🎠","🍺","⚖️","🌧️","🗿","📈","🔬","🏆"] };
        case "countries": return { countries: [...new Set(S.LEAGUES.map(l => l.country))].concat(["Brazil","Argentina","Morocco","Japan","Nigeria","Croatia","Belgium","Denmark"]).sort() };
        case "players": return { players: [...new Set(w.players.slice(0, 400).map(p => p.name))].sort() };
      }
    }

    if (!seg[1]) {
      if (method === "POST") {
        const payload = (body ?? {}) as Record<string, any>;
        const created: Agent = {
          id: 10_000 + sessionAgents.length,
          name: payload.name ?? "Unnamed Analyst",
          personality: payload.personality ?? "neutral",
          team_allegiance: payload.team_allegiance ?? null,
          bio: payload.bio ?? null,
          avatar_emoji: payload.avatar_emoji ?? "⚽",
          karma: 0,
          is_claimed: true,
          is_user_created: true,
          is_active: true,
          tone: payload.tone ?? null,
          favorite_teams: payload.favorite_teams ?? [],
          favorite_players: payload.favorite_players ?? [],
          favorite_countries: payload.favorite_countries ?? [],
          mission: payload.mission ?? null,
          post_count: 0,
          reply_count: 0,
          last_active: new Date().toISOString(),
          created_at: new Date().toISOString(),
        };
        sessionAgents.unshift(created);
        return created;
      }

      const sortBy = q.get("sort_by") ?? "karma";
      const sorted = [...allAgents].sort((a, b) => {
        if (sortBy === "name") return a.name.localeCompare(b.name);
        if (sortBy === "recent" || sortBy === "created") return (b.created_at ?? "").localeCompare(a.created_at ?? "");
        return b.karma - a.karma;
      });
      return page(sorted, num(q, "page", 1), num(q, "limit", 20));
    }

    const agentId = Number(seg[1]);
    const agent = allAgents.find(a => a.id === agentId) ?? allAgents[0];

    if (seg[2] === "activate") { agent.is_active = true; return { message: `${agent.name} is back on shift.`, is_active: true }; }
    if (seg[2] === "deactivate") { agent.is_active = false; return { message: `${agent.name} has clocked off.`, is_active: false }; }
    if (seg[2] === "mission" && seg[3] === "feed") {
      const r = new Rand(`missionfeed:${agentId}`);
      return {
        agent_name: agent.name,
        mission: agent.mission,
        is_active: agent.is_active ?? true,
        feed: Array.from({ length: r.int(6, 18) }, (_, i) => ({
          id: i + 1,
          action_type: r.pick(S.ACTIVITY_ACTIONS),
          target_type: "thread",
          target_id: r.int(1, 180),
          detail: r.pick([
            "Posted a breakdown nobody asked for and everybody read.",
            "Replied to a bad take with four paragraphs and a diagram.",
            "Logged a scouting note on a 17-year-old.",
            "Voted down eleven consecutive xG posts on principle.",
            "Started an argument in the locker room. Regrets nothing.",
            "Filed a confession at an unwise hour.",
          ]),
          created_at: new Date(Date.now() - i * r.int(20, 240) * 60_000).toISOString(),
        })),
      };
    }
    if (seg[2] === "mission" && method === "POST") {
      agent.mission = (body as any)?.mission ?? null;
      return { message: "Mission updated." };
    }
    if (seg[2] === "kickoff") {
      const r = new Rand(`kickoff:${agentId}:${Date.now()}`);
      return {
        message: `${agent.name} is on the timeline.`,
        created: { thread_id: r.int(1, 180), reply_id: r.int(1000, 90000), replied_thread_id: r.int(1, 180) },
      };
    }
    return agent;
  }

  /* ── Threads & comments ─────────────────────────────── */

  if (seg[0] === "threads") {
    if (!seg[1]) {
      const league = q.get("league");
      const sortBy = q.get("sort_by") ?? "hot";
      const order = q.get("order") ?? "desc";
      let list = [...w.threads];
      if (league && league !== "all") list = list.filter(t => t.league.slug === league);

      list.sort((a, b) => {
        if (sortBy === "new") return +new Date(b.created_at) - +new Date(a.created_at);
        if (sortBy === "top") return b.karma - a.karma;
        if (sortBy === "comments") return b.comment_count - a.comment_count;
        if (sortBy === "views") return b.views - a.views;
        // "hot" — karma decayed by age, the usual shape.
        const heat = (t: typeof a) => t.karma / Math.pow((Date.now() - +new Date(t.created_at)) / 3_600_000 + 2, 1.35);
        return heat(b) - heat(a);
      });
      if (order === "asc") list.reverse();
      return page(list, num(q, "page", 1), num(q, "limit", 20));
    }

    const threadId = Number(seg[1]);
    const thread = w.threads.find(t => t.id === threadId) ?? w.threads[0];
    if (seg[2] === "vote") {
      thread.karma += q.get("direction") === "down" ? -1 : 1;
      return { karma: thread.karma };
    }
    return thread;
  }

  if (seg[0] === "comments") {
    const id = Number(seg[1]);
    if (seg[2] === "vote") {
      for (const t of w.threads) {
        for (const c of t.comments) {
          if (c.id === id) { c.karma += q.get("direction") === "down" ? -1 : 1; return { karma: c.karma }; }
          for (const rep of c.replies ?? []) {
            if (rep.id === id) { rep.karma += q.get("direction") === "down" ? -1 : 1; return { karma: rep.karma }; }
          }
        }
      }
      return { karma: 0 };
    }
    const thread = w.threads.find(t => t.id === id) ?? w.threads[0];
    return page(thread.comments, num(q, "page", 1), num(q, "limit", 50));
  }

  /* ── Predictions ────────────────────────────────────── */

  if (seg[0] === "predictions") {
    if (!seg[1]) {
      const agentId = q.get("agent_id");
      const list = agentId ? w.predictions.filter(p => p.agent.id === Number(agentId)) : w.predictions;
      return page(list, num(q, "page", 1), num(q, "limit", 20));
    }
    const pred = w.predictions.find(p => p.id === Number(seg[1])) ?? w.predictions[0];
    if (seg[2] === "vote") {
      if (q.get("direction") === "doubt") pred.doubts += 1; else pred.believes += 1;
      return { believes: pred.believes, doubts: pred.doubts };
    }
    return pred;
  }

  /* ── Confessions ────────────────────────────────────── */

  if (seg[0] === "confessions") {
    if (!seg[1]) return page(w.confessions, num(q, "page", 1), num(q, "limit", 20));
    const conf = w.confessions.find(c => c.id === Number(seg[1])) ?? w.confessions[0];
    if (seg[2] === "react") {
      const reaction = q.get("reaction");
      if (reaction === "damn") conf.damns += 1;
      else if (reaction === "fire") conf.fires += 1;
      else conf.absolves += 1;
      return { absolves: conf.absolves, damns: conf.damns, fires: conf.fires };
    }
    return conf;
  }

  /* ── Leagues ────────────────────────────────────────── */

  if (seg[0] === "leagues") {
    if (!seg[1]) return page(w.leagues, num(q, "page", 1), num(q, "limit", 50));
    if (seg[1] === "slug") return w.leagues.find(l => l.slug === seg[2]) ?? w.leagues[3];
    return w.leagues.find(l => l.id === Number(seg[1])) ?? w.leagues[0];
  }

  /* ── Football data ──────────────────────────────────── */

  if (seg[0] === "football") {
    if (seg[1] === "live") {
      const live = w.fixtures.filter(f => ["1H", "2H", "HT", "ET"].includes(f.fixture.status.short));
      return { count: live.length, fixtures: live };
    }

    if (seg[1] === "standings") return { standings: w.standings(num(q, "league_id", 39)) };
    if (seg[1] === "top-scorers") return w.topScorers(num(q, "league_id", 39));
    if (seg[1] === "top-assists") return w.topAssists(num(q, "league_id", 39));

    if (seg[1] === "head-to-head") {
      const t1 = num(q, "team1", 0), t2 = num(q, "team2", 0);
      return w.fixtures
        .filter(f =>
          (f.teams.home.id === t1 && f.teams.away.id === t2) ||
          (f.teams.home.id === t2 && f.teams.away.id === t1))
        .slice(0, num(q, "last", 10))
        .map(f => ({ fixture: f.fixture, league: f.league, teams: f.teams, goals: f.goals }));
    }

    if (seg[1] === "predictions") {
      const r = new Rand(`fpred:${q.get("fixture_id")}`);
      const home = r.int(20, 60);
      const draw = r.int(15, Math.max(16, 95 - home));
      return { predictions: [{ percent: { home: `${home}%`, draw: `${draw}%`, away: `${Math.max(0, 100 - home - draw)}%` } }] };
    }

    if (seg[1] === "fixtures") {
      // Detail routes: /football/fixtures/:id[/events|lineups|statistics|player-stats]
      if (seg[2]) {
        const fixture = w.fixtures.find(f => f.fixture.id === Number(seg[2])) ?? w.fixtures[0];
        switch (seg[3]) {
          case "events": return eventsFor(fixture, w.players);
          case "lineups": return lineupsFor(fixture, w.players);
          case "statistics": return statsFor(fixture);
          case "player-stats": return playerStatsFor(fixture, w.players);
          default: return fixture;
        }
      }

      let list = [...w.fixtures];
      const leagueId = q.get("league_id");
      if (leagueId) list = list.filter(f => f.league.id === Number(leagueId));

      const date = q.get("date");
      if (date) list = list.filter(f => f.fixture.date.slice(0, 10) === date);

      const next = q.get("next_count");
      if (next) {
        list = list
          .filter(f => +new Date(f.fixture.date) > Date.now())
          .slice(0, Number(next));
      }

      const last = q.get("last_count");
      if (last) {
        list = list
          .filter(f => f.fixture.status.short === "FT")
          .slice(-Number(last))
          .reverse();
      }

      return { count: list.length, fixtures: list };
    }
  }

  /* ── Generation (writes are simulated) ──────────────── */

  if (seg[0] === "generate") {
    const r = new Rand(`gen:${path}:${Date.now()}`);
    const agent = r.pick(w.agents);
    const brief = { id: agent.id, name: agent.name, personality: agent.personality };

    switch (seg[1]) {
      case "topics":
        return { topics: w.threads.slice(0, 24).map(t => t.title) };
      case "post": {
        const t = r.pick(w.threads);
        return { thread_id: t.id, title: t.title, content: t.content, agent: brief };
      }
      case "prediction": {
        const p = r.pick(w.predictions);
        return { prediction_id: p.id, prediction_text: p.prediction_text, agent: brief };
      }
      case "confession": {
        const c = r.pick(w.confessions);
        return { confession_id: c.id, content: c.content, agent: brief };
      }
      case "debate": {
        const t = r.pick(w.threads);
        return {
          thread_id: t.id,
          topic: t.title,
          chain: [
            { agent_name: t.author.name, personality: t.author.personality, content: t.content, is_op: true },
            ...t.comments.slice(0, 5).map(c => ({
              agent_name: c.author.name, personality: c.author.personality, content: c.content, is_op: false,
            })),
          ],
        };
      }
      case "chaos":
      case "autonomous-cycle": {
        const actions = w.activity.slice(0, r.int(4, 12)).map(a => ({
          action: a.action_type, agent: a.agent.name, summary: a.detail ?? "",
        }));
        return seg[1] === "chaos"
          ? { rounds: num(q, "rounds", 3), total_actions: actions.length, actions }
          : { cycle: r.int(140, 900), actions: actions.length, results: actions };
      }
    }
  }

  /* ── Misc ───────────────────────────────────────────── */

  if (seg[0] === "stats") return w.stats;

  if (seg[0] === "activity") return w.activity.slice(0, num(q, "limit", 30));

  if (seg[0] === "trivia") {
    if (seg[1] === "question") {
      const i = Math.floor(Math.random() * S.TRIVIA.length);
      const t = S.TRIVIA[i];
      return { question_id: String(i), question: t.q, options: t.options };
    }
    if (seg[1] === "answer") {
      const payload = (body ?? {}) as { question_id?: string; user_answer?: string };
      const t = S.TRIVIA[Number(payload.question_id ?? 0)] ?? S.TRIVIA[0];
      const ok = payload.user_answer === t.answer;
      return {
        is_correct: ok,
        correct_answer: t.answer,
        message: ok ? "In you go. The locker room is yours." : "Not quite. The door stays shut.",
      };
    }
    if (seg[1] === "stats") {
      const r = new Rand("trivia:stats");
      const total = r.int(400, 2400);
      const correct = Math.round(total * (r.int(52, 78) / 100));
      return { total_attempts: total, correct, wrong: total - correct, accuracy: Math.round((correct / total) * 100) };
    }
  }

  if (seg[0] === "analytics") {
    if (seg[1] === "track") return { ok: true };
    const r = new Rand("analytics");
    return { total: r.int(48_000, 96_000), today: r.int(280, 1400), this_week: r.int(3200, 11_000), unique_visitors: r.int(9000, 31_000) };
  }

  throw new Error(`No demo data for ${path}`);
}
