import streamlit as st
import httpx
import os
import json
import subprocess
from pathlib import Path

st.set_page_config(page_title="MeritScore — W.A.R.V.I.S", page_icon="⚡", layout="wide")

_WARVIS_LOGO_SVG = """
<div style="display:flex;flex-direction:column;align-items:flex-start;gap:10px;padding:24px 0 12px 0;">
  <svg width="72" height="72" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="wg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#5ce8ff"/>
        <stop offset="100%" stop-color="#00a8cc"/>
      </linearGradient>
      <radialGradient id="wcore" cx="0.5" cy="0.5" r="0.5">
        <stop offset="0%"   stop-color="#e8fbff" stop-opacity="1"/>
        <stop offset="30%"  stop-color="#5ce8ff" stop-opacity="0.85"/>
        <stop offset="70%"  stop-color="#00a8cc" stop-opacity="0.25"/>
        <stop offset="100%" stop-color="#00a8cc" stop-opacity="0"/>
      </radialGradient>
      <style>
        @keyframes wh{0%,100%{opacity:.2}50%{opacity:.45}}
        @keyframes wc{0%,100%{opacity:.4}50%{opacity:.7}}
        .wh{animation:wh 3.2s infinite}
        .wc{animation:wc 2.4s infinite}
      </style>
    </defs>
    <!-- outer halo -->
    <circle cx="32" cy="32" r="30" fill="url(#wcore)" opacity="0.2" class="wh"/>
    <!-- reactor ring -->
    <circle cx="32" cy="32" r="30" fill="#0b1218" stroke="url(#wg)" stroke-width="1.8"/>
    <!-- inner ring -->
    <circle cx="32" cy="32" r="27" fill="none" stroke="url(#wg)" stroke-width="0.7" opacity="0.55"/>
    <!-- 8 segment ticks -->
    <g stroke="url(#wg)" stroke-width="1" stroke-linecap="round" opacity="0.7">
      <line x1="32" y1="2"    x2="32" y2="6"/>
      <line x1="32" y1="58"   x2="32" y2="62"/>
      <line x1="2"  y1="32"   x2="6"  y2="32"/>
      <line x1="58" y1="32"   x2="62" y2="32"/>
      <line x1="10.8" y1="10.8" x2="13.6" y2="13.6"/>
      <line x1="50.4" y1="50.4" x2="53.2" y2="53.2"/>
      <line x1="50.4" y1="13.6" x2="53.2" y2="10.8"/>
      <line x1="10.8" y1="53.2" x2="13.6" y2="50.4"/>
    </g>
    <!-- core glow -->
    <circle cx="32" cy="30" r="16" fill="url(#wcore)" opacity="0.4" class="wc"/>
    <!-- inverted triangle -->
    <path d="M12 17 L52 17 L32 52 Z" fill="#0b1218" stroke="url(#wg)" stroke-width="2.4" stroke-linejoin="round"/>
    <!-- inner triangle echo -->
    <path d="M16.5 19.5 L47.5 19.5 L32 47 Z" fill="none" stroke="url(#wg)" stroke-width="0.7" stroke-linejoin="round" opacity="0.5"/>
    <!-- W -->
    <path d="M21 23 L26 33 L32 26 L38 33 L43 23" fill="none" stroke="#e8fbff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" filter="drop-shadow(0 0 1.6px #5ce8ff)"/>
    <!-- spark dot -->
    <circle cx="32" cy="42" r="2" fill="#ffffff"/>
    <circle cx="32" cy="42" r="4" fill="#5ce8ff" opacity="0.4"/>
  </svg>
  <div style="display:flex;flex-direction:column;gap:4px;">
    <span style="font-family:'JetBrains Mono',monospace;font-weight:700;font-size:22px;letter-spacing:0.02em;color:#f3f5f8;line-height:1;">
      W<span style="color:#00d4ff;">.</span>A<span style="color:#00d4ff;">.</span>R<span style="color:#00d4ff;">.</span>V<span style="color:#00d4ff;">.</span>I<span style="color:#00d4ff;">.</span>S
    </span>
    <span style="font-family:'Space Grotesk',sans-serif;font-size:10px;letter-spacing:0.32em;color:#5b6675;text-transform:uppercase;">
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
