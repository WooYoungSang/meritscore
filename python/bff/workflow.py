"""KeeperHub workflow orchestration (Sword #3).

3-Step pipeline: CHECK → VALIDATE → EXECUTE
Fallback chain: KH Workflow → direct contract call → PENDING badge
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Tuple

import httpx

from .chain import check_merit_threshold, validate_merit

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_KH_BASE_URL = os.getenv("KH_BASE_URL", "")
_KH_API_KEY = os.getenv("KH_API_KEY", "")
_KH_TIMEOUT = float(os.getenv("KH_TIMEOUT_SECONDS", "10"))
_KH_MAX_RETRIES = int(os.getenv("KH_MAX_RETRIES", "3"))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _probe_kh_schemas() -> bool:
    """Validate that KH endpoint supports required action schemas.

    Checks list_action_schemas for execute_contract_call on Base Sepolia (84532).
    Returns True if probe succeeds; False if KH is unreachable or schema absent.
    """
    if not _KH_BASE_URL:
        return False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{_KH_BASE_URL.rstrip('/')}/v1/schemas/actions",
                params={"chain_id": 84532},
                headers={"Authorization": f"Bearer {_KH_API_KEY}"},
            )
            resp.raise_for_status()
            schemas: list[str] = resp.json().get("schemas", [])
            supported = "execute_contract_call" in schemas
            logger.info("KH probe: schemas=%s supported=%s", schemas, supported)
            return supported
    except Exception as exc:
        logger.warning("KH probe failed: %s", exc)
        return False


async def _call_kh_execute(address: str, threshold: int) -> str:
    """Call KeeperHub /v1/workflows/execute with exponential backoff.

    Args:
        address: Ethereum address of the agent.
        threshold: Merit threshold (1e4 scale).

    Returns:
        "OK" on success, "PENDING" on failure after all retries.
    """
    endpoint = f"{_KH_BASE_URL.rstrip('/')}/v1/workflows/execute"
    headers = {
        "Authorization": f"Bearer {_KH_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "chain_id": 84532,  # Base Sepolia (KH does not support 0G Galileo 16602)
        "address": address,
        "action": "distribute_merit",
        "threshold": threshold,
    }

    for attempt in range(_KH_MAX_RETRIES):
        backoff = 0.5 * (2 ** attempt)  # 0.5s, 1s, 2s
        try:
            async with httpx.AsyncClient(timeout=_KH_TIMEOUT) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)
                resp.raise_for_status()
                logger.info("KH execute OK for %s (attempt %d)", address[:10], attempt + 1)
                return "OK"
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "KH execute HTTP %s (attempt %d/%d): %s",
                exc.response.status_code, attempt + 1, _KH_MAX_RETRIES, exc.response.text[:120],
            )
        except Exception as exc:
            logger.warning("KH execute error (attempt %d/%d): %s", attempt + 1, _KH_MAX_RETRIES, exc)

        if attempt < _KH_MAX_RETRIES - 1:
            await asyncio.sleep(backoff)

    logger.error("KH execute failed after %d attempts — returning PENDING", _KH_MAX_RETRIES)
    return "PENDING"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def check_and_validate_merit(
    address: str,
    threshold: int,
    rpc_url: str,
) -> Tuple[bool, bool]:
    """Execute CHECK and VALIDATE steps of the KeeperHub 3-step workflow.

    CHECK  — queries MeritCore (0G Galileo) for score ≥ threshold.
    VALIDATE — calls MeritVault.validate() on Base Sepolia for attestation.

    Args:
        address: Ethereum address of the agent.
        threshold: Merit score threshold in 1e4 scale (e.g. 5000 = 0.5).
        rpc_url: RPC endpoint for Base Sepolia (MeritVault lives here).

    Returns:
        (check_ok, validate_ok)
    """
    try:
        check_ok = await check_merit_threshold(address, threshold, rpc_url)
    except Exception as exc:
        logger.warning("CHECK step failed for %s: %s", address[:10], exc)
        check_ok = False

    try:
        validate_ok = await validate_merit(address, rpc_url)
    except Exception as exc:
        logger.warning("VALIDATE step failed for %s: %s", address[:10], exc)
        validate_ok = False

    return check_ok, validate_ok


async def execute_workflow(address: str, threshold: int) -> str:
    """Execute the EXECUTE step of the KeeperHub 3-step workflow.

    Fallback chain:
      1. KH Workflow API (/v1/workflows/execute) with exponential backoff
      2. If KH_BASE_URL unset or probe fails → return "PENDING" (badge mode)

    Args:
        address: Ethereum address of the agent.
        threshold: Merit score threshold (1e4 scale), passed to KH payload.

    Returns:
        "OK" if KeeperHub executed successfully, "PENDING" otherwise.
    """
    if not _KH_BASE_URL:
        logger.info("KH_BASE_URL not configured — EXECUTE returns PENDING for %s", address[:10])
        return "PENDING"

    # Layer 1: probe schema support before attempting execute
    schema_ok = await _probe_kh_schemas()
    if not schema_ok:
        logger.warning("KH schema probe failed — skipping execute for %s", address[:10])
        return "PENDING"

    # Layer 2: workflow execute with retry + backoff
    return await _call_kh_execute(address, threshold)
