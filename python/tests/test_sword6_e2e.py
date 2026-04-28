"""
Sword #6 E2E Tests: Uniswap Merit-Gated Swap

Tests the /uniswap/swap endpoint with:
  C. Quote test (mocked liquidity)
  E. Merit gate E2E (alice/carol → 403, bob → 200)

Note: Live swap execution (Section D) skipped due to liquidity unavailability
on Base Sepolia. Tests use BFF running on localhost:61235.
"""

import pytest
import requests

BFF_URL = "http://localhost:61235"
WETH = "0x4200000000000000000000000000000000000006"
USDC = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"


class TestSword6E2E:
    """Sword #6: Uniswap Merit-Gated Swap E2E"""

    def test_c_quote_bob_weth_to_usdc(self):
        """Section C: E2E Quote Test — bob requests 0.001 WETH → USDC quote"""
        response = requests.post(
            f"{BFF_URL}/uniswap/swap",
            json={
                "action": "quote",
                "address": "bob",
                "from_token": WETH,
                "to_token": USDC,
                "amount_in": "1000000000000000",  # 0.001 WETH
            }
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        # Assertions per spec
        assert "amount_out" in data, "amount_out missing"
        amount_out = int(data["amount_out"]) if isinstance(data["amount_out"], str) else data["amount_out"]
        assert amount_out > 0, f"amount_out must be > 0, got {data['amount_out']}"
        assert "fee_tier" in data, "fee_tier missing"
        assert data["fee_tier"] in {500, 3000}, f"fee_tier must be 500 or 3000, got {data['fee_tier']}"
        assert data.get("action") == "quote", "action should be quote"

    def test_e1_alice_merit_gate_403(self):
        """Section E.1: Merit gate — alice (merit 0.2641 < 0.5) → 403"""
        response = requests.post(
            f"{BFF_URL}/uniswap/swap",
            json={
                "action": "quote",
                "address": "alice",
                "from_token": WETH,
                "to_token": USDC,
                "amount_in": "1000000000000000",
            }
        )

        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        data = response.json()
        assert data.get("error") == "merit_below_threshold", f"Expected merit_below_threshold, got {data.get('error')}"
        assert data.get("merit") == 0.2641, f"Expected alice merit 0.2641, got {data.get('merit')}"
        assert data.get("threshold") == 0.5, f"Expected threshold 0.5, got {data.get('threshold')}"

    def test_e2_carol_merit_gate_403(self):
        """Section E.2: Merit gate — carol (merit 0.0) → 403"""
        response = requests.post(
            f"{BFF_URL}/uniswap/swap",
            json={
                "action": "quote",
                "address": "carol",
                "from_token": WETH,
                "to_token": USDC,
                "amount_in": "1000000000000000",
            }
        )

        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        data = response.json()
        assert data.get("error") == "merit_below_threshold", f"Expected merit_below_threshold, got {data.get('error')}"
        assert data.get("merit") == 0.0, f"Expected carol merit 0.0, got {data.get('merit')}"
        assert data.get("threshold") == 0.5, f"Expected threshold 0.5, got {data.get('threshold')}"

    def test_d_live_swap_skipped(self):
        """
        Section D: Live Swap (SKIPPED)

        Note: This test documents the kill switch. Live swap execution was skipped
        because QuoterV2 reverted on both fee tiers (500, 3000) on Base Sepolia,
        indicating liquidity unavailability. Per spec, this is acceptable; the
        endpoint works in mock mode for demo purposes.
        """
        pytest.skip("Kill switch triggered: liquidity unavailable on Base Sepolia")
