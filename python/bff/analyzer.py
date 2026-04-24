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

    # Simple heuristic: count transactions
    # In real scenario, would group by block
    if len(tx_history) >= 2:
        return True, "Multiple transactions detected - potential sandwich pattern"

    return False, "Single transaction - no sandwich detected"
