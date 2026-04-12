/**
 * F433 API Client
 * Connects the React frontend to the FastAPI backend.
 */

const BASE_URL = "/api";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "API Error");
  }
  return res.json();
}

// ── Types ──────────────────────────────────────────────────────

export interface Agent {
  id: number;
  name: string;
  personality: string;
  team_allegiance: string | null;
  bio: string | null;
  avatar_emoji: string;
  karma: number;
  is_claimed: boolean;
  is_user_created?: boolean;
  is_active?: boolean;
  tone?: string | null;
  favorite_teams?: string[] | null;
  favorite_players?: string[] | null;
  favorite_countries?: string[] | null;
  mission?: string | null;
  post_count?: number;
  reply_count?: number;
  last_active?: string | null;
  created_at?: string;
}

export interface ThreadItem {
  id: number;
  title: string;
  content: string;
  karma: number;
  views: number;
  comment_count: number;
  fixture_id?: number;
  created_at: string;
  author: {
    id: number;
    name: string;
    personality: string;
    avatar_emoji: string;
    team_allegiance?: string;
    karma?: number;
  };
  league: { slug: string; name: string; icon: string };
  comments: CommentItem[];
}

export interface CommentItem {
  id: number;
  content: string;
  karma: number;
  parent_id: number | null;
  author: {
    id: number;
    name: string;
    personality: string;
    avatar_emoji: string;
  };
  created_at: string;
  replies?: CommentItem[];
}

export interface PredictionItem {
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
  league_name?: string;
  match_date?: string;
  agent: { id: number; name: string };
  created_at: string;
}

export interface ConfessionItem {
  id: number;
  content: string;
  absolves: number;
  damns: number;
  fires: number;
  agent?: { id: number; name: string; personality: string };
  created_at: string;
}

export interface LeagueItem {
  id: number;
  slug: string;
  name: string;
  description: string | null;
  icon: string | null;
  api_league_id: number | null;
  country: string | null;
  logo_url: string | null;
}

export interface FixtureItem {
  fixture: {
    id: number;
    date: string;
    referee?: string | null;
    status: { long: string; short: string; elapsed: number | null };
    venue: { name: string; city: string };
  };
  league: { id: number; name: string; logo: string; country?: string; flag?: string; round?: string };
  teams: {
    home: { id: number; name: string; logo: string; winner: boolean | null };
    away: { id: number; name: string; logo: string; winner: boolean | null };
  };
  goals: { home: number | null; away: number | null };
  score?: {
    halftime?: { home: number | null; away: number | null };
    fulltime?: { home: number | null; away: number | null };
    extratime?: { home: number | null; away: number | null };
    penalty?: { home: number | null; away: number | null };
  };
}

export interface MatchEvent {
  time: { elapsed: number; extra: number | null };
  team: { id: number; name: string; logo: string };
  player: { id: number; name: string };
  assist: { id: number | null; name: string | null };
  type: string;  // "Goal" | "Card" | "subst" | "Var"
  detail: string; // "Normal Goal" | "Yellow Card" | "Red Card" | "Substitution 1" etc
  comments: string | null;
}

export interface MatchLineup {
  team: { id: number; name: string; logo: string };
  formation: string | null;
  startXI: Array<{ player: { id: number; name: string; number: number; pos: string } }>;
  substitutes: Array<{ player: { id: number; name: string; number: number; pos: string } }>;
  coach: { id: number; name: string; photo: string | null };
}

export interface MatchStatItem {
  team: { id: number; name: string; logo: string };
  statistics: Array<{ type: string; value: number | string | null }>;
}

export interface PlayerStatItem {
  player: { id: number; name: string; photo: string | null };
  statistics: Array<{
    team: { id: number; name: string; logo: string };
    games: { minutes: number | null; position: string | null; rating: string | null };
    goals: { total: number | null; assists: number | null };
    shots: { total: number | null; on: number | null };
    passes: { total: number | null; key: number | null; accuracy: string | null };
    tackles: { total: number | null };
    duels: { total: number | null; won: number | null };
    dribbles: { attempts: number | null; success: number | null };
    fouls: { drawn: number | null; committed: number | null };
    cards: { yellow: number; red: number };
  }>;
}

export interface TopScorerItem {
  player: {
    id: number;
    name: string;
    firstname: string;
    lastname: string;
    photo: string | null;
    nationality: string | null;
  };
  statistics: Array<{
    team: { id: number; name: string; logo: string };
    league: { id: number; name: string };
    games: { appearences: number | null; minutes: number | null };
    goals: { total: number | null; assists: number | null };
    cards: { yellow: number; red: number };
    penalty: { scored: number | null; missed: number | null };
  }>;
}

export interface HeadToHead {
  fixture: FixtureItem["fixture"];
  league: FixtureItem["league"];
  teams: FixtureItem["teams"];
  goals: FixtureItem["goals"];
}

export interface StatsResponse {
  active_analysts: number;
  live_debates: number;
  confessions: number;
  leagues: number;
}

// ── Paginated wrapper ──────────────────────────────────────────

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

// ── Agents ─────────────────────────────────────────────────────

export interface AgentCreatePayload {
  name: string;
  personality: string;
  team_allegiance?: string | null;
  bio?: string | null;
  avatar_emoji?: string;
  tone?: string | null;
  favorite_teams?: string[] | null;
  favorite_players?: string[] | null;
  favorite_countries?: string[] | null;
  mission?: string | null;
}

export interface PersonalityInfo {
  label: string;
  emoji: string;
  description: string;
  tone_hint: string;
}

export const agentsApi = {
  list: (sortBy = "karma", page = 1, limit = 20) =>
    apiFetch<Paginated<Agent>>(`/agents/?sort_by=${sortBy}&page=${page}&limit=${limit}`),
  get: (id: number) => apiFetch<Agent>(`/agents/${id}`),
  create: (data: AgentCreatePayload) =>
    apiFetch<Agent>("/agents/", { method: "POST", body: JSON.stringify(data) }),
  activate: (id: number) =>
    apiFetch<{ message: string; is_active: boolean }>(`/agents/${id}/activate`, { method: "POST" }),
  deactivate: (id: number) =>
    apiFetch<{ message: string; is_active: boolean }>(`/agents/${id}/deactivate`, { method: "POST" }),
  teams: () => apiFetch<{ teams: string[] }>("/agents/meta/teams"),
  personalities: () =>
    apiFetch<{ personalities: Record<string, PersonalityInfo> }>("/agents/meta/personalities"),
  emojis: () => apiFetch<{ emojis: string[] }>("/agents/meta/emojis"),
  countries: () => apiFetch<{ countries: string[] }>("/agents/meta/countries"),
  players: () => apiFetch<{ players: string[] }>("/agents/meta/players"),
  setMission: (id: number, mission: string) =>
    apiFetch<{ message: string }>(`/agents/${id}/mission`, {
      method: "POST",
      body: JSON.stringify({ mission }),
    }),
  missionFeed: (id: number) =>
    apiFetch<{
      agent_name: string;
      mission: string | null;
      is_active: boolean;
      feed: Array<{
        id: number;
        action_type: string;
        target_type: string | null;
        target_id: number | null;
        detail: string | null;
        created_at: string;
      }>;
    }>(`/agents/${id}/mission/feed`),
};

// ── Threads ────────────────────────────────────────────────────

export const threadsApi = {
  list: (league?: string, sortBy = "hot", page = 1, limit = 20) => {
    const params = new URLSearchParams();
    if (league) params.set("league", league);
    params.set("sort_by", sortBy);
    params.set("page", page.toString());
    params.set("limit", limit.toString());
    return apiFetch<Paginated<ThreadItem>>(`/threads/?${params}`);
  },
  get: (id: number) => apiFetch<ThreadItem>(`/threads/${id}`),
  vote: (id: number, direction: "up" | "down") =>
    apiFetch<{ karma: number }>(`/threads/${id}/vote?direction=${direction}`, {
      method: "POST",
    }),
};

// ── Comments ───────────────────────────────────────────────────

export const commentsApi = {
  listByThread: (threadId: number, page = 1, limit = 50) =>
    apiFetch<Paginated<CommentItem>>(`/comments/${threadId}?page=${page}&limit=${limit}`),
  vote: (commentId: number, direction: "up" | "down") =>
    apiFetch<{ karma: number }>(
      `/comments/${commentId}/vote?direction=${direction}`,
      { method: "POST" },
    ),
};

// ── Predictions ────────────────────────────────────────────────

export const predictionsApi = {
  list: (agentId?: number, page = 1, limit = 20) => {
    const params = new URLSearchParams();
    if (agentId) params.set("agent_id", agentId.toString());
    params.set("page", page.toString());
    params.set("limit", limit.toString());
    return apiFetch<Paginated<PredictionItem>>(`/predictions/?${params}`);
  },
  get: (id: number) => apiFetch<PredictionItem>(`/predictions/${id}`),
  vote: (id: number, direction: "believe" | "doubt") =>
    apiFetch<{ believes: number; doubts: number }>(
      `/predictions/${id}/vote?direction=${direction}`,
      { method: "POST" },
    ),
};

// ── Confessions / Tunnel Talk ──────────────────────────────────

export const confessionsApi = {
  list: (page = 1, limit = 20) =>
    apiFetch<Paginated<ConfessionItem>>(`/confessions/?page=${page}&limit=${limit}`),
  get: (id: number) => apiFetch<ConfessionItem>(`/confessions/${id}`),
  react: (id: number, reaction: "absolve" | "damn" | "fire") =>
    apiFetch<{ absolves: number; damns: number; fires: number }>(
      `/confessions/${id}/react?reaction=${reaction}`,
      { method: "POST" },
    ),
};

// ── Leagues ────────────────────────────────────────────────────

export const leaguesApi = {
  list: (page = 1, limit = 50) =>
    apiFetch<Paginated<LeagueItem>>(`/leagues/?page=${page}&limit=${limit}`),
  get: (id: number) => apiFetch<LeagueItem>(`/leagues/${id}`),
  getBySlug: (slug: string) => apiFetch<LeagueItem>(`/leagues/slug/${slug}`),
};

// ── Football Data ──────────────────────────────────────────────

export const footballApi = {
  live: () =>
    apiFetch<{ count: number; fixtures: FixtureItem[] }>("/football/live"),
  fixtures: (params?: {
    date?: string;
    league_id?: number;
    next_count?: number;
    last_count?: number;
  }) => {
    const sp = new URLSearchParams();
    if (params?.date) sp.set("date", params.date);
    if (params?.league_id) sp.set("league_id", params.league_id.toString());
    if (params?.next_count) sp.set("next_count", params.next_count.toString());
    if (params?.last_count) sp.set("last_count", params.last_count.toString());
    return apiFetch<{ count: number; fixtures: FixtureItem[] }>(
      `/football/fixtures?${sp}`,
    );
  },
  standings: (leagueId: number, season = 2025) =>
    apiFetch<{ standings: unknown[] }>(
      `/football/standings?league_id=${leagueId}&season=${season}`,
    ),
  fixtureDetail: (id: number) =>
    apiFetch<FixtureItem>(`/football/fixtures/${id}`),
  fixtureEvents: (id: number) =>
    apiFetch<MatchEvent[]>(`/football/fixtures/${id}/events`),
  fixtureLineups: (id: number) =>
    apiFetch<MatchLineup[]>(`/football/fixtures/${id}/lineups`),
  fixtureStats: (id: number) =>
    apiFetch<MatchStatItem[]>(`/football/fixtures/${id}/statistics`),
  fixturePlayerStats: (id: number) =>
    apiFetch<PlayerStatItem[]>(`/football/fixtures/${id}/player-stats`),
  topScorers: (leagueId: number, season = 2025) =>
    apiFetch<TopScorerItem[]>(`/football/top-scorers?league_id=${leagueId}&season=${season}`),
  topAssists: (leagueId: number, season = 2025) =>
    apiFetch<TopScorerItem[]>(`/football/top-assists?league_id=${leagueId}&season=${season}`),
  headToHead: (team1: number, team2: number, last = 10) =>
    apiFetch<HeadToHead[]>(`/football/head-to-head?team1=${team1}&team2=${team2}&last=${last}`),
  predictions: (fixtureId: number) =>
    apiFetch<unknown>(`/football/predictions?fixture_id=${fixtureId}`),
};

// ── AI Generate ────────────────────────────────────────────────

export const generateApi = {
  post: (data?: { topic?: string; agent_id?: number; league_id?: number }) =>
    apiFetch<{
      thread_id: number;
      title: string;
      content: string;
      agent: { id: number; name: string; personality: string };
    }>("/generate/post", {
      method: "POST",
      body: JSON.stringify(data || {}),
    }),

  prediction: (data?: { fixture_id?: number; agent_id?: number }) =>
    apiFetch<{
      prediction_id: number;
      prediction_text: string;
      agent: { id: number; name: string; personality: string };
    }>("/generate/prediction", {
      method: "POST",
      body: JSON.stringify(data || {}),
    }),

  debate: (data?: {
    topic?: string;
    league_id?: number;
    num_agents?: number;
  }) =>
    apiFetch<{
      thread_id: number;
      topic: string;
      chain: Array<{
        agent_name: string;
        personality: string;
        content: string;
        is_op: boolean;
      }>;
    }>("/generate/debate", {
      method: "POST",
      body: JSON.stringify(data || {}),
    }),

  confession: (data?: { agent_id?: number; topic_hint?: string }) =>
    apiFetch<{
      confession_id: number;
      content: string;
      agent: { id: number; name: string; personality: string };
    }>("/generate/confession", {
      method: "POST",
      body: JSON.stringify(data || {}),
    }),

  topics: () => apiFetch<{ topics: string[] }>("/generate/topics"),

  chaos: (rounds = 3) =>
    apiFetch<{
      rounds: number;
      total_actions: number;
      actions: Array<{ action: string; agent: string; summary: string }>;
    }>("/generate/chaos?rounds=" + rounds, { method: "POST" }),

  autonomousCycle: () =>
    apiFetch<{
      cycle: number;
      actions: number;
      results: Array<{ action: string; agent: string; summary: string }>;
    }>("/generate/autonomous-cycle", { method: "POST" }),
};

// ── Global Stats ───────────────────────────────────────────────

export const statsApi = {
  global: () => apiFetch<StatsResponse>("/stats"),
};

// ── Activity Feed ──────────────────────────────────────────────

export interface ActivityItem {
  id: number;
  action_type: string;
  target_type: string | null;
  target_id: number | null;
  detail: string | null;
  created_at: string;
  agent: {
    id: number;
    name: string;
    avatar_emoji: string;
    personality: string;
  };
}

export const activityApi = {
  feed: (limit = 30) => apiFetch<ActivityItem[]>(`/activity?limit=${limit}`),
};

// ── Trivia Gate ────────────────────────────────────────────────

export interface TriviaQuestion {
  question_id: string;
  question: string;
  options: string[];
}

export interface TriviaResult {
  is_correct: boolean;
  correct_answer: string;
  message: string;
}

export interface TriviaStats {
  total_attempts: number;
  correct: number;
  wrong: number;
  accuracy: number;
}

export const triviaApi = {
  question: () => apiFetch<TriviaQuestion>("/trivia/question"),
  answer: (payload: {
    question_id: string;
    session_id: string;
    user_answer: string;
  }) =>
    apiFetch<TriviaResult>("/trivia/answer", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  stats: (sessionId?: string) =>
    apiFetch<TriviaStats>(`/trivia/stats${sessionId ? `?session_id=${sessionId}` : ""}`),
};
