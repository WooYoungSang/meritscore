# MeritScore Demo Script — 60s

**Target length:** ≤ 60s narration
**Live URL:** https://meritscore.warvis.org
**Recording date:** 2026-05-03 (record on or before 2026-05-03)

Layout: each section gives **(t)** elapsed seconds, **VO** (voice-over),
**SCREEN** (what's visible), and **CLICK** (the operator action).

---

## 0:00–0:05 — Problem (5s)

- **VO:** "Onchain agents are anonymous. Anyone can spin one up and claim merit. So how do you give them money — or let them spend yours — without trust?"
- **SCREEN:** Title card or landing of https://meritscore.warvis.org
- **CLICK:** none (or fade in)

## 0:05–0:10 — MeritScore in one line (5s)

- **VO:** "MeritScore is a verifiable reputation primitive for autonomous agents — six on-chain Swords across 0G, KeeperHub, ZK, and Base."
- **SCREEN:** App home, agent picker visible (Alice / Bob / Carol)
- **CLICK:** Hover the three agent avatars

---

## 0:10–0:30 — Bob: merit-gated swap (20s)

- **VO:** "Bob's an honest arbitrage agent. His on-chain merit is 0.67. That clears 0.5, the threshold for protocol access — and it just unlocked a real Uniswap swap on Base Sepolia."
- **SCREEN → CLICK:**
  1. Click **Bob** in the agent picker
  2. Click tab **Sword #1 LIVE EVAL** → score `0.6703` shown live from MeritCore on 0G Galileo
  3. Click tab **Sword #6 UNISWAP** → click **Quote** (`0.001 WETH → USDC`, ~0.16 USDC, **price impact 0.0%**)
  4. Click **Execute Swap** → tx hash appears
- **CALLOUT (on-screen overlay):**
  `tx 0x0c7c4ed5142950e771c4ac99178764a512bbc5a12f18513b3672b57d7cdcf897`
  **Base Sepolia · live**

## 0:30–0:40 — Alice: AI sandwich detection (10s)

- **VO:** "Alice ran a sandwich attack last week. Our AI Enrich pipeline replays her tx history through Gemma 4 — verdict: adversarial. Her merit collapses to 0.26, below the gate."
- **SCREEN → CLICK:**
  1. Click **Alice** in the agent picker
  2. Click tab **Sword #4 AI ANALYZE** → "gaming_detected: true · adversarial_agent: true · merit_penalty: 0.5"
  3. Brief glance at **Sword #6 UNISWAP** → 403 banner: `merit_below_threshold (0.2641 < 0.5)`

---

## 0:40–0:50 — ZK proof: threshold without revealing score (10s)

- **VO:** "Bob proved he was over the threshold without revealing the score itself. Same primitive scales to private credit, KYC-light DeFi, agent-to-agent payments — anywhere a number must be true but cannot be public."
- **SCREEN → CLICK:**
  1. Switch back to **Bob**
  2. Click tab **Sword #5 ZK PROOF** → Groth16 proof object + verifier ✓
- **CALLOUT:** "merit ≥ 0.5 — score never disclosed"

## 0:50–0:55 — Evidence panel: TEE attestation + KH log glance (5s)

- **VO:** "All evidence is cryptographically verified — from TEE compute attestation to on-chain orchestration logs."
- **SCREEN:** Glance at **Sword #2 TEE** card (compute_hash visible) and brief line from **Sword #3 KH WORKFLOW** log
- **CLICK:** None (quick visual glance only)

## 0:55–1:00 — CTA (5s)

- **VO:** "Six Swords, all live. meritscore.warvis.org. Scores you can verify, agents you can trust."
- **SCREEN:** Final card with URL + GitHub badge + "EthGlobal OpenAgents 2026"
- **CLICK:** none (hold final frame)

---

## Operator notes

- **Pre-roll setup (off-camera):** open browser at https://meritscore.warvis.org, refresh once, default agent = Bob. Have a second tab open at the BaseScan link for the demo tx in case judges want proof later.
- **Tabs in order:** LIVE → UNISWAP (Bob, 0:10–0:30) → AI (Alice, 0:30–0:40) → UNISWAP glance (Alice 403, quick) → ZK (Bob, 0:40–0:50) → TEE + KH log glance (0:50–0:55).
- **Carol removed from live demo** — KeeperHub validation takes too long for 60s. TEE + KH log glance covers Swords #2 and #3 in evidence panel.
- **Quote-only mode if Sepolia faucet drains:** if the live `Execute Swap` reverts during recording, fall back to Quote-only and the existing tx hash overlay (`0x0c7c4...`) — narrate "and that's the tx we landed earlier today".
- **Dual-resolution OK:** verified end-to-end at 1920x1080 and 1366x768 (`scripts/verify_ui_tabs.py`, 0 console errors, no tab-bar overflow).

## Timing budget

| Section | Plan (s) | Cumulative |
|---|---:|---:|
| Problem | 5 | 5 |
| MeritScore intro | 5 | 10 |
| Bob (merit-gated swap) | 20 | 30 |
| Alice (AI sandwich detection) | 10 | 40 |
| ZK proof (threshold without score) | 10 | 50 |
| Evidence panel (TEE + KH log) | 5 | 55 |
| CTA | 5 | 60 |
