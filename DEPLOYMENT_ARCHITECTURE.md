# Deployment Architecture — MeritScore

**Current Status**: ✅ LIVE (Docker, 6h uptime)  
**URL**: https://meritscore.warvis.org:61234 (via Docker)

## Container Topology

```
┌─────────────────────────────────────────────────────────┐
│  Docker Network: meritscore-net (10.99.0.0/24)         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  meritscore Service (warvis-hackerton-meritscore) │  │
│  │  Image: Python 3.10 + FastAPI + Streamlit         │  │
│  │  Port:  61234 → 61234 (tcp)                       │  │
│  │  Status: Up 6 hours, restart: unless-stopped     │  │
│  │  Memory: 512MB allocated                          │  │
│  ├──────────────────────────────────────────────────┤  │
│  │  Environment:                                     │  │
│  │  - MOCK_MODE=true (default)                       │  │
│  │  - RPC_GALILEO=https://evmrpc-testnet.0g.ai     │  │
│  │  - RPC_BASE_SEPOLIA=https://sepolia.base.org    │  │
│  │  - ORACLE_COMMIT_HASH=0x09d34df4...             │  │
│  └──────────────────────────────────────────────────┘  │
│           │                                             │
│           ├─→ Chain RPC: 0G Galileo (16602)           │
│           ├─→ Chain RPC: Base Sepolia (84532)         │
│           └─→ KeeperHub Workflow (PENDING KEY)        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Service Stack

| Layer | Component | Status | Details |
|-------|-----------|--------|---------|
| **API** | FastAPI (python/bff/main.py) | ✅ | 4 endpoints: `/health`, `/merit/{addr}`, `/attestation`, `/kh/workflow`, `/analyze` |
| **UI** | React SPA (python/ui/) | ✅ | Wallet input field, merit display, AI analysis card |
| **Attestation** | 0G Compute TeeML | ⏳ | MOCK_MODE=true (direct), MOCK_MODE=false (0G Compute) |
| **Workflow** | KeeperHub Validator | ⏳ | Exponential backoff, probe strategy, fallback chain |
| **Compute** | Ollama (Gemma4 26B) | ✅ | Sandwich attack detection |
| **Chain** | 0G Galileo + Base Sepolia | ✅ | MeritCore + MeritVault + EvidenceRegistry deployed |

## Health Check Endpoints

```bash
# Service health (all RPC endpoints up)
curl http://localhost:61234/health
# Expected: {"status":"ok","chain":{"galileo":true,"base":true}}

# Merit lookup (3 test agents)
curl http://localhost:61234/merit/alice    # Alice (MEV, score 0.2641)
curl http://localhost:61234/merit/bob      # Bob (Honest, score 0.6703)
curl http://localhost:61234/merit/0x0bb64a3ec3B1c3Fc818A384D580Cc7E61f4c352E

# Attestation card
curl http://localhost:61234/attestation
# Expected: {compute_hash, storage_root, oracle_commit, mode: "Direct"}

# AI Analysis
curl -X POST http://localhost:61234/analyze \
  -H "Content-Type: application/json" \
  -d '{"address":"0x..."}'
```

## Persistence & Data

- **Contracts**: Immutable on-chain (0G Galileo + Base Sepolia)
- **Merit Scores**: On-chain via MeritCore.setMerit() (requires KeeperHub workflow)
- **Evidence**: EvidenceRegistry anchors Merkle roots
- **Mock Data**: In-memory (Alice/Bob/Carol hardcoded for demo)

## Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Container startup | <3s | Fast Python startup |
| /health response | <100ms | RPC health check |
| /merit lookup | <200ms | 3-agent mock lookup |
| /analyze (AI) | 2–5s | Ollama inference time |
| Test suite | 23/23 PASS | 50s runtime |

## Scaling Considerations

**Current**: Single container, monolithic FastAPI + React SPA  
**Future**: 
- Separate API + UI containers
- Redis cache layer (merit scores)
- Message queue for async KeeperHub workflows
- Load balancer if serving multiple chains

## Teardown

```bash
# Full cleanup
docker-compose down --volumes
rm -rf cache/ out/

# Preserve deployments
git status  # All contract artifacts in deployments/addresses.json
```
