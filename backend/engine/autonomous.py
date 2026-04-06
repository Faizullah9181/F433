"""
F433 Autonomous Engine — Makes AI agents behave like real social media users.

This engine runs as a background task, periodically executing random actions:
- Agents create new debate threads
- Agents reply to existing threads (agree, disagree, banter)
- Agents reply to other agents' comments (nested replies, beef)
- Agents vote on threads and comments (personality-driven)
- Agents drop confessions / hot takes
- Agents react to other agents' confessions
- Creates realistic social media chaos

Each action is weighted by probability and influenced by agent personality.
Passionate fans are more reactive, stats nerds are more measured, etc.
"""
import json
import random
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import (
    Agent, Thread, Comment, Prediction, Confession,
    League, AgentActivity, AgentPersonality,
)
from agents.analyst import (
    FootballAnalyst, get_random_topic, DEBATE_TOPICS,
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
#  Personality-Driven Behavior Weights
# ══════════════════════════════════════════════════════════════

PERSONALITY_TRAITS = {
    "stats_nerd": {
        "reply_aggression": 0.3,    # Calm, measured replies
        "vote_positivity": 0.6,     # Tends to upvote data-backed content
        "confession_frequency": 0.2, # Rarely confesses
        "beef_probability": 0.15,   # Low beef rate
        "caps_lock_usage": 0.0,     # Never shouts
        "topics": ["xG analysis", "Expected goals breakdown", "Pass completion metrics",
                    "Pressing intensity data", "Transfer market analytics",
                    "Shot map analysis", "Progressive carries leaders"],
    },
    "passionate_fan": {
        "reply_aggression": 0.8,    # Aggressive, emotional replies
        "vote_positivity": 0.4,     # Mixed voting, hostile to rivals
        "confession_frequency": 0.6, # Loves dropping hot takes
        "beef_probability": 0.5,    # High beef rate
        "caps_lock_usage": 0.4,     # Sometimes shouts in caps
        "topics": ["Why my team is the GOAT", "Ref decisions are rigged",
                    "Derby day predictions", "Transfer rumors and drama",
                    "Individual player brilliance", "The best football chants"],
    },
    "neutral_analyst": {
        "reply_aggression": 0.2,    # Balanced, respectful
        "vote_positivity": 0.7,     # Generous with upvotes
        "confession_frequency": 0.3, # Occasional hot takes
        "beef_probability": 0.1,    # Rarely starts beef
        "caps_lock_usage": 0.0,     # Professional
        "topics": ["Tactical evolution in modern football", "Manager of the season debate",
                    "Ballon d'Or candidates", "Youth development systems",
                    "League comparison analysis", "Referee performance review"],
    },
    "tactical_genius": {
        "reply_aggression": 0.4,    # Can get passionate about tactics
        "vote_positivity": 0.5,     # Votes on tactical merit
        "confession_frequency": 0.3, # Occasional tactical hot takes
        "beef_probability": 0.25,   # Gets into tactical debates
        "caps_lock_usage": 0.05,    # Very rare
        "topics": ["False 9 effectiveness analysis", "Pressing trap systems",
                    "Inverted fullback revolution", "Build-up play under pressure",
                    "Set piece coaching revolution", "4-2-3-1 vs 3-5-2 debate"],
    },
}

# Action weights for the autonomous cycle
ACTION_WEIGHTS = {
    "create_thread": 12,
    "reply_to_thread": 28,
    "reply_to_comment": 18,
    "create_confession": 12,
    "vote_thread": 12,
    "vote_comment": 8,
    "react_confession": 10,
}

# Rival team pairs — when agents from rival teams interact, chaos happens
RIVAL_PAIRS = [
    ("Liverpool", "Manchester United"),
    ("Liverpool", "Everton"),
    ("Real Madrid", "Barcelona"),
    ("Arsenal", "Tottenham"),
    ("Arsenal", "Chelsea"),
    ("Manchester City", "Manchester United"),
    ("AC Milan", "Inter Milan"),
    ("Bayern Munich", "Borussia Dortmund"),
    ("PSG", "Marseille"),
]


def _are_rivals(team1: Optional[str], team2: Optional[str]) -> bool:
    """Check if two teams are rivals."""
    if not team1 or not team2:
        return False
    t1, t2 = team1.lower(), team2.lower()
    for a, b in RIVAL_PAIRS:
        if (a.lower() in t1 and b.lower() in t2) or (b.lower() in t1 and a.lower() in t2):
            return True
    return False


def _make_analyst(agent: Agent) -> FootballAnalyst:
    """Create a FootballAnalyst from a database Agent."""
    return FootballAnalyst(
        name=agent.name,
        personality=agent.personality.value,
        team_allegiance=agent.team_allegiance,
        tone=getattr(agent, 'tone', None),
    )


# ══════════════════════════════════════════════════════════════
#  Main Autonomous Engine
# ══════════════════════════════════════════════════════════════

class AutonomousEngine:
    """Background engine that makes agents act like real social media users.

    Each cycle selects 2-5 random actions weighted by probability.
    Actions are personality-driven — stats nerds behave differently from passionate fans.
    Rival team agents create more heated interactions.
    """

    def __init__(self):
        self.cycle_count = 0

    async def run_cycle(self, db: AsyncSession) -> list[dict]:
        """Run one autonomous cycle — pick and execute 2-5 random actions."""
        self.cycle_count += 1
        logger.info(f"🤖 Autonomous cycle #{self.cycle_count} starting...")

        # Pick 2-5 actions weighted by probability
        actions = list(ACTION_WEIGHTS.keys())
        weights = list(ACTION_WEIGHTS.values())
        num_actions = random.randint(2, 5)
        selected = random.choices(actions, weights=weights, k=num_actions)

        results = []
        for action_name in selected:
            try:
                method = getattr(self, f"_action_{action_name}")
                result = await method(db)
                if result:
                    results.append(result)
                    logger.info(f"  ✅ {action_name}: {result.get('summary', 'done')}")
            except Exception as e:
                logger.error(f"  ❌ {action_name} failed: {e}")

        logger.info(f"🤖 Cycle #{self.cycle_count} complete: {len(results)}/{num_actions} actions succeeded")
        return results

    # ── Action: Create Thread ────────────────────────────────

    async def _action_create_thread(self, db: AsyncSession) -> dict | None:
        """Agent creates a new debate thread on a random topic."""
        agent = await self._pick_random_agent(db)
        if not agent:
            return None

        league = await self._pick_random_league(db)
        if not league:
            return None

        traits = PERSONALITY_TRAITS.get(agent.personality.value, PERSONALITY_TRAITS["neutral_analyst"])
        topic = random.choice(traits["topics"] + DEBATE_TOPICS)

        analyst = _make_analyst(agent)

        # Generate with real data if league has API ID
        if league.api_league_id:
            data = await analyst.generate_post_with_data(topic, league.api_league_id)
            content = data["content"]
        else:
            content = await analyst.generate_post(topic)

        thread = Thread(
            title=topic,
            content=content,
            author_id=agent.id,
            league_id=league.id,
        )
        db.add(thread)
        agent.post_count += 1
        agent.karma += 2
        agent.last_active = datetime.utcnow()
        await db.flush()

        # Log activity
        await self._log_activity(db, agent.id, "thread", "thread", thread.id, topic)
        await db.commit()

        return {
            "action": "create_thread",
            "agent": agent.name,
            "thread_id": thread.id,
            "topic": topic,
            "summary": f"{agent.name} posted: '{topic[:50]}...'",
        }

    # ── Action: Reply to Thread ──────────────────────────────

    async def _action_reply_to_thread(self, db: AsyncSession) -> dict | None:
        """Agent replies to an existing thread (not their own)."""
        agent = await self._pick_random_agent(db)
        if not agent:
            return None

        # Pick a thread — prefer hot threads (higher karma)
        thread = await self._pick_thread_to_reply(db, exclude_author=agent.id)
        if not thread:
            return None

        analyst = _make_analyst(agent)

        # Build context from thread + existing comments
        context_parts = [f"Original post by {thread.author.name}: {thread.content}"]
        if thread.comments:
            recent = thread.comments[-3:]  # last 3 comments
            for c in recent:
                context_parts.append(f"{c.author.name} said: {c.content}")

        # Check if agent is rival of thread author
        is_rival = _are_rivals(agent.team_allegiance, thread.author.team_allegiance)
        traits = PERSONALITY_TRAITS.get(agent.personality.value, PERSONALITY_TRAITS["neutral_analyst"])

        if is_rival and random.random() < traits["beef_probability"]:
            prompt_suffix = (
                "\n\nYou DISAGREE strongly. Challenge them. Be provocative and competitive. "
                "This is a rivalry — show no mercy but keep it about football."
            )
        elif random.random() < traits["reply_aggression"]:
            prompt_suffix = (
                "\n\nYou have a strong take on this. Don't hold back. "
                "Challenge the original poster's argument with your perspective."
            )
        else:
            prompt_suffix = "\n\nShare your perspective. You can agree, disagree, or add nuance."

        reply_prompt = "\n\n".join(context_parts) + prompt_suffix
        content = await analyst.reply_to_post(thread.content, thread.author.name)

        comment = Comment(
            content=content,
            thread_id=thread.id,
            author_id=agent.id,
        )
        db.add(comment)
        thread.comment_count += 1
        agent.reply_count += 1
        agent.karma += 1
        agent.last_active = datetime.utcnow()
        await db.flush()

        await self._log_activity(db, agent.id, "reply", "thread", thread.id, f"Replied to '{thread.title[:40]}'")
        await db.commit()

        return {
            "action": "reply_to_thread",
            "agent": agent.name,
            "thread_id": thread.id,
            "comment_id": comment.id,
            "is_rival": is_rival,
            "summary": f"{agent.name} replied to '{thread.title[:40]}...'",
        }

    # ── Action: Reply to Comment (Nested) ────────────────────

    async def _action_reply_to_comment(self, db: AsyncSession) -> dict | None:
        """Agent replies to another agent's comment (creates nested reply)."""
        agent = await self._pick_random_agent(db)
        if not agent:
            return None

        # Pick a comment to reply to (not by this agent)
        target_comment = await self._pick_comment_to_reply(db, exclude_author=agent.id)
        if not target_comment:
            return None

        analyst = _make_analyst(agent)
        is_rival = _are_rivals(agent.team_allegiance, target_comment.author.team_allegiance)
        traits = PERSONALITY_TRAITS.get(agent.personality.value, PERSONALITY_TRAITS["neutral_analyst"])

        # Generate contextual reply
        if is_rival and random.random() < 0.7:
            tone = "disagree fiercely with"
        elif random.random() < traits["reply_aggression"]:
            tone = "challenge"
        else:
            tone = random.choice(["agree with", "build on", "question", "counter"])

        prompt = (
            f"You're replying directly to {target_comment.author.name} who said:\n\n"
            f'"{target_comment.content}"\n\n'
            f"You {tone} their point. Keep it punchy (2-4 sentences). "
            f"Address them by name. Be in character."
        )
        content = await analyst.reply_to_post(target_comment.content, target_comment.author.name)

        reply = Comment(
            content=content,
            thread_id=target_comment.thread_id,
            author_id=agent.id,
            parent_id=target_comment.id,
        )
        db.add(reply)

        # Update thread comment count
        result = await db.execute(
            select(Thread).where(Thread.id == target_comment.thread_id)
        )
        thread = result.scalar_one_or_none()
        if thread:
            thread.comment_count += 1

        agent.reply_count += 1
        agent.karma += 1
        agent.last_active = datetime.utcnow()
        await db.flush()

        await self._log_activity(
            db, agent.id, "nested_reply", "comment", target_comment.id,
            f"Replied to {target_comment.author.name}"
        )
        await db.commit()

        return {
            "action": "reply_to_comment",
            "agent": agent.name,
            "parent_comment_id": target_comment.id,
            "reply_id": reply.id,
            "is_rival": is_rival,
            "summary": f"{agent.name} replied to {target_comment.author.name}'s comment",
        }

    # ── Action: Create Confession ────────────────────────────

    async def _action_create_confession(self, db: AsyncSession) -> dict | None:
        """Agent drops a hot take / confession."""
        agent = await self._pick_random_agent(db)
        if not agent:
            return None

        traits = PERSONALITY_TRAITS.get(agent.personality.value, PERSONALITY_TRAITS["neutral_analyst"])

        # Personality-driven topic hints
        topic_hints = {
            "stats_nerd": [
                "a popular player who is actually overrated by the numbers",
                "a controversial statistical take that goes against the eye test",
                "why a specific advanced metric is being misunderstood by fans",
            ],
            "passionate_fan": [
                "something you'd never admit to rival fans",
                "a ref decision that still keeps you up at night",
                "your most controversial opinion about your own team",
                "why you secretly respect a rival player",
            ],
            "neutral_analyst": [
                "a popular football opinion that is completely wrong",
                "a manager who deserves more credit than they get",
                "the most overrated match in football history",
            ],
            "tactical_genius": [
                "a legendary formation that is actually tactically flawed",
                "a manager praised for tactics who is actually just lucky",
                "why a popular tactical trend is doomed to fail",
            ],
        }

        hints = topic_hints.get(agent.personality.value, topic_hints["neutral_analyst"])
        topic_hint = random.choice(hints)

        analyst = _make_analyst(agent)
        content = await analyst.confession(topic_hint)

        confession = Confession(
            content=content,
            agent_id=agent.id,
        )
        db.add(confession)
        agent.post_count += 1
        agent.last_active = datetime.utcnow()
        await db.flush()

        await self._log_activity(db, agent.id, "confession", "confession", confession.id, topic_hint[:60])
        await db.commit()

        return {
            "action": "create_confession",
            "agent": agent.name,
            "confession_id": confession.id,
            "summary": f"{agent.name} dropped a confession",
        }

    # ── Action: Vote on Thread ───────────────────────────────

    async def _action_vote_thread(self, db: AsyncSession) -> dict | None:
        """Agent votes on a thread (personality-driven up/down)."""
        agent = await self._pick_random_agent(db)
        if not agent:
            return None

        # Pick a thread to vote on (prefer recent ones)
        result = await db.execute(
            select(Thread).options(selectinload(Thread.author))
            .order_by(desc(Thread.created_at))
            .limit(20)
        )
        threads = result.scalars().all()
        threads = [t for t in threads if t.author_id != agent.id]
        if not threads:
            return None

        thread = random.choice(threads)
        traits = PERSONALITY_TRAITS.get(agent.personality.value, PERSONALITY_TRAITS["neutral_analyst"])
        is_rival = _are_rivals(agent.team_allegiance, thread.author.team_allegiance)

        # Decide vote direction
        if is_rival:
            direction = "down" if random.random() < 0.65 else "up"
        elif random.random() < traits["vote_positivity"]:
            direction = "up"
        else:
            direction = "down"

        if direction == "up":
            thread.karma += 1
            thread.author.karma += 1
        else:
            thread.karma -= 1
            thread.author.karma = max(0, thread.author.karma - 1)

        agent.last_active = datetime.utcnow()
        await self._log_activity(
            db, agent.id, "vote", "thread", thread.id, direction
        )
        await db.commit()

        return {
            "action": "vote_thread",
            "agent": agent.name,
            "thread_id": thread.id,
            "direction": direction,
            "summary": f"{agent.name} {direction}voted '{thread.title[:30]}...'",
        }

    # ── Action: Vote on Comment ──────────────────────────────

    async def _action_vote_comment(self, db: AsyncSession) -> dict | None:
        """Agent votes on a comment."""
        agent = await self._pick_random_agent(db)
        if not agent:
            return None

        result = await db.execute(
            select(Comment).options(selectinload(Comment.author))
            .order_by(desc(Comment.created_at))
            .limit(30)
        )
        comments = result.scalars().all()
        comments = [c for c in comments if c.author_id != agent.id]
        if not comments:
            return None

        comment = random.choice(comments)
        traits = PERSONALITY_TRAITS.get(agent.personality.value, PERSONALITY_TRAITS["neutral_analyst"])
        is_rival = _are_rivals(agent.team_allegiance, comment.author.team_allegiance)

        if is_rival:
            direction = "down" if random.random() < 0.6 else "up"
        elif random.random() < traits["vote_positivity"]:
            direction = "up"
        else:
            direction = "down"

        if direction == "up":
            comment.karma += 1
            comment.author.karma += 1
        else:
            comment.karma -= 1
            comment.author.karma = max(0, comment.author.karma - 1)

        agent.last_active = datetime.utcnow()
        await self._log_activity(db, agent.id, "vote", "comment", comment.id, direction)
        await db.commit()

        return {
            "action": "vote_comment",
            "agent": agent.name,
            "comment_id": comment.id,
            "direction": direction,
            "summary": f"{agent.name} {direction}voted a comment by {comment.author.name}",
        }

    # ── Action: React to Confession ──────────────────────────

    async def _action_react_confession(self, db: AsyncSession) -> dict | None:
        """Agent reacts to a confession (absolve/damn/fire)."""
        agent = await self._pick_random_agent(db)
        if not agent:
            return None

        result = await db.execute(
            select(Confession).options(selectinload(Confession.agent))
            .order_by(desc(Confession.created_at))
            .limit(15)
        )
        confessions = result.scalars().all()
        confessions = [c for c in confessions if c.agent_id != agent.id]
        if not confessions:
            return None

        confession = random.choice(confessions)
        traits = PERSONALITY_TRAITS.get(agent.personality.value, PERSONALITY_TRAITS["neutral_analyst"])

        # Personality-driven reaction
        if agent.personality == AgentPersonality.PASSIONATE_FAN:
            reaction = random.choices(
                ["fire", "damn", "absolve"], weights=[50, 30, 20], k=1
            )[0]
        elif agent.personality == AgentPersonality.STATS_NERD:
            reaction = random.choices(
                ["damn", "absolve", "fire"], weights=[40, 40, 20], k=1
            )[0]
        else:
            reaction = random.choice(["absolve", "damn", "fire"])

        if reaction == "absolve":
            confession.absolves += 1
        elif reaction == "damn":
            confession.damns += 1
        elif reaction == "fire":
            confession.fires += 1

        agent.last_active = datetime.utcnow()
        await self._log_activity(
            db, agent.id, "react", "confession", confession.id, reaction
        )
        await db.commit()

        return {
            "action": "react_confession",
            "agent": agent.name,
            "confession_id": confession.id,
            "reaction": reaction,
            "summary": f"{agent.name} reacted '{reaction}' to a confession",
        }

    # ══════════════════════════════════════════════════════════
    #  Helper Methods
    # ══════════════════════════════════════════════════════════

    async def _pick_random_agent(self, db: AsyncSession) -> Agent | None:
        """Pick a random active agent."""
        result = await db.execute(select(Agent).where(Agent.is_active == True))
        agents = result.scalars().all()
        return random.choice(agents) if agents else None

    async def _pick_random_league(self, db: AsyncSession) -> League | None:
        """Pick a random league (weighted toward popular ones)."""
        result = await db.execute(select(League))
        leagues = result.scalars().all()
        return random.choice(leagues) if leagues else None

    async def _pick_thread_to_reply(
        self, db: AsyncSession, exclude_author: int | None = None
    ) -> Thread | None:
        """Pick a thread to reply to — prefers hot threads."""
        query = (
            select(Thread)
            .options(
                selectinload(Thread.author),
                selectinload(Thread.comments).selectinload(Comment.author),
            )
            .order_by(desc(Thread.karma), desc(Thread.created_at))
            .limit(20)
        )
        result = await db.execute(query)
        threads = result.scalars().all()

        if exclude_author:
            threads = [t for t in threads if t.author_id != exclude_author]

        if not threads:
            return None

        # Weighted selection — hot threads get more attention
        weights = [max(1, t.karma + 5) for t in threads]
        return random.choices(threads, weights=weights, k=1)[0]

    async def _pick_comment_to_reply(
        self, db: AsyncSession, exclude_author: int | None = None
    ) -> Comment | None:
        """Pick a comment to reply to."""
        query = (
            select(Comment)
            .options(selectinload(Comment.author))
            .order_by(desc(Comment.created_at))
            .limit(30)
        )
        result = await db.execute(query)
        comments = result.scalars().all()

        if exclude_author:
            comments = [c for c in comments if c.author_id != exclude_author]

        return random.choice(comments) if comments else None

    async def _log_activity(
        self, db: AsyncSession, agent_id: int,
        action_type: str, target_type: str | None,
        target_id: int | None, detail: str | None
    ):
        """Log an agent activity."""
        activity = AgentActivity(
            agent_id=agent_id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
        )
        db.add(activity)


# ══════════════════════════════════════════════════════════════
#  Singleton engine instance
# ══════════════════════════════════════════════════════════════
engine = AutonomousEngine()
