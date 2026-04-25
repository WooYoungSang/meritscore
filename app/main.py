import streamlit as st
import httpx
import os

st.set_page_config(page_title="warvis-hackerton Merit Score", page_icon="⚡")
st.caption("Experian for agents. Credit scores for robots.")

BFF_URL = os.getenv("BFF_URL", "https://meritscore.warvis.org")

st.title("⚡ Agent Merit Score")

addr = st.text_input("Agent address (Base Sepolia)", placeholder="0x... or alice / bob / carol")

if st.button("Score Agent") and addr:
    with st.spinner("Scoring..."):
        try:
            r = httpx.get(f"{BFF_URL}/merit/{addr}", timeout=30)
            r.raise_for_status()
            data = r.json()
            score = data.get("score", 0)
            col1, col2 = st.columns(2)
            col1.metric("Merit Score", f"{score:.4f}")
            verdict = "✅ APPROVED" if score >= 0.5 else ("⚠️ LOW" if score >= 0.1 else "❌ FLAGGED")
            col2.metric("Verdict", verdict)
            if "ai_reasoning" in data:
                with st.expander("AI Reasoning"):
                    st.write(data["ai_reasoning"])
        except Exception as e:
            st.error(f"Error: {e}")

st.markdown("---")
st.markdown("**Demo agents**: alice (MEV bot, 0.26) | bob (Arb agent, 0.67) | carol (new, 0.00)")
