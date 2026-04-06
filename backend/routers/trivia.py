"""
Trivia router — Locker Room gate.

Generates football trivia questions via AI and records every attempt (right or wrong).
"""
import json
import logging
import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from database.connection import get_db
from database.models import LockerRoomEntry

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Fallback questions (used when AI is unavailable) ────────────
FALLBACK_QUESTIONS = [
    {
        "question": "Which country has won the most FIFA World Cups?",
        "options": ["Germany", "Brazil", "Argentina", "Italy"],
        "answer": "Brazil",
    },
    {
        "question": "Who holds the record for most goals in a single calendar year?",
        "options": ["Cristiano Ronaldo", "Lionel Messi", "Gerd Müller", "Pelé"],
        "answer": "Lionel Messi",
    },
    {
        "question": "Which club has won the most UEFA Champions League titles?",
        "options": ["AC Milan", "Barcelona", "Real Madrid", "Bayern Munich"],
        "answer": "Real Madrid",
    },
    {
        "question": "In which year was the first FIFA World Cup held?",
        "options": ["1928", "1930", "1934", "1950"],
        "answer": "1930",
    },
    {
        "question": "Who scored the 'Hand of God' goal?",
        "options": ["Pelé", "Diego Maradona", "Zinedine Zidane", "Ronaldinho"],
        "answer": "Diego Maradona",
    },
    {
        "question": "Which Premier League team is nicknamed 'The Gunners'?",
        "options": ["Chelsea", "Tottenham", "Arsenal", "Liverpool"],
        "answer": "Arsenal",
    },
    {
        "question": "What does 'xG' stand for in football analytics?",
        "options": ["Extra Goals", "Expected Goals", "Exact Goals", "Extreme Goals"],
        "answer": "Expected Goals",
    },
    {
        "question": "Which footballer has won the most Ballon d'Or awards?",
        "options": ["Cristiano Ronaldo", "Lionel Messi", "Michel Platini", "Johan Cruyff"],
        "answer": "Lionel Messi",
    },
    {
        "question": "What is the maximum number of substitutions allowed in a standard FIFA match?",
        "options": ["3", "4", "5", "6"],
        "answer": "5",
    },
    {
        "question": "Which country hosted the 2022 FIFA World Cup?",
        "options": ["Russia", "Qatar", "Saudi Arabia", "UAE"],
        "answer": "Qatar",
    },
    {
        "question": "Who is the all-time top scorer in Premier League history?",
        "options": ["Wayne Rooney", "Thierry Henry", "Alan Shearer", "Andrew Cole"],
        "answer": "Alan Shearer",
    },
    {
        "question": "Which team completed 'The Invincibles' season in 2003-04?",
        "options": ["Manchester United", "Arsenal", "Chelsea", "Liverpool"],
        "answer": "Arsenal",
    },
    {
        "question": "What colour card results in a player being sent off?",
        "options": ["Yellow", "Red", "Blue", "Green"],
        "answer": "Red",
    },
    {
        "question": "Which player is known as 'CR7'?",
        "options": ["Kaká", "Cristiano Ronaldo", "Ronaldinho", "Romário"],
        "answer": "Cristiano Ronaldo",
    },
    {
        "question": "How many players are on each team during a standard football match?",
        "options": ["9", "10", "11", "12"],
        "answer": "11",
    },
]


async def _generate_ai_question() -> dict | None:
    """Try to generate a football trivia question via ADK agent. Returns None on failure."""
    try:
        from google.adk.agents import LlmAgent
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types as genai_types
        from agents.analyst import _get_model

        agent = LlmAgent(
            name="trivia_master",
            model=_get_model(),
            description="Football trivia question generator",
            instruction="""You are a football trivia master. Generate ONE multiple-choice football question.
The question should test real football knowledge — covering history, players, teams, tournaments, rules, records, or tactics.
Vary the difficulty: mix easy, medium, and hard questions.
Cover a wide range of topics: World Cups, club football, individual records, transfers, managers, stadiums, rules, iconic moments, etc.

You MUST respond with ONLY valid JSON in this exact format, nothing else:
{"question": "Your question here?", "options": ["A", "B", "C", "D"], "answer": "The correct option"}

Rules:
- Exactly 4 options, one must be the correct answer
- The correct answer must exactly match one of the options
- Questions must be factually correct
- No duplicate options
- Keep the question concise (1-2 sentences max)""",
            generate_content_config=genai_types.GenerateContentConfig(
                temperature=1.0,
                max_output_tokens=300,
            ),
        )

        session_service = InMemorySessionService()
        runner = Runner(agent=agent, app_name="f433_trivia", session_service=session_service)
        session = await session_service.create_session(app_name="f433_trivia", user_id="gate")

        prompts = [
            "Generate a football trivia question about a legendary player.",
            "Generate a football trivia question about a World Cup moment.",
            "Generate a football trivia question about club football history.",
            "Generate a football trivia question about football rules or tactics.",
            "Generate a football trivia question about transfer records.",
            "Generate a football trivia question about a national team.",
            "Generate a football trivia question about a specific tournament.",
            "Generate a football trivia question about a stadium or derby.",
            "Generate a football trivia question about a manager or coaching legend.",
            "Generate a football trivia question about football records and statistics.",
        ]

        content = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=random.choice(prompts))],
        )

        final_text = ""
        async for event in runner.run_async(user_id="gate", session_id=session.id, new_message=content):
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_text += part.text

        # Parse JSON from response (strip markdown fences if present)
        cleaned = final_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

        data = json.loads(cleaned)

        # Validate structure
        if (
            isinstance(data.get("question"), str)
            and isinstance(data.get("options"), list)
            and len(data["options"]) == 4
            and isinstance(data.get("answer"), str)
            and data["answer"] in data["options"]
        ):
            return data

        logger.warning(f"AI trivia question failed validation: {data}")
        return None

    except Exception as e:
        logger.warning(f"AI trivia generation failed, using fallback: {e}")
        return None


# ── Schemas ─────────────────────────────────────────────────────

class TriviaQuestion(BaseModel):
    question: str
    options: list[str]

class TriviaAnswer(BaseModel):
    session_id: str
    question: str
    options: list[str]
    correct_answer: str
    user_answer: str

class TriviaResult(BaseModel):
    is_correct: bool
    correct_answer: str
    message: str


# ── Endpoints ───────────────────────────────────────────────────

@router.get("/question", response_model=TriviaQuestion)
async def get_trivia_question():
    """Generate a random football trivia question (AI-powered with fallback)."""
    q = await _generate_ai_question()
    if q is None:
        q = random.choice(FALLBACK_QUESTIONS)
    # Shuffle options so correct answer isn't always in the same position
    options = list(q["options"])
    random.shuffle(options)
    return TriviaQuestion(question=q["question"], options=options)


@router.post("/answer", response_model=TriviaResult)
async def submit_trivia_answer(answer: TriviaAnswer, db: AsyncSession = Depends(get_db)):
    """Check answer and record the attempt in the database."""
    is_correct = answer.user_answer.strip().lower() == answer.correct_answer.strip().lower()

    entry = LockerRoomEntry(
        session_id=answer.session_id,
        question=answer.question,
        options=json.dumps(answer.options),
        correct_answer=answer.correct_answer,
        user_answer=answer.user_answer,
        is_correct=is_correct,
    )
    db.add(entry)
    await db.commit()

    if is_correct:
        messages = [
            "You're in. Welcome to the locker room. 🏟️",
            "Correct! A true football mind. Step inside. ⚽",
            "That's the right answer. You belong here. 🔥",
            "Nailed it. The locker room doors are open. 🚪",
        ]
    else:
        messages = [
            f"Wrong. The answer was {answer.correct_answer}. Try again, casual. ❌",
            f"Nope — it's {answer.correct_answer}. Real fans know this. Come back when you're ready. 🚫",
            f"Not quite. {answer.correct_answer} was the one. Football isn't for everyone. 😤",
            f"Incorrect. The answer is {answer.correct_answer}. Study up and try again. 📚",
        ]

    return TriviaResult(
        is_correct=is_correct,
        correct_answer=answer.correct_answer,
        message=random.choice(messages),
    )


@router.get("/stats")
async def get_trivia_stats(session_id: str | None = None, db: AsyncSession = Depends(get_db)):
    """Get trivia attempt stats — optionally filtered by session."""
    base = select(LockerRoomEntry)
    if session_id:
        base = base.where(LockerRoomEntry.session_id == session_id)

    total = (await db.execute(
        select(func.count()).select_from(LockerRoomEntry).where(
            LockerRoomEntry.session_id == session_id) if session_id else
        select(func.count()).select_from(LockerRoomEntry)
    )).scalar() or 0

    correct = (await db.execute(
        select(func.count()).select_from(LockerRoomEntry).where(
            LockerRoomEntry.is_correct == True,
            LockerRoomEntry.session_id == session_id) if session_id else
        select(func.count()).select_from(LockerRoomEntry).where(
            LockerRoomEntry.is_correct == True)
    )).scalar() or 0

    return {
        "total_attempts": total,
        "correct": correct,
        "wrong": total - correct,
        "accuracy": round(correct / total * 100, 1) if total > 0 else 0,
    }
