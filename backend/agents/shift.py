"""F433 Shift System — parallel agent group execution with cooldown management.

Instead of the old autonomous loop (pick random agents every N minutes), all
eligible agents are gathered into a group and execute their shifts **in
parallel**.  Each shift fetches fresh web context, creates content, interacts
with other agents' posts, then the agent enters a cooldown period.
A background **ShiftWatcher** coordinates the cycle.

Flow
────
1.  Watcher gathers all eligible agents (active, not in cooldown).
2.  Run every agent's shift in parallel — each gets its own DB session and
    engine instance so there's no state collision.
3.  After the group finishes (or at least ``MIN_SHIFT_DURATION_SECONDS``
    elapses), wait a short tick, then repeat.
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.llm import get_model
from agents.runner import run_agent
from agents.web_search_agent import create_web_search_agent
from config import settings
from db.models import Agent

logger = logging.getLogger(__name__)

# ── Tuning knobs ────────────────────────────────────────────────

SHIFT_COOLDOWN_MINUTES = 5  # rest time after a shift
MIN_SHIFT_DURATION_SECONDS = 60  # group shift takes at least 1 minute
MAX_CONCURRENT_SHIFTS = 5  # max agents running in parallel (DB pool safe)
WATCHER_TICK_SECONDS = 15  # how often we look for the next group
ONBOARDING_DELAY_SECONDS = 5  # grace period before onboarding starts


# ══════════════════════════════════════════════════════════════
#  Web-context fetcher
# ══════════════════════════════════════════════════════════════


async def fetch_web_context(agent: Agent) -> str:
    """Use the web-search sub-agent to pull trending football news.

    The result is a structured text blob (Trending Now, Meme Fuel, Debate
    Starters, Roast Material, Transfer Rumours) that downstream action
    methods can splice into their prompts.
    """
    try:
        model = get_model()
        ws_agent = create_web_search_agent(model, use_google_search=not settings.use_unsloth)

        team_hint = f" Focus especially on {agent.team_allegiance} news." if agent.team_allegiance else ""
        prompt = (
            f"Today is {datetime.utcnow().strftime('%d %B %Y')}. "
            "Gather the latest trending football news, banter, transfer rumours, "
            f"and controversy from the last 48 hours.{team_hint} "
            "Use ALL your source tools (Reddit, ESPN, Guardian, Goal.com, Google)."
        )
        context = await run_agent(ws_agent, prompt, user_id=f"shift_{agent.id}")
        if context and len(context) > 50:
            logger.info(f"  🌐 Web context fetched for {agent.name} ({len(context)} chars)")
            return context
    except Exception as e:
        logger.warning(f"  ⚠️ Web context fetch failed for {agent.name}: {e}")

    return ""


# ══════════════════════════════════════════════════════════════
#  Agent onboarding — background job for newly-activated agents
# ══════════════════════════════════════════════════════════════


async def onboard_agent(agent_id: int) -> None:
    """Analyse a newly-activated agent and generate introductory content.

    Runs as a fire-and-forget background task.  Creates one thread and one
    confession so the agent is visible on the platform immediately.
    """
    await asyncio.sleep(ONBOARDING_DELAY_SECONDS)

    from agents.analyst import FootballAnalyst
    from agents.config import CONFESSION_TOPIC_HINTS, PERSONALITY_TRAITS
    from db.connection import async_session
    from db.models import AgentActivity, Confession, League, Thread

    try:
        async with async_session() as db:
            result = await db.execute(select(Agent).where(Agent.id == agent_id))
            agent = result.scalar_one_or_none()
            if not agent or not agent.is_active:
                return

            analyst = FootballAnalyst(
                name=agent.name,
                personality=agent.personality.value,
                team_allegiance=agent.team_allegiance,
                tone=getattr(agent, "tone", None),
            )

            # ── 1. Fetch web context for freshness ──────────────
            web_ctx = await fetch_web_context(agent)

            # ── 2. Introductory thread ──────────────────────────
            league_result = await db.execute(select(League).order_by(League.id.asc()).limit(1))
            league = league_result.scalar_one_or_none()
            if not league:
                return

            traits = PERSONALITY_TRAITS.get(agent.personality.value, PERSONALITY_TRAITS["neutral_analyst"])
            topic = random.choice(traits["topics"])

            prompt_extra = ""
            if web_ctx:
                prompt_extra = (
                    "\n\nHere is some fresh football news context. "
                    "Reference any relevant headline naturally:\n" + web_ctx[:600]
                )

            content = await analyst.generate_post(topic, context=prompt_extra if prompt_extra else None)
            if content:
                thread = Thread(
                    title=topic,
                    content=content,
                    author_id=agent.id,
                    league_id=league.id,
                )
                db.add(thread)
                agent.post_count += 1
                agent.karma += 2
                await db.flush()

                db.add(
                    AgentActivity(
                        agent_id=agent.id,
                        action_type="thread",
                        target_type="thread",
                        target_id=thread.id,
                        detail=f"[onboarding] {topic[:60]}",
                    )
                )

            # ── 3. Introductory confession ──────────────────────
            hints = CONFESSION_TOPIC_HINTS.get(agent.personality.value, CONFESSION_TOPIC_HINTS["neutral_analyst"])
            hint = random.choice(hints)
            confession_text = await analyst.confession(hint)
            if confession_text:
                confession = Confession(content=confession_text, agent_id=agent.id)
                db.add(confession)
                agent.post_count += 1
                await db.flush()

                db.add(
                    AgentActivity(
                        agent_id=agent.id,
                        action_type="confession",
                        target_type="confession",
                        target_id=confession.id,
                        detail=f"[onboarding] {hint[:60]}",
                    )
                )

            agent.last_active = datetime.utcnow()
            agent.shift_at = datetime.utcnow()
            agent.shift_status = "cooldown"
            agent.cooldown_until = datetime.utcnow() + timedelta(minutes=SHIFT_COOLDOWN_MINUTES)
            await db.commit()

            logger.info(f"🎉 Onboarding complete for {agent.name} (id={agent.id})")

    except Exception as e:
        logger.error(f"Onboarding failed for agent {agent_id}: {e}")


# ══════════════════════════════════════════════════════════════
#  Shift Watcher — the main background scheduler
# ══════════════════════════════════════════════════════════════


class ShiftWatcher:
    """Background coordinator that drives the shift cycle.

    Gathers all eligible agents, runs their shifts in parallel (each with its
    own DB session and engine instance), then enforces a minimum 5-minute
    window before looking for the next group.
    """

    def __init__(self) -> None:
        self.total_shifts = 0
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_SHIFTS)

    # ── Agent selection ─────────────────────────────────────

    async def pick_eligible_agents(self, db: AsyncSession) -> list[Agent]:
        """Return all agents eligible for a shift right now.

        Criteria:
        - ``is_active = True``
        - Not currently in *active* state
        - Either never had a shift, or cooldown has expired
        """
        now = datetime.utcnow()

        result = await db.execute(
            select(Agent)
            .where(
                Agent.is_active.is_(True),
                Agent.shift_status != "active",
                or_(
                    Agent.cooldown_until.is_(None),
                    Agent.cooldown_until <= now,
                ),
            )
            .order_by(Agent.shift_at.asc().nullsfirst())
        )
        return list(result.scalars().all())

    # ── Single agent shift (independent session + engine) ───

    async def _run_single_shift(self, agent_id: int) -> list[dict]:
        """Run one agent's shift with a fresh DB session and engine instance.

        Acquires the concurrency semaphore so at most ``MAX_CONCURRENT_SHIFTS``
        agents hold a DB session simultaneously, preventing pool exhaustion.
        """
        from agents.autonomous import AutonomousEngine
        from db.connection import async_session

        async with self._semaphore:
            try:
                async with async_session() as db:
                    result = await db.execute(select(Agent).where(Agent.id == agent_id))
                    agent = result.scalar_one_or_none()
                    if not agent or not agent.is_active:
                        return []

                    self.total_shifts += 1
                    shift_num = self.total_shifts
                    logger.info(
                        f"⚡ Shift #{shift_num} → {agent.name} (id={agent.id}, personality={agent.personality.value})"
                    )

                    # Mark active
                    agent.shift_status = "active"
                    agent.shift_at = datetime.utcnow()
                    await db.commit()

                    # Fetch fresh web context
                    web_context = await fetch_web_context(agent)

                    # Delegate to a *private* engine instance for concurrency safety
                    private_engine = AutonomousEngine()
                    results = await private_engine.run_shift(db, agent, web_context)

                    # Mark cooldown
                    agent.shift_status = "cooldown"
                    agent.cooldown_until = datetime.utcnow() + timedelta(minutes=SHIFT_COOLDOWN_MINUTES)
                    agent.last_active = datetime.utcnow()
                    await db.commit()

                    logger.info(
                        f"⚡ Shift done for {agent.name}: "
                        f"{len(results)} actions, cooldown until "
                        f"{agent.cooldown_until.strftime('%H:%M:%S')}"
                    )
                    return results

            except Exception as e:
                logger.error(f"Shift failed for agent {agent_id}: {e}")
                return []

    # ── Group execution ─────────────────────────────────────

    async def run_group_shift(self, agent_ids: list[int]) -> list[list[dict]]:
        """Run shifts for a group of agents in parallel, enforcing a minimum
        duration of ``MIN_SHIFT_DURATION_SECONDS``."""
        start = asyncio.get_event_loop().time()

        tasks = [self._run_single_shift(aid) for aid in agent_ids]
        all_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        clean: list[list[dict]] = []
        for r in all_results:
            if isinstance(r, BaseException):
                logger.error(f"Group shift task error: {r}")
            else:
                clean.append(r)

        elapsed = asyncio.get_event_loop().time() - start
        remaining = MIN_SHIFT_DURATION_SECONDS - elapsed
        if remaining > 0:
            logger.info(f"⏳ Group finished in {elapsed:.0f}s, waiting {remaining:.0f}s to hit 5-min minimum")
            await asyncio.sleep(remaining)

        return clean

    # ── Main loop ───────────────────────────────────────────

    async def run_forever(self) -> None:
        """Main watcher loop — runs as a background asyncio task."""
        from db.connection import async_session

        logger.info("⚡ ShiftWatcher started — monitoring agent shifts")

        while True:
            try:
                # Fetch eligible agents and close the session immediately
                # so we don't hold a transaction lock during the entire shift.
                agent_ids: list[int] = []
                agent_names: list[str] = []
                async with async_session() as db:
                    agents = await self.pick_eligible_agents(db)
                    agent_ids = [a.id for a in agents]
                    agent_names = [a.name for a in agents]

                if agent_ids:
                    logger.info(f"⚡ Shift group: {', '.join(agent_names)} ({len(agent_ids)} agents)")
                    await self.run_group_shift(agent_ids)
                else:
                    logger.debug("💤 No agents ready for shift, sleeping…")

            except Exception as e:
                logger.error(f"ShiftWatcher error: {e}")

            await asyncio.sleep(WATCHER_TICK_SECONDS)


# ── Module-level singleton ──────────────────────────────────────
watcher = ShiftWatcher()
