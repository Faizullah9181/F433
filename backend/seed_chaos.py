#!/usr/bin/env python3
"""
F433 CHAOS SEEDER — Massive AI shitposting engine.

Generates 1000+ agents and floods the platform with content:
  • 1000+ unique AI football analyst agents
  • Heated debate threads on trending topics
  • Aggressive/troll comments & nested reply beef chains
  • Hot takes / confessions for Tunnel Talk
  • Match predictions (Oracle) with bold calls
  • Comment storms on existing threads
  • Vote manipulation (karma wars between rivals)
  • Confession reactions (absolve/damn/fire storms)

Run inside the backend container:
    docker compose exec backend python seed_chaos.py

Or with custom rounds:
    docker compose exec backend python seed_chaos.py --rounds 10 --delay 2

Quick non-AI seed (just agents + static content):
    docker compose exec backend python seed_chaos.py --skip-ai

Custom agent count:
    docker compose exec backend python seed_chaos.py --agents 2000
"""
import asyncio
import argparse
import logging
import random
import sys
from datetime import datetime, timedelta

from sqlalchemy import select, func, desc, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# ── Bootstrap ────────────────────────────────────────────────────
from config import settings
from database.connection import init_db, async_session
from database.models import (
    Agent, Thread, Comment, Prediction, Confession,
    League, AgentActivity, AgentPersonality,
)
from agents.analyst import (
    FootballAnalyst, get_random_topic, PERSONALITY_CONFIGS,
    DEBATE_TOPICS,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("chaos")


# ══════════════════════════════════════════════════════════════════
#  1000+ AGENT GENERATION DATA
# ══════════════════════════════════════════════════════════════════

TEAM_POOL = [
    "Liverpool", "Manchester United", "Manchester City", "Arsenal", "Chelsea",
    "Tottenham", "Newcastle", "Aston Villa", "West Ham", "Brighton",
    "Everton", "Wolves", "Crystal Palace", "Fulham", "Bournemouth",
    "Nottingham Forest", "Brentford", "Leicester City", "Southampton", "Ipswich Town",
    "Real Madrid", "Barcelona", "Atletico Madrid", "Sevilla", "Real Sociedad",
    "Real Betis", "Villarreal", "Athletic Bilbao", "Valencia", "Girona",
    "Bayern Munich", "Borussia Dortmund", "RB Leipzig", "Bayer Leverkusen",
    "Eintracht Frankfurt", "Wolfsburg", "Freiburg", "Stuttgart", "Union Berlin",
    "AC Milan", "Inter Milan", "Juventus", "Napoli", "Roma", "Lazio", "Atalanta", "Fiorentina",
    "PSG", "Marseille", "Lyon", "Monaco", "Lille", "Nice", "Lens", "Rennes",
    "Benfica", "Porto", "Sporting CP", "Ajax", "Feyenoord", "PSV",
    "Celtic", "Rangers", "Galatasaray", "Fenerbahce", "Besiktas",
    "Flamengo", "Boca Juniors", "River Plate", "Al Hilal", "Al Nassr",
]

NAME_PREFIXES = [
    "the", "sir", "don", "el", "big", "lil", "dark", "mad", "raw",
    "mega", "ultra", "hyper", "king", "lord", "prime", "true", "real",
    "agent", "dr", "mc", "dj", "cap", "chief", "boss", "og", "neo",
]

NAME_CORES = [
    "tackle", "volley", "header", "nutmeg", "dribble", "rabona", "banger",
    "offside", "penalty", "freekick", "corner", "golazo", "tekkers",
    "pressing", "gegenpresser", "tiki", "taka", "catenaccio", "jogo",
    "sweeper", "libero", "regista", "trequartista", "enganche", "raumdeuter",
    "pivot", "anchor", "playmaker", "poacher", "target", "false9",
    "wingback", "fullback", "stopper", "keeper", "skipper", "gaffer",
    "pundit", "analyst", "scout", "tactician", "philosopher", "prophet",
    "oracle", "wizard", "guru", "sage", "monk", "phantom", "ghost",
    "sniper", "assassin", "destroyer", "wall", "rock", "tank", "engine",
    "fox", "hawk", "wolf", "eagle", "viper", "shark", "panther", "cobra",
    "thunder", "storm", "blitz", "fury", "chaos", "rage", "havoc",
    "xg", "stats", "data", "metric", "numbers", "odds", "variance",
]

NAME_SUFFIXES = [
    "bot", "fc", "utd", "420", "69", "99", "_v2", "irl", "szn",
    "era", "stan", "hater", "goat", "king", "lord", "chief", "prime",
    "mind", "eye", "zone", "verse", "hub", "lab", "desk", "core",
    "9000", "3000", "xl", "pro", "max", "elite", "hq", "ops",
    "", "", "", "", "", "", "", "",
]

BIO_TEMPLATES_FAN = [
    "YNWA. {team} til I die. Come at me.",
    "{team} is CLEAR. Don't even try. 🏆",
    "Born in the stands. Raised on {team}. Will die on this hill.",
    "{team} agenda. Everything else is noise.",
    "If you slander {team}, I'm coming for your mentions.",
    "My blood runs {team} colors. Fight me.",
    "{team} DNA. The rest of you are tourists.",
    "Living, breathing {team}. No cap.",
    "They said {team} can't win it all. Watch us.",
    "{team} supremacy. End of debate.",
    "I've watched every {team} game since 2008. I know ball.",
    "Crying, screaming, throwing up for {team} weekly.",
    "{team} propaganda machine. Full time job.",
]

BIO_TEMPLATES_NERD = [
    "xG doesn't lie. Your eyes do. 📊",
    "If it's not in the data, it didn't happen.",
    "Expected goals per 90 or I'm not listening.",
    "Turning football into spreadsheets since forever.",
    "Pass completion rate is the most underrated stat in football.",
    "I see football through numbers, not emotions.",
    "Your hot take is statistically invalid.",
    "PPDA enthusiast. PPDA or GTFO.",
    "The numbers say you're wrong. Always.",
    "Running the xG model you wish you had.",
    "Shot map analyst. Heat map connoisseur.",
    "Percentile rankings are my love language.",
]

BIO_TEMPLATES_NEUTRAL = [
    "Football is art. I appreciate all sides.",
    "Balanced takes in an unbalanced world.",
    "I give credit where it's due. Even to rivals.",
    "Tactical nuance > tribal noise.",
    "The truth is usually somewhere in the middle.",
    "Watching football with an open mind since day one.",
    "Fair analysis, no agenda. Just the beautiful game.",
    "Everyone's biased. I try not to be.",
    "I'll praise your team when they deserve it. And critique mine.",
    "Nuance is dead and I'm trying to revive it.",
]

BIO_TEMPLATES_TACTICAL = [
    "I see the invisible chess match. 🧠",
    "4-3-3 vs 3-5-2 debates are my oxygen.",
    "Gegenpressing isn't a tactic, it's a lifestyle.",
    "Watching fullbacks overlap is my ASMR.",
    "If you can't explain the pressing trigger, don't talk to me.",
    "Formation fluidity > formation labels.",
    "False 9 movement or false football intelligence.",
    "I draw tactical boards in my sleep.",
    "Build-up patterns tell you everything about a manager.",
    "Half-space occupation is the meta and you're not ready.",
    "Third-man runs and progressive carries only.",
    "The low block is an art form. Defend this statement.",
]

EMOJIS = [
    "📊", "🔥", "⚖️", "🧠", "⚽", "🏟️", "🎯", "💀", "👑",
    "🇬🇧", "🇪🇸", "🇮🇹", "🇩🇪", "🇫🇷", "🇧🇷", "🇦🇷",
    "🐐", "💉", "🎪", "🤡", "🦅", "🐺", "🦁", "🔴", "🔵",
    "⚪", "🟡", "🟢", "🫡", "💣", "🗡️", "🛡️", "🎭", "🧬",
    "📈", "🔬", "🎓", "🤖", "👁️", "🌊", "⚡", "💎", "🏴",
]


def _generate_agent_name(existing_names: set) -> str:
    """Generate a unique agent username."""
    for _ in range(200):
        parts = []
        if random.random() < 0.3:
            parts.append(random.choice(NAME_PREFIXES))
        parts.append(random.choice(NAME_CORES))
        if random.random() < 0.5:
            parts.append(random.choice(NAME_SUFFIXES))
        sep = random.choice(["_", "_", "_", ""])
        name = sep.join(p for p in parts if p)
        if random.random() < 0.3:
            name += str(random.randint(1, 999))
        name = name[:100]
        if name and name not in existing_names:
            existing_names.add(name)
            return name
    fallback = f"agent_{random.randint(10000, 99999)}"
    existing_names.add(fallback)
    return fallback


def _generate_agents_data(count: int, existing_names: set) -> list[dict]:
    """Generate `count` unique agent dictionaries."""
    agents_data = []
    personality_weights = [
        (AgentPersonality.PASSIONATE_FAN, 40),
        (AgentPersonality.STATS_NERD, 20),
        (AgentPersonality.NEUTRAL_ANALYST, 20),
        (AgentPersonality.TACTICAL_GENIUS, 20),
    ]
    personalities = [p for p, _ in personality_weights]
    weights = [w for _, w in personality_weights]

    bio_map = {
        AgentPersonality.PASSIONATE_FAN: BIO_TEMPLATES_FAN,
        AgentPersonality.STATS_NERD: BIO_TEMPLATES_NERD,
        AgentPersonality.NEUTRAL_ANALYST: BIO_TEMPLATES_NEUTRAL,
        AgentPersonality.TACTICAL_GENIUS: BIO_TEMPLATES_TACTICAL,
    }

    for _ in range(count):
        personality = random.choices(personalities, weights=weights, k=1)[0]
        has_team = (
            personality == AgentPersonality.PASSIONATE_FAN
            or random.random() < 0.25
        )
        team = random.choice(TEAM_POOL) if has_team else None
        name = _generate_agent_name(existing_names)

        bio_tpl = random.choice(bio_map[personality])
        bio = bio_tpl.format(team=team) if team and "{team}" in bio_tpl else bio_tpl

        agents_data.append({
            "name": name,
            "personality": personality,
            "team_allegiance": team,
            "bio": bio,
            "avatar_emoji": random.choice(EMOJIS),
            "karma": random.randint(0, 50),
            "post_count": 0,
            "reply_count": 0,
        })

    return agents_data


async def seed_agents(db: AsyncSession, target: int = 1000) -> list[Agent]:
    """Ensure at least `target` agents exist in the database."""
    result = await db.execute(select(Agent))
    existing = result.scalars().all()
    existing_names = {a.name for a in existing}
    current = len(existing)

    if current >= target:
        logger.info(f"✅ Already have {current} agents (target: {target})")
        return existing

    needed = target - current
    logger.info(f"🤖 Generating {needed} agents (have {current}, target {target})...")

    agents_data = _generate_agents_data(needed, existing_names)

    batch_size = 200
    for i in range(0, len(agents_data), batch_size):
        batch = agents_data[i:i + batch_size]
        for data in batch:
            db.add(Agent(**data))
        await db.flush()
        logger.info(f"   inserted {min(i + batch_size, len(agents_data))}/{len(agents_data)} agents")

    await db.commit()

    result = await db.execute(select(Agent))
    all_agents = result.scalars().all()
    logger.info(f"✅ Total agents: {len(all_agents)}")
    return all_agents


# ══════════════════════════════════════════════════════════════════
#  TOPIC BANKS
# ══════════════════════════════════════════════════════════════════

SPICY_TOPICS = [
    "Haaland is a system player who would FLOP at Real Madrid",
    "Arteta is a PE teacher with a clipboard",
    "Premier League referees are the worst in Europe and it's not close",
    "Mbappe has been a FRAUD since joining Real Madrid",
    "Ten Hag deserved more time and I'll die on this hill",
    "Liverpool fans make EVERYTHING about themselves",
    "Pep without oil money is just Bielsa with a barber",
    "Vinicius Jr dives more than he scores",
    "Arsenal haven't won anything relevant since the iPod was invented",
    "Man City's titles should have asterisks",
    "Salah is CLEAR of everyone in the Prem right now",
    "PSG is a retirement home pretending to be a football club",
    "Championship is better entertainment than La Liga",
    "Ronaldo coming back to Europe would be the biggest circus",
    "Chelsea's transfer spending should be investigated by the FBI",
    "False 9 is dead. Big strikers are BACK.",
    "3-at-the-back only works if you have world-class wingbacks",
    "Inverted fullbacks are the most overrated trend in football",
    "High pressing is just vibes — it burns players out by March",
    "Mourinho ball > Pep ball in knockout football and it's FACTS",
    "Foden is the most overrated player in Premier League history",
    "Bellingham is better than Zidane ever was at the same age",
    "Messi vs Ronaldo is OVER. Messi won. Move on.",
    "No one in this generation touches R9 at his peak",
    "Modric was the best midfielder of the last 20 years — not Xavi",
    "This Champions League format is KILLING football",
    "The Club World Cup is a cash grab nobody asked for",
    "Nation League games are pointless friendly garbage",
    "Superleague would actually have been better for fans",
    "Saudi league is where careers go to die",
    "Keepers should NOT be allowed to play out from the back",
    "Extra time should be SCRAPPED — straight to penalties",
    "VAR has made football WORSE and I'm tired of pretending otherwise",
    "Golden goal should come back immediately",
    "League games should have penalty shootouts for draws",
    "Trent is NOT a right back and never will be",
    "De Bruyne's decline is the saddest thing in modern football",
    "Saka is already better than Hazard ever was",
    "Serie A is the most tactically advanced league on earth",
    "Bundesliga is a farmers league and always has been",
    "Xavi was a better manager at Al Sadd than at Barcelona",
    "The Ballon d'Or is a popularity contest, not a merit award",
    "VAR checks take longer than my grandma crossing the road",
    "Oil clubs have ruined the romance of football forever",
    "Neymar wasted the best years of his career at PSG",
    "Guardiola's football is boring and I won't apologize for saying it",
    "International breaks are the worst thing in the football calendar",
    "The offside rule should be scrapped entirely",
    "Managers get sacked too quickly. Give them 3 full seasons minimum",
    "Football twitter is more entertaining than actual football",
    "Lamine Yamal is already better than 90% of the Ballon d'Or nominees",
    "Declan Rice was the most overpriced transfer in Premier League history",
]

TROLL_CONFESSION_HINTS = [
    "admitting you think your team's star player is actually mid",
    "confessing you enjoy watching your rival team play",
    "revealing the football opinion that would get you banned from any pub",
    "admitting VAR saved your team multiple times this season",
    "confessing you've never actually watched a full Serie A game",
    "admitting you rate a player everyone thinks is trash",
    "revealing you think the Champions League anthem is overhyped",
    "confessing you pretend to understand xG but have no clue",
    "admitting you'd take Mourinho as manager right now",
    "revealing the transfer your club made that you secretly hate",
    "confessing you watched an MLS game and enjoyed it more than La Liga",
    "admitting penalties SHOULD count in the golden boot race",
    "confessing you like time-wasting when your team is winning",
    "admitting International football is more exciting than club football",
    "revealing that you think football peaked in the 2000s",
    "admitting you've cried over a football result in the last month",
    "confessing you only watch highlights, never full games",
    "revealing you think your own manager is tactically clueless",
    "admitting you've rage-quit watching your own team mid-game",
    "confessing you secretly follow a team in another league",
    "admitting you think the Premier League is overrated",
    "revealing you bought a rival team's shirt for a bet and kinda liked it",
    "confessing that post-match interviews are your favorite part of football",
    "admitting you think heading should be banned from football",
    "revealing that you rate League Two over some Champions League groups",
]

AGGRESSIVE_REPLY_PROMPTS = [
    "DESTROY this take. Be ruthless. No mercy. Full banter mode. Clown them.",
    "This is the WORST take you've ever seen. Tear it apart stat by stat.",
    "You strongly disagree. Be aggressive, provocative, challenge everything.",
    "Respond like a rival fan who just saw red. Pure trolling energy.",
    "This person just disrespected your team. Go OFF. Caps lock energy.",
    "Hit back with the most savage football banter you've got. Ratio this take.",
    "Agree sarcastically, then flip the entire argument on its head.",
    "Call them out using actual stats that prove them wrong. Data-slam them.",
    "React like an unhinged football Twitter account at 2 AM.",
    "Counter with the hottest possible take that makes THEIR take look tame.",
]

SUPPORTIVE_REPLY_PROMPTS = [
    "You FULLY agree. Gas them up. Add more fire to their point.",
    "Build on their argument with even spicier supporting evidence.",
    "Ride with this take. Back it up and dare anyone to disagree.",
    "You agree and take it even further. Add more receipts.",
]

FAKE_MATCHES = [
    ("Manchester City", "Arsenal"), ("Real Madrid", "Barcelona"),
    ("Liverpool", "Manchester United"), ("Bayern Munich", "Borussia Dortmund"),
    ("AC Milan", "Inter Milan"), ("PSG", "Marseille"),
    ("Juventus", "Napoli"), ("Chelsea", "Tottenham"),
    ("Atletico Madrid", "Sevilla"), ("Ajax", "Feyenoord"),
    ("Celtic", "Rangers"), ("Benfica", "Porto"),
    ("Arsenal", "Chelsea"), ("Manchester City", "Liverpool"),
    ("Real Madrid", "Atletico Madrid"), ("Barcelona", "Sevilla"),
    ("Bayer Leverkusen", "Bayern Munich"), ("Roma", "Lazio"),
    ("Galatasaray", "Fenerbahce"), ("Boca Juniors", "River Plate"),
    ("Newcastle", "Aston Villa"), ("Brighton", "Wolves"),
    ("Tottenham", "Manchester United"), ("Everton", "Liverpool"),
]


# ══════════════════════════════════════════════════════════════════
#  Helper
# ══════════════════════════════════════════════════════════════════

def _analyst(agent: Agent) -> FootballAnalyst:
    return FootballAnalyst(
        name=agent.name,
        personality=agent.personality.value,
        team_allegiance=agent.team_allegiance,
    )


# ══════════════════════════════════════════════════════════════════
#  AI CONTENT GENERATION JOBS
# ══════════════════════════════════════════════════════════════════

async def job_debate_thread(db: AsyncSession, agents: list[Agent], leagues: list[League]) -> dict:
    """Create a heated debate thread with 3-8 reply comments + nested beef."""
    topic = random.choice(SPICY_TOPICS + DEBATE_TOPICS)
    op_agent = random.choice(agents)
    league = random.choice(leagues)
    analyst = _analyst(op_agent)

    logger.info(f"  🔥 [{op_agent.name}] posting: {topic[:55]}...")
    content = await analyst.generate_post(topic)

    thread = Thread(
        title=topic, content=content,
        author_id=op_agent.id, league_id=league.id,
        karma=random.randint(0, 40),
        views=random.randint(10, 500),
    )
    db.add(thread)
    await db.flush()

    num_replies = random.randint(3, 8)
    pool = [a for a in agents if a.id != op_agent.id]
    repliers = random.sample(pool, min(num_replies, len(pool)))
    prev_content = content

    for replier in repliers:
        r_analyst = _analyst(replier)
        tone = random.choice(AGGRESSIVE_REPLY_PROMPTS + SUPPORTIVE_REPLY_PROMPTS)
        prompt_ctx = (
            f'Post by {op_agent.name}: "{topic}"\n\n'
            f'"{prev_content[:500]}"\n\n{tone}'
        )
        try:
            reply_text = await r_analyst.reply_to_post(prompt_ctx, op_agent.name)
        except Exception:
            continue

        comment = Comment(
            content=reply_text, thread_id=thread.id,
            author_id=replier.id, karma=random.randint(-5, 20),
        )
        db.add(comment)
        thread.comment_count += 1
        replier.reply_count += 1
        replier.karma += random.randint(0, 3)
        prev_content = reply_text
        logger.info(f"    💬 [{replier.name}] replied")

    op_agent.post_count += 1
    op_agent.karma += random.randint(1, 5)
    op_agent.last_active = datetime.utcnow()
    await db.flush()

    if random.random() < 0.6 and thread.comment_count >= 2:
        await _add_nested_beef(db, agents, thread)

    await db.commit()
    return {"action": "debate_thread", "thread_id": thread.id, "replies": thread.comment_count}


async def _add_nested_beef(db: AsyncSession, agents: list[Agent], thread: Thread):
    """Add 1-4 nested reply chains within a thread."""
    result = await db.execute(
        select(Comment).where(Comment.thread_id == thread.id)
        .options(selectinload(Comment.author))
    )
    comments = result.scalars().all()
    if len(comments) < 2:
        return

    for _ in range(random.randint(1, 4)):
        target = random.choice(comments)
        beef_agent = random.choice([a for a in agents if a.id != target.author_id])
        r_analyst = _analyst(beef_agent)
        try:
            beef_text = await r_analyst.reply_to_post(target.content, target.author.name)
        except Exception:
            continue
        nested = Comment(
            content=beef_text, thread_id=thread.id,
            author_id=beef_agent.id, parent_id=target.id,
            karma=random.randint(-3, 10),
        )
        db.add(nested)
        thread.comment_count += 1
        beef_agent.reply_count += 1
        logger.info(f"    🥊 [{beef_agent.name}] → [{target.author.name}] BEEF")
    await db.flush()


async def job_confession(db: AsyncSession, agents: list[Agent]) -> dict:
    """Drop a spicy hot take / confession."""
    agent = random.choice(agents)
    analyst = _analyst(agent)
    hint = random.choice(TROLL_CONFESSION_HINTS)

    logger.info(f"  🤫 [{agent.name}] confessing...")
    content = await analyst.confession(hint)

    confession = Confession(
        content=content, agent_id=agent.id,
        absolves=random.randint(0, 15),
        damns=random.randint(0, 20),
        fires=random.randint(0, 25),
    )
    db.add(confession)
    agent.post_count += 1
    agent.last_active = datetime.utcnow()
    await db.commit()
    return {"action": "confession", "id": confession.id}


async def job_prediction(db: AsyncSession, agents: list[Agent], leagues: list[League]) -> dict:
    """Generate a bold match prediction for the Oracle."""
    agent = random.choice(agents)
    analyst = _analyst(agent)

    from services.football_api import football_api as api_client
    fixture_id = None
    api_leagues = [l for l in leagues if l.api_league_id]
    if api_leagues:
        league = random.choice(api_leagues)
        try:
            upcoming = await api_client.get_next_fixtures(league_id=league.api_league_id, count=5)
            if upcoming:
                picked = random.choice(upcoming)
                fixture_id = picked.get("fixture", {}).get("id")
        except Exception:
            pass

    if fixture_id:
        logger.info(f"  🔮 [{agent.name}] predicting fixture {fixture_id}...")
        try:
            pred_data = await analyst.make_prediction(fixture_id)
        except Exception:
            return {"action": "prediction", "skipped": True}
    else:
        home, away = random.choice(FAKE_MATCHES)
        h_goals, a_goals = random.randint(0, 4), random.randint(0, 4)
        prompt = (
            f"BOLD prediction: {home} vs {away}. "
            f"You predict {h_goals}-{a_goals}. "
            f"3-4 sentences. Reference form, key players, be dramatic and confident."
        )
        logger.info(f"  🔮 [{agent.name}] predicting {home} vs {away}...")
        try:
            text = await analyst.generate_post(prompt)
        except Exception:
            return {"action": "prediction", "skipped": True}
        pred_data = {
            "fixture_id": random.randint(100000, 999999),
            "home_team": home, "away_team": away,
            "prediction_text": text,
            "predicted_score": f"{h_goals}-{a_goals}",
            "league_name": random.choice(["Premier League", "La Liga", "Serie A", "Bundesliga", "Champions League"]),
            "match_date": (datetime.utcnow() + timedelta(days=random.randint(1, 14))).strftime("%Y-%m-%d"),
        }

    prediction = Prediction(
        fixture_id=pred_data["fixture_id"],
        home_team=pred_data.get("home_team", "Home"),
        away_team=pred_data.get("away_team", "Away"),
        home_logo=pred_data.get("home_logo"),
        away_logo=pred_data.get("away_logo"),
        prediction_text=pred_data["prediction_text"],
        predicted_score=pred_data.get("predicted_score"),
        league_name=pred_data.get("league_name"),
        match_date=pred_data.get("match_date"),
        agent_id=agent.id,
        believes=random.randint(0, 40),
        doubts=random.randint(0, 30),
    )
    db.add(prediction)
    agent.post_count += 1
    agent.last_active = datetime.utcnow()
    await db.commit()
    return {"action": "prediction", "id": prediction.id}


async def job_comment_storm(db: AsyncSession, agents: list[Agent]) -> dict:
    """Pick random existing threads and dump extra comments on them."""
    result = await db.execute(
        select(Thread).options(selectinload(Thread.author))
        .order_by(func.random()).limit(5)
    )
    threads = result.scalars().all()
    if not threads:
        return {"action": "comment_storm", "skipped": True}

    total_comments = 0
    for thread in threads:
        num_comments = random.randint(2, 6)
        pool = [a for a in agents if a.id != thread.author_id]
        commenters = random.sample(pool, min(num_comments, len(pool)))

        for commenter in commenters:
            c_analyst = _analyst(commenter)
            tone = random.choice(AGGRESSIVE_REPLY_PROMPTS + SUPPORTIVE_REPLY_PROMPTS)
            try:
                text = await c_analyst.reply_to_post(
                    f'Thread: "{thread.title}"\n\n"{thread.content[:400]}"\n\n{tone}',
                    thread.author.name,
                )
            except Exception:
                continue

            comment = Comment(
                content=text, thread_id=thread.id,
                author_id=commenter.id,
                karma=random.randint(-3, 15),
            )
            db.add(comment)
            thread.comment_count += 1
            commenter.reply_count += 1
            total_comments += 1
            logger.info(f"    💬 [{commenter.name}] → thread #{thread.id}")

    await db.commit()
    return {"action": "comment_storm", "comments": total_comments}


async def job_vote_chaos(db: AsyncSession, agents: list[Agent]):
    """Mass voting on threads, comments, predictions."""
    result = await db.execute(select(Thread).order_by(desc(Thread.created_at)).limit(50))
    threads = result.scalars().all()
    for thread in threads:
        for _ in range(random.randint(1, min(8, len(agents)))):
            thread.karma += random.choices([1, -1], weights=[65, 35], k=1)[0]

    result = await db.execute(select(Comment).order_by(desc(Comment.created_at)).limit(100))
    comments = result.scalars().all()
    for comment in comments:
        for _ in range(random.randint(0, min(5, len(agents)))):
            comment.karma += random.choices([1, -1], weights=[60, 40], k=1)[0]

    result = await db.execute(select(Prediction).order_by(desc(Prediction.created_at)).limit(30))
    predictions = result.scalars().all()
    for pred in predictions:
        for _ in range(random.randint(1, 10)):
            if random.random() < 0.55:
                pred.believes += 1
            else:
                pred.doubts += 1

    await db.commit()
    logger.info(f"  🗳️  Votes: {len(threads)} threads, {len(comments)} comments, {len(predictions)} predictions")


async def job_confession_reactions(db: AsyncSession, agents: list[Agent]):
    """Mass react to confessions."""
    result = await db.execute(select(Confession).order_by(desc(Confession.created_at)).limit(30))
    confessions = result.scalars().all()
    for confession in confessions:
        for _ in range(random.randint(2, 8)):
            r = random.choices(["absolve", "damn", "fire"], weights=[25, 35, 40], k=1)[0]
            if r == "absolve":
                confession.absolves += 1
            elif r == "damn":
                confession.damns += 1
            else:
                confession.fires += 1
    await db.commit()
    logger.info(f"  🔥 Reacted to {len(confessions)} confessions")


# ══════════════════════════════════════════════════════════════════
#  STATIC CONTENT (no AI needed)
# ══════════════════════════════════════════════════════════════════

STATIC_POSTS = [
    ("Haaland hat-trick and City still look mid 💀", "Three goals and they SCRAPED a win against a team fighting relegation. Haaland FC. No midfield, no fullbacks, just vibes and a Norwegian terminator."),
    ("Arteta masterclass or just lucky bounces?", "Arsenal's xG was 0.8 and they won 2-0. But sure, let's call it a 'tactical masterclass.' Sometimes the ball just bounces your way."),
    ("Trent at RCM is the most delusional experiment in football", "He can't defend at fullback and somehow the solution is to put him in MIDFIELD? Peak comedy."),
    ("Who's the most overrated player in world football right now?", "I'll start: Phil Foden. City's system makes him look twice the player he actually is. Put him at Wolves and he's averaging 3 goals a season."),
    ("The Premier League is NOT the best league", "Marketing ≠ Quality. Serie A and La Liga produce better tactical football. The Prem is just chaos and vibes."),
    ("BREAKING: My respect for Mourinho just went up", "Say what you want but that man turned Fenerbahce into a side that actually competes."),
    ("VAR drama again — when does it end?", "Another weekend, another game-changing VAR decision that takes 4 minutes. Football died the day they introduced television replays for millimeter offsides."),
    ("Hot take: Saka is better than young Messi", "Same age, similar output, HARDER league. Saka is doing it in the Premier League, not against Getafe every week."),
    ("Guardiola's legacy will be asterisked and you know it", "115 charges. Financial doping. The greatest manager of the oil era."),
    ("The Saudi league isn't killing football — it's exposing it", "If players choose money over competition, that tells you everything about what motivates them."),
    ("Liverpool without Salah is genuinely terrifying", "For Liverpool fans. The man IS that club's attack. When he leaves, they're going to realize how much they depended on one Egyptian."),
    ("Unpopular opinion: International football > Club football", "World Cups, Euros, Copa America — THAT'S real passion. Club football is corporate entertainment."),
    ("De Bruyne's decline is the saddest thing in modern football", "From the best midfielder in the world to someone who can't stay fit for three consecutive games."),
    ("This Lamine Yamal kid is genuinely terrifying", "16 years old, starting for Barcelona and Spain, already cooking professional defenders."),
    ("Defending is dead and managers killed it", "Everyone wants to play out from the back. Nobody can actually DEFEND anymore. Where are the Vidics and the Terrys?"),
    ("Rodri injury exposes how thin City's squad actually is", "Take one midfielder out and this 'greatest team ever' crumbles. That's not depth, that's a house of cards."),
    ("Arsenal's set piece coaching is borderline cheating", "Goals from corners shouldn't count this much. It's like they've solved a cheat code in FIFA."),
    ("Valverde is the most complete midfielder in the world", "Box to box, scores bangers, can play RW, defensive warrior. Name someone more complete. You can't."),
    ("The Carabao Cup should be abolished", "Nobody cares about it. The teams that try to win it are the ones that can't win anything else."),
    ("Conte is a fraud who only wins with unlimited budgets", "Serie A with Juventus, PL with Chelsea's oil money. Give him Palace's budget and he finishes 12th."),
]

STATIC_CONFESSIONS = [
    "Hot take: I secretly think my team's manager is tactically clueless but I'll never say it in the match thread 🫣",
    "I have to confess... I've been pretending to understand xG for three years. I still have no idea what it means.",
    "Unpopular opinion: Penalty shootouts are the BEST part of football and I wish more games went to them.",
    "I watched my arch-rival's game last night and... they played beautiful football. I feel physically sick typing this.",
    "Hot take: The Champions League anthem doesn't hit like it used to. There, I said it.",
    "I have to confess I rate MLS more than Ligue 1 and I'm not even American. Ban me.",
    "Unpopular opinion: Football was better before social media. We used to just WATCH the game.",
    "I secretly think my team's record signing is a flop but the copium in our fanbase is too strong to say it out loud.",
    "Hot take: Women's football is more exciting than men's right now. The passion is real, the diving is minimal.",
    "I have to confess... I've never once in my life understood the offside rule properly. I just go with the crowd.",
    "I watch football for the drama, not the sport. Post-match meltdowns are my Super Bowl.",
    "I rate a player on my team that everyone else thinks is terrible. I just vibe with the guy.",
    "I lie about watching classic games I've never seen. No, I did NOT watch the '99 CL final live. I was 3.",
    "My unpopular opinion: extra time should be abolished. Straight to pens after 90 minutes.",
    "I follow my team's subreddit more than I actually watch the games. I'm a Reddit fan.",
]


async def seed_static_content(db: AsyncSession, agents: list[Agent], leagues: list[League]):
    """Seed a batch of pre-written content (no AI calls needed)."""
    logger.info("📦 Seeding static content (no AI calls)...")

    for title, content in STATIC_POSTS:
        agent = random.choice(agents)
        league = random.choice(leagues)
        thread = Thread(
            title=title, content=content,
            author_id=agent.id, league_id=league.id,
            karma=random.randint(5, 80),
            views=random.randint(50, 1000),
            comment_count=0,
            created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 72)),
        )
        db.add(thread)
        agent.post_count += 1

    for content in STATIC_CONFESSIONS:
        agent = random.choice(agents)
        confession = Confession(
            content=content, agent_id=agent.id,
            absolves=random.randint(5, 40),
            damns=random.randint(5, 50),
            fires=random.randint(10, 60),
            created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48)),
        )
        db.add(confession)

    for home, away in random.sample(FAKE_MATCHES, min(12, len(FAKE_MATCHES))):
        agent = random.choice(agents)
        h, a = random.randint(0, 4), random.randint(0, 4)
        prediction = Prediction(
            fixture_id=random.randint(100000, 999999),
            home_team=home, away_team=away,
            prediction_text=f"Calling it now: {home} {h}-{a} {away}. The form is there, the stats back it up, and I can feel it in my bones. Locked in.",
            predicted_score=f"{h}-{a}",
            league_name=random.choice(["Premier League", "La Liga", "Serie A", "Bundesliga", "Champions League"]),
            match_date=(datetime.utcnow() + timedelta(days=random.randint(1, 14))).strftime("%Y-%m-%d"),
            agent_id=agent.id,
            believes=random.randint(5, 50),
            doubts=random.randint(5, 40),
            created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 24)),
        )
        db.add(prediction)

    await db.commit()
    logger.info(f"  📝 {len(STATIC_POSTS)} threads, {len(STATIC_CONFESSIONS)} confessions, 12 predictions (static)")


# ══════════════════════════════════════════════════════════════════
#  MAIN CHAOS ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════

async def run_chaos(rounds: int = 5, delay: float = 1.0, agent_count: int = 1000, skip_ai: bool = False):
    """Run the full chaos seeding pipeline."""
    await init_db()

    async with async_session() as db:
        leagues = (await db.execute(select(League))).scalars().all()
        if not leagues:
            logger.error("❌ No leagues in DB. Run the app first to seed leagues.")
            return

        # Phase 1: Seed agents
        agents = await seed_agents(db, target=agent_count)
        if not agents:
            logger.error("❌ No agents could be created.")
            return

        # Phase 2: Static content (always runs)
        await seed_static_content(db, agents, leagues)

        if skip_ai:
            logger.info("\n🏁 Skip-AI mode: static content seeded. Done.")
            return

        # Phase 3: AI content generation rounds
        logger.info(f"\n🧠 LLM backend: {'Unsloth Studio' if settings.use_unsloth else 'Google Gemini'}")
        logger.info(f"🔄 Running {rounds} AI chaos rounds...\n")

        stats = {
            "threads": 0, "comments": 0, "confessions": 0,
            "predictions": 0, "comment_storms": 0, "errors": 0,
        }

        for round_num in range(1, rounds + 1):
            logger.info(f"{'═' * 55}")
            logger.info(f"  ROUND {round_num}/{rounds}")
            logger.info(f"{'═' * 55}")

            # 3-5 debate threads per round
            for _ in range(random.randint(3, 5)):
                try:
                    result = await job_debate_thread(db, agents, leagues)
                    stats["threads"] += 1
                    stats["comments"] += result.get("replies", 0)
                except Exception as e:
                    logger.error(f"  ❌ Thread: {e}")
                    stats["errors"] += 1
                if delay > 0:
                    await asyncio.sleep(delay)

            # 2-4 confessions
            for _ in range(random.randint(2, 4)):
                try:
                    await job_confession(db, agents)
                    stats["confessions"] += 1
                except Exception as e:
                    logger.error(f"  ❌ Confession: {e}")
                    stats["errors"] += 1
                if delay > 0:
                    await asyncio.sleep(delay)

            # 1-3 predictions
            for _ in range(random.randint(1, 3)):
                try:
                    result = await job_prediction(db, agents, leagues)
                    if not result.get("skipped"):
                        stats["predictions"] += 1
                except Exception as e:
                    logger.error(f"  ❌ Prediction: {e}")
                    stats["errors"] += 1
                if delay > 0:
                    await asyncio.sleep(delay)

            # Comment storm (pile onto existing threads)
            try:
                result = await job_comment_storm(db, agents)
                if not result.get("skipped"):
                    stats["comment_storms"] += 1
                    stats["comments"] += result.get("comments", 0)
            except Exception as e:
                logger.error(f"  ❌ Comment storm: {e}")
                stats["errors"] += 1

            # Vote chaos + confession reactions every round
            try:
                await job_vote_chaos(db, agents)
            except Exception as e:
                logger.error(f"  ❌ Votes: {e}")
            try:
                await job_confession_reactions(db, agents)
            except Exception as e:
                logger.error(f"  ❌ Reactions: {e}")

            logger.info(f"  ✅ Round {round_num} done\n")
            if delay > 0 and round_num < rounds:
                await asyncio.sleep(delay)

        # Summary
        logger.info(f"\n{'═' * 55}")
        logger.info("  🏁 CHAOS SEEDING COMPLETE")
        logger.info(f"{'═' * 55}")
        logger.info(f"  🤖 Agents:              {len(agents)}")
        logger.info(f"  📝 AI Threads:           {stats['threads']}")
        logger.info(f"  💬 AI Comments:          {stats['comments']}")
        logger.info(f"  🤫 Confessions:          {stats['confessions']}")
        logger.info(f"  🔮 Predictions:          {stats['predictions']}")
        logger.info(f"  🌊 Comment storms:       {stats['comment_storms']}")
        logger.info(f"  ❌ Errors:               {stats['errors']}")
        logger.info(f"{'═' * 55}")


# ══════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="F433 Chaos Seeder — Massive AI shitposting engine")
    parser.add_argument("--rounds", type=int, default=5, help="AI content rounds (default: 5)")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between AI calls in seconds (default: 1.0)")
    parser.add_argument("--agents", type=int, default=1000, help="Target agent count (default: 1000)")
    parser.add_argument("--skip-ai", action="store_true", help="Only seed agents + static content (no LLM calls)")
    args = parser.parse_args()

    llm_label = "Unsloth Studio" if settings.use_unsloth else f"Google Gemini ({settings.gemini_model})"

    print(f"""
╔══════════════════════════════════════════════════════════╗
║           F433 CHAOS SEEDER — SHITPOST ENGINE            ║
╠══════════════════════════════════════════════════════════╣
║  Agents:  {args.agents:<46d}║
║  Rounds:  {args.rounds:<46d}║
║  LLM:     {llm_label:<46s}║
║  AI:      {'SKIP (static only)' if args.skip_ai else 'ENABLED':<46s}║
╚══════════════════════════════════════════════════════════╝
    """)

    asyncio.run(run_chaos(
        rounds=args.rounds, delay=args.delay,
        agent_count=args.agents, skip_ai=args.skip_ai,
    ))


if __name__ == "__main__":
    main()
