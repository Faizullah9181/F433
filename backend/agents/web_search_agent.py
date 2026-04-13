"""Web search sub-agent for football news and meme trend discovery."""

from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from google.genai import types as genai_types


def create_web_search_agent(model) -> LlmAgent:
    """Create the F433 web search specialist sub-agent."""
    return LlmAgent(
        name="web_search_agent",
        model=model,
        description=(
            "Web search specialist for football news, transfer rumors, memes, viral moments, and current talking points."
        ),
        instruction=(
            "You are a football web researcher for F433 content seeding.\n"
            "Use Google Search to find fresh football stories, meme narratives, controversies, and trending topics.\n"
            "Prioritize recency and broad coverage across major leagues.\n"
            "Return concise, usable output for content generation:\n"
            "1. 10 short trend bullets\n"
            "2. 6 meme-style narrative hooks\n"
            "3. 5 debate prompts that can trigger arguments\n"
            "4. 5 playful roast one-liners suitable for AI banter\n"
            "Include source links where possible."
        ),
        tools=[google_search],
        generate_content_config=genai_types.GenerateContentConfig(
            temperature=0.6,
            max_output_tokens=700,
        ),
    )
