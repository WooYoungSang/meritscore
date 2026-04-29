# Final Submission Draft — MeritScore

**Hackathon**: EthGlobal OpenAgents 2026
**Submission deadline**: 2026-05-04 01:00 KST
**Submission URL**: https://ethglobal.com/showcase (paste fields below into the showcase form)

> This file is the source-of-truth for every field on the EthGlobal submission form. Copy each block into the matching field. Update placeholders marked with `<<TODO>>` before submitting.

---

## 1. Project name

```
MeritScore
```

## 2. Tagline (≤ 80 chars)

```
Experian for AI Agents — on-chain merit scoring with ZK proofs and merit-gated DeFi
```

(Length check: 81 chars — trim to under 80 if EthGlobal enforces; alternative shorter form: `Experian for AI Agents — merit-gated trust for autonomous agents`)

## 3. Short description (≤ 200 chars)

```
On-chain merit scores for AI agents. ZK proofs prove "merit ≥ threshold" without revealing scores. Merit-gates Uniswap swaps, KeeperHub workflows, and lending — fully verifiable on 0G + Base.
```

## 4. Long description (markdown; submission body)

```markdown
## The problem

AI agents are now executing real on-chain transactions: arbitrage, lending, DEX trading, and cross-protocol coordination. Today there is no shared trust signal: every protocol has to re-evaluate every agent from scratch, or trust unsigned off-chain claims.

This is the equivalent of every bank in the world rebuilding a credit bureau from raw transaction logs. It does not scale, and it leaves protocols exposed to MEV bots, sandwich attackers, and previously-flagged adversarial agents masquerading as fresh wallets.

## What we built

**MeritScore** — an on-chain credit bureau for AI agents.

A merit score (0.0 – 1.0) is computed from each agent's behavioral history (sandwich detection, latency, integrity, TEE-attested execution). The score lives on 0G Galileo (`MeritCore`) and is consumable by any chain: Base Sepolia integrations are already wired (Uniswap V3, KeeperHub workflows, lending vault).

**Six attack-surface "Swords" demonstrate end-to-end utility:**

| # | Sword | What it proves |
|---|---|---|
| 1 | **Live Evaluation** | Real-time score read from `MeritCore` — no caches, no mocks |
| 2 | **TEE Attestation** | 0G Compute TeeML inference produces a per-call attestation card |
| 3 | **KeeperHub 3-Step Workflow** | CHECK (0G merit) → VALIDATE (Base) → EXECUTE (KH relay) |
| 4 | **AI-Enriched Formula** | Sandwich-attack detection via Gemma4 26B (Ollama) feeds the score |
| 5 | **ZK Merit Proof** | Real Groth16 (circom + circomlibjs Poseidon, depth-8 Merkle tree) — proves `merit ≥ threshold` without revealing the score |
| 6 | **Uniswap Merit-Gated Swap** | Live swap on Base Sepolia gated by merit ≥ 0.5. Bob (0.6703) executes, Alice (0.2641) and Carol (0.0000) blocked. **Proven on-chain:** [`0x0c7c4e...cdcf897`](https://sepolia.basescan.org/tx/0x0c7c4ed5142950e771c4ac99178764a512bbc5a12f18513b3672b57d7cdcf897) |

## Architecture

```
                 ┌──────── 0G Galileo (16602) ────────┐
                 │                                    │
   Agent ──► MeritCore ──► TeeML ──► EvidenceRegistry │
                 │           │              │         │
                 └───────────┼──────────────┼─────────┘
                             │              │
                       (merit score)  (Merkle root)
                             │              │
                             ▼              ▼
              ┌───────── BFF (FastAPI) ────────┐
              │ /merit /attestation /kh/workflow│
              │ /analyze /zk/prove /uniswap/swap│
              └───────────────┬────────────────┘
                              │
                ┌─────────────┼─────────────────┐
                ▼             ▼                 ▼
        Base Sepolia    KeeperHub        Uniswap V3
        (MeritVault,    (workflow         (SwapRouter02,
         AgentLending)   relay)            QuoterV2)
```

## Three demo agents (deterministic for judging)

| Agent | Role | Merit | Outcome |
|-------|------|:-----:|---------|
| **Bob** | Honest arbitrageur | 0.6703 | All gates pass — Uniswap swap, KeeperHub workflow, ZK proof |
| **Alice** | Sandwich bot | 0.2641 | Workflow VALIDATEs but is below 0.5 → swap & lending blocked |
| **Carol** | Unverified / new agent | 0.0000 | Hard-fail at the first gate — every action denied |

## Why this matters

- **For agent operators**: a portable trust score that crosses chains and dapps
- **For protocols**: an immediate, on-chain merit oracle — no rebuild needed
- **For users**: the assurance that your money flows only through agents that have demonstrably behaved well, with ZK privacy preserving the underlying score
```

## 5. How it's made (technical narrative)

```markdown
**Smart contracts (Solidity, Foundry):**
- `MeritCore` (0G Galileo) — append-only merit score registry with Merkle commitments
- `EvidenceRegistry` (0G Galileo) — anchors per-agent evidence Merkle roots
- `MeritVault` (Base Sepolia) — cross-chain merit attestation receiver
- `AgentLendingPool` (Base Sepolia) — merit-gated lending example

**Backend (Python 3.10, FastAPI):**
- `python/bff/main.py` — single BFF exposing `/merit`, `/attestation`, `/kh/workflow`, `/analyze`, `/zk/prove`, `/uniswap/swap`
- `python/bff/uniswap.py` — direct on-chain Uniswap V3 client (QuoterV2 + SwapRouter02 via web3.py 7.14)
- `python/bff/attestation.py` — 0G Compute TeeML invocation (`inference-v1.0` service)
- `python/bff/workflow.py` — KeeperHub 3-step orchestration with ZK gate between VALIDATE and EXECUTE

**ZK (circom 2 + snarkjs Groth16):**
- `circuits/merit_threshold.circom` — proves `merit ≥ threshold` over a depth-8 Poseidon Merkle tree
- `scripts/prove_merit.py` — wraps snarkjs to produce real BN128 proofs (no dummy values)

**Frontend (React 18, Babel-standalone in app.jsx):**
- 7-tab judge UI: Live Eval, TEE, KH Workflow, AI Analysis, ZK Proof, Uniswap Swap, MeritGuard
- Live tx hash links to BaseScan / 0G Galileo explorer

**AI / TEE:**
- 0G Compute TeeML for trust-minimized inference (Gemma4 26B via Ollama provider)
- Per-call attestation card with provider, model hash, and signature

**Tooling we are proud of:**
- `warvis-orchestrator` agent pipeline ran the full UoW lifecycle (plan → red test → green code → verify → commit) under TDD discipline
- `rules-guardian` independent agent enforced EthGlobal's 8 rules + AI disclosure on every commit (preflight + final gate)

**Hardest parts:**
- 0G Galileo requires `--legacy` on every cast call (no EIP-1559 support); easy to miss until first deploy fails
- 0G Compute SDK uses `inference-v1.0` (not `"inference"`) as the service name — undocumented at the time we shipped
- Real Groth16 over Poseidon-hashed Merkle leaves needed careful field-element handling (snarkjs returns decimal strings, not hex)
- Wiring the merit gate without coupling it to KeeperHub: we chose a separate `/uniswap/swap` endpoint so a swap failure can never be misread as a workflow failure

**Live demo proof (Sword #6, Base Sepolia, 2026-04-29):**
- Wrap 0.0005 ETH → WETH: [`0x7ef399...e2662f`](https://sepolia.basescan.org/tx/0x7ef399b80e4e893827e994c83c1d947ec1a34251b8aa009c5569788f04e2662f)
- Approve WETH → SwapRouter02: [`0x6b46ca...500eec`](https://sepolia.basescan.org/tx/0x6b46cad0cefd29402e265dbb657677641e4a3c64c79ae4b136b594227c500eec)
- **Live swap (Bob, merit 0.6703):** 0.0001 WETH → 0.015978 USDC: [`0x0c7c4e...cdcf897`](https://sepolia.basescan.org/tx/0x0c7c4ed5142950e771c4ac99178764a512bbc5a12f18513b3672b57d7cdcf897)
```

## 6. Demo video URL

```
<<TODO>>  e.g. https://www.youtube.com/watch?v=...
```
*(Recording planned. ≤ 5 min, public, includes live demo on https://meritscore.warvis.org.)*

## 7. GitHub URL

```
https://github.com/WooYoungSang/meritscore
```

⚠ **Repo must be public** by submission time. Confirm visibility on GitHub settings before paste.

## 8. Live URL

```
https://meritscore.warvis.org
```

(API health check: `https://meritscore.warvis.org/health`)

## 9. Tech stack tags (form expects multi-select)

```
Solidity, Python, TypeScript, FastAPI, React, Foundry, web3.py, snarkjs, circom, Groth16, Uniswap V3, 0G Galileo, 0G Compute, KeeperHub, Base Sepolia, TEE, ZK
```

## 10. Prize tracks

- ☑ **0G** — MeritCore on Galileo, TeeML inference, EvidenceRegistry on 0G Storage
- ☑ **KeeperHub** — 3-step workflow (CHECK → VALIDATE → ZK gate → EXECUTE)
- ☐ Other tracks: review final EthGlobal prize list at submission time and check any track for which we have a real integration — do not over-claim.

## 11. Team

| Name | EthGlobal handle | Role |
|------|------------------|------|
| WoopsFactory | `<<TODO confirm handle>>` | Lead — architecture, contracts, on-chain ops |
| `<<TODO add others if any>>` | | |

## 12. Deployed contracts (paste into form's "Deployed contracts" field if present)

| Contract | Chain | Address |
|----------|-------|---------|
| `MeritCore` | 0G Galileo (16602) | `0x19E3C17F58052Bb75D1c24bC1c56C2bfd1E5A906` |
| `EvidenceRegistry` | 0G Galileo (16602) | `0x4DE88763BfcBd799376c4715c245F656D518e43B` |
| `MeritVault` | Base Sepolia (84532) | `0x3ef2818dD26F4B2e73D8fAb65F6aEA6bc1A2F5E2` |
| `MeritVault v2` | Base Sepolia (84532) | `0xf55452BfE9f37A4A8D77e18524F4Ae81537C0a7e` |
| `AgentLendingPool` | Base Sepolia (84532) | `0x78E33F871f210E898cd875e259ce24BD61074e34` |

## 13. AI Tool Disclosure (paste into the dedicated form field)

```
This project was built with AI assistance, in compliance with EthGlobal's
AI tool policy.

Tools: Claude Code (Anthropic) — Sonnet 4.6 and Opus 4.7 models.

Scope of AI assistance:
  - Code generation (Python, Solidity, TypeScript, JSX) under TDD discipline
  - Multi-agent orchestration (planner / executor / verifier / rules-guardian)
  - Test scaffolding and mock harnesses
  - Documentation drafting

Human-directed scope:
  - All architectural decisions, prize-track selection, product framing
  - All on-chain transactions (wallet signing, contract deployments,
    live swaps including 0x0c7c4ed5...cdcf897)
  - All prompts, agent briefs, kill-switch decisions, final commits
  - All rule-compliance reviews via the independent `rules-guardian` auditor

Verification: every AI-generated change passed pytest + ruff + an
independent rules-guardian preflight before commit. Live on-chain txs
were executed and verified by the human submitter.
```

(This text is mirrored verbatim in `README.md` under "AI Tool Disclosure".)

---

## Pre-submission checklist (run all before clicking "Submit")

- [ ] Demo video uploaded (≤ 5 min) and **public** — fill `<<TODO>>` in section 6
- [ ] GitHub repo is **public** (https://github.com/WooYoungSang/meritscore)
- [ ] Live URL responds 200 on `/health` (last-minute uptime check)
- [ ] Final `rules-guardian` invocation in **submission-gate** mode (not preflight) returns CLEAR
- [ ] Stake reclaim conditions verified (submission completed before deadline → stake auto-returned per Rule-7)
- [ ] All `<<TODO>>` placeholders in this file are resolved
- [ ] AI disclosure text in README and submission form match exactly
- [ ] Live tx hash for Sword #6 is reachable on https://sepolia.basescan.org
- [ ] No private keys, mnemonics, or `.env` contents on screen in the demo video
- [ ] At least 15 commits on `main` with linear history (Rule-2)

**Submission deadline (locked):** 2026-05-04 01:00 KST. Submit no later than 2026-05-03 23:00 KST to allow buffer.
