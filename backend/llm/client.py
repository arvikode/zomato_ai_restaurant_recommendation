"""
LLM client - Gemini (default) with Grok fallback; optional Ollama (local).
Try Gemini first; if it fails and GROK_API_KEY is set, try Grok.
Set LLM_PROVIDER=gemini (default), grok, or ollama.
"""

import json
import logging
import os
import re
from typing import Any

import httpx

from backend.llm.prompts import build_system_prompt, build_user_prompt

logger = logging.getLogger(__name__)

# Default: Gemini, with Grok as fallback when Gemini fails
LLM_PROVIDER_DEFAULT = "gemini"


def _get_ollama_config() -> tuple[str, str]:
    """Read Ollama (local) config. No API key needed."""
    base_url = (os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434/v1").rstrip("/")
    model = (os.getenv("OLLAMA_MODEL") or "llama3.2").strip()
    return base_url, model


def _get_gemini_config() -> tuple[str, str]:
    """Read Gemini config from environment."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
    return api_key, model


def _get_grok_config() -> tuple[str, str, str]:
    """Read Grok config from environment."""
    api_key = os.getenv("GROK_API_KEY", "")
    model = os.getenv("GROK_MODEL", "grok-4")
    base_url = os.getenv("GROK_BASE_URL", "https://api.x.ai/v1").rstrip("/")
    return api_key, model, base_url


def _is_grok_configured() -> bool:
    """True if Grok can be used (for fallback)."""
    api_key = os.getenv("GROK_API_KEY", "").strip()
    return bool(api_key and api_key != "dummy-key-replace-me")


def _extract_json(text: str) -> dict | None:
    """Extract JSON object from response, handling markdown code blocks."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _call_gemini(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    """Call Gemini generateContent API. Returns {'text': str} or {'error': str}."""
    api_key, model = _get_gemini_config()
    if not api_key:
        return {"error": "GEMINI_API_KEY is not configured. Set it in .env (get a key from https://aistudio.google.com/apikey)."}
    if api_key.strip().lower() in ("dummy", "your-api-key-here", ""):
        return {"error": "GEMINI_API_KEY is still the placeholder. Replace it in .env with a real key from https://aistudio.google.com/apikey."}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0},
    }

    verify_ssl = os.getenv("LLM_VERIFY_SSL", "true").strip().lower() not in ("0", "false", "no")

    try:
        with httpx.Client(timeout=60.0, verify=verify_ssl) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        body = (e.response.text or "").strip()[:500]
        logger.exception("Gemini API error: %s", body)
        return {"error": f"LLM API error: {e.response.status_code}. {body}" if body else f"LLM API error: {e.response.status_code}"}
    except httpx.RequestError as e:
        logger.exception("Gemini request failed: %s", e)
        return {"error": f"LLM request failed: {e!s}"}

    data = response.json()
    candidates = data.get("candidates") or []
    if not candidates:
        return {"error": "Empty LLM response (no candidates)"}
    parts = candidates[0].get("content", {}).get("parts") or []
    if not parts:
        return {"error": "Empty LLM response (no parts)"}
    text = parts[0].get("text", "").strip()
    if not text:
        return {"error": "Empty LLM response"}
    return {"text": text}


def _call_ollama(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    """Call local Ollama (OpenAI-compatible). No API key. Returns {'text': str} or {'error': str}."""
    base_url, model = _get_ollama_config()
    url = f"{base_url}/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0,
        "stream": False,
    }

    try:
        # Local LLM can be slower; use 120s timeout
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
    except httpx.ConnectError as e:
        logger.exception("Ollama connection failed: %s", e)
        return {"error": "Cannot connect to Ollama. Start it with: ollama serve (and run 'ollama pull <model>')."}
    except httpx.HTTPStatusError as e:
        body = (e.response.text or "").strip()[:500]
        logger.exception("Ollama API error: %s", body)
        return {"error": f"LLM API error: {e.response.status_code}. {body}" if body else f"LLM API error: {e.response.status_code}"}
    except httpx.RequestError as e:
        logger.exception("Ollama request failed: %s", e)
        return {"error": f"LLM request failed: {e!s}"}

    data = response.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        return {"error": "Empty LLM response"}
    return {"text": content}


def _call_grok(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    """Call Grok (OpenAI-compatible) chat/completions. Returns {'text': str} or {'error': str}."""
    api_key, model, base_url = _get_grok_config()
    if not api_key:
        return {"error": "GROK_API_KEY is not configured. Set it in .env (get a key from https://console.x.ai)."}
    if api_key.strip() == "dummy-key-replace-me":
        return {"error": "GROK_API_KEY is still the placeholder. Replace it in .env with a real key from https://console.x.ai."}

    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0,
    }

    verify_ssl = os.getenv("LLM_VERIFY_SSL", "true").strip().lower() not in ("0", "false", "no")

    try:
        with httpx.Client(timeout=60.0, verify=verify_ssl) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        body = (e.response.text or "").strip()[:500]
        logger.exception("Grok API error: %s", body)
        return {"error": f"LLM API error: {e.response.status_code}. {body}" if body else f"LLM API error: {e.response.status_code}"}
    except httpx.RequestError as e:
        logger.exception("Grok request failed: %s", e)
        return {"error": "LLM request failed"}

    data = response.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        return {"error": "Empty LLM response"}
    return {"text": content}


def rank_restaurants(
    restaurants: list[dict],
    city: str,
    price_category: str,
    limit: int,
) -> dict[str, Any]:
    """
    Call LLM: Gemini (default) with Grok fallback; or grok/ollama only.
    Returns parsed recommendations or error dict.
    """
    if not restaurants:
        return {"error": "No restaurants to rank"}

    provider = (os.getenv("LLM_PROVIDER") or LLM_PROVIDER_DEFAULT).strip().lower()
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(restaurants, city, price_category, limit)

    if provider == "grok":
        result = _call_grok(system_prompt, user_prompt)
    elif provider == "ollama":
        result = _call_ollama(system_prompt, user_prompt)
    else:
        # default: Gemini first, then Grok fallback
        result = _call_gemini(system_prompt, user_prompt)
        if "error" in result and _is_grok_configured():
            logger.info("Gemini failed, trying Grok fallback: %s", result.get("error", "")[:80])
            result = _call_grok(system_prompt, user_prompt)

    if "error" in result:
        return result

    content = result.get("text", "")
    parsed = _extract_json(content)
    if not parsed:
        return {"error": "Invalid JSON in LLM response"}

    if "recommendations" not in parsed or not isinstance(parsed["recommendations"], list):
        return {"error": "LLM response missing recommendations array"}

    return parsed
