# MeritScore Demo Script — Tier A (R11)

## Opening Hook (0:00–0:15)

**Narrator:**
> "An AI agent just lost $50,000 in a sandwich attack. No one checked its credit score."
>
> "Meet MeritScore: the first on-chain credit system for AI agents."

**Visual:** Dark background, glowing red error indicator showing sandwich attack, $50K loss.

---

## Problem Statement (0:15–0:30)

**Narrator:**
> "Today, AI agents execute billions in DeFi transactions autonomously—but there's no way to tell a trusted arbitrage bot from a malicious sandwich attacker."
>
> "DeFi protocols are flying blind. They either ban all agents or trust them all equally."

**Visual:** Split screen showing two agents—honest arbitrage bot on left, sandwich attacker on right.

---

## Solution Intro (0:30–0:45)

**Narrator:**
> "MeritScore changes that."
>
> "We rate agent behavior on-chain and issue verifiable credit scores. High-merit agents unlock liquidity and low rates. Bad actors get blocked or require collateral."

**Visual:** MeritScore logo appears, animated three-chain (0G Galileo + Base) visualization.

---

## Live Demo (0:45–2:00)

### Demo Segment 1: Honest Agent (Bob)

**Narrator:**
> "Here's Bob—an honest arbitrage bot with a clean trading history."

**Action:**
1. Navigate to https://meritscore.warvis.org
2. Click on "Agent Bob" card
3. Show score: **0.6703** ✅ **APPROVED**
4. Highlight: "Workflow mode · Clean trading history · High integrity"
5. Display sparkline showing stable upward trend

**Visual:** Green checkmark, "APPROVED" verdict, merit score display with animation.

---

### Demo Segment 2: Adversarial Agent (Carol)

**Narrator:**
> "Now meet Carol. Carol's running a sandwich attack—frontrunning, targeting victims, then backrunning."

**Action:**
1. Click on "Agent Carol" card
2. Show **⚠️ ADVERSARIAL AGENT DETECTED** banner
3. Show score: **0.0000** ⏸ **BLOCKED**
4. Click "Live Eval" tab → enter `carol` or `0xca401ca401ca401ca401ca401ca401ca401ca401`
5. Run evaluation → Show AI analysis: **"⚠ Sandwich pattern detected"**
6. Highlight the red warning: "Sandwich attack signature · MEV searcher behavior · High risk"

**Visual:** Red warning banner, ⚠️ icon, "BLOCKED" verdict, sandwich attack pattern highlighted in transaction history.

---

### Demo Segment 3: Partial Agent (Alice)

**Narrator:**
> "Alice is borderline—some sandwiching detected, but not a full attacker. She gets a conditional score."

**Action:**
1. Click on "Agent Alice" card
2. Show score: **0.2641** ❌ **REJECTED**
3. Click "Live Eval" tab → enter `alice`
4. Show AI analysis: "Sandwich pattern detected"
5. Explain: "Merit penalized until she cleans her behavior"

**Visual:** Orange/red transition, "REJECTED" verdict, merit score display.

---

## Sword Technologies (1:45–1:50)

**Narrator:**
> "MeritScore is built on four technologies:"
>
> "**Sword #1:** Live evaluation button—real-time merit scoring in your wallet."
>
> "**Sword #2:** TEE attestation—cryptographic proof sealed in trusted hardware."
>
> "**Sword #3:** KeeperHub workflow—automated validation on-chain."
>
> "**Sword #4:** AI enrichment—Gemma4 sandwich detection."

**Visual:** Quickly show each tab: Live Eval, TEE Attestation, KH Workflow, AI Analysis.

---

## Call to Action (1:50–2:00)

**Narrator:**
> "MeritScore: For protocols that want to trust agents. For agents that deserve to be trusted."
>
> "https://meritscore.warvis.org"

**Visual:** MeritScore homepage, chains lighting up, final tagline: "The Experian for AI Agents"

---

## Key Talking Points

- **Problem:** AI agents entering DeFi at scale with no credit infrastructure
- **Solution:** On-chain reputation system with verifiable scores (0–1.0 scale)
- **Demo Impact:** Show honest agent (Bob ✅) vs. sandwich attacker (Carol ⚠️)
- **Tech:** 4 Sword architecture (Live Eval + TEE + KH + AI)
- **Business:** Gating DeFi access, reducing slippage attacks, protecting LPs

---

## Timing Checklist

- [ ] Opening hook (0:00–0:15): 15s
- [ ] Problem statement (0:15–0:30): 15s
- [ ] Solution intro (0:30–0:45): 15s
- [ ] Live demo (0:45–1:50): 65s
  - [ ] Bob approval (20s)
  - [ ] Carol adversarial detection (25s)
  - [ ] Alice rejection (15s)
  - [ ] Sword overview (5s)
- [ ] Call to action (1:50–2:00): 10s

**Total: 2:00 (120 seconds)**

---

## Demo Environment Setup

**Prerequisites:**
- MeritScore live at https://meritscore.warvis.org (port 61234)
- Docker container running: `docker-compose up`
- Ollama running (sandwich detection model)
- RPC endpoints active: 0G Galileo + Base Sepolia

**Test Agents:**
- **Alice:** score 0.2641 (rejected, sandwich pattern)
- **Bob:** score 0.6703 (approved, clean)
- **Carol:** score 0.0000 (blocked, adversarial — new for R11)

---

## Post-Demo Follow-up

After 2:00 demo, offer:
- Live question interaction (type wallet addresses)
- Show TEE attestation proof
- Explain KeeperHub workflow integration
- Discuss cross-chain score synchronization (0G → Base)

