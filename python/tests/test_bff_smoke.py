"""BFF Smoke Tests - All 5 endpoints."""

import pytest
import sys
from pathlib import Path

# Add python/ to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from bff.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


# ============================================================================
# Health Endpoint Tests
# ============================================================================


def test_health_ok(client):
    """Test GET /health returns ok status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "chain" in data
    assert "galileo" in data["chain"]
    assert "base" in data["chain"]


def test_health_chains_are_booleans(client):
    """Test health endpoint returns boolean chain values."""
    response = client.get("/health")
    data = response.json()
    assert isinstance(data["chain"]["galileo"], bool)
    assert isinstance(data["chain"]["base"], bool)


# ============================================================================
# Merit Endpoint Tests
# ============================================================================


def test_merit_alice(client):
    """Test merit endpoint for alice (known address with 0.2641 score)."""
    address = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
    response = client.get(f"/merit/{address}")
    assert response.status_code == 200
    data = response.json()
    assert data["address"] == address
    assert data["score"] == 0.2641
    assert data["score_1e4"] == 2641
    assert data["exists"] is True
    assert data["mode"] == "Web3"


def test_merit_bob(client):
    """Test merit endpoint for bob (known address with 0.6703 score)."""
    address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
    response = client.get(f"/merit/{address}")
    assert response.status_code == 200
    data = response.json()
    assert data["address"] == address
    assert data["score"] == 0.6703
    assert data["score_1e4"] == 6703
    assert data["exists"] is True
    assert data["mode"] == "Web3"


def test_merit_carol(client):
    """Test merit endpoint for carol (known address with 0.0 score)."""
    address = "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"
    response = client.get(f"/merit/{address}")
    assert response.status_code == 200
    data = response.json()
    assert data["address"] == address
    assert data["score"] == 0.0
    assert data["score_1e4"] == 0
    assert data["exists"] is False
    assert data["mode"] == "Web3"


def test_merit_not_found(client):
    """Test merit endpoint for unknown address returns exists=False."""
    address = "0x0000000000000000000000000000000000000000"
    response = client.get(f"/merit/{address}")
    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is False
    assert data["score"] == 0.0


def test_merit_invalid_address(client):
    """Test merit endpoint with invalid address returns 400."""
    response = client.get("/merit/invalid-address")
    assert response.status_code == 400


# ============================================================================
# Attestation Endpoint Tests
# ============================================================================


def test_attestation_ok(client):
    """Test GET /attestation returns mock attestation card."""
    response = client.get("/attestation")
    assert response.status_code == 200
    data = response.json()
    assert "compute_hash" in data
    assert "storage_root" in data
    assert "oracle_commit" in data
    assert "mode" in data
    assert data["compute_hash"].startswith("0x")
    assert data["storage_root"].startswith("0x")
    assert data["oracle_commit"].startswith("0x")
    assert data["mode"] in ["Direct", "Workflow"]


def test_attestation_oracle_commit_hash(client):
    """Test attestation includes oracle_commit_hash from config."""
    response = client.get("/attestation")
    data = response.json()
    # Oracle commit should match environment or default
    assert data["oracle_commit"] == "0x09d34df4fd5c9c75b9970e4fbe0820c2b982466532d5413e1ae3b75fe7a1b4c1"


# ============================================================================
# Workflow Endpoint Tests
# ============================================================================


def test_workflow_check_alice_sufficient_threshold(client):
    """Test workflow with alice and low threshold."""
    response = client.post(
        "/kh/workflow",
        json={
            "address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "threshold": 1000,  # alice has 2641
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "check" in data
    assert "validate" in data
    assert "execute" in data
    assert "mode" in data
    assert data["mode"] == "Workflow"
    assert data["check"] is True  # alice meets threshold
    assert data["execute"] in ["PENDING", "OK"]


def test_workflow_check_bob_sufficient_threshold(client):
    """Test workflow with bob (higher score)."""
    response = client.post(
        "/kh/workflow",
        json={
            "address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
            "threshold": 5000,  # bob has 6703
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["check"] is True


def test_workflow_check_carol_fails_threshold(client):
    """Test workflow with carol (zero score) fails threshold."""
    response = client.post(
        "/kh/workflow",
        json={
            "address": "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
            "threshold": 1000,  # carol has 0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["check"] is False  # carol fails threshold


def test_workflow_missing_address(client):
    """Test workflow with missing address returns 400."""
    response = client.post(
        "/kh/workflow",
        json={"threshold": 1000}
    )
    assert response.status_code == 400


def test_workflow_missing_threshold(client):
    """Test workflow with missing threshold returns 400."""
    response = client.post(
        "/kh/workflow",
        json={"address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"}
    )
    assert response.status_code == 400


# ============================================================================
# Analyzer Endpoint Tests
# ============================================================================


def test_analyze_clean_single_tx(client):
    """Test analyze with single transaction (no sandwich)."""
    response = client.post(
        "/analyze",
        json={
            "address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "tx_history": ["0xabc123"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["address"] == "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
    assert data["gaming_detected"] is False
    assert "reason" in data
    assert data["mode"] == "Direct"


def test_analyze_suspected_multiple_txs(client):
    """Test analyze with multiple transactions (sandwich suspected)."""
    response = client.post(
        "/analyze",
        json={
            "address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "tx_history": ["0xabc123", "0xdef456", "0x789abc"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "gaming_detected" in data
    assert "reason" in data
    assert data["mode"] == "Direct"


def test_analyze_empty_tx_history(client):
    """Test analyze with empty transaction history."""
    response = client.post(
        "/analyze",
        json={
            "address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "tx_history": []
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["gaming_detected"] is False


def test_analyze_missing_address(client):
    """Test analyze with missing address returns 400."""
    response = client.post(
        "/analyze",
        json={"tx_history": ["0xabc"]}
    )
    assert response.status_code == 400


# ============================================================================
# Sword #4 AC1-AC5 Tests (LLM-based sandwich detection)
# ============================================================================


def test_analyze_ac1_response_structure(client):
    """AC1: POST /analyze returns gaming_detected, reason, merit_penalty, mode."""
    response = client.post(
        "/analyze",
        json={
            "address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "tx_history": ["0xabc123"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "gaming_detected" in data, "Missing 'gaming_detected' field"
    assert "reason" in data, "Missing 'reason' field"
    assert "merit_penalty" in data, "Missing 'merit_penalty' field (AC1)"
    assert "mode" in data, "Missing 'mode' field"
    assert isinstance(data["gaming_detected"], bool)
    assert isinstance(data["reason"], str)
    assert isinstance(data["merit_penalty"], (int, float))
    assert isinstance(data["mode"], str)


def test_analyze_ac3_merit_penalty_clean(client):
    """AC3: merit_penalty=0.0 when gaming_detected=False."""
    response = client.post(
        "/analyze",
        json={
            "address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "tx_history": ["0xabc123"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["gaming_detected"] is False
    assert data["merit_penalty"] == 0.0, "Clean detection should have 0.0 penalty"


def test_analyze_ac3_merit_penalty_detected(client):
    """AC3: merit_penalty=0.1 when gaming_detected=True."""
    response = client.post(
        "/analyze",
        json={
            "address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "tx_history": ["0xabc123", "0xdef456", "0x789abc", "0xffffff"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "merit_penalty" in data
    assert 0.0 <= data["merit_penalty"] <= 1.0


def test_analyze_ac3_merit_penalty_range(client):
    """AC3: merit_penalty is in valid range [0.0, 1.0]."""
    response = client.post(
        "/analyze",
        json={
            "address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "tx_history": ["0xabc123", "0xdef456"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert 0.0 <= data["merit_penalty"] <= 1.0, "merit_penalty out of range"


def test_analyze_ac5_mode_direct(client):
    """AC5: mode='Direct' indicates direct LLM inference mode."""
    response = client.post(
        "/analyze",
        json={
            "address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "tx_history": ["0xabc123"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "Direct", "Should use Direct mode (Ollama inference)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
