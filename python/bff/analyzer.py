"""Sandwich detection and MEV analysis (Sword #4)."""

from typing import Tuple


def detect_sandwich(address: str, tx_history: list) -> Tuple[bool, str]:
    """
    Detect sandwich attacks using simple heuristics.

    Heuristic: If 2+ transactions in same block → SUSPECTED

    Args:
        address: Ethereum address
        tx_history: List of transaction hashes or block/tx pairs

    Returns:
        (gaming_detected, reason)
    """
    if not tx_history:
        return False, "No transaction history provided"

    if not isinstance(tx_history, list):
        return False, "Transaction history must be a list"

    # Detect explicit sandwich keywords
    text = " ".join(str(tx) for tx in tx_history).lower()
    if "frontrun" in text and "backrun" in text:
        return True, "Sandwich pattern detected: frontrun/backrun pair found in transaction history"

    # Detect same-block buy-sell pairs (block number repeated)
    import re
    blocks = re.findall(r"block\s+(\d+)", text)
    if len(blocks) != len(set(blocks)):
        return True, "Multiple transactions in the same block detected — likely sandwich attack"

    return False, "No sandwich pattern detected in transaction history"
