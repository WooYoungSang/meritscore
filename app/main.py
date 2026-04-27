import streamlit as st
import httpx
import os
import json
import subprocess
from pathlib import Path

st.set_page_config(page_title="MeritScore — W.A.R.V.I.S", page_icon="⚡", layout="wide")

_WARVIS_LOGO_SVG = """
<div style="display:flex;align-items:center;gap:18px;padding:20px 0 8px 0;">
  <svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="wg" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stop-color="#5ce8ff"/>
        <stop offset="100%" stop-color="#00a8cc"/>
      </linearGradient>
    </defs>
    <rect x="2" y="2" width="60" height="60" rx="14" fill="#0b1218" stroke="url(#wg)" stroke-width="1.5"/>
    <path d="M14 44 L24 24 L32 38 L40 24 L50 44"
          fill="none" stroke="url(#wg)" stroke-width="3.2"
          stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="32" cy="14" r="2.6" fill="#5ce8ff"/>
  </svg>
  <div style="display:flex;flex-direction:column;gap:2px;">
    <span style="font-family:'JetBrains Mono',monospace;font-weight:700;font-size:28px;letter-spacing:0.12em;color:#f3f5f8;line-height:1;">
      W<span style="color:#00d4ff;">.</span>A<span style="color:#00d4ff;">.</span>R<span style="color:#00d4ff;">.</span>V<span style="color:#00d4ff;">.</span>I<span style="color:#00d4ff;">.</span>S
    </span>
    <span style="font-family:'Space Grotesk',sans-serif;font-size:11px;letter-spacing:0.32em;color:#5ce8ff;text-transform:uppercase;">
      A Rather Very Intelligent System
    </span>
  </div>
</div>
"""
st.markdown(_WARVIS_LOGO_SVG, unsafe_allow_html=True)
st.caption("MeritScore — Experian for AI Agents · EthGlobal OpenAgents 2026")

BFF_URL = os.getenv("BFF_URL", "https://meritscore.warvis.org")
PROJECT_ROOT = Path(__file__).parent.parent

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Merit Score",
    "🏅 Attestation",
    "⚙️ KH Workflow",
    "🤖 AI Analyze",
    "🔒 ZK Proof"
])

# ============================================================================
# Tab 1: Merit Score
# ============================================================================
with tab1:
    st.header("Agent Merit Score")

    col1, col2 = st.columns([3, 1])
    with col1:
        addr = st.text_input(
            "Agent address",
            placeholder="0x... or alice / bob / carol",
            key="score_input"
        )
    with col2:
        score_button = st.button("Score Agent", key="score_button")

    if score_button and addr:
        with st.spinner("Scoring..."):
            try:
                r = httpx.get(f"{BFF_URL}/merit/{addr}", timeout=30)
                r.raise_for_status()
                data = r.json()
                score = data.get("score", 0)

                col_score, col_verdict = st.columns(2)
                with col_score:
                    st.metric("Merit Score", f"{score:.4f}")
                with col_verdict:
                    if score >= 0.5:
                        verdict = "✅ APPROVED"
                    elif score >= 0.1:
                        verdict = "⚠️ LOW"
                    else:
                        verdict = "❌ FLAGGED"
                    st.metric("Verdict", verdict)

                if "ai_reasoning" in data:
                    with st.expander("AI Reasoning"):
                        st.write(data["ai_reasoning"])
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")
    st.markdown("**Demo agents**: alice (MEV bot, 0.26) | bob (Arb agent, 0.67) | carol (new, 0.00)")

# ============================================================================
# Tab 2: Attestation (placeholder)
# ============================================================================
with tab2:
    st.header("TEE Attestation")
    st.info("Attestation card endpoint: GET /attestation")
    st.write("0G Compute TEE proof of computation on-chain.")

# ============================================================================
# Tab 3: KH Workflow (placeholder)
# ============================================================================
with tab3:
    st.header("KeeperHub 3-Step Workflow")
    st.info("Workflow endpoint: POST /kh/workflow (CHECK → VALIDATE → EXECUTE)")
    st.write("Log execution traces and validation results.")

# ============================================================================
# Tab 4: AI Analyze (placeholder)
# ============================================================================
with tab4:
    st.header("AI Sandwich Detection")
    st.info("AI analysis endpoint: POST /analyze (Gemma4 26B / Ollama)")
    st.write("Detects adversarial patterns in transaction sequences.")

# ============================================================================
# Tab 5: ZK Proof
# ============================================================================
with tab5:
    st.header("🔒 Privacy Tier — ZK Merit Proof")

    st.markdown("""
    **Prove your merit score meets a threshold WITHOUT revealing your score.**

    - **Circuit**: Poseidon hash + Merkle tree + threshold comparison
    - **Proof**: Groth16 (~1.5KB, ~200ms on web)
    - **Verifier**: On-chain Solidity smart contract (Base Sepolia ready)
    """)

    st.subheader("Generate Anonymous Proof")

    col_agent, col_threshold = st.columns(2)
    with col_agent:
        agent = st.selectbox(
            "Agent",
            ["bob", "alice", "carol"],
            key="zk_agent"
        )
    with col_threshold:
        threshold = st.slider(
            "Threshold (0-9999)",
            min_value=0,
            max_value=9999,
            value=5000,
            key="zk_threshold"
        )

    if st.button("🔐 Generate Proof for " + agent.upper(), key="zk_button"):
        with st.spinner("Generating ZK proof..."):
            try:
                # Call prover script
                result = subprocess.run(
                    [
                        "python",
                        str(PROJECT_ROOT / "scripts" / "prove_merit.py"),
                        "--agent", agent,
                        "--threshold", str(threshold)
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                # Parse output JSON from last line
                output_lines = result.stdout.strip().split('\n')
                json_start = None
                for i, line in enumerate(output_lines):
                    if line.startswith('{'):
                        json_start = i
                        break

                if json_start is not None:
                    proof_data = json.loads('\n'.join(output_lines[json_start:]))

                    if proof_data.get("success"):
                        st.success("✓ Proof generated successfully!")

                        col_root, col_threshold_display = st.columns(2)
                        with col_root:
                            st.metric(
                                "Merkle Root",
                                f"{proof_data['merkleRoot']}"
                            )
                        with col_threshold_display:
                            st.metric(
                                "Threshold",
                                f"{proof_data['threshold']}"
                            )

                        with st.expander("Proof Details"):
                            st.json(proof_data)

                        st.markdown("---")
                        st.markdown("""
                        **On-Chain Verification**

                        Agent address: **HIDDEN** 🔐
                        Agent score: **HIDDEN** 🔐
                        Merit ≥ threshold: **✅ CRYPTOGRAPHICALLY CERTAIN**

                        This proof can be verified on Base Sepolia by any verifier contract.
                        No sensitive information is revealed.
                        """)
                    else:
                        st.error(f"❌ Proof generation failed: {proof_data.get('reason', 'Unknown error')}")
                else:
                    st.error(f"Error parsing output:\n{result.stdout}\n{result.stderr}")
            except subprocess.TimeoutExpired:
                st.error("Proof generation timeout")
            except Exception as e:
                st.error(f"Error: {e}")

st.markdown("---")
st.caption("Proof-of-Merit | EthGlobal Open Agents Hackathon 2026")
