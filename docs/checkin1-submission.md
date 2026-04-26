# Check-in #1 Submission — MeritScore

**Deadline**: 2026-04-28 12:59 KST  
**EthGlobal**: OpenAgents 2026

---

## Project Name
**MeritScore** — Experian for AI Agents

## One-Line Description
On-chain merit scoring system that evaluates AI agent trustworthiness via ZK proofs, TEE attestation, and sandwich attack detection.

## Live Demo
- **URL**: https://meritscore.warvis.org
- **API**: https://meritscore.warvis.org/health

## What We Built (D+1 to D+3)

### 5 Swords — All Complete ✅

| # | Feature | Status | Sponsor |
|:-:|---------|:------:|---------|
| 1 | Live Evaluation Button — real-time merit score | ✅ | 0G |
| 2 | TEE Attestation Card — 0G Compute TeeML | ✅ | 0G |
| 3 | KeeperHub 3-Step Workflow (CHECK→VALIDATE→EXECUTE) | ✅ | KeeperHub |
| 4 | AI Sandwich Detection — Gemma4 26B via Ollama | ✅ | 0G |
| 5 | ZK Merit Proof — Groth16 circom circuit | ✅ | — |

### Deployed Contracts

| Contract | Chain | Address |
|----------|-------|---------|
| MeritCore | 0G Galileo (16602) | `0x19E3C17F58052Bb75D1c24bC1c56C2bfd1E5A906` |
| MeritVault | Base Sepolia (84532) | `0x3ef2818dD26F4B2e73D8fAb65F6aEA6bc1A2F5E2` |
| EvidenceRegistry | 0G Galileo (16602) | `0x4DE88763BfcBd799376c4715c245F656D518e43B` |
| AgentLendingPool | Base Sepolia (84532) | `0x78E33F871f210E898cd875e259ce24BD61074e34` |

### BFF API Endpoints (Live)

```
GET  /health          → chain connectivity (galileo + base)
GET  /merit/{address} → merit score (0G TeeML inference)
GET  /attestation     → TEE attestation card
POST /kh/workflow     → KeeperHub CHECK→VALIDATE→EXECUTE
POST /analyze         → AI sandwich detection
POST /zk/prove        → ZK merit proof generation
```

## Sponsor Integrations

### 0G Network
- **MeritCore** contract deployed on 0G Galileo for on-chain merit storage
- **0G Compute TeeML** — real inference via `inference-v1.0` service
- **EvidenceRegistry** — Merkle-anchored evidence storage on 0G Storage
- Wallet: `0x0bb64a3ec3B1c3Fc818A384D580Cc7E61f4c352E`

### KeeperHub
- 3-step workflow: CHECK (0G merit) → VALIDATE (Base Sepolia) → EXECUTE (KH webhook)
- Workflow ID: `tvuif5erkbfo9pmf5e8uz`
- Live: `POST /kh/workflow` returns `{"execute": "OK"}`
- Auth: `wfb_` webhook bearer token via `/api/workflows/{id}/webhook`

### Base (Coinbase)
- MeritVault deployed on Base Sepolia for cross-chain attestation
- AgentLendingPool — composability demo (merit-gated lending)

## Tech Stack
- **Contracts**: Solidity + Foundry (0G Galileo + Base Sepolia)
- **Backend**: FastAPI (Python) — dockerized, port 61234
- **AI**: Gemma4 26B via Ollama (sandwich detection)
- **ZK**: circom + snarkjs (Groth16 proof)
- **Infra**: Docker Compose, meritscore.warvis.org

## Key Learnings

1. **0G Galileo requires `--legacy` flag** for all forge/cast commands (EIP-1559 not supported)
2. **0G Compute service name**: must be `"inference-v1.0"` (not `"inference"`)
3. **KeeperHub webhook**: `POST /api/workflows/{id}/webhook` with `wfb_` bearer key (not `kh_` API key)

## What's Next (D+3 to D+7)

- [ ] Demo video recording (3 min)
- [ ] KeeperHub feedback bounty submission
- [ ] 0G ESP Grant application (D+7)
- [ ] Social amplification (Twitter/Farcaster thread)
- [ ] Final submission polish
