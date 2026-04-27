"""
TDD Red phase: ZK Real Proof Generation

Test that prove_merit.py generates real snarkjs groth16 proofs,
not dummy pi_a/pi_b/pi_c values.
"""

import json
import subprocess
import sys


def test_zk_real_proof_bob_passes():
    """AC1: Real proof generation for bob (score=6703, threshold=5000)."""
    result = subprocess.run(
        [sys.executable, "scripts/prove_merit.py", "--agent", "bob", "--threshold", "5000"],
        capture_output=True,
        text=True,
        cwd="/home/jang/Workspace/warvis-hackerton",
        timeout=120,
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Parse JSON output
    lines = result.stdout.split('\n')
    json_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith('{'):
            json_start = i
            break
    
    assert json_start is not None, f"No JSON in output:\n{result.stdout}"
    
    json_text = '\n'.join(lines[json_start:])
    proof_data = json.loads(json_text)
    
    # Verify success flag
    assert proof_data.get("success") is True, f"Proof generation failed: {proof_data}"
    
    # AC1: proof contains valid BN128 values, not dummy "0x123" etc
    assert "proof" in proof_data, "No proof in result"
    proof = proof_data["proof"]

    # Check pi_a format (should be 2-element array of large hex strings)
    assert "pi_a" in proof, "No pi_a in proof"
    assert isinstance(proof["pi_a"], list), "pi_a should be a list"
    assert len(proof["pi_a"]) >= 2, "pi_a should have at least 2 elements"

    pi_a_0 = proof["pi_a"][0]

    # Valid BN128 values are hex strings starting with 0x and >4 chars
    # Dummy values like "0x123" are much shorter
    assert isinstance(pi_a_0, str), "pi_a[0] should be string"
    assert pi_a_0.startswith("0x"), f"pi_a[0] should be hex: {pi_a_0[:20]}"

    hex_part = pi_a_0[2:]
    # Valid proof values should be longer than trivial dummy (0x123 = 5 chars)
    assert len(hex_part) > 8, f"pi_a[0] too short (likely dummy): {pi_a_0}"

    # Verify it's actual hex
    try:
        int(hex_part, 16)
    except ValueError:
        raise AssertionError(f"pi_a[0] not valid hex: {pi_a_0}")

    print("✓ Valid proof generated for bob")
    print(f"  pi_a[0]: {pi_a_0[:50]}...")


def test_zk_real_proof_alice_fails():
    """AC2: Alice (score=2641) cannot prove threshold=5000."""
    result = subprocess.run(
        [sys.executable, "scripts/prove_merit.py", "--agent", "alice", "--threshold", "5000"],
        capture_output=True,
        text=True,
        cwd="/home/jang/Workspace/warvis-hackerton",
        timeout=60,
    )
    
    # Script should fail or return success=False
    lines = result.stdout.split('\n')
    json_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith('{'):
            json_start = i
            break
    
    assert json_start is not None, "No JSON in output"
    json_text = '\n'.join(lines[json_start:])
    proof_data = json.loads(json_text)
    
    # Should not be successful
    assert proof_data.get("success") is not True, "Alice should fail threshold check"
    print("✓ Alice correctly rejected (score < threshold)")


if __name__ == "__main__":
    test_zk_real_proof_bob_passes()
    test_zk_real_proof_alice_fails()
    print("\n✅ All ZK proof tests passed")
