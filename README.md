# MeritScore

> Experian for AI agents — on-chain credit scores that gate DeFi access across 0G + Base.

> **Built during EthGlobal OpenAgents hackathon — 2026-04-25T01:00+09:00**

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

### Four Sword Architecture

**Sword #2: TEE Attestation Card**
- Computes a 3-hash proof: `compute_hash(inference result) + storage_root(evidence) + oracle_commit(scores)`
- Attestation sealed in Trusted Execution Environment via 0G Compute
- Storage root anchored to EvidenceRegistry on-chain

**Sword #3: KeeperHub Workflow**
- CHECK: Request agent evidence from API
- VALIDATE: Verify attestation + score bounds
- EXECUTE: Update on-chain merit scores if valid

**Sword #4: AI Enrich**
- Runs Gemma4 26B via Ollama for sandwich attack detection
- Classifies agent behavior: `honest / mev_searcher / sandwich_attacker`
- Feeds classification to merit oracle

**Sword #1: Recovery Path** *(in progress)*
- Appeals / score dispute mechanism
- Planned for future iterations

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

## 4 Sword Features

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

### ⏳ Sword #1: Recovery Path *(future iteration)*
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
- Sword #3: KH 3-Step Workflow (CHECK → VALIDATE → EXECUTE)
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
- **Workflow**: Agent uses KeeperHub workflow (CHECK→VALIDATE→EXECUTE)
- **Web3**: Agent interacts via Web3 provider (ethers.js / web3.py)

---

## Contact & Community

- **GitHub:** [WooYoungSang/meritscore](https://github.com/WooYoungSang/meritscore)
- **Twitter:** [@MeritScore](https://twitter.com/meritscore)
- **Discord:** Join EthGlobal OpenAgents community

---

**Built with ❤️ during EthGlobal OpenAgents Hackathon**  
*2026-04-25 — 2026-05-04*
