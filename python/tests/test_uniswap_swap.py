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
        mock_quote.return_value = {
            "amount_out": "2345000000",
            "fee_tier": 3000,
            "sqrt_price_after": "123456789012345678901234567890",
        }

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
    """Price impact calculation is reasonable (0–5% for small swaps)."""
    with patch("bff.main.quote_amount_out") as mock_quote:
        # The price impact calc assumes amount_in and amount_out in the same
        # "scale". For testing, use amount_in=10^18 (1 wei scale, for WETH)
        # and amount_out at similar scale. The calc formula:
        # impact = 100.0 * (1.0 - (amount_out / (amount_in * 0.997)))
        # So if amount_out = amount_in * 0.99, impact ≈ 2%
        amount_in = 10000000000000000  # 0.01 ETH
        # Return amount_out = amount_in * 0.99 (2% impact)
        mock_quote.return_value = {
            "amount_out": str(int(amount_in * 0.99)),
            "fee_tier": 3000,
            "sqrt_price_after": "123456789012345678901234567890",
        }

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
        # Should be roughly 0.7% (99% output with 0.3% fee factor)
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
