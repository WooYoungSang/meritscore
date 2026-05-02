"""Abstract base for autonomous swarm agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AgentDecision:
    """Result of a single agent's autonomous evaluation."""
    agent_id: str
    role: str
    verdict: str          # "APPROVE" | "REJECT" | "ABSTAIN"
    confidence: float     # 0.0–1.0
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    supporting_data: dict = field(default_factory=dict)


class AutonomousAgent(ABC):
    """Base class for all swarm validation agents."""

    agent_id: str
    role: str

    @abstractmethod
    async def evaluate(self, address: str, **kwargs) -> AgentDecision:
        """Independently evaluate an agent address. Must not call other agents."""

    async def health_check(self) -> bool:
        return True
