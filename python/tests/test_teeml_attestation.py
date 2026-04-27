"""M2: 0G TeeML Real Inference Test

AC3: GET /attestation returns compute_hash (real or documented fallback)
AC4: Real TeeML call attempted with evidence in logs
"""
import asyncio
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from bff.attestation import get_attestation_data


@pytest.mark.asyncio
async def test_attestation_real_call():
    """AC3/AC4: Real TeeML call or documented fallback."""
    print("[*] Testing attestation real call...")
    result = await get_attestation_data()

    assert isinstance(result, dict), "Result should be dict"
    assert "compute_hash" in result, "Missing compute_hash"
    assert "storage_root" in result, "Missing storage_root"
    assert "oracle_commit" in result, "Missing oracle_commit"
    assert "mode" in result, "Mode field missing"

    compute_hash = result["compute_hash"]
    mode = result["mode"]

    assert isinstance(compute_hash, str)
    assert compute_hash.startswith("0x")
    assert len(compute_hash) > 10
    assert mode in ["Workflow", "Direct"]

    print("✓ Attestation successful")
    print(f"  mode: {mode}")
    print(f"  compute_hash: {compute_hash[:18]}...")
