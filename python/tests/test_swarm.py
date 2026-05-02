"""Swarm consensus engine tests."""

from __future__ import annotations

import pytest

from bff.agents.base import AgentDecision, AutonomousAgent
from bff.swarm.consensus import SwarmConsensus, SwarmConsensusEngine
from bff.swarm.registry import AgentRegistry


# ---------------------------------------------------------------------------
# Stub agents for deterministic testing
# ---------------------------------------------------------------------------

class _ApproveAgent(AutonomousAgent):
    agent_id = "stub-approve"
    role = "Stub Approver"

    async def evaluate(self, address: str, **kwargs) -> AgentDecision:
        return AgentDecision(
            agent_id=self.agent_id, role=self.role,
            verdict="APPROVE", confidence=0.9, reasoning="always approve",
        )


class _RejectAgent(AutonomousAgent):
    agent_id = "stub-reject"
    role = "Stub Rejecter"

    async def evaluate(self, address: str, **kwargs) -> AgentDecision:
        return AgentDecision(
            agent_id=self.agent_id, role=self.role,
            verdict="REJECT", confidence=0.9, reasoning="always reject",
        )


class _AbstainAgent(AutonomousAgent):
    agent_id = "stub-abstain"
    role = "Stub Abstainer"

    async def evaluate(self, address: str, **kwargs) -> AgentDecision:
        return AgentDecision(
            agent_id=self.agent_id, role=self.role,
            verdict="ABSTAIN", confidence=0.5, reasoning="always abstain",
        )


class _ErrorAgent(AutonomousAgent):
    agent_id = "stub-error"
    role = "Stub Error"

    async def evaluate(self, address: str, **kwargs) -> AgentDecision:
        raise RuntimeError("simulated failure")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unanimous_approve():
    engine = SwarmConsensusEngine([_ApproveAgent(), _ApproveAgent()])
    result = await engine.evaluate("bob")
    assert result.final_verdict == "APPROVE"
    assert result.consensus_score > 0.5
    assert result.dissent_score == 0.0


@pytest.mark.asyncio
async def test_unanimous_reject():
    engine = SwarmConsensusEngine([_RejectAgent(), _RejectAgent()])
    result = await engine.evaluate("carol")
    assert result.final_verdict == "REJECT"
    assert result.dissent_score == 0.0


@pytest.mark.asyncio
async def test_split_vote_abstain():
    """Equal weight APPROVE vs REJECT → direction=0 → ABSTAIN."""
    engine = SwarmConsensusEngine([_ApproveAgent(), _RejectAgent()])
    result = await engine.evaluate("alice")
    assert result.final_verdict == "ABSTAIN"
    assert result.dissent_score > 0.0


@pytest.mark.asyncio
async def test_majority_wins():
    """2 APPROVE vs 1 REJECT → APPROVE wins."""
    engine = SwarmConsensusEngine([_ApproveAgent(), _ApproveAgent(), _RejectAgent()])
    result = await engine.evaluate("bob")
    assert result.final_verdict == "APPROVE"


@pytest.mark.asyncio
async def test_error_agent_skipped():
    """A crashing agent is skipped; remaining agents still reach consensus."""
    engine = SwarmConsensusEngine([_ApproveAgent(), _ErrorAgent()])
    result = await engine.evaluate("bob")
    assert result.final_verdict == "APPROVE"
    assert len(result.agent_votes) == 1


@pytest.mark.asyncio
async def test_all_abstain():
    engine = SwarmConsensusEngine([_AbstainAgent(), _AbstainAgent()])
    result = await engine.evaluate("alice")
    assert result.final_verdict == "ABSTAIN"


@pytest.mark.asyncio
async def test_to_dict_shape():
    engine = SwarmConsensusEngine([_ApproveAgent()])
    result = await engine.evaluate("bob")
    d = result.to_dict()
    assert "final_verdict" in d
    assert "consensus_score" in d
    assert "dissent_score" in d
    assert "agent_votes" in d
    assert "swarm_id" in d
    assert "timestamp" in d
    assert d["agent_votes"][0]["agent_id"] == "stub-approve"


def test_registry_has_four_agents():
    registry = AgentRegistry()
    agents = registry.all_agents()
    ids = {a.agent_id for a in agents}
    assert "merit-evaluator" in ids
    assert "sandwich-detector" in ids
    assert "attestation" in ids
    assert "zk-verifier" in ids
    assert len(agents) == 4
