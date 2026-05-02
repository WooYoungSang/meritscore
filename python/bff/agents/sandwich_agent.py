"""MEV sandwich-attack detection agent."""

from __future__ import annotations

import logging

from .base import AgentDecision, AutonomousAgent

logger = logging.getLogger(__name__)

_DEMO_TX_HISTORY = {
    "alice": [
        "frontrun swap ETH→USDC 1.5 ETH block 19100201 (gasPrice 115gwei)",
        "target swap ETH→USDC 1.2 ETH block 19100201 (gasPrice 80gwei)",
        "backrun swap USDC→ETH 1.5 ETH block 19100201 (gasPrice 115gwei)",
        "swap USDC→ETH 0.5 ETH at 2024-01-15T10:23:01Z",
        "swap ETH→USDC 0.3 ETH at 2024-01-16T14:05:44Z",
    ],
    "bob": [
        "addLiquidity USDC/ETH 1000 USDC at 2024-02-01T09:00:00Z",
        "removeLiquidity USDC/ETH 500 USDC at 2024-02-10T11:30:00Z",
        "swap WBTC→ETH 0.1 BTC at 2024-02-15T16:45:00Z",
    ],
    "carol": [
        "frontrun swap ETH→USDC 2.0 ETH block 19234501 (gasPrice 120gwei)",
        "target swap ETH→USDC 1.5 ETH block 19234501 (gasPrice 85gwei)",
        "backrun swap USDC→ETH 2.0 ETH block 19234501 (gasPrice 120gwei)",
        "frontrun swap ETH→DAI 3.0 ETH block 19301822 (gasPrice 150gwei)",
        "target swap ETH→DAI 2.5 ETH block 19301822 (gasPrice 90gwei)",
        "backrun swap DAI→ETH 3.0 ETH block 19301822 (gasPrice 150gwei)",
    ],
}


class SandwichDetectorAgent(AutonomousAgent):
    """Uses Gemma4 26B LLM to detect MEV sandwich patterns."""

    agent_id = "sandwich-detector"
    role = "MEV Sandwich Risk Analyst"

    async def evaluate(  # noqa: E501
        self, address: str, tx_history: list | None = None, **kwargs
    ) -> AgentDecision:
        from ..sandwich_detector import detect_sandwich_llm

        history = tx_history or _DEMO_TX_HISTORY.get(address.lower(), [])
        if not history:
            return AgentDecision(
                agent_id=self.agent_id,
                role=self.role,
                verdict="ABSTAIN",
                confidence=0.3,
                reasoning="No transaction history available for analysis",
            )

        try:
            # 10s timeout — fall back to heuristic if Ollama is slow
            import asyncio as _aio
            gaming_detected, reason, penalty = await _aio.wait_for(
                detect_sandwich_llm(address, history), timeout=10.0
            )
        except _aio.TimeoutError:
            try:
                from ..analyzer import detect_sandwich as _heuristic
                gaming_detected, reason = _heuristic(address, history)
                reason = f"[heuristic] {reason}"
                penalty = 0.1 if gaming_detected else 0.0
            except Exception as heur_exc:
                logger.warning("SandwichDetectorAgent: heuristic fallback failed (%s)", heur_exc)
                return AgentDecision(
                    agent_id=self.agent_id, role=self.role,
                    verdict="ABSTAIN", confidence=0.25,
                    reasoning=f"Analysis inconclusive (LLM timeout + heuristic failed): {heur_exc}",
                )
        except Exception as exc:
            logger.warning("SandwichDetectorAgent: detection failed (%s)", exc)
            return AgentDecision(
                agent_id=self.agent_id,
                role=self.role,
                verdict="ABSTAIN",
                confidence=0.0,
                reasoning=f"Analysis failed: {exc}",
            )

        verdict = "REJECT" if gaming_detected else "APPROVE"
        # High confidence when sandwich is clearly detected; moderate when clean
        confidence = 0.88 if gaming_detected else 0.62

        return AgentDecision(
            agent_id=self.agent_id,
            role=self.role,
            verdict=verdict,
            confidence=confidence,
            reasoning=reason or "No sandwich attack pattern detected",
            supporting_data={"gaming_detected": gaming_detected, "merit_penalty": penalty},
        )
