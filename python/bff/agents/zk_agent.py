"""ZK merit proof verification agent."""

from __future__ import annotations

import logging
from typing import Any

from .base import AgentDecision, AutonomousAgent

logger = logging.getLogger(__name__)


class ZKProofAgent(AutonomousAgent):
    """Generates and verifies a Groth16 ZK proof for merit threshold."""

    agent_id = "zk-verifier"
    role = "ZK Merit Proof Validator"

    async def evaluate(self, address: str, threshold: Any = 5000, **kwargs) -> AgentDecision:
        from ..workflow import zk_verify_merit

        # Normalise threshold to 1e4 int.
        # Swarm passes float 0–1 (e.g. 0.5); zk_verify_merit expects int 1e4 (e.g. 5000).
        if isinstance(threshold, float):
            if not (0.0 <= threshold <= 1.0):
                raise ValueError(f"Float threshold must be 0.0–1.0, got {threshold}")
            threshold_1e4 = int(threshold * 10000)
            threshold_display = threshold          # already 0–1 float for display
        else:
            threshold_1e4 = int(threshold)
            threshold_display = threshold_1e4 / 10000  # convert to 0–1 for display

        try:
            result = await zk_verify_merit(address, threshold_1e4)
        except Exception as exc:
            logger.warning("ZKProofAgent: zk_verify_merit failed (%s)", exc)
            return AgentDecision(
                agent_id=self.agent_id,
                role=self.role,
                verdict="ABSTAIN",
                confidence=0.0,
                reasoning=f"ZK proof generation failed: {exc}",
            )

        verified = result.get("verified", False)
        # workflow.py returns "reason" on failure (not "status")
        reason = result.get("reason", result.get("status", "unknown"))

        if verified:
            verdict = "APPROVE"
            confidence = 0.95
            reasoning = (
                f"Groth16 proof verified: score ≥ {threshold_display:.4f} without revealing value"
            )
        elif result.get("skipped"):
            verdict = "ABSTAIN"
            confidence = 0.30
            reasoning = "ZK proof skipped: address not in demo set"
        elif ("below threshold" in reason or "below_threshold" in reason
              or "proof_failed" in reason or "< threshold" in reason
              or "cannot be generated" in reason):
            verdict = "REJECT"
            confidence = 0.85
            reasoning = f"ZK proof rejected: merit below threshold {threshold_display:.4f}"
        else:
            verdict = "ABSTAIN"
            confidence = 0.10
            reasoning = f"ZK proof inconclusive: {reason}"

        return AgentDecision(
            agent_id=self.agent_id,
            role=self.role,
            verdict=verdict,
            confidence=confidence,
            reasoning=reasoning,
            supporting_data=result,
        )
