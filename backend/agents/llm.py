"""LLM backend resolution — Google Gemini / Unsloth Studio via LiteLLM."""

import logging
import os

import requests

from config import settings

logger = logging.getLogger(__name__)

# ── ADK environment ─────────────────────────────────────────────

os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")
if settings.google_api_key:
    os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key)


# ── Unsloth Studio auth (cached) ───────────────────────────────

_unsloth_token: str | None = None
_unsloth_active_model: str | None = None


def _unsloth_login() -> str:
    """Authenticate with Unsloth Studio and cache the bearer token."""
    global _unsloth_token
    if _unsloth_token:
        return _unsloth_token
    resp = requests.post(
        f"{settings.unsloth_base_url}/api/auth/login",
        json={"username": settings.unsloth_username, "password": settings.unsloth_password},
        timeout=10,
    )
    resp.raise_for_status()
    _unsloth_token = resp.json()["access_token"]
    logger.info("Unsloth Studio login OK")
    return _unsloth_token


def _unsloth_get_active_model() -> str:
    """Discover the active model loaded in Unsloth Studio."""
    global _unsloth_active_model
    if _unsloth_active_model:
        return _unsloth_active_model
    token = _unsloth_login()
    resp = requests.get(
        f"{settings.unsloth_base_url}/v1/status",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    _unsloth_active_model = resp.json().get("active_model", "default")
    logger.info(f"Unsloth active model: {_unsloth_active_model}")
    return _unsloth_active_model


def _build_unsloth_model():
    """Build a LiteLlm model instance pointing at Unsloth Studio."""
    from google.adk.models.lite_llm import LiteLlm

    token = _unsloth_login()
    model_name = settings.unsloth_model or _unsloth_get_active_model()
    return LiteLlm(
        model=f"hosted_vllm/{model_name}",
        api_base=f"{settings.unsloth_base_url}/v1",
        api_key=token,
        extra_body={"stream": False},
    )


def get_model():
    """Return the ADK-compatible model object based on active backend setting."""
    if settings.use_unsloth:
        logger.info("Using Unsloth Studio LLM backend")
        try:
            return _build_unsloth_model()
        except requests.RequestException as exc:
            logger.warning(
                "Unsloth unavailable at %s (%s). Falling back to Gemini model '%s'.",
                settings.unsloth_base_url,
                exc,
                settings.gemini_model,
            )
            return settings.gemini_model
    logger.debug("Using Google Gemini LLM backend")
    return settings.gemini_model
