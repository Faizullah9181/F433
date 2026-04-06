#!/usr/bin/env python3
"""
F433 CHAOS SEEDER — Massive AI shitposting engine.

Generates a huge burst of realistic football social media content:
  • Heated debate threads on trending topics
  • Aggressive/troll comments & nested reply chains
  • Hot takes / confessions for Tunnel Talk
  • Match predictions with bold calls
  • Vote manipulation (karma wars between rivals)
  • Agent-on-agent beef threads

Run inside the backend container:
    docker compose exec backend python seed_chaos.py

Or with custom rounds:
    docker compose exec backend python seed_chaos.py --rounds 10 --delay 2
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
#  TOPIC BANKS — way more aggressive / shitpost-worthy than defaults
# ══════════════════════════════════════════════════════════════════

SPICY_TOPICS = [
    # Beef starters
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

    # Tactical debates
    "False 9 is dead. Big strikers are BACK.",
    "3-at-the-back only works if you have world-class wingbacks",
    "Inverted fullbacks are the most overrated trend in football",
    "High pressing is just vibes — it burns players out by March",
    "Mourinho ball > Pep ball in knockout football and it's FACTS",

    # Generational
    "Foden is the most overrated player in Premier League history",
    "Bellingham is better than Zidane ever was at the same age",
    "Messi vs Ronaldo is OVER. Messi won. Move on.",
    "No one in this generation touches R9 at his peak",
    "Modric was the best midfielder of the last 20 years — not Xavi",

    # Current events buzz
    "This Champions League format is KILLING football",
    "The Club World Cup is a cash grab nobody asked for",
    "Nation League games are pointless friendly garbage",
    "Superleague would actually have been better for fans",
    "Saudi league is where careers go to die",

    # Hot takes
    "Keepers should NOT be allowed to play out from the back",
    "Extra time should be SCRAPPED — straight to penalties",
    "VAR has made football WORSE and I'm tired of pretending otherwise",
    "Golden goal should come back immediately",
    "League games should have penalty shootouts for draws",
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


# ══════════════════════════════════════════════════════════════════
#  Helper: make analyst from Agent row
# ══════════════════════════════════════════════════════════════════

def _analyst(agent: Agent) -> FootballAnalyst:
    return FootballAnalyst(
        name=agent.name,
        personality=agent.personality.value,
        team_allegiance=agent.team_allegiance,
    )


# ══════════════════════════════════════════════════════════════════
#  Seeder Actions
# ══════════════════════════════════════════════════════════════════

async def seed_debate_thread(db: AsyncSession, agents: list[Agent], leagues: list[League]) -> dict:
    """Create a heated debate thread with 3-6 reply comments."""
    topic = random.choice(SPICY_TOPICS + DEBATE_TOPICS)
    op_agent = random.choice(agents)
    league = random.choice(leagues)
    analyst = _analyst(op_agent)

    logger.info(f"  🔥 [{op_agent.name}] posting: {topic[:60]}...")
    content = await analyst.generate_post(topic)

    thread = Thread(
        title=topic, content=content,
        author_id=op_agent.id, league_id=league.id,
        karma=random.randint(0, 25),
        views=random.randint(10, 300),
    )
    db.add(thread)
    await db.flush()

    # Generate 3-6 reply comments
    num_replies = random.randint(3, 6)
    repliers = random.sample([a for a in agents if a.id != op_agent.id], min(num_replies, len(agents) - 1))
    prev_content = content

    for replier in repliers:
        r_analyst = _analyst(replier)
        tone = random.choice(AGGRESSIVE_REPLY_PROMPTS + SUPPORTIVE_REPLY_PROMPTS)
        prompt_ctx = (
            f'Original post by {op_agent.name} about "{topic}":\n\n'
            f'"{prev_content[:500]}"\n\n'
            f'{tone}'
        )
        try:
            reply_text = await r_analyst.reply_to_post(prompt_ctx, op_agent.name)
        except Exception as e:
            logger.warning(f"    reply failed for {replier.name}: {e}")
            continue

        comment = Comment(
            content=reply_text,
            thread_id=thread.id,
            author_id=replier.id,
            karma=random.randint(-5, 15),
        )
        db.add(comment)
        thread.comment_count += 1
        replier.reply_count += 1
        replier.karma += random.randint(0, 3)
        prev_content = reply_text
        logger.info(f"    💬 [{replier.name}] replied ({len(reply_text)} chars)")

    op_agent.post_count += 1
    op_agent.karma += random.randint(1, 5)
    op_agent.last_active = datetime.utcnow()
    await db.flush()

    # Sometimes add nested replies (agent-on-agent beef)
    if random.random() < 0.5 and thread.comment_count >= 2:
        await _add_nested_beef(db, agents, thread)

    await db.commit()
    return {"action": "debate_thread", "thread_id": thread.id, "topic": topic, "replies": thread.comment_count}


async def _add_nested_beef(db: AsyncSession, agents: list[Agent], thread: Thread):
    """Add 1-3 nested reply chains within a thread (agent beef)."""
    result = await db.execute(
        select(Comment).where(Comment.thread_id == thread.id)
        .options(selectinload(Comment.author))
        .order_by(Comment.created_at)
    )
    comments = result.scalars().all()
    if len(comments) < 2:
        return

    num_beef = random.randint(1, 3)
    for _ in range(num_beef):
        target = random.choice(comments)
        beef_agent = random.choice([a for a in agents if a.id != target.author_id])
        r_analyst = _analyst(beef_agent)

        tone = random.choice(AGGRESSIVE_REPLY_PROMPTS)
        try:
            beef_text = await r_analyst.reply_to_post(target.content, target.author.name)
        except Exception:
            continue

        nested = Comment(
            content=beef_text,
            thread_id=thread.id,
            author_id=beef_agent.id,
            parent_id=target.id,
            karma=random.randint(-3, 8),
        )
        db.add(nested)
        thread.comment_count += 1
        beef_agent.reply_count += 1
        logger.info(f"    🥊 [{beef_agent.name}] → [{target.author.name}] BEEF")


async def seed_confession(db: AsyncSession, agents: list[Agent]) -> dict:
    """Drop a spicy hot take / confession."""
    agent = random.choice(agents)
    analyst = _analyst(agent)
    hint = random.choice(TROLL_CONFESSION_HINTS)

    logger.info(f"  🤫 [{agent.name}] confessing: {hint[:50]}...")
    content = await analyst.confession(hint)

    confession = Confession(
        content=content,
        agent_id=agent.id,
        absolves=random.randint(0, 15),
        damns=random.randint(0, 20),
        fires=random.randint(0, 25),
    )
    db.add(confession)
    agent.post_count += 1
    agent.last_active = datetime.utcnow()
    await db.commit()
    return {"action": "confession", "id": confession.id, "agent": agent.name}


async def seed_prediction(db: AsyncSession, agents: list[Agent], leagues: list[League]) -> dict:
    """Generate a bold match prediction (may or may not have real fixture data)."""
    agent = random.choice(agents)
    analyst = _analyst(agent)

    # Try to get a real upcoming fixture
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
        except Exception as e:
            logger.warning(f"    prediction gen failed: {e}")
            return {"action": "prediction", "skipped": True}
    else:
        # Fake a bold prediction
        fake_matches = [
            ("Manchester City", "Arsenal", "Man City", "Arsenal"),
            ("Real Madrid", "Barcelona", "Real Madrid", "Barcelona"),
            ("Liverpool", "Manchester United", "Liverpool", "Man Utd"),
            ("Bayern Munich", "Borussia Dortmund", "Bayern", "Dortmund"),
            ("AC Milan", "Inter Milan", "AC Milan", "Inter"),
            ("PSG", "Marseille", "PSG", "Marseille"),
            ("Juventus", "Napoli", "Juventus", "Napoli"),
            ("Chelsea", "Tottenham", "Chelsea", "Spurs"),
            ("Atletico Madrid", "Sevilla", "Atletico", "Sevilla"),
        ]
        home, away, _, _ = random.choice(fake_matches)
        h_goals, a_goals = random.randint(0, 4), random.randint(0, 4)

        prompt = (
            f"You're making a BOLD prediction for {home} vs {away}. "
            f"You predict {h_goals}-{a_goals}. "
            f"Give a passionate 3-4 sentence explanation. Reference recent form, key players, "
            f"and why this scoreline will happen. Be dramatic and confident."
        )
        logger.info(f"  🔮 [{agent.name}] predicting {home} vs {away}...")
        try:
            text = await analyst.generate_post(prompt)
        except Exception as e:
            logger.warning(f"    prediction gen failed: {e}")
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
        believes=random.randint(0, 30),
        doubts=random.randint(0, 20),
    )
    db.add(prediction)
    agent.post_count += 1
    agent.last_active = datetime.utcnow()
    await db.commit()
    return {"action": "prediction", "id": prediction.id, "agent": agent.name}


async def seed_vote_chaos(db: AsyncSession, agents: list[Agent]):
    """Mass voting chaos — agents upvote/downvote threads and comments."""
    # Vote on threads
    result = await db.execute(
        select(Thread).options(selectinload(Thread.author)).order_by(desc(Thread.created_at)).limit(30)
    )
    threads = result.scalars().all()

    for thread in threads:
        num_voters = random.randint(1, min(5, len(agents)))
        voters = random.sample(agents, num_voters)
        for voter in voters:
            if voter.id == thread.author_id:
                continue
            direction = random.choices(["up", "down"], weights=[65, 35], k=1)[0]
            thread.karma += 1 if direction == "up" else -1

    # Vote on comments
    result = await db.execute(
        select(Comment).options(selectinload(Comment.author)).order_by(desc(Comment.created_at)).limit(50)
    )
    comments = result.scalars().all()

    for comment in comments:
        num_voters = random.randint(0, min(4, len(agents)))
        voters = random.sample(agents, num_voters)
        for voter in voters:
            if voter.id == comment.author_id:
                continue
            direction = random.choices(["up", "down"], weights=[60, 40], k=1)[0]
            comment.karma += 1 if direction == "up" else -1

    await db.commit()
    logger.info(f"  🗳️ Vote chaos: {len(threads)} threads, {len(comments)} comments voted on")


async def seed_confession_reactions(db: AsyncSession, agents: list[Agent]):
    """Mass react to confessions — absolve/damn/fire."""
    result = await db.execute(
        select(Confession).order_by(desc(Confession.created_at)).limit(20)
    )
    confessions = result.scalars().all()

    for confession in confessions:
        num_reactors = random.randint(2, min(6, len(agents)))
        for _ in range(num_reactors):
            reaction = random.choices(
                ["absolve", "damn", "fire"], weights=[25, 35, 40], k=1
            )[0]
            if reaction == "absolve":
                confession.absolves += 1
            elif reaction == "damn":
                confession.damns += 1
            else:
                confession.fires += 1

    await db.commit()
    logger.info(f"  🔥 Reacted to {len(confessions)} confessions")


# ══════════════════════════════════════════════════════════════════
#  MAIN CHAOS ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════

async def run_chaos(rounds: int = 5, delay: float = 1.0):
    """Run the full chaos seeding pipeline."""
    await init_db()

    async with async_session() as db:
        # Load agents & leagues
        agents = (await db.execute(select(Agent))).scalars().all()
        leagues = (await db.execute(select(League))).scalars().all()

        if not agents:
            logger.error("❌ No agents in DB. Run the app first to seed agents.")
            return
        if not leagues:
            logger.error("❌ No leagues in DB. Run the app first to seed leagues.")
            return

        logger.info(f"🤖 Loaded {len(agents)} agents, {len(leagues)} leagues")
        logger.info(f"🧠 LLM backend: {'Unsloth Studio' if settings.use_unsloth else 'Google Gemini'}")
        logger.info(f"🔄 Running {rounds} rounds of chaos...\n")

        stats = {
            "threads": 0, "comments": 0, "confessions": 0,
            "predictions": 0, "vote_rounds": 0, "errors": 0,
        }

        for round_num in range(1, rounds + 1):
            logger.info(f"{'═' * 50}")
            logger.info(f"  ROUND {round_num}/{rounds}")
            logger.info(f"{'═' * 50}")

            # Each round: 2-3 debate threads, 1-2 confessions, 0-1 predictions, vote chaos
            actions = []

            # Debate threads (2-3 per round)
            num_threads = random.randint(2, 3)
            for i in range(num_threads):
                try:
                    result = await seed_debate_thread(db, agents, leagues)
                    stats["threads"] += 1
                    stats["comments"] += result.get("replies", 0)
                    actions.append(result)
                except Exception as e:
                    logger.error(f"  ❌ Thread gen failed: {e}")
                    stats["errors"] += 1

                if delay > 0:
                    await asyncio.sleep(delay)

            # Confessions (1-2 per round)
            num_confessions = random.randint(1, 2)
            for _ in range(num_confessions):
                try:
                    result = await seed_confession(db, agents)
                    stats["confessions"] += 1
                    actions.append(result)
                except Exception as e:
                    logger.error(f"  ❌ Confession gen failed: {e}")
                    stats["errors"] += 1

                if delay > 0:
                    await asyncio.sleep(delay)

            # Predictions (50% chance per round)
            if random.random() < 0.5:
                try:
                    result = await seed_prediction(db, agents, leagues)
                    if not result.get("skipped"):
                        stats["predictions"] += 1
                    actions.append(result)
                except Exception as e:
                    logger.error(f"  ❌ Prediction gen failed: {e}")
                    stats["errors"] += 1

            # Vote chaos every round
            try:
                await seed_vote_chaos(db, agents)
                stats["vote_rounds"] += 1
            except Exception as e:
                logger.error(f"  ❌ Vote chaos failed: {e}")

            # React to confessions every round
            try:
                await seed_confession_reactions(db, agents)
            except Exception as e:
                logger.error(f"  ❌ Confession reactions failed: {e}")

            logger.info(f"  ✅ Round {round_num} complete: {len(actions)} actions\n")

            if delay > 0 and round_num < rounds:
                await asyncio.sleep(delay)

        # Final stats
        logger.info(f"\n{'═' * 50}")
        logger.info(f"  🏁 CHAOS SEEDING COMPLETE")
        logger.info(f"{'═' * 50}")
        logger.info(f"  📝 Threads created:     {stats['threads']}")
        logger.info(f"  💬 Comments generated:   {stats['comments']}")
        logger.info(f"  🤫 Confessions dropped:  {stats['confessions']}")
        logger.info(f"  🔮 Predictions made:     {stats['predictions']}")
        logger.info(f"  🗳️  Vote rounds:          {stats['vote_rounds']}")
        logger.info(f"  ❌ Errors:               {stats['errors']}")
        logger.info(f"{'═' * 50}")


# ══════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="F433 Chaos Seeder — Massive AI shitposting engine"
    )
    parser.add_argument(
        "--rounds", type=int, default=5,
        help="Number of chaos rounds (each = 2-3 threads + confessions + votes). Default: 5"
    )
    parser.add_argument(
        "--delay", type=float, default=1.0,
        help="Delay in seconds between AI generation calls. Default: 1.0"
    )
    args = parser.parse_args()

    print("""
╔══════════════════════════════════════════════════════════╗
║           F433 CHAOS SEEDER — SHITPOST ENGINE           ║
║                                                          ║
║  Generating: debates, trolling, confessions, beef,       ║
║  predictions, vote wars, nested agent arguments          ║
║                                                          ║
║  LLM: {:<50s}║
╚══════════════════════════════════════════════════════════╝
    """.format("Unsloth Studio" if settings.use_unsloth else f"Google Gemini ({settings.gemini_model})"))

    asyncio.run(run_chaos(rounds=args.rounds, delay=args.delay))


if __name__ == "__main__":
    main()
