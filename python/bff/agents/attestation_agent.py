"""0G Compute TEE attestation agent."""

from __future__ import annotations

import logging

from .base import AgentDecision, AutonomousAgent

logger = logging.getLogger(__name__)


class AttestationAgent(AutonomousAgent):
    """Verifies TEE attestation via 0G Compute. ABSTAIN when unavailable."""

    agent_id = "attestation"
    role = "TEE Attestation Verifier"

    async def evaluate(self, address: str, **kwargs) -> AgentDecision:
        from ..attestation import get_attestation_data

        try:
            data = await get_attestation_data()
        except Exception as exc:
            logger.warning("AttestationAgent: attestation failed (%s)", exc)
            return AgentDecision(
                agent_id=self.agent_id,
                role=self.role,
                verdict="ABSTAIN",
                confidence=0.0,
                reasoning=f"Attestation service unavailable: {exc}",
            )

        compute_ok = data.get("compute_ok", False)
        storage_ok = data.get("storage_ok", False)
        fallback = data.get("fallback_reason")

        if compute_ok and storage_ok:
            # TEE verifies the computation platform, not the agent's merit.
            # ABSTAIN with high confidence = "measurements are trustworthy, score is real"
            verdict = "ABSTAIN"
            confidence = 0.90
            provider = data.get("provider", "unknown")
            reasoning = f"TEE verified via {provider} — computation integrity confirmed"
        elif fallback:
            verdict = "ABSTAIN"
            confidence = 0.40
            reasoning = f"Attestation fallback: {fallback}"
        else:
            verdict = "ABSTAIN"
            confidence = 0.20
            reasoning = "Attestation inconclusive"

        return AgentDecision(
            agent_id=self.agent_id,
            role=self.role,
            verdict=verdict,
            confidence=confidence,
            reasoning=reasoning,
            supporting_data={
                "compute_ok": compute_ok,
                "storage_ok": storage_ok,
                "fallback_reason": fallback,
                "mode": data.get("mode"),
            },
        )
