"""Ollama API client for LLM-based sandwich detection."""

import asyncio
import logging
import os
from typing import Optional, Tuple

import aiohttp

logger = logging.getLogger(__name__)

# Environment defaults
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL", "http://localhost:29134"
)
OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL", "gemma4:26b-a4b-it-q4_K_M"
)
OLLAMA_TIMEOUT = 30  # seconds


SANDWICH_PROMPT = (
    "Analyze the following transaction history for sandwich "
    "attack patterns. A sandwich attack occurs when an attacker "
    "places transactions before and after a victim's transaction "
    "in the same block to extract value.\n\n"
    "Transaction history: {tx_history}\n\n"
    "Respond with exactly one of:\n"
    "GAMING_DETECTED: <reason in one sentence>\n"
    "CLEAN: <reason in one sentence>"
)


async def call_ollama(
    prompt: str,
    model: str = OLLAMA_MODEL,
    base_url: str = OLLAMA_BASE_URL,
    timeout: int = OLLAMA_TIMEOUT,
) -> Optional[str]:
    """Call Ollama API for text generation.

    Args:
        prompt: Input prompt
        model: Model name
        base_url: Ollama API base URL
        timeout: Request timeout in seconds

    Returns:
        Generated text response, or None on error
    """
    try:
        url = f"{base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("response", "").strip()
                else:
                    logger.warning(f"Ollama API returned {resp.status}")
                    return None
    except asyncio.TimeoutError:
        logger.warning(f"Ollama API timeout after {timeout}s")
        return None
    except Exception as e:
        logger.warning(f"Ollama API error: {e}")
        return None


def parse_llm_response(response: str) -> Tuple[bool, str]:
    """Parse LLM response to extract gaming detection and reason.

    Args:
        response: LLM response text

    Returns:
        (gaming_detected, reason)
    """
    if not response:
        return False, "No LLM response"

    if "GAMING_DETECTED" in response:
        reason = response.split("GAMING_DETECTED:")[-1].strip()
        return True, reason or "Gaming detected"
    elif "CLEAN" in response:
        reason = response.split("CLEAN:")[-1].strip()
        return False, reason or "Transaction is clean"
    else:
        # Fallback: no clear marker
        return False, "Inconclusive LLM response"
