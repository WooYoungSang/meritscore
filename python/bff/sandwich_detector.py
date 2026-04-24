"""LLM-based sandwich attack detection with fallback to heuristic."""

import logging
from typing import Tuple

from .analyzer import detect_sandwich as detect_sandwich_heuristic
from .ollama_client import SANDWICH_PROMPT, call_ollama, parse_llm_response

logger = logging.getLogger(__name__)


async def detect_sandwich_llm(
    address: str,
    tx_history: list,
    mode: str = "Direct",
) -> Tuple[bool, str, float]:
    """Detect sandwich attacks using LLM (Ollama) with fallback.

    Args:
        address: Ethereum address
        tx_history: List of transaction hashes
        mode: Detection mode ("Direct" for LLM)

    Returns:
        (gaming_detected, reason, merit_penalty)
        - gaming_detected: bool
        - reason: explanation string
        - merit_penalty: float in [0.0, 1.0]
            - 0.0 if clean
            - 0.1 if gaming detected
    """
    if not tx_history:
        return False, "No transaction history provided", 0.0

    # Format transaction history for LLM
    tx_str = (
        ", ".join(tx_history)
        if isinstance(tx_history, list)
        else str(tx_history)
    )
    prompt = SANDWICH_PROMPT.format(tx_history=tx_str)

    # Call Ollama
    llm_response = await call_ollama(prompt)

    if llm_response:
        gaming_detected, reason = parse_llm_response(llm_response)
        merit_penalty = 0.1 if gaming_detected else 0.0
        logger.info(
            f"LLM detection: {gaming_detected}, penalty: {merit_penalty}"
        )
        return gaming_detected, reason, merit_penalty
    else:
        # Fallback to heuristic
        logger.info("Falling back to heuristic detection")
        gaming_detected, reason = detect_sandwich_heuristic(
            address, tx_history
        )
        merit_penalty = 0.1 if gaming_detected else 0.0
        return gaming_detected, reason, merit_penalty
