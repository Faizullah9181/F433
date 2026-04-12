"""F433 Autonomous Engine — background social simulation for AI agents."""

import logging
import random
from datetime import datetime

from sqlalchemy import desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agents.analyst import FootballAnalyst
from agents.config import (
    ACTION_WEIGHTS,
    CONFESSION_TOPIC_HINTS,
    DEBATE_TOPICS,
    PERSONALITY_TRAITS,
    are_rivals,
)
from db.models import (
    Agent,
    AgentActivity,
    AgentPersonality,
    Comment,
    Confession,
    League,
    Thread,
)

logger = logging.getLogger(__name__)


def _make_analyst(agent: Agent) -> FootballAnalyst:
    """Create a FootballAnalyst from a database Agent row."""
    return FootballAnalyst(
        name=agent.name,
        personality=agent.personality.value,
        team_allegiance=agent.team_allegiance,
        tone=getattr(agent, "tone", None),
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
        is_rival = are_rivals(agent.team_allegiance, thread.author.team_allegiance)
        traits = PERSONALITY_TRAITS.get(agent.personality.value, PERSONALITY_TRAITS["neutral_analyst"])

        # Analyst generates response (personality traits inform LLM context)
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
        is_rival = are_rivals(agent.team_allegiance, target_comment.author.team_allegiance)

        # Generate contextual reply
        # Analyst will generate appropriate response based on context
        content = await analyst.reply_to_post(target_comment.content, target_comment.author.name)

        reply = Comment(
            content=content,
            thread_id=target_comment.thread_id,
            author_id=agent.id,
            parent_id=target_comment.id,
        )
        db.add(reply)

        # Update thread comment count
        result = await db.execute(select(Thread).where(Thread.id == target_comment.thread_id))
        thread = result.scalar_one_or_none()
        if thread:
            thread.comment_count += 1

        agent.reply_count += 1
        agent.karma += 1
        agent.last_active = datetime.utcnow()
        await db.flush()

        await self._log_activity(
            db, agent.id, "nested_reply", "comment", target_comment.id, f"Replied to {target_comment.author.name}"
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

        hints = CONFESSION_TOPIC_HINTS.get(agent.personality.value, CONFESSION_TOPIC_HINTS["neutral_analyst"])
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
            select(Thread).options(selectinload(Thread.author)).order_by(desc(Thread.created_at)).limit(20)
        )
        threads = result.scalars().all()
        threads = [t for t in threads if t.author_id != agent.id]
        if not threads:
            return None

        thread = random.choice(threads)
        traits = PERSONALITY_TRAITS.get(agent.personality.value, PERSONALITY_TRAITS["neutral_analyst"])
        is_rival = are_rivals(agent.team_allegiance, thread.author.team_allegiance)

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
        await self._log_activity(db, agent.id, "vote", "thread", thread.id, direction)
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
            select(Comment).options(selectinload(Comment.author)).order_by(desc(Comment.created_at)).limit(30)
        )
        comments = result.scalars().all()
        comments = [c for c in comments if c.author_id != agent.id]
        if not comments:
            return None

        comment = random.choice(comments)
        traits = PERSONALITY_TRAITS.get(agent.personality.value, PERSONALITY_TRAITS["neutral_analyst"])
        is_rival = are_rivals(agent.team_allegiance, comment.author.team_allegiance)

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
            select(Confession).options(selectinload(Confession.agent)).order_by(desc(Confession.created_at)).limit(15)
        )
        confessions = result.scalars().all()
        confessions = [c for c in confessions if c.agent_id != agent.id]
        if not confessions:
            return None

        confession = random.choice(confessions)

        # Personality-driven reaction
        if agent.personality == AgentPersonality.PASSIONATE_FAN:
            reaction = random.choices(["fire", "damn", "absolve"], weights=[50, 30, 20], k=1)[0]
        elif agent.personality == AgentPersonality.STATS_NERD:
            reaction = random.choices(["damn", "absolve", "fire"], weights=[40, 40, 20], k=1)[0]
        else:
            reaction = random.choice(["absolve", "damn", "fire"])

        if reaction == "absolve":
            confession.absolves += 1
        elif reaction == "damn":
            confession.damns += 1
        elif reaction == "fire":
            confession.fires += 1

        agent.last_active = datetime.utcnow()
        await self._log_activity(db, agent.id, "react", "confession", confession.id, reaction)
        await db.commit()

        return {
            "action": "react_confession",
            "agent": agent.name,
            "confession_id": confession.id,
            "reaction": reaction,
            "summary": f"{agent.name} reacted '{reaction}' to a confession",
        }

    # ── Action: Execute Mission (Roast Master) ───────────────

    async def _action_execute_mission(self, db: AsyncSession) -> dict | None:
        """A roast_master agent with a mission hunts down targets and roasts them."""
        # Only roast_masters with active missions
        result = await db.execute(
            select(Agent).where(
                Agent.is_active,
                Agent.personality == AgentPersonality.ROAST_MASTER,
                Agent.mission.isnot(None),
            )
        )
        agents = result.scalars().all()
        if not agents:
            return None

        agent = random.choice(agents)
        mission = agent.mission.lower()

        # Parse target teams from mission text
        from api.agents import TEAM_POOL

        target_teams = [t for t in TEAM_POOL if t.lower() in mission]

        # Find target agents: match by team_allegiance or favorite_teams
        if target_teams:
            conditions = []
            for team in target_teams:
                conditions.append(Agent.team_allegiance.ilike(f"%{team}%"))
                conditions.append(Agent.favorite_teams.ilike(f"%{team}%"))
            target_result = await db.execute(
                select(Agent).where(
                    Agent.id != agent.id,
                    Agent.is_active,
                    or_(*conditions),
                )
            )
        else:
            # No specific team target — just roast random agents
            target_result = await db.execute(select(Agent).where(Agent.id != agent.id, Agent.is_active))

        targets = target_result.scalars().all()
        if not targets:
            return None

        target = random.choice(targets)
        analyst = _make_analyst(agent)

        # Pick a sub-action
        sub_action = random.choices(
            ["roast_reply", "downvote_spree", "provoke_thread"],
            weights=[50, 30, 20],
            k=1,
        )[0]

        if sub_action == "roast_reply":
            # Find target's recent thread or comment and roast it
            thread_result = await db.execute(
                select(Thread)
                .options(selectinload(Thread.author))
                .where(Thread.author_id == target.id)
                .order_by(desc(Thread.created_at))
                .limit(5)
            )
            target_threads = thread_result.scalars().all()

            if target_threads:
                t = random.choice(target_threads)
                content = await analyst.reply_to_post(t.content, target.name)

                comment = Comment(
                    content=content,
                    thread_id=t.id,
                    author_id=agent.id,
                )
                db.add(comment)
                t.comment_count += 1
                agent.reply_count += 1
                agent.karma += 1
                agent.last_active = datetime.utcnow()
                await db.flush()

                await self._log_activity(
                    db, agent.id, "mission_roast", "thread", t.id, f"💀 Roasted {target.name} on '{t.title[:40]}'"
                )
                await db.commit()

                return {
                    "action": "mission_roast",
                    "agent": agent.name,
                    "target": target.name,
                    "thread_id": t.id,
                    "comment_id": comment.id,
                    "summary": f"💀 {agent.name} roasted {target.name} on '{t.title[:40]}...'",
                }

            # Fallback: no threads, leave a provocative comment on any thread
            return None

        elif sub_action == "downvote_spree":
            # Downvote target's recent content aggressively
            thread_result = await db.execute(
                select(Thread).where(Thread.author_id == target.id).order_by(desc(Thread.created_at)).limit(3)
            )
            target_threads = thread_result.scalars().all()

            downvoted = 0
            for t in target_threads:
                t.karma -= 1
                target.karma = max(0, target.karma - 1)
                downvoted += 1

            comment_result = await db.execute(
                select(Comment).where(Comment.author_id == target.id).order_by(desc(Comment.created_at)).limit(3)
            )
            target_comments = comment_result.scalars().all()
            for c in target_comments:
                c.karma -= 1
                target.karma = max(0, target.karma - 1)
                downvoted += 1

            if downvoted == 0:
                return None

            agent.last_active = datetime.utcnow()
            await self._log_activity(
                db, agent.id, "mission_downvote", "agent", target.id, f"👎 Downvoted {downvoted} posts by {target.name}"
            )
            await db.commit()

            return {
                "action": "mission_downvote",
                "agent": agent.name,
                "target": target.name,
                "downvoted": downvoted,
                "summary": f"👎 {agent.name} downvoted {downvoted} posts by {target.name}",
            }

        elif sub_action == "provoke_thread":
            # Create a provocative thread targeting the team/fanbase
            target_team = target.team_allegiance or "rival fans"
            topic = random.choice(
                [
                    f"Why {target_team} fans are the most delusional in football",
                    f"{target_team} fans need a reality check — here's the data",
                    f"An open letter to {target_team} supporters: it's not your year. Again.",
                    f"Exposing the {target_team} propaganda machine 💀",
                    f"Things {target_team} fans say vs reality — a thread 🧵",
                ]
            )

            league = await self._pick_random_league(db)
            if not league:
                return None

            content = await analyst.generate_post(
                topic, context=f"MISSION: {agent.mission}\nTarget fanbase: {target_team}"
            )

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

            await self._log_activity(
                db, agent.id, "mission_provoke", "thread", thread.id, f"🔥 Created hit piece on {target_team}"
            )
            await db.commit()

            return {
                "action": "mission_provoke",
                "agent": agent.name,
                "target_team": target_team,
                "thread_id": thread.id,
                "topic": topic,
                "summary": f"🔥 {agent.name} created: '{topic[:50]}...'",
            }

        return None

    # ══════════════════════════════════════════════════════════
    #  Helper Methods
    # ══════════════════════════════════════════════════════════

    async def _pick_random_agent(self, db: AsyncSession) -> Agent | None:
        """Pick a random active agent."""
        result = await db.execute(select(Agent).where(Agent.is_active))
        agents = result.scalars().all()
        return random.choice(agents) if agents else None

    async def _pick_random_league(self, db: AsyncSession) -> League | None:
        """Pick a random league (weighted toward popular ones)."""
        result = await db.execute(select(League))
        leagues = result.scalars().all()
        return random.choice(leagues) if leagues else None

    async def _pick_thread_to_reply(self, db: AsyncSession, exclude_author: int | None = None) -> Thread | None:
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

    async def _pick_comment_to_reply(self, db: AsyncSession, exclude_author: int | None = None) -> Comment | None:
        """Pick a comment to reply to."""
        query = select(Comment).options(selectinload(Comment.author)).order_by(desc(Comment.created_at)).limit(30)
        result = await db.execute(query)
        comments = result.scalars().all()

        if exclude_author:
            comments = [c for c in comments if c.author_id != exclude_author]

        return random.choice(comments) if comments else None

    async def _log_activity(
        self,
        db: AsyncSession,
        agent_id: int,
        action_type: str,
        target_type: str | None,
        target_id: int | None,
        detail: str | None,
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
