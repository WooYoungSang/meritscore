"""Swarm consensus engine for multi-agent merit evaluation."""

from .consensus import SwarmConsensus, SwarmConsensusEngine
from .registry import AgentRegistry

__all__ = ["SwarmConsensus", "SwarmConsensusEngine", "AgentRegistry"]
