"""On-chain merit score evaluator agent."""

from __future__ import annotations

import logging
import os

from .base import AgentDecision, AutonomousAgent

logger = logging.getLogger(__name__)

_RPC = os.getenv("RPC_GALILEO", "https://evmrpc-testnet.0g.ai")

_AGENT_ALIASES = {
    "alice": "0xa11cea1a11cea1a11cea1a11cea1a11cea1a11ce",
    "bob":   "0xb0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0",
    "carol": "0xca401ca401ca401ca401ca401ca401ca401ca401",
}


class MeritEvaluatorAgent(AutonomousAgent):
    """Reads on-chain MeritCore score and votes APPROVE / REJECT."""

    agent_id = "merit-evaluator"
    role = "On-Chain Merit Scorer"

    async def evaluate(self, address: str, threshold: float = 0.5, **kwargs) -> AgentDecision:
        from ..chain import get_merit

        resolved = _AGENT_ALIASES.get(address.lower(), address)
        try:
            data = await get_merit(resolved, _RPC)
            score = float(data.get("score", 0.0))
        except Exception as exc:
            logger.warning("MeritEvaluatorAgent: get_merit failed (%s)", exc)
            return AgentDecision(
                agent_id=self.agent_id,
                role=self.role,
                verdict="ABSTAIN",
                confidence=0.0,
                reasoning=f"Chain query failed: {exc}",
            )

        verdict = "APPROVE" if score >= threshold else "REJECT"
        # Confidence: distance from threshold normalised to [0.4, 0.95]
        confidence = min(0.95, 0.4 + abs(score - threshold) * 1.1)

        return AgentDecision(
            agent_id=self.agent_id,
            role=self.role,
            verdict=verdict,
            confidence=round(confidence, 4),
            reasoning=f"On-chain score {score:.4f} vs threshold {threshold:.4f}",
            supporting_data={"score": score, "threshold": threshold},
        )
