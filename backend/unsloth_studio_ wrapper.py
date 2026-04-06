"""Unsloth Studio + Google ADK Integration via LiteLLM."""

import asyncio
import requests

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

UNSLOTH_BASE_URL = "http://127.0.0.1:8888"
UNSLOTH_USERNAME = "unsloth"
UNSLOTH_PASSWORD = "12345678"


def unsloth_login(base_url: str, username: str, password: str) -> str:
    resp = requests.post(
        f"{base_url}/api/auth/login",
        json={"username": username, "password": password},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def get_inference_status(base_url: str, token: str) -> dict:
    resp = requests.get(
        f"{base_url}/v1/status",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def load_model(base_url: str, token: str, model_path: str) -> dict:
    resp = requests.post(
        f"{base_url}/v1/load",
        headers={"Authorization": f"Bearer {token}"},
        json={"model_path": model_path},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def list_downloaded_models(base_url: str, token: str) -> list[dict]:
    resp = requests.get(
        f"{base_url}/api/models/local",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("models", [])


def test_direct_chat(base_url: str, token: str):
    resp = requests.post(
        f"{base_url}/v1/chat/completions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "model": "default",
            "messages": [{"role": "user", "content": "Hello! Who are you?"}],
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 256,
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    print(f"  {data['choices'][0]['message']['content']}")
    return data


def get_weather(city: str) -> dict:
    """Get the current weather for a city.

    Args:
        city: The city name to get weather for.
    """
    weather_data = {
        "new york": "Sunny, 25°C",
        "london": "Cloudy, 15°C",
        "tokyo": "Rainy, 20°C",
        "mumbai": "Hot, 35°C",
    }
    city_lower = city.lower()
    if city_lower in weather_data:
        return {"status": "success", "report": f"Weather in {city}: {weather_data[city_lower]}"}
    return {"status": "error", "error_message": f"No weather data for '{city}'."}


def calculate(expression: str) -> dict:
    """Evaluate a simple math expression safely.

    Args:
        expression: A math expression like '2 + 2' or '100 / 5'.
    """
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return {"status": "error", "error_message": "Invalid characters in expression."}
    try:
        result = eval(expression)  # noqa: S307
        return {"status": "success", "result": str(result)}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


def create_adk_agent(token: str, model_name: str) -> Agent:
    return Agent(
        model=LiteLlm(
            model=f"hosted_vllm/{model_name}",
            api_base=f"{UNSLOTH_BASE_URL}/v1",
            api_key=token,
            extra_body={"stream": False},
        ),
        name="unsloth_assistant",
        description="A helpful assistant powered by a local Unsloth Studio model.",
        instruction=(
            "You are a helpful assistant running on a local Unsloth Studio model. "
            "You can check weather for cities and do simple math calculations. "
            "Be concise and helpful."
        ),
        tools=[get_weather, calculate],
    )


async def run_agent(user_message: str, token: str, model_name: str):
    agent = create_adk_agent(token, model_name)
    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name="unsloth_test", session_service=session_service)
    session = await session_service.create_session(app_name="unsloth_test", user_id="user1")

    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_message)],
    )

    print(f"\n>>> User: {user_message}")
    print(">>> Assistant: ", end="", flush=True)

    async for event in runner.run_async(
        user_id="user1", session_id=session.id, new_message=content
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text, end="", flush=True)
    print()


def main():
    print("=" * 60)
    print("Unsloth Studio + Google ADK Integration")
    print("=" * 60)

    print("\n[1] Logging in...")
    try:
        token = unsloth_login(UNSLOTH_BASE_URL, UNSLOTH_USERNAME, UNSLOTH_PASSWORD)
        print(f"    ✓ Token: {token[:20]}...")
    except Exception as e:
        print(f"    ✗ Login failed: {e}")
        return

    print("\n[2] Checking models...")
    try:
        status = get_inference_status(UNSLOTH_BASE_URL, token)
        active_model = status.get("active_model")
        available = [m["id"] for m in list_downloaded_models(UNSLOTH_BASE_URL, token)]

        if active_model:
            print(f"    ✓ Active: {active_model}")
        else:
            print("    ⚠ No model loaded.")

        if available:
            print("\n    Downloaded models:")
            for i, m in enumerate(available, 1):
                marker = " ← active" if m.lower() == (active_model or "").lower() else ""
                print(f"      [{i}] {m}{marker}")

            choice = input("\n    Switch model? Enter number (or Enter to skip): ").strip()
            if choice:
                idx = int(choice) - 1
                if 0 <= idx < len(available) and available[idx].lower() != (active_model or "").lower():
                    print(f"    Loading {available[idx]}...")
                    load_model(UNSLOTH_BASE_URL, token, available[idx])
                    active_model = available[idx]
                    print(f"    ✓ Switched to: {active_model}")

        if not active_model:
            print("    ✗ No model loaded.")
            return
    except Exception as e:
        print(f"    ✗ Failed: {e}")
        return

    print("\n[3] Direct API test...")
    try:
        test_direct_chat(UNSLOTH_BASE_URL, token)
        print("    ✓ Works!")
    except Exception as e:
        print(f"    ✗ Failed: {e}")
        return

    print("\n[4] Running ADK agent...")
    try:
        asyncio.run(run_agent("What's the weather in Tokyo?", token, active_model))
        asyncio.run(run_agent("Calculate 42 * 17 + 3", token, active_model))
        asyncio.run(run_agent("Tell me a short joke", token, active_model))
    except Exception as e:
        print(f"    ✗ ADK agent failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()