"""ADK Runner infrastructure — single session service, shared run helper."""

import logging

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

logger = logging.getLogger(__name__)

APP_NAME = "f433"
session_service = InMemorySessionService()


async def run_agent(agent: LlmAgent, prompt: str, user_id: str = "system") -> str:
    """Execute an ADK agent through the Runner pipeline and return final text."""
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
    session = await session_service.create_session(app_name=APP_NAME, user_id=user_id)
    content = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=prompt)],
    )

    final_text = ""
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=content,
        ):
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_text += part.text
    except Exception as e:
        logger.error(f"Agent run error [{agent.name}]: {e}")
        return f"*{agent.name} encountered an error*"

    return final_text.strip() or f"*{agent.name} has nothing to say*"
