"""Multi-agent weighted consensus engine."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from ..agents.base import AgentDecision, AutonomousAgent

logger = logging.getLogger(__name__)


@dataclass
class SwarmConsensus:
    """Aggregated decision from all swarm agents."""
    final_verdict: str          # "APPROVE" | "REJECT" | "ABSTAIN"
    consensus_score: float      # 0.0–1.0  (distance from neutral = confidence)
    dissent_score: float        # 0.0–1.0  (fraction of minority voters)
    agent_votes: list[AgentDecision]
    swarm_id: str = field(default_factory=lambda: f"swarm-{uuid4().hex[:8]}")
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "final_verdict": self.final_verdict,
            "consensus_score": round(self.consensus_score, 4),
            "dissent_score": round(self.dissent_score, 4),
            "agent_votes": [
                {
                    "agent_id": v.agent_id,
                    "role": v.role,
                    "verdict": v.verdict,
                    "confidence": round(v.confidence, 4),
                    "reasoning": v.reasoning,
                }
                for v in self.agent_votes
            ],
            "swarm_id": self.swarm_id,
            "timestamp": self.timestamp.isoformat(),
        }


class SwarmConsensusEngine:
    """
    Runs all registered agents in parallel and aggregates votes.

    Each agent votes independently (APPROVE / REJECT / ABSTAIN).
    Final verdict = weighted majority, where weight = agent confidence.
    Dissent score = fraction of votes opposing the majority.
    """

    def __init__(self, agents: list[AutonomousAgent]) -> None:
        self._agents = agents

    async def evaluate(self, address: str, **kwargs) -> SwarmConsensus:
        """Run all agents concurrently and compute consensus."""
        tasks = [
            self._run_agent(agent, address, **kwargs)
            for agent in self._agents
        ]
        raw = await asyncio.gather(*tasks)
        votes: list[AgentDecision] = list(raw)  # asyncio.gather returns a list
        valid = [v for v in votes if v is not None]

        if not valid:
            return SwarmConsensus(
                final_verdict="ABSTAIN",
                consensus_score=0.0,
                dissent_score=0.0,
                agent_votes=[],
            )

        # Weighted directional score: APPROVE=+1, REJECT=−1, ABSTAIN=0
        total_weight = sum(v.confidence for v in valid)
        weighted_sum = sum(
            (1 if v.verdict == "APPROVE" else -1 if v.verdict == "REJECT" else 0)
            * v.confidence
            for v in valid
        )
        direction = weighted_sum / total_weight if total_weight > 0 else 0.0

        if direction >= 0.25:
            final_verdict = "APPROVE"
        elif direction <= -0.25:
            final_verdict = "REJECT"
        else:
            final_verdict = "ABSTAIN"

        # Dissent = minority faction weight / total weight
        approve_w = sum(v.confidence for v in valid if v.verdict == "APPROVE")
        reject_w  = sum(v.confidence for v in valid if v.verdict == "REJECT")
        minority_w = min(approve_w, reject_w)
        dissent = minority_w / total_weight if total_weight > 0 else 0.0

        return SwarmConsensus(
            final_verdict=final_verdict,
            consensus_score=round(abs(direction), 4),
            dissent_score=round(dissent, 4),
            agent_votes=valid,
        )

    async def _run_agent(
        self, agent: AutonomousAgent, address: str, **kwargs
    ) -> AgentDecision | None:
        try:
            return await asyncio.wait_for(
                agent.evaluate(address=address, **kwargs), timeout=15.0
            )
        except asyncio.TimeoutError:
            logger.warning("Agent %s timed out", agent.agent_id)
        except Exception as exc:
            logger.warning("Agent %s raised: %s", agent.agent_id, exc)
        return None
