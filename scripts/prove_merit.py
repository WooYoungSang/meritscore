#!/usr/bin/env python3
"""
Merit Threshold ZK Prover

Generates zero-knowledge proofs for agent merit scores.
Agents can prove they meet a threshold WITHOUT revealing their score.

Usage:
    python scripts/prove_merit.py --agent bob --threshold 5000
    python scripts/prove_merit.py --agent alice --threshold 5000  # Will fail (score too low)
"""

import json
import subprocess
import sys
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

# Locked constants from CLAUDE.md
AGENTS = {
    "alice": 2641,    # 0.2641 * 10000
    "bob": 6703,      # 0.6703 * 10000
    "carol": 0,       # 0.0000 * 10000
}

PROJECT_ROOT = Path(__file__).parent.parent


def build_merkle_tree_real() -> Dict[str, Any]:
    """
    Build depth-8 merkle tree using real Poseidon hash via circomlibjs.
    Returns the JSON output from build_merkle.js.
    """
    result = subprocess.run(
        ["node", "scripts/build_merkle.js"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(PROJECT_ROOT),
    )
    if result.returncode != 0:
        raise RuntimeError(f"build_merkle.js failed: {result.stderr}")
    return json.loads(result.stdout.strip())


def generate_witness(agent: str, threshold: int, tree: Dict[str, Any]) -> Dict[str, Any]:
    """Generate circuit witness from real merkle tree data."""
    if agent not in AGENTS:
        raise ValueError(f"Unknown agent: {agent}")

    score = AGENTS[agent]
    if score < threshold:
        raise RuntimeError(
            f"Agent {agent} score {score} < threshold {threshold}: proof cannot be generated"
        )

    agent_data = tree["agents"][agent]
    # Field elements must be strings — JSON floats lose precision on 77-digit BN254 numbers
    return {
        "agentAddr": agent_data["addr"],
        "agentScore": agent_data["score"],
        "merklePath": agent_data["merklePath"],
        "pathIndices": [str(x) for x in agent_data["pathIndices"]],
        "merkleRoot": tree["root"],
        "threshold": str(threshold),
    }


def generate_proof(agent: str, threshold: int) -> Dict[str, Any]:
    """
    Generate ZK proof for agent merit threshold.

    Args:
        agent: "alice", "bob", or "carol"
        threshold: Score threshold to prove against (0-9999)

    Returns:
        dict with proof, publicSignals, and metadata
    """
    if agent not in AGENTS:
        raise ValueError(f"Unknown agent: {agent}")

    score = AGENTS[agent]
    print(f"[*] Generating proof for {agent} (score={score})")
    print(f"    Threshold: {threshold}")

    # Build real merkle tree via circomlibjs
    print(f"[*] Building depth-8 merkle tree (real Poseidon)...")
    tree = build_merkle_tree_real()
    merkle_root = int(tree["root"])
    print(f"[✓] Merkle root: {merkle_root}")

    # Generate witness
    try:
        witness = generate_witness(agent, threshold, tree)
    except RuntimeError as e:
        print(f"[!] {e}")
        return {
            "agent": agent,
            "threshold": threshold,
            "score": score,
            "success": False,
            "reason": str(e),
        }

    print(f"[✓] Witness generated")
    print(f"    agentAddr: {witness['agentAddr']}")
    print(f"    agentScore: {witness['agentScore']}")
    print(f"    merkleRoot: {witness['merkleRoot']}")
    print(f"    pathIndices: {witness['pathIndices']}")

    # Real snarkjs groth16 proof generation
    print(f"[*] Attempting real snarkjs groth16 proof generation...")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            witness_json_path = os.path.join(tmpdir, "witness.json")
            with open(witness_json_path, "w") as f:
                json.dump(witness, f)

            wtns_path = os.path.join(tmpdir, "witness.wtns")
            compute_witness_js = PROJECT_ROOT / "scripts" / "compute_witness.js"

            print(f"[*] Computing witness binary via WASM")
            result = subprocess.run(
                ["node", str(compute_witness_js), witness_json_path, wtns_path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(PROJECT_ROOT),
            )
            if result.returncode != 0:
                raise RuntimeError(f"compute_witness.js failed: {result.stderr}")
            print(f"[✓] Witness binary computed")

            proof_path = os.path.join(tmpdir, "proof.json")
            public_path = os.path.join(tmpdir, "public.json")
            zkey_path = PROJECT_ROOT / "merit_final.zkey"

            print(f"[*] Generating groth16 proof with {zkey_path.name}")
            result = subprocess.run(
                ["npx", "snarkjs", "groth16", "prove",
                 str(zkey_path), wtns_path, proof_path, public_path],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(PROJECT_ROOT),
            )
            if result.returncode != 0:
                raise RuntimeError(f"snarkjs groth16 prove failed: {result.stderr}")
            print(f"[✓] groth16 proof generated successfully")

            with open(proof_path) as f:
                proof = json.load(f)
            with open(public_path) as f:
                public_signals = json.load(f)

            print(f"    pi_a: {str(proof['pi_a'])[:60]}...")
            print(f"    public signals: {public_signals}")

            return {
                "agent": agent,
                "threshold": threshold,
                "score": score,
                "merkleRoot": merkle_root,
                "success": True,
                "proof": proof,
                "publicSignals": public_signals,
                "metadata": {
                    "proofSize": "1.5KB",
                    "verificationGas": "~200000",
                    "onChainReady": True,
                },
            }

    except Exception as e:
        print(f"[!] Real proof generation failed: {e}")
        return {
            "agent": agent,
            "threshold": threshold,
            "score": score,
            "merkleRoot": merkle_root,
            "success": False,
            "reason": str(e),
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Merit Threshold ZK Prover")
    parser.add_argument("--agent", required=True, choices=list(AGENTS.keys()),
                        help="Agent to prove for (alice, bob, carol)")
    parser.add_argument("--threshold", type=int, default=5000,
                        help="Merit threshold to prove (0-9999)")

    args = parser.parse_args()
    result = generate_proof(args.agent, args.threshold)

    print("\n[Result]")
    print(json.dumps(result, indent=2))

    if not result.get("success", False):
        sys.exit(1)


if __name__ == "__main__":
    main()
