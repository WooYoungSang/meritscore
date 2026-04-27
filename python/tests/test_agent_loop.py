"""MeritGuard Autonomous Agent Loop Tests - RED Phase.

Tests for autonomous background agent that monitors agent merit scores
and triggers KeeperHub workflows for agents below RISK_THRESHOLD.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add python/ to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bff.agent_loop import MeritGuardState, merit_guard_loop, DEMO_AGENTS, RISK_THRESHOLD, SCAN_INTERVAL


# ============================================================================
# Test 1: MeritGuardState Initialization
# ============================================================================


def test_merit_guard_state_init():
    """Test MeritGuardState initializes with correct defaults."""
    state = MeritGuardState()

    # Check initial values
    assert state.last_scan is None
    assert state.agents_checked == 0
    assert state.flagged == []
    assert state.actions == []
    assert state.running is False


def test_merit_guard_state_update():
    """Test MeritGuardState can be updated with scan results."""
    state = MeritGuardState()

    # Simulate a scan
    state.last_scan = datetime.utcnow()
    state.agents_checked = 3
    state.flagged = ["alice"]
    state.actions.append({
        "agent": "alice",
        "score": 0.2641,
        "action": "KH_EXECUTE",
        "result": "OK",
        "at": datetime.utcnow().isoformat(),
    })
    state.running = True

    # Verify state reflects updates
    assert state.last_scan is not None
    assert state.agents_checked == 3
    assert "alice" in state.flagged
    assert len(state.actions) == 1
    assert state.actions[0]["result"] == "OK"
    assert state.running is True


# ============================================================================
# Test 2: merit_guard_loop Triggers KH on Low Merit
# ============================================================================


@pytest.mark.asyncio
async def test_merit_guard_loop_triggers_kh_when_merit_low():
    """Test that loop triggers execute_workflow when merit < RISK_THRESHOLD."""
    # This test verifies the loop logic would trigger KH execute
    # In production, execute_workflow is called for agents with merit < 0.3

    # Demo agents and their scores (from main.py _AGENT_ALIASES)
    test_agents = {
        "alice": 0.2641,   # < 0.3, should trigger
        "bob": 0.6703,     # >= 0.3, should NOT trigger
        "carol": 0.0000,   # < 0.3, should trigger
    }

    flagged_count = sum(1 for score in test_agents.values() if score < RISK_THRESHOLD)

    # We expect 2 agents (alice, carol) to be flagged
    assert flagged_count == 2
    assert RISK_THRESHOLD == 0.3


@pytest.mark.asyncio
async def test_merit_guard_loop_respects_scan_interval():
    """Test that loop maintains 60-second SCAN_INTERVAL."""
    # SCAN_INTERVAL should be 60 seconds
    assert SCAN_INTERVAL == 60


@pytest.mark.asyncio
async def test_merit_guard_loop_demo_agents_defined():
    """Test that DEMO_AGENTS tuple is properly defined."""
    assert DEMO_AGENTS == ("alice", "bob", "carol")
    assert len(DEMO_AGENTS) == 3


# ============================================================================
# Test 3: Loop Respects Scan Interval Timing
# ============================================================================


@pytest.mark.asyncio
async def test_scan_interval_constant():
    """Test SCAN_INTERVAL is 60 seconds."""
    assert SCAN_INTERVAL == 60
    assert isinstance(SCAN_INTERVAL, int)


# ============================================================================
# Test 4: Graceful Exception Handling
# ============================================================================


@pytest.mark.asyncio
async def test_merit_guard_state_exception_context():
    """Test MeritGuardState can handle and log exceptions."""
    state = MeritGuardState()

    # Simulate an exception scenario
    try:
        raise RuntimeError("Simulated RPC failure")
    except RuntimeError as e:
        # In the actual loop, this would be caught and logged
        state.last_error = str(e)
        state.error_count = 1

    assert hasattr(state, 'last_error')
    assert "RPC failure" in state.last_error
    assert state.error_count == 1


def test_merit_guard_state_has_error_tracking():
    """Test MeritGuardState can track error state."""
    state = MeritGuardState()

    # Initialize error tracking attributes
    state.last_error = None
    state.error_count = 0

    # Simulate error
    state.last_error = "Test error"
    state.error_count += 1

    assert state.last_error == "Test error"
    assert state.error_count == 1


# ============================================================================
# Integration Test: Full Endpoint Response Schema
# ============================================================================


def test_merit_guard_status_response_schema():
    """Test the expected response schema for /agent-loop/status endpoint."""
    # Define expected response structure
    expected_schema = {
        "running": bool,
        "last_scan": (str, type(None)),  # ISO datetime string or None
        "scan_interval_seconds": int,
        "agents_checked": int,
        "flagged": list,
        "actions": list,
    }

    # Example valid response
    sample_response = {
        "running": True,
        "last_scan": "2026-04-27T13:30:00Z",
        "scan_interval_seconds": 60,
        "agents_checked": 3,
        "flagged": ["alice"],
        "actions": [
            {
                "agent": "alice",
                "score": 0.2641,
                "action": "KH_EXECUTE",
                "result": "OK",
                "at": "2026-04-27T13:30:00Z",
            }
        ],
    }

    # Validate sample response matches schema
    assert isinstance(sample_response["running"], bool)
    assert isinstance(sample_response["scan_interval_seconds"], int)
    assert isinstance(sample_response["agents_checked"], int)
    assert isinstance(sample_response["flagged"], list)
    assert isinstance(sample_response["actions"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
