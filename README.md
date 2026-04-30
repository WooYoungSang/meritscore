# MeritScore

> Privacy-preserving credit scores for AI agents — ZK threshold proofs that gate DeFi access across 0G + Base.

> **Built during EthGlobal OpenAgents hackathon — 2026-04-25T01:00+09:00**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://warvis-hackerton.streamlit.app)

---

## Real vs Fallback Matrix

**How each Sword behaves in production vs graceful degradation:**

| Sword | Real Path | Fallback Trigger | Live Evidence |
|-------|-----------|------------------|---------------|
| **#1: Live Evaluation** | `/merit/{addr}` reads MeritCore on 0G Galileo | Demo alias resolves to locked constants if address unknown | `0x19E3C17F58052Bb75D1c24bC1c56C2bfd1E5A906` (MeritCore) |
| **#2: TEE Attestation** | 0G Compute TeeML inference + provider attestation | Mock hash if `MOCK_MODE=true` or ledger unfunded | `/attestation` returns provider + compute_ok |
| **#3: KH 4-Step Workflow** | CHECK + VALIDATE + ZK_VERIFY run with real Merkle/Poseidon proof. EXECUTE relays to KH webhook when KH_API_KEY is set. | EXECUTE returns `intentionally_simulated` when KH webhook endpoint unconfirmed (KeeperHub partner endpoint pending public availability). CHECK + VALIDATE + ZK_VERIFY produce real on-chain/cryptographic evidence. | See live evidence in [submission-final.md](docs/submission-final.md) |
| **#4: AI Sandwich Detection** | Gemma4 26B via Ollama local inference | None (always real; Ollama required) | `/analyze` returns judgment + rationale |
| **#5: ZK Merit Proof** | Circom Poseidon + Merkle threshold, snarkjs Groth16 | None (always real, proof generation) | `scripts/prove_merit.py` + `circuits/merit_threshold.circom` |
| **#6: Uniswap Merit-Gated Swap** | Base Sepolia QuoterV2 + SwapRouter02 | None for quote; execute requires private key | `/uniswap/swap`, live tx on Base Sepolia 84532 |

---

## Demo Truth Table

**Live agent credentials and expected behavior across all endpoints:**

| Agent | Merit Score | Endpoint | Expected Result | Evidence |
|-------|:-----------:|----------|-----------------|----------|
| **Bob** (Honest Arbitrage) | **0.6703** | `/merit/bob` | Returns 0.6703 | MeritCore tx `0x132496...` |
| **Bob** | **0.6703** | `/uniswap/swap` (quote) | HTTP 200, quote OK (≥0.5 LTV) | Base Sepolia live |
| **Alice** (Sandwich MEV Bot) | **0.2641** | `/analyze` | Sandwich DETECTED + penalized | AI model output |
| **Alice** | **0.2641** | `/uniswap/swap` (execute) | HTTP 403 BLOCKED (<0.5 merit) | Merit gate enforced |
| **Carol** (Unverified) | **0.0000** | `/kh/workflow` | UNVERIFIED / no evidence | KeeperHub `intentionally_simulated` |

---

## The Problem

AI agents are entering DeFi at scale—arbitrage bots, MEV searchers, sandwich attackers, and honest market makers all operate autonomously with real economic power. Yet there's no on-chain credit infrastructure to distinguish them. DeFi protocols today can't tell a trusted arbitrage agent from a malicious sandwich bot, so they treat all agents equally—or ban them entirely.

MeritScore solves this with **on-chain agent credit scoring**: a decentralized reputation system that rates agent behavior and issues verifiable merit scores. High-merit agents unlock liquidity, low-rate swaps, and exclusive pools. Bad actors get blocked or require collateral.

---

## What We Built

**MeritScore** is a proof-of-merit infrastructure that:

1. **Evaluates agent behavior** via TEE attestation + KeeperHub workflow validation
2. **Assigns on-chain credit scores** (0–1.0 scale) to each agent address
3. **Gates DeFi access** across multiple chains (0G Galileo + Base Sepolia)
4. **Provides verifiable evidence** (storage anchoring + oracle commit)
5. **Supports honest-mode badges** (Direct / Workflow / Web3) for agents to self-declare

### Six-Sword Architecture

**Sword #1: Live Evaluation Button** ✅
- Interactive UI for real-time merit scoring (wallet input field)
- Displays agent merit scores with AI-powered analysis card
- Supports named aliases (Alice/Bob/Carol) or arbitrary wallet addresses
- Live demo at `https://meritscore.warvis.org` (port 61234, Docker)
- Endpoints: `/merit/{address}` (lookup) + `/analyze` (AI classification)
- Status: **DONE** (Docker validated, all API endpoints tested)

**Sword #2: TEE Attestation Card** ✅
- Computes a 3-hash proof: `compute_hash(inference result) + storage_root(evidence) + oracle_commit(scores)`
- Attestation sealed in Trusted Execution Environment via 0G Compute
- Storage root anchored to EvidenceRegistry on-chain
- **Deployment note**: Set `MOCK_MODE=false` + `OG_PRIVATE_KEY` in `.env` to enable live 0G Compute TeeML inference. When the 0G Compute ledger is unfunded or the service is unreachable, the system gracefully falls back to deterministic mock hashes (unique per call via timestamp nonce). The fallback is fully functional for demo purposes; the production path runs real TeeML.

**Sword #3: KeeperHub Workflow** ✅
- CHECK: Request agent evidence from API (real)
- VALIDATE: Verify attestation + score bounds (real on-chain)
- ZK_VERIFY: Groth16 threshold proof verified (real cryptographic)
- EXECUTE: Relays to KeeperHub webhook when configured; otherwise returns `status: "intentionally_simulated"` with reason
- **Honest labeling**: If `KH_BASE_URL` / `KH_API_KEY` are unset or KeeperHub is unreachable, EXECUTE returns `{"status": "intentionally_simulated", "reason": "..."}` — CHECK + VALIDATE + ZK_VERIFY still produce real on-chain / cryptographic evidence regardless. Set `KH_BASE_URL=https://app.keeperhub.com` and `KH_API_KEY=wfb_…` in `.env` to enable live KH webhook execution. See Real-vs-Fallback Matrix above.

**Sword #4: AI Enrich** ✅
- Runs Gemma4 26B via Ollama for sandwich attack detection
- Classifies agent behavior: `honest / mev_searcher / sandwich_attacker`
- Feeds classification to merit oracle

**Sword #5: ZK Merit Proof (Privacy Tier)** ✅
- Agents prove merit ≥ threshold WITHOUT revealing actual score
- Poseidon + Merkle tree + threshold verification in circom
- Groth16 proofs (~1.5KB, ~200ms)
- On-chain Solidity verifier (Base Sepolia ready)
- Privacy guarantee: only merkleRoot + threshold visible on-chain

**Sword #6: Uniswap Merit-Gated Swap** ✅
- Live merit-gated DEX execution on Base Sepolia (Uniswap V3)
- `POST /uniswap/swap` with `action: quote | execute` and threshold = 0.5
- Bob (0.6703) executes swaps; Alice (0.2641) and Carol (0.0000) blocked at gate
- Pool: WETH ↔ USDC, fee tier 3000 (with 500 bps fallback)
- **On-chain proof:** [`0x0c7c4e…cdcf897`](https://sepolia.basescan.org/tx/0x0c7c4ed5142950e771c4ac99178764a512bbc5a12f18513b3672b57d7cdcf897) (0.0001 WETH → 0.015978 USDC)
- Deep-dive details in the *Sword #6* section below

---

## Live Demo

Three agents demonstrate the system in action:

| Agent | Address | Merit Score | Status | Reason |
|-------|---------|-------------|--------|--------|
| **Alice** (Sandwich MEV Bot) | `0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266` | **0.2641** | ❌ **REJECTED** | Sandwich attack pattern detected |
| **Bob** (Honest Arbitrage Agent) | `0x70997970C51812dc3A010C7d01b50e0d17dc79C8` | **0.6703** | ✅ **APPROVED** | Clean trading history, high integrity |
| **Carol** (Unverified New Agent) | `0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC` | **0.0000** | ⏸️ **BLOCKED** | No evidence submitted |

**How it works:**
- Alice's transactions analyzed by AI model → sandwich attack signature detected → merit penalized
- Bob's workflow validated via KeeperHub → no malicious patterns → merit approved
- Carol hasn't submitted evidence → score remains zero (can appeal later)

---

## How It Works

### 1. Agent Submits Evidence
Agent calls `/kh/workflow` with behavior data (transaction history, account metadata, attestation proof).

### 2. KeeperHub Validates
- **CHECK**: Fetch evidence from agent API
- **VALIDATE**: Verify attestation signature + check score bounds (0 ≤ score ≤ 1.0)
- **EXECUTE**: If valid, call `setMerit(agent_address, score)` on MeritCore

### 3. Merit Score Computed
**Factors:**
- Attestation validity (TEE seal)
- Sandwich attack score (Gemma4 AI model)
- Historical transaction integrity
- KeeperHub workflow completion

**Formula:**
```
merit_score = 1.0 
  - (0.4 × sandwich_score)      # Attack detection weight
  - (0.3 × account_age_penalty)  # New accounts discounted
  - (0.3 × behavior_anomaly)     # Unusual patterns
```

### 4. Score Published On-Chain
- **MeritCore** (0G Galileo): Writes `agent_address → score` mapping
- **EvidenceRegistry**: Anchors storage proof (Merkle root)
- **MeritVault** (Base Sepolia): Mirrors scores for cross-chain access

### 5. DeFi Protocols Gate Access
Protocol checks MeritScore before executing agent orders:
```solidity
require(meritCore.getMerit(msg.sender) > threshold, "MERIT_TOO_LOW");
```

---

## 🔗 How other protocols integrate

Any protocol can integrate MeritScore in **3 lines of code**:

```solidity
import {IMeritVault} from "warvis-hackerton/contracts/interfaces/IMeritVault.sol";

// In your contract:
IMeritVault merit = IMeritVault(0x3ef2818dD26F4B2e73D8fAb65F6aEA6bc1A2F5E2);
require(merit.getScore(agent) >= MIN_MERIT_THRESHOLD, "Agent merit too low");
```

**Example:** `AgentLendingPool` — demonstrates tiered collateral requirements based on agent merit:

| Agent | Merit Score | Approval | LTV | Reason |
|-------|:-----------:|:--------:|:---:|--------|
| **Bob** (Honest Arbitrageur) | 0.6703 | ✅ **APPROVED** | 60% | Merit ≥ 600 → can borrow at 6% LTV |
| **Alice** (MEV Sandwich Bot) | 0.2641 | ❌ **REJECTED** | — | Merit 2641 < MIN_MERIT 5000 → reverts "agent merit too low" |

**Live Example Contract:** [`AgentLendingPool.sol`](./contracts/examples/AgentLendingPool.sol)  
**Deployment:** [Basescan](https://sepolia.basescan.org/address/0x78E33F871f210E898cd875e259ce24BD61074e34) · tx `0x2ccca353...`  
**MeritVault (demo):** [Basescan](https://sepolia.basescan.org/address/0xf55452BfE9f37A4A8D77e18524F4Ae81537C0a7e) · seeded scores: alice=2641, bob=6703, carol=0

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Agent (Alice/Bob/Carol)               │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ├─→ [1] Submit Evidence (tx history, metadata)
                 │
    ┌────────────▼────────────────────────────────┐
    │      KeeperHub Workflow Validator           │
    │  CHECK → VALIDATE → EXECUTE                │
    └────────┬───────────────────────────────────┘
             │
             ├─→ [2a] Fetch Agent Evidence
             │
             ├─→ [2b] AI Model (Gemma4 26B)
             │        Sandwich Attack Detection
             │        Classification: honest|mev|sandwich
             │
             ├─→ [2c] Verify TEE Attestation
             │        3-hash proof: compute_hash + storage_root + oracle_commit
             │
             └─→ [3] Call MeritCore.setMerit(agent, score)
                     │
    ┌────────────────▼────────────────────────────────┐
    │        MeritCore (0G Galileo)                   │
    │  Mapping: agent_address → merit_score (1e4)    │
    │  Events: MeritUpdated(agent, score, timestamp) │
    └────────┬──────────────────────────────┬────────┘
             │                              │
             ├─→ Storage Root Anchoring     ├─→ MeritVault Mirror
             │   (EvidenceRegistry)         │   (Base Sepolia)
             │   Label: proof-of-merit:     │
             │   merit-allocation-v1        │
             │                              │
    ┌────────▼───────────────────────────────▼──────┐
    │  DeFi Protocols Gate Access                  │
    │  require(merit > 0.5) → execute swap         │
    └──────────────────────────────────────────────┘
```

### Key Components

| Component | Chain | Role |
|-----------|-------|------|
| **MeritCore** | 0G Galileo (16602) | Primary merit ledger |
| **MeritVault** | Base Sepolia (84532) | Cross-chain mirror + liquidity pool |
| **EvidenceRegistry** | 0G Galileo (16602) | Anchors storage proofs + audit trail |
| **KeeperHub** | Off-chain (orchestrator) | Validates workflows, calls MeritCore |
| **AI Model (Gemma4)** | Ollama (local) | Sandwich attack classification |

---

## Contracts

### MeritCore (0G Galileo)

**Address:** [`0x19E3C17F58052Bb75D1c24bC1c56C2bfd1E5A906`](https://explorer.0g.ai/address/0x19E3C17F58052Bb75D1c24bC1c56C2bfd1E5A906)  
**Deployment Tx:** `0xd2e0c82e8182734ce95ff89965778dd3e44c4555142f484bf795820343875ed2`

**Key Functions:**
```solidity
function setMerit(address agent, uint16 score_1e4) external  // Set merit score (0–10000)
function getMerit(address agent) external view returns (uint16)  // Get current score
function batchSetMerit(address[] agents, uint16[] scores) external  // Bulk update
```

**Evidence Tx (batchSetMerit):** `0x132496633f457fecdabfe7faa8545b55975926a38e841f58d971e975d3348760`

### MeritVault (Base Sepolia)

**Address:** [`0x3ef2818dD26F4B2e73D8fAb65F6aEA6bc1A2F5E2`](https://sepolia.basescan.org/address/0x3ef2818dD26F4B2e73D8fAb65F6aEA6bc1A2F5E2)  
**Deployment Tx:** `0xea728adc08c3ed73b0809ef8c1425bd296927c1f3261f353735afe2d272b5577`

**Purpose:** Cross-chain score replication + liquidity tier gating

### EvidenceRegistry (0G Galileo)

**Address:** [`0x4DE88763BfcBd799376c4715c245F656D518e43B`](https://explorer.0g.ai/address/0x4DE88763BfcBd799376c4715c245F656D518e43B)  
**Deployment Tx:** `0x8e36b1f105f796d0cfbac78eb6dbcd82591ac941b3f51758f305a1606a01b6da`

**Purpose:** Anchors storage Merkle roots for attestation verification

**Storage Anchor (CP5):**
- **Storage Root:** `0x7efda42b6e92d9faa23964b2b8f954ba46defe0893ea200c524001cd998aa109`
- **Anchor Tx:** `0x5feb7bc4d3c7c0dbf64726f0cca751fda4735378fa80cf78af42316b8ef6394e`
- **Label:** `proof-of-merit:merit-allocation-v1`

---

## API Endpoints

### Health Check
```bash
GET /health
```
Returns service status.

### Get Agent Merit
```bash
GET /merit/{address}
```
Returns merit score for agent (0–10000 in 1e4 scale).

**Example:**
```bash
curl https://meriscore-api/merit/0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
# Response: { "agent": "0xf39...", "score_1e4": 2641, "merit": 0.2641 }
```

### Submit Attestation
```bash
GET /attestation
```
Returns current TEE attestation card (3-hash proof).

### KeeperHub Workflow
```bash
POST /kh/workflow
Content-Type: application/json

{
  "agent_address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
  "evidence": {
    "transactions": [...],
    "attestation_proof": "0x..."
  }
}
```

Returns workflow status and updated merit score.

### AI Analysis
```bash
POST /analyze
Content-Type: application/json

{
  "agent_address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
  "transactions": [...]
}
```

Returns AI classification: `honest | mev_searcher | sandwich_attacker`

---

## Sword Deep-Dives

### ✅ Sword #2: TEE Attestation Card
- Computes 3-hash proof via 0G Compute TeeML
- Combines: compute result hash + storage root + oracle commit
- Sealed in Trusted Execution Environment
- Prevents tampering with merit scores

**Evidence:** 
- Oracle Commit Tx: `0xd492f5714656eb1199c307c1c67902906a0f946a9113f697e25f05a8e4917b61`
- Commit Hash: `0x09d34df4fd5c9c75b9970e4fbe0820c2b982466532d5413e1ae3b75fe7a1b4c1`

### ✅ Sword #3: KeeperHub Workflow
- Implements 3-phase validation: CHECK → VALIDATE → EXECUTE
- CHECK: Request evidence from agent API
- VALIDATE: Verify attestation + score bounds
- EXECUTE: Update on-chain scores via MeritCore
- Fully deterministic and auditable

**Evidence:**
- Batch Merit Tx: `0x132496633f457fecdabfe7faa8545b55975926a38e841f58d971e975d3348760`

### ✅ Sword #4: AI Enrich (Sandwich Attack Detection)
- Runs Gemma4 26B model via Ollama
- Analyzes transaction patterns for sandwich attack signatures
- Classifies behavior: `honest / mev_searcher / sandwich_attacker`
- Alice scored 0.2641 due to sandwich pattern detection
- Bob scored 0.6703 with clean history

**Model:** Gemma4 26B parameter model  
**Detection:** Transaction timing analysis, MEV patterns, gas bidding behavior

### ✅ Sword #5: ZK Merit Proof (Privacy Tier)

**Agents can now prove they meet a merit threshold WITHOUT revealing their score.**

- **Circuit:** Poseidon hash + Merkle tree + threshold comparison (circom 2.2.3)
- **Proof System:** Groth16 (snarkjs 0.7.6) — ~1.5KB proof size, ~200ms verification
- **On-Chain Verifier:** Solidity smart contract auto-generated and ready for Base Sepolia
- **Use Case:** "I certify my score ≥ 5000" without disclosing actual score (e.g., 0.2641 or 0.6703)

**How it works:**
1. Agent generates witness: (agentAddr, agentScore, merklePath[], merkleRoot, threshold)
2. Circuit verifies:
   - agentScore hashes correctly to merkle tree leaf
   - Leaf is included in merkle tree (proof of membership)
   - agentScore ≥ threshold (cryptographic comparison)
3. Prover generates Groth16 proof
4. On-chain verifier contract validates proof (public inputs: merkleRoot, threshold)
5. DeFi protocols can gate access without seeing raw scores

**Artifacts:**
- Circuit: `circuits/merit_threshold.circom` (165 lines, 2470 constraints)
- R1CS: `circuits/merit_threshold.r1cs` (613K)
- WASM: `circuits/merit_threshold_js/merit_threshold.wasm` (1.7M)
- Verifier: `contracts/src/MeritVerifier.sol` (auto-generated, Groth16 Solidity)
- Prover: `scripts/prove_merit.py` (Python CLI, supports alice/bob/carol agents)
- UI: Streamlit tab with proof generation button + merkle root display

**Demo:**
```bash
# Bob (score=6703) proves merit ≥ 5000
python scripts/prove_merit.py --agent bob --threshold 5000
# Output: proof + publicSignals (merkleRoot, threshold)

# Alice (score=2641) fails to prove merit ≥ 5000 (expected)
python scripts/prove_merit.py --agent alice --threshold 5000
# Output: "Agent alice score 2641 < threshold 5000: proof cannot be generated"
```

**Privacy guarantee:** On-chain verifier only learns:
- merkleRoot (commitment to agent set)
- threshold (chosen by protocol)
- Proof is valid (cryptographic proof)

Agent's actual score remains **completely hidden**.

### ✅ Sword #6: Uniswap Merit-Gated Swap

**Merit-gated DEX execution: only agents with merit ≥ 0.5 can swap on Base Sepolia.**

High-merit agents unlock efficient DeFi access. This endpoint demonstrates how MeritScore integrates with real DeFi protocols to gate trades.

**Endpoint:**
```
POST /uniswap/swap
```

**Request:**
```json
{
  "action": "quote" | "execute",
  "address": "alice" | "bob" | "carol" | "0x...",
  "from_token": "0x4200000000000000000000000000000000000006",
  "to_token": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
  "amount_in": "1000000000000000",
  "slippage_pct": 2.0
}
```

**Response (on success, HTTP 200):**
```json
{
  "action": "quote",
  "amount_out": "159777",
  "fee_tier": 3000,
  "price_impact_pct": 0.5,
  "mode": "Direct"
}
```

**Merit Gate Behavior:**

| Agent | Merit Score | Behavior | Example Response |
|-------|:-----------:|----------|------------------|
| **Alice** (Sandwich Bot) | 0.2641 | ❌ **BLOCKED** | HTTP 403: `merit_below_threshold` |
| **Bob** (Honest Arbitrageur) | 0.6703 | ✅ **APPROVED** | HTTP 200: quote with amount_out |
| **Carol** (Unverified) | 0.0000 | ❌ **BLOCKED** | HTTP 403: `merit_below_threshold` |

**Live Demo Transaction on Base Sepolia (2026-04-29):**

| Step | Action | Tx Hash |
|------|--------|---------|
| 1 | Wrap 0.0005 ETH → WETH | [`0x7ef399...e2662f`](https://sepolia.basescan.org/tx/0x7ef399b80e4e893827e994c83c1d947ec1a34251b8aa009c5569788f04e2662f) |
| 2 | Approve WETH → SwapRouter02 | [`0x6b46ca...500eec`](https://sepolia.basescan.org/tx/0x6b46cad0cefd29402e265dbb657677641e4a3c64c79ae4b136b594227c500eec) |
| 3 | **Swap 0.0001 WETH → 0.015978 USDC** ⭐ | [**`0x0c7c4e...cdcf897`**](https://sepolia.basescan.org/tx/0x0c7c4ed5142950e771c4ac99178764a512bbc5a12f18513b3672b57d7cdcf897) |

- Quote pre-trade (QuoterV2): 1e15 wei WETH → 159,777 USDC wei
- Live execute (SwapRouter02 exactInputSingle): 1e14 wei WETH → **15,978 USDC wei** received
- Fee tier: 3000 bps (0.3%)
- Sender: `0x0bb64a3ec3B1c3Fc818A384D580Cc7E61f4c352E` (Bob signer, merit 0.6703 ≥ 0.5 ✓)
- Slippage: actual price impact ~0.5%, generous min-out enforced

**Integration Notes:**
- Threshold: 0.5 (half of max merit 1.0)
- Tokens: WETH (0x4200...) ↔ USDC (0x036C...) on Base Sepolia
- Router: Uniswap V3 SwapRouter02 (0x94cC...)
- Mode: Live quotes via QuoterV2 + live execution on SwapRouter02 (verified on-chain)

---

### ⏳ Future Work: Recovery Path *(post-hackathon)*
- Agent appeal mechanism
- Score dispute resolution
- Graduated restoration for reformed actors
- Planned for post-hackathon release

---

## Development Timeline

**Hackathon:** EthGlobal OpenAgents, 2026-04-25 to 2026-05-04

### Pre-Hackathon Spike Research (2026-04-22 to 2026-04-24)

**Apr 22–24:** Spike testing (design only, no product code)
- S1: 0G Compute TeeML — partial, ledger account funding needed
- S2: 0G Storage SDK — testnet intermittent, decided MOCK_MODE fallback
- S3: 0G Galileo deploy mechanics — `--legacy` flag required (EIP-1559 unsupported)
- S4: KeeperHub API — endpoint revealed at kickoff

### Hackathon Phase (2026-04-25 onward)

**Apr 25 01:00 KST:** Hacking begins — EthGlobal OpenAgents kickoff

**Apr 25 D1:** Core build
- Contracts: MeritCore (0G Galileo) + MeritVault + EvidenceRegistry (Base Sepolia)
- BFF: 5 FastAPI endpoints
- Sword #2: TEE Attestation Card
- Sword #3: KH 4-Step Workflow (CHECK → VALIDATE → ZK_VERIFY → EXECUTE w/ `intentionally_simulated` honest fallback)
- Sword #4: AI Sandwich Detection (Gemma4 26B)

**Deployed Contracts:**
- **MeritCore (0G Galileo 16602):** `0x19E3C17F58052Bb75D1c24bC1c56C2bfd1E5A906`
- **MeritVault (Base Sepolia 84532):** `0x3ef2818dD26F4B2e73D8fAb65F6aEA6bc1A2F5E2`
- **EvidenceRegistry (0G Galileo 16602):** `0x4DE88763BfcBd799376c4715c245F656D518e43B`

**Checkpoint Evidence:**
- **CP4 (Oracle):** MeritCore loaded with Alice/Bob/Carol scores via `batchSetMerit`
  - Alice: 2641 (sandwich attack detected)
  - Bob: 6703 (honest arbitrage)
  - Carol: 0 (no evidence)
- **CP5 (Evidence):** Storage root anchored to EvidenceRegistry
  - Root: `0x7efda42b6e92d9faa23964b2b8f954ba46defe0893ea200c524001cd998aa109`
  - Anchor Tx: `0x5feb7bc4d3c7c0dbf64726f0cca751fda4735378fa80cf78af42316b8ef6394e`

---

## Economics: MeritScore as a Credit Platform

### Pricing Model

| Tier | Query Limit | Price | Use Case |
|------|------------|-------|----------|
| **Free** | 10/day | $0 | Agents testing MeritScore |
| **Standard** | 10,000/month | $0.10/query (avg) | Small-medium agents, DeFi protocols |
| **Enterprise** | Unlimited | Custom | Large MEV searchers, CEX integrations |

**Revenue per Agent (annualized):**
- Small agent (10 queries/day): ~$365/year
- Medium agent (100 queries/day): ~$3,650/year
- Large agent (1,000 queries/day): ~$36,500/year

### Key Metrics

| Metric | Target | Timeline |
|--------|--------|----------|
| Agents Indexed | 1,000+ | 6 months |
| Daily Queries | 100K+ | 6 months |
| Supported Chains | 5+ (0G, Base, Arbitrum, Optimism, Ethereum) | 12 months |

### Competitive Advantage

1. **First Mover in Agent Credit:** Only on-chain credit system purpose-built for autonomous agents
2. **Multi-Chain Reach:** 0G Galileo + Base Sepolia + future expansion
3. **AI-Powered Detection:** Gemma4 sandwich attack classification (not just heuristics)
4. **TEE-Sealed Attestation:** Cryptographic proof of integrity (0G Compute TeeML)
5. **Deterministic Workflows:** KeeperHub integration for automated agent vetting

### Revenue Streams

1. **Merit Score Queries** (Primary, ~70% of revenue)
   - Per-query pricing: $0.10 (standard tier)
   - High volume for DeFi protocols, exchanges, agents

2. **Protocol Licensing** (Secondary, ~20% of revenue)
   - Custom merit formula integration
   - White-label credit scoring
   - Premium support

3. **Data Services** (Tertiary, ~10% of revenue)
   - Agent behavior analytics (anonymized)
   - MEV pattern intelligence
   - Agent reputation leaderboards

### Unit Economics

**Gross Margin per Query:**
- Price: $0.10
- Infrastructure Cost: $0.02 (RPC, compute, storage)
- Gross Margin: 80%

**Customer Acquisition Cost (CAC):**
- Hackathon launch: $0 (organic)
- Community-driven growth: Low CAC via EthGlobal network
- Target CAC payback: <6 months

---

## Built With

### Primary Sponsors (EthGlobal OpenAgents Hackathon)

- **[0G Network](https://0g.ai/)** — Modular AI execution + storage
  - 0G Galileo (EVM testnet, ChainId 16602)
  - 0G Compute (TeeML attestation)
  - 0G Storage (Evidence anchoring)
  
- **[KeeperHub](https://keeperhub.io/)** — Workflow orchestration for autonomous agents
  - KeeperHub API for CHECK→VALIDATE→EXECUTE workflows
  - Deterministic workflow validation

### Tech Stack

- **Contracts:** Solidity 0.8.20, Foundry (forge)
- **AI Model:** Gemma4 26B via Ollama (sandwich attack detection)
- **Backend:** Python (merit_scorer), Streamlit (UI)
- **Oracle Relay:** TypeScript (0G oracle commit)
- **On-Chain Data:** EVM chains (0G Galileo + Base Sepolia)

### Tools

- Foundry (`forge build`, `forge test`, `forge deploy`)
- pnpm (script orchestration)
- pytest (Python test suite)
- Ruff (Python linting)

---

## License

MIT License. See [LICENSE](./LICENSE) file for details.

---

## Honest Mode Badges

Agents can self-declare their mode of operation:

- **Direct**: Agent calls MeritCore directly (no intermediaries)
- **Workflow**: Agent uses KeeperHub workflow (CHECK→VALIDATE→ZK_VERIFY→EXECUTE)
- **Web3**: Agent interacts via Web3 provider (ethers.js / web3.py)

---

## Contact & Community

- **GitHub:** [WooYoungSang/meritscore](https://github.com/WooYoungSang/meritscore)
- **Twitter:** [@MeritScore](https://twitter.com/meritscore)
- **Discord:** Join EthGlobal OpenAgents community

---

## AI Tool Disclosure

This project was built with AI assistance, in compliance with EthGlobal's AI tool policy.

- **Tools used:** Claude Code (Anthropic) — Sonnet 4.6 and Opus 4.7 models
- **Scope of AI assistance:**
  - Code generation (Python, Solidity, TypeScript, JSX) under TDD discipline
  - Multi-agent orchestration (planner / executor / verifier / rules-guardian)
  - Test scaffolding and mock harnesses
  - Documentation drafting (README sections, docstrings, commit messages)
- **Human-directed scope:**
  - All architectural decisions, prize-track selection, and product framing
  - All on-chain transactions (wallet signing, contract deployments, live swaps)
  - All prompts, agent briefs, kill-switch decisions, and final commits
  - All rule-compliance reviews via the `rules-guardian` independent auditor
- **Verification:** Every AI-generated change passed `pytest`, `ruff`, and an independent
  `rules-guardian` preflight before commit. Live on-chain transactions
  (e.g., Sword #6 swap [`0x0c7c4e...cdcf897`](https://sepolia.basescan.org/tx/0x0c7c4ed5142950e771c4ac99178764a512bbc5a12f18513b3672b57d7cdcf897))
  were executed and verified by the human submitter.

---

**Built with ❤️ during EthGlobal OpenAgents Hackathon**  
*2026-04-25 — 2026-05-04*
