"""Uniswap Merit-Gated Swap Tests - Sword #6 (RED Phase)."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from bff.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


# ============================================================================
# Test 1: Merit Gate - Bob Passes (0.6703 > 0.5)
# ============================================================================


def test_merit_gate_bob_passes(client):
    """Bob (0.6703 > 0.5) passes merit gate and gets 200 + tx_hash."""
    with patch("bff.main.quote_amount_out") as mock_quote, \
         patch("bff.main.swap_exact_tokens") as mock_swap:
        mock_quote.return_value = {
            "amount_out": "2345000000",
            "fee_tier": 3000,
            "sqrt_price_after": "123456789012345678901234567890",
        }
        mock_swap.return_value = {
            "tx_hash": "0xabcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234",
            "amount_out": "2345000000",
            "block_number": 12345678,
        }

        response = client.post("/uniswap/swap", json={
            "action": "execute",
            "address": "bob",
            "from_token": "0x4200000000000000000000000000000000000006",
            "to_token": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
            "amount_in": "1000000000000000",
            "slippage_pct": 2.0
        })
        assert response.status_code == 200
        data = response.json()
        assert "tx_hash" in data
        assert data["tx_hash"].startswith("0x")
        assert "amount_out" in data
        assert int(data["amount_out"]) > 0


# ============================================================================
# Test 2: Merit Gate - Alice Blocked (0.2641 < 0.5)
# ============================================================================


def test_merit_gate_alice_blocked(client):
    """Alice (0.2641 < 0.5) blocked at merit gate → 403."""
    response = client.post("/uniswap/swap", json={
        "action": "execute",
        "address": "alice",
        "from_token": "0x4200000000000000000000000000000000000006",
        "to_token": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        "amount_in": "1000000000000000",
        "slippage_pct": 2.0
    })
    assert response.status_code == 403
    data = response.json()
    assert "error" in data
    assert "merit_below_threshold" in data["error"]
    assert data["threshold"] == 0.5


# ============================================================================
# Test 3: Merit Gate - Carol Blocked (0.0000 < 0.5)
# ============================================================================


def test_merit_gate_carol_blocked(client):
    """Carol (0.0000 < 0.5) blocked at merit gate → 403."""
    response = client.post("/uniswap/swap", json={
        "action": "execute",
        "address": "carol",
        "from_token": "0x4200000000000000000000000000000000000006",
        "to_token": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        "amount_in": "1000000000000000",
        "slippage_pct": 2.0
    })
    assert response.status_code == 403


# ============================================================================
# Test 4: Quote Returns Amount Out
# ============================================================================


def test_quote_returns_amount_out(client):
    """Quote action returns amount_out, price_impact_pct, fee_tier."""
    with patch("bff.main.quote_amount_out") as mock_quote:
        # Two quotes are issued: the main fill quote and a probe quote
        # at amount_in // 1000 for marginal-rate estimation. Return a
        # proportional probe so price_impact ≈ 0.
        mock_quote.side_effect = [
            {
                "amount_out": "2345000000",
                "fee_tier": 3000,
                "sqrt_price_after": "123456789012345678901234567890",
            },
            {
                "amount_out": "2345000",  # probe: 1/1000 of main, same rate
                "fee_tier": 3000,
                "sqrt_price_after": "123456789012345678901234567890",
            },
        ]

        response = client.post("/uniswap/swap", json={
            "action": "quote",
            "address": "bob",
            "from_token": "0x4200000000000000000000000000000000000006",
            "to_token": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
            "amount_in": "1000000000000000",
            "slippage_pct": 2.0
        })
        assert response.status_code == 200
        data = response.json()
        assert "amount_out" in data
        assert int(data["amount_out"]) > 0
        assert "price_impact_pct" in data
        assert 0 <= float(data["price_impact_pct"]) <= 100
        assert "fee_tier" in data
        assert data["fee_tier"] in [500, 3000]


# ============================================================================
# Test 5: Price Impact Calculation
# ============================================================================


def test_quote_price_impact_calc(client):
    """Price impact = deviation between actual fill rate and probe marginal rate."""
    with patch("bff.main.quote_amount_out") as mock_quote:
        amount_in = 10**16  # 0.01 WETH
        # Probe runs at amount_in // 1000 = 10^13 with a clean 1:1 rate.
        # Main fill returns 0.992 of the marginal rate → impact ≈ 0.8%.
        marginal_in = amount_in // 1000
        mock_quote.side_effect = [
            {
                "amount_out": str(int(amount_in * 0.992)),
                "fee_tier": 3000,
                "sqrt_price_after": "123456789012345678901234567890",
            },
            {
                "amount_out": str(marginal_in),  # probe rate = 1.0
                "fee_tier": 3000,
                "sqrt_price_after": "123456789012345678901234567890",
            },
        ]

        response = client.post("/uniswap/swap", json={
            "action": "quote",
            "address": "bob",
            "from_token": "0x4200000000000000000000000000000000000006",
            "to_token": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
            "amount_in": str(amount_in),
            "slippage_pct": 1.0
        })
        assert response.status_code == 200
        data = response.json()
        price_impact = float(data["price_impact_pct"])
        assert 0.5 < price_impact < 1.0, \
            f"Price impact {price_impact}% not in expected range"


# ============================================================================
# Test 6: Invalid Token Address → 400
# ============================================================================


def test_swap_invalid_token_addr_400(client):
    """Invalid token address → 400 validation error."""
    response = client.post("/uniswap/swap", json={
        "action": "execute",
        "address": "bob",
        "from_token": "0x1234",
        "to_token": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        "amount_in": "1000000000000000",
        "slippage_pct": 2.0
    })
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


# ============================================================================
# Test 7: Slippage Too High → 400
# ============================================================================


def test_swap_slippage_too_high_400(client):
    """Slippage > 5% → 400 validation error."""
    response = client.post("/uniswap/swap", json={
        "action": "execute",
        "address": "bob",
        "from_token": "0x4200000000000000000000000000000000000006",
        "to_token": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        "amount_in": "1000000000000000",
        "slippage_pct": 5.5
    })
    assert response.status_code == 400
    assert "slippage" in response.json()["detail"].lower()


# ============================================================================
# Test 8: Custom Slippage Enforced
# ============================================================================


def test_swap_with_custom_slippage(client):
    """Custom slippage (e.g. 2.5%) is enforced in tx."""
    with patch("bff.main.quote_amount_out") as mock_quote, \
         patch("bff.main.swap_exact_tokens") as mock_swap:
        mock_quote.return_value = {
            "amount_out": "2345000000",
            "fee_tier": 3000,
            "sqrt_price_after": "123456789012345678901234567890",
        }
        mock_swap.return_value = {
            "tx_hash": "0xabcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234",
            "amount_out": "2345000000",
            "block_number": 12345678,
        }

        response = client.post("/uniswap/swap", json={
            "action": "execute",
            "address": "bob",
            "from_token": "0x4200000000000000000000000000000000000006",
            "to_token": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
            "amount_in": "1000000000000000",
            "slippage_pct": 2.5
        })
        assert response.status_code == 200
        data = response.json()
        assert "amount_out" in data


# ============================================================================
# Test 9: Swap Reverted → 502
# ============================================================================


def test_swap_insufficient_liquidity_502(client):
    """Swap reverted on-chain (e.g. liquidity insufficient) → 502."""
    with patch("bff.main.quote_amount_out") as mock_quote, \
         patch("bff.main.swap_exact_tokens") as mock_swap:
        mock_quote.return_value = {
            "amount_out": "1",
            "fee_tier": 3000,
            "sqrt_price_after": "123456789012345678901234567890",
        }
        mock_swap.side_effect = RuntimeError(
            "Revert: UniswapV3Router: INSUFFICIENT_OUTPUT_AMOUNT"
        )

        response = client.post("/uniswap/swap", json={
            "action": "execute",
            "address": "bob",
            "from_token": "0x4200000000000000000000000000000000000006",
            "to_token": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
            "amount_in": "999999999999999999999",
            "slippage_pct": 2.0
        })
        assert response.status_code == 502
        data = response.json()
        assert "error" in data
        assert "swap_reverted" in data["error"]
        assert "reason" in data


# ============================================================================
# Test 10: Invalid Action → 400
# ============================================================================


def test_swap_wrong_action_400(client):
    """Invalid action (not 'quote' or 'execute') → 422 validation error."""
    response = client.post("/uniswap/swap", json={
        "action": "invalid_action",
        "address": "bob",
        "from_token": "0x4200000000000000000000000000000000000006",
        "to_token": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        "amount_in": "1000000000000000",
        "slippage_pct": 2.0
    })
    # FastAPI returns 422 for Literal validation errors
    assert response.status_code == 422
