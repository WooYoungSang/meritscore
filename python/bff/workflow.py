"""KeeperHub workflow orchestration (Sword #3)."""

import os
import logging
from typing import Tuple
import httpx

from .chain import check_merit_threshold, validate_merit

logger = logging.getLogger(__name__)


async def check_and_validate_merit(
    address: str, threshold: int, rpc_url: str
) -> Tuple[bool, bool]:
    """
    Execute CHECK and VALIDATE steps of KeeperHub workflow.

    Args:
        address: Ethereum address
        threshold: Merit score threshold (1e4 scale)
        rpc_url: RPC endpoint for Base Sepolia (MeritVault)

    Returns:
        (check_ok, validate_ok)
    """
    try:
        check_ok = await check_merit_threshold(address, threshold, rpc_url)
    except Exception:
        check_ok = False

    try:
        validate_ok = await validate_merit(address, rpc_url)
    except Exception:
        validate_ok = False

    return check_ok, validate_ok


async def execute_workflow(address: str, threshold: int) -> str:
    """
    Execute KeeperHub workflow (EXECUTE step).

    Calls KeeperHub endpoint if KH_BASE_URL environment variable is set.
    If not set, returns PENDING to indicate workflow is queued.

    Args:
        address: Ethereum address
        threshold: Merit score threshold (not used for KH call, for logging only)

    Returns:
        "OK" | "PENDING"
    """
    kh_base_url = os.getenv("KH_BASE_URL")

    if not kh_base_url:
        logger.info(f"KH_BASE_URL not set; returning PENDING for {address}")
        return "PENDING"

    kh_api_key = os.getenv("KH_API_KEY", "")

    async def _call_kh():
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                endpoint = f"{kh_base_url.rstrip('/')}/v1/workflows/execute"
                headers = {
                    "Authorization": f"Bearer {kh_api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "address": address,
                    "action": "distribute_merit",
                }

                logger.debug(f"Calling KH endpoint: {endpoint}")
                response = await client.post(endpoint, json=payload, headers=headers)
                response.raise_for_status()

                logger.info(f"KeeperHub workflow executed for {address}: status {response.status_code}")
                return "OK"
        except Exception as e:
            logger.error(f"KeeperHub workflow execution failed: {e}")
            # Return PENDING instead of failing to allow graceful degradation
            return "PENDING"

    return await _call_kh()
