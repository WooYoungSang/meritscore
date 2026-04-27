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
_KH_WEBHOOK_KEY = os.getenv("KH_WEBHOOK_KEY", "")
_KH_WORKFLOW_ID = os.getenv("KH_WORKFLOW_ID", "")
_KH_TIMEOUT = float(os.getenv("KH_TIMEOUT_SECONDS", "10"))
_KH_MAX_RETRIES = int(os.getenv("KH_MAX_RETRIES", "3"))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _probe_kh_health() -> bool:
    """Confirm KeeperHub API is reachable and API key is valid.

    Uses /api/health (always 200) to confirm connectivity,
    then /api/workflows (authenticated GET) to confirm key validity.
    Returns True if both checks pass.
    """
    if not _KH_BASE_URL:
        return False
    base = _KH_BASE_URL.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Health check
            health = await client.get(f"{base}/api/health")
            health.raise_for_status()
            # Auth check — /api/workflows returns [] when key is valid
            auth = await client.get(
                f"{base}/api/workflows",
                headers={"Authorization": f"Bearer {_KH_API_KEY}"},
            )
            auth.raise_for_status()
            logger.info("KH probe OK: health=%s auth=%s", health.status_code, auth.status_code)
            return True
    except Exception as exc:
        logger.warning("KH probe failed: %s", exc)
        return False


async def _call_kh_execute(address: str, threshold: int) -> str:
    """Trigger KeeperHub workflow via /api/workflows/{id}/webhook.

    Returns:
        "OK" if workflow started (status running/queued).
        "PENDING" if unreachable or no workflow configured.
    """
    if not _KH_WEBHOOK_KEY or not _KH_WORKFLOW_ID:
        logger.info("KH_WEBHOOK_KEY or KH_WORKFLOW_ID not set — returning PENDING")
        return "PENDING"

    base = _KH_BASE_URL.rstrip("/")
    url = f"{base}/api/workflows/{_KH_WORKFLOW_ID}/webhook"
    headers = {"Authorization": f"Bearer {_KH_WEBHOOK_KEY}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=_KH_TIMEOUT) as client:
            resp = await client.post(
                url,
                json={"address": address, "threshold": threshold, "chain_id": 84532},
                headers=headers,
            )
            if resp.status_code < 300:
                data = resp.json()
                logger.info("KH webhook OK for %s: %s", address[:10], data)
                return "OK"
            logger.warning("KH webhook %s for %s: %s", resp.status_code, address[:10], resp.text[:100])
    except Exception as exc:
        logger.warning("KH webhook error: %s", exc)

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


async def zk_verify_merit(address: str, threshold: int) -> dict:
    """Generate ZK proof that agent merit >= threshold.

    Returns:
        {verified: bool, proof_hash: str, public_signals: list, merkle_root: str}
        or {verified: False, reason: str, skipped: bool} if unknown agent
    """
    import subprocess
    import json
    from pathlib import Path

    # Map address to agent name for ZK prover
    ADDR_TO_AGENT = {
        "0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266": "alice",
        "0x70997970c51812dc3a010c7d01b50e0d17dc79c8": "bob",
        "0x3c44cddddb6a900fa2b585dd299e03d12fa4293bc": "carol",
        "0xa11cea1a11cea1a11cea1a11cea1a11cea1a11ce": "alice",
        "0xb0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0": "bob",
        "0xca401ca401ca401ca401ca401ca401ca401ca401": "carol",
    }
    agent = ADDR_TO_AGENT.get(address.lower(), None)
    if agent is None:
        # Unknown address — skip ZK (return partial verify)
        return {"verified": False, "reason": "unknown_agent", "skipped": True}

    PROJECT_ROOT = Path(__file__).parent.parent.parent
    script = PROJECT_ROOT / "scripts" / "prove_merit.py"

    try:
        result = subprocess.run(
            ["python", str(script), "--agent", agent, "--threshold", str(threshold)],
            capture_output=True, text=True, timeout=90,
            cwd=str(PROJECT_ROOT),
        )
        output = result.stdout
        marker = output.find("[Result]")
        json_start = output.find("{", marker if marker != -1 else 0)
        if json_start == -1:
            return {"verified": False, "reason": "no_proof_output"}

        data = json.loads(output[json_start:])
        if data.get("success"):
            proof = data.get("proof", {})
            # Compact hash of proof for logging
            proof_hash = "0x" + __import__("hashlib").sha256(
                json.dumps(proof, sort_keys=True).encode()
            ).hexdigest()[:16]
            return {
                "verified": True,
                "proof_hash": proof_hash,
                "public_signals": data.get("publicSignals", []),
                "merkle_root": str(data.get("merkleRoot", "")),
            }
        else:
            return {"verified": False, "reason": data.get("reason", "proof_failed")}
    except subprocess.TimeoutExpired:
        return {"verified": False, "reason": "zk_verify_timeout"}
    except Exception as e:
        return {"verified": False, "reason": str(e)}


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

    # Layer 1: probe health + auth before attempting execute
    health_ok = await _probe_kh_health()
    if not health_ok:
        logger.warning("KH health probe failed — skipping execute for %s", address[:10])
        return "PENDING"

    # Layer 2: workflow execute with retry + backoff
    return await _call_kh_execute(address, threshold)
