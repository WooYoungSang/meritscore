"""MeritGuard Autonomous Agent Loop.

Background agent that monitors merit scores every 60 seconds.
Agents with merit < RISK_THRESHOLD (0.3) automatically trigger KeeperHub workflows.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .chain import get_merit

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Demo agent on-chain addresses (seeded in MeritCore on 0G Galileo)
DEMO_AGENTS = {
    "alice": "0xa11cea1a11cea1a11cea1a11cea1a11cea1a11ce",
    "bob":   "0xb0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0",
    "carol": "0xca401ca401ca401ca401ca401ca401ca401ca401",
}
RISK_THRESHOLD = 0.3
SCAN_INTERVAL = 60  # seconds
RPC_GALILEO = os.getenv("RPC_GALILEO", "https://evmrpc-testnet.0g.ai")


# ---------------------------------------------------------------------------
# State Management
# ---------------------------------------------------------------------------


@dataclass
class MeritGuardState:
    """In-memory state for MeritGuard autonomous agent."""

    last_scan: Optional[datetime] = None
    agents_checked: int = 0
    flagged: list[str] = field(default_factory=list)
    actions: list[dict] = field(default_factory=list)
    running: bool = False
    last_error: Optional[str] = None
    error_count: int = 0

    def to_dict(self) -> dict:
        """Serialize state to JSON-compatible dict."""
        return {
            "running": self.running,
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
            "scan_interval_seconds": SCAN_INTERVAL,
            "agents_checked": self.agents_checked,
            "flagged": self.flagged,
            "actions": self.actions,
        }


# Global state instance
_state = MeritGuardState()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_state() -> MeritGuardState:
    """Get current MeritGuard state."""
    return _state


async def merit_guard_loop():
    """
    Autonomous background loop that monitors agent merit scores.

    - Runs every SCAN_INTERVAL (60 seconds)
    - For each demo agent, retrieves merit score
    - Flags agents with score < RISK_THRESHOLD (0.3)
    - Triggers KH execute workflow for flagged agents
    - Maintains in-memory state for /agent-loop/status endpoint

    This coroutine is designed to be run as a background task via
    FastAPI lifespan context manager.
    """
    global _state
    _state.running = True

    logger.info("MeritGuard autonomous agent started (interval=%ds, threshold=%.1f)",
                SCAN_INTERVAL, RISK_THRESHOLD)

    while True:
        try:
            await _scan_and_act()
            await asyncio.sleep(SCAN_INTERVAL)
        except asyncio.CancelledError:
            logger.info("MeritGuard loop cancelled (shutdown)")
            _state.running = False
            break
        except Exception as e:
            logger.error("MeritGuard loop error: %s", e, exc_info=True)
            _state.last_error = str(e)
            _state.error_count += 1
            # Continue loop despite errors (autonomous behavior)
            await asyncio.sleep(SCAN_INTERVAL)


async def _scan_and_act():
    """
    Single scan cycle: check all agents, flag at-risk, trigger workflows.

    Updates _state with:
    - last_scan: current timestamp
    - agents_checked: number of agents evaluated
    - flagged: list of agent names below threshold
    - actions: details of each workflow triggered
    """
    global _state

    _state.last_scan = datetime.utcnow()
    _state.agents_checked = 0
    _state.flagged = []

    for agent, address in DEMO_AGENTS.items():
        _state.agents_checked += 1

        # Query real MeritCore contract on 0G Galileo
        try:
            merit_data = await get_merit(address, RPC_GALILEO)
            score = merit_data.get("score", 0.0)
        except Exception as e:
            logger.warning("MeritGuard: get_merit(%s) failed: %s", agent, e)
            score = 0.0

        # Check if flagged
        if score < RISK_THRESHOLD:
            _state.flagged.append(agent)

            # Trigger KH execute workflow
            threshold_1e4 = int(RISK_THRESHOLD * 10000)
            result = await _trigger_kh_execute(agent, score, threshold_1e4)

            _state.actions.append({
                "agent": agent,
                "score": score,
                "action": "KH_EXECUTE",
                "result": result,
                "at": datetime.utcnow().isoformat(),
            })

            logger.info("[MeritGuard] Flagged %s (score=%.4f) → KH %s",
                       agent, score, result)

    # Log scan summary
    if _state.flagged:
        flagged_str = ", ".join(_state.flagged)
        logger.info("[MeritGuard] scan complete: %d agents checked, %d flagged (%s)",
                   _state.agents_checked, len(_state.flagged), flagged_str)
    else:
        logger.info("[MeritGuard] scan complete: %d agents checked, 0 flagged",
                   _state.agents_checked)


async def _trigger_kh_execute(agent: str, score: float, threshold_1e4: int) -> str:
    """
    Trigger KeeperHub execute workflow for at-risk agent.

    In production, this would call execute_workflow() from workflow.py.
    For now, returns "OK" to simulate successful trigger.

    Args:
        agent: Agent alias (alice/bob/carol)
        score: Merit score (0.0-1.0)
        threshold_1e4: Threshold in 1e4 scale (e.g., 3000 = 0.3)

    Returns:
        "OK" if workflow triggered, "PENDING" if KH unreachable
    """
    # Import here to avoid circular imports
    from .workflow import execute_workflow

    try:
        # Get agent address from main.py aliases
        from .main import _AGENT_ALIASES
        alias_info = _AGENT_ALIASES.get(agent)
        if not alias_info:
            logger.warning("Agent %s not in aliases", agent)
            return "PENDING"

        address = alias_info["address"]

        # Call execute_workflow with address and threshold
        result = await execute_workflow(address, threshold_1e4)
        return result
    except Exception as e:
        logger.warning("Failed to trigger KH for %s: %s", agent, e)
        return "PENDING"


if __name__ == "__main__":
    # Debug: print state
    asyncio.run(merit_guard_loop())
