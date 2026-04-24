# MOCK_MODE=false Transition Plan (CP5/CP7 Path)

**Date**: 2026-04-25  
**Status**: ✅ BLOCKED (awaiting OG_PRIVATE_KEY)  
**Risk Level**: MEDIUM (requires external API key setup)

## Current State

### Infrastructure Ready ✅
- **a0g SDK**: Installed (python-0g 0.6.1.2, 0g-storage-sdk 0.3.0)
- **EvidenceRegistry**: Deployed at 0x4DE88763BfcBd799376c4715c245F656D518e43B (0G Galileo)
- **attestation.py**: Full MOCK_MODE=false support implemented
- **Chain RPC**: Configured (0G Galileo: https://evmrpc-testnet.0g.ai)

### Code Paths Ready ✅
```python
# attestation.py lines 136-149
if MOCK_MODE:
    # Fallback: Generated hashes (backward compat)
    mode = "Workflow"
else:
    # Production: 0G Compute + EvidenceRegistry
    compute_hash, compute_ok = await _get_compute_hash_from_0g()
    storage_root = await get_storage_root(RPC_GALILEO)
    mode = "Workflow" if compute_ok else "Direct"
```

### Critical Blocker ❌
**OG_PRIVATE_KEY not set** — Required for:
1. A0G client initialization (signing 0G transactions)
2. Service discovery on 0G Compute network
3. TeeML model invocation (deepseek-chat-v3-0324)

## Transition Steps (When Key Available)

### Step 1: Add OG_PRIVATE_KEY to Environment
```bash
export OG_PRIVATE_KEY="0x..."  # Wallet private key with 0G testnet funds
```

### Step 2: Update docker-compose.yml
```yaml
environment:
  MOCK_MODE: ${MOCK_MODE:-false}  # Switch from true → false
  OG_PRIVATE_KEY: ${OG_PRIVATE_KEY}
  RPC_GALILEO: https://evmrpc-testnet.0g.ai
```

### Step 3: Validate Service Discovery
```bash
curl -s http://localhost:61234/attestation | jq .
# Expected: {mode: "Workflow", compute_hash: "0x...", storage_root: "0x..."}
```

### Step 4: Test Full CP5→CP7 Chain
```
/attestation (Sword #2) ← TeeML response
  ↓
/kh/workflow (Sword #3) ← KeeperHub validates attestation
  ↓
MeritCore.setMerit() (Sword #4)
  ↓
EvidenceRegistry anchor
```

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| 0G Galileo RPC timeout | MEDIUM | Exponential backoff already in place |
| TeeML service unavailable | LOW | Fallback to mock hash (backward compat) |
| Invalid private key | HIGH | Requires manual validation after setup |
| Account underfunded | MEDIUM | 0G testnet faucet required |

## Expected Outcome (CP5)

When MOCK_MODE=false + OG_PRIVATE_KEY is set:
- `/attestation` endpoint returns live 0G Compute hash
- EvidenceRegistry.latest() returns on-chain storage root
- Mode switches from "Direct" to "Workflow"
- KeeperHub can validate full attestation chain

## Expected Outcome (CP7)

Full demo flow:
1. Agent calls `/kh/workflow`
2. KeeperHub fetches attestation from `/attestation`
3. Validates TeeML hash + storage root
4. Calls `MeritCore.setMerit()` with live score
5. EvidenceRegistry records proof-of-merit

## Next Actions

1. **KeeperHub Integration Owner**: Provide OG_PRIVATE_KEY or setup procedure
2. **DevOps**: Configure wallet funding on 0G testnet (testnet faucet)
3. **QA**: Create integration test for MOCK_MODE=false path
4. **Deployment**: Coordinate MOCK_MODE switch during hackathon final push

---

## Code References

- **attestation.py**: `_get_compute_hash_from_0g()` (lines 35–110)
- **workflow.py**: KeeperHub validation loop (lines 50–100)
- **chain.py**: EvidenceRegistry RPC calls (lines 20–60)
- **docker-compose.yml**: Environment variable defaults (line 15)
