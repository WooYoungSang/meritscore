"""Dynamic agent registry — discovers built-in and (future) on-chain agents."""

from __future__ import annotations

import logging

from ..agents.base import AutonomousAgent
from ..agents.merit_evaluator import MeritEvaluatorAgent
from ..agents.sandwich_agent import SandwichDetectorAgent
from ..agents.attestation_agent import AttestationAgent
from ..agents.zk_agent import ZKProofAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Manages the active swarm agent pool."""

    def __init__(self) -> None:
        # Built-in agents always registered
        self._agents: list[AutonomousAgent] = [
            MeritEvaluatorAgent(),
            SandwichDetectorAgent(),
            AttestationAgent(),
            ZKProofAgent(),
        ]

    def all_agents(self) -> list[AutonomousAgent]:
        return list(self._agents)

    async def agents_with_health(self) -> list[dict]:
        result = []
        for agent in self._agents:
            try:
                healthy = await agent.health_check()
            except Exception:
                healthy = False
            result.append({
                "agent_id": agent.agent_id,
                "role": agent.role,
                "healthy": healthy,
            })
        return result
