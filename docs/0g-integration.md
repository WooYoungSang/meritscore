# 0G Integration Guide: MeritScore as Autonomous Agent Framework

**Prize Track:** 0G Partner Prize — "Best Autonomous Agent / Agent Framework"

---

## Prize Requirements Mapping

The EthGlobal OpenAgents 2026 0G prize requires:

1. **Autonomous agent system** — looping behavior without human intervention
2. **Working example** — live demo with real transactions
3. **README + setup instructions** — documented integration path
4. **Live demo** — accessible URL with live functionality

**MeritScore qualifies via MeritGuard, an autonomous agent loop that:**

- Monitors on-chain merit scores every 30 seconds
- Detects low-merit agents attempting DeFi access
- Auto-triggers KeeperHub workflow validation
- Posts evidence to 0G Storage (EvidenceRegistry)
- Updates merit scores on-chain (MeritCore)
- Runs without human intervention — fully autonomous

---

## How MeritScore Qualifies

### The Problem It Solves

Autonomous agents are entering DeFi at scale — arbitrage bots, MEV searchers, sandwich attackers — but blockchains lack credit infrastructure to distinguish good actors from malicious ones. MeritScore solves this with **on-chain agent credit scoring**.

### The MeritGuard Autonomous Loop

```python
# File: python/bff/agent_loop.py
async def merit_guard_loop():
    """Autonomous loop that monitors and validates agents without human intervention."""
    while True:
        # 1. Scan all monitored agents
        for agent_address in MONITORED_AGENTS:
            score = await get_merit(agent_address, RPC_GALILEO)
            
            # 2. Detect low-merit agents
            if score < MERIT_THRESHOLD:
                # 3. Auto-trigger KeeperHub workflow
                evidence = await check_and_validate_merit(agent_address, threshold=5000)
                
                # 4. Post evidence to 0G Storage
                await anchor_evidence_to_registry(evidence)
                
                # 5. Update merit score on-chain
                await set_merit(agent_address, new_score)
        
        # Loop every 30 seconds — no human needed
        await asyncio.sleep(30)
```

**Verification:** `/agent-loop/status` endpoint returns current loop state with agents checked, actions taken.

---

## 0G Integration Surface

MeritScore integrates with three 0G products for autonomous agent monitoring:

| Component | Product | Role | Contract/Endpoint |
|-----------|---------|------|-------------------|
| **TeeML Inference** | 0G Compute | TEE-attested merit scoring | `/attestation` (python/bff/attestation.py:47–115) |
| **Evidence Anchoring** | 0G Storage | Immutable audit trail via EvidenceRegistry | Contract: `0x4DE88763...` (Galileo 16602) |
| **Merit Ledger** | 0G Galileo (EVM) | On-chain score mapping for agents | Contract: `0x19E3C17F...` (Galileo 16602) |

### 1. 0G Compute TeeML Attestation (Sword #2)

**File:** `python/bff/attestation.py` (lines 47–115)

Real call flow:
```python
def _invoke_0g_compute() -> tuple[str, bool]:
    """Invoke TeeML chatbot via 0G Compute SDK."""
    client = A0G(private_key=OG_PRIVATE_KEY, network="testnet")
    services = client.get_all_services()
    tee_provider = next(s for s in services if s.verifiability == "TeeML")
    
    oai = client.get_openai_client(tee_provider.provider)
    resp = oai.chat.completions.create(
        model=tee_provider.model,
        messages=[{"role": "user", "content": "Attest this merit score..."}],
        max_tokens=32,
    )
    compute_hash = "0x" + hashlib.sha256(resp.choices[0].message.content.encode()).hexdigest()
    return compute_hash, True  # success
```

**Live Proof Checklist:**

```bash
# 1. Check attestation endpoint (returns compute_hash from real or mock TeeML)
curl -s https://meritscore.warvis.org/attestation | jq .

# Expected response:
# {
#   "compute_hash": "0x...",      # TeeML inference hash
#   "storage_root": "0x7efda42...",  # From EvidenceRegistry.latest()
#   "oracle_commit": "0x09d34df4...", # Commit hash
#   "mode": "Workflow",             # "Workflow" if real, "Direct" if mock
#   "compute_ok": true|false,       # 0G Compute SDK reachable
#   "provider": "0g-compute"        # which provider was used
# }

# 2. Verify EvidenceRegistry on 0G Galileo
cast call 0x4DE88763BfcBd799376c4715c245F656D518e43B "latest()" \
  --rpc-url https://evmrpc-testnet.0g.ai --legacy

# Expected output:
# 0x7efda42b6e92d9faa23964b2b8f954ba46defe0893ea200c524001cd998aa109  (rootHash)
# proof-of-merit:merit-allocation-v1                                     (label)
# 1234567                                                                 (anchoredAt)
```

### 2. 0G Storage Evidence Registry (on Galileo)

**Contract:** `0x4DE88763BfcBd799376c4715c245F656D518e43B` (Galileo 16602)  
**Solidity:** `contracts/src/EvidenceRegistry.sol` (lines 1–42)

Evidence anchoring is immutable and queryable on-chain:

```solidity
contract EvidenceRegistry {
    struct Evidence {
        bytes32 rootHash;      // Merkle root of off-chain evidence
        string label;          // "proof-of-merit:merit-allocation-v1"
        uint256 anchoredAt;    // Block number
    }
    
    function latest() external view returns (bytes32, string memory, uint256)
    function anchor(bytes32 rootHash, string calldata label) external returns (uint256 id)
}
```

**Live Proof Checklist:**

```bash
# 3. Count evidence entries anchored
cast call 0x4DE88763BfcBd799376c4715c245F656D518e43B "count()" \
  --rpc-url https://evmrpc-testnet.0g.ai --legacy

# Expected: 1 or more evidence anchors exist

# 4. Read specific evidence entry (index 0)
cast call 0x4DE88763BfcBd799376c4715c245F656D518e43B "entries(uint256)" 0 \
  --rpc-url https://evmrpc-testnet.0g.ai --legacy
```

### 3. 0G Galileo MeritCore (Merit Ledger)

**Contract:** `0x19E3C17F58052Bb75D1c24bC1c56C2bfd1E5A906` (Galileo 16602)  
**Solidity:** `contracts/src/MeritCore.sol`

Merit scores are stored per-agent on Galileo and indexed by MeritGuard loop:

```solidity
contract MeritCore {
    mapping(address => uint16) public scores;  // 1e4 scale (0–10000)
    
    function getMerit(address agent) external view returns (uint16)
    function setMerit(address agent, uint16 score_1e4) external
    function batchSetMerit(address[] agents, uint16[] scores) external
}
```

**Live Proof Checklist:**

```bash
# 5. Query Bob's merit (honest arbitrageur, expected 0.6703)
curl -s https://meritscore.warvis.org/merit/bob | jq .

# Expected response:
# {
#   "address": "0xb0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0",
#   "score": 0.6703,
#   "score_1e4": 6703,
#   "exists": true,
#   "mode": "Workflow"
# }

# 6. Query Alice's merit (sandwich bot, expected 0.2641)
curl -s https://meritscore.warvis.org/merit/alice | jq .

# 7. Query Carol (unverified, expected 0.0)
curl -s https://meritscore.warvis.org/merit/carol | jq .

# 8. Read from MeritCore contract directly
cast call 0x19E3C17F58052Bb75D1c24bC1c56C2bfd1E5A906 \
  "getMerit(address)" 0xb0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0 \
  --rpc-url https://evmrpc-testnet.0g.ai --legacy

# Expected: 6703 (in 1e4 scale)
```

---

## Autonomous Loop Evidence

**Endpoint:** `GET /agent-loop/status`

The MeritGuard autonomous agent publishes its loop state every 30 seconds:

```bash
# 9. Check MeritGuard loop status
curl -s https://meritscore.warvis.org/agent-loop/status | jq .

# Expected response:
# {
#   "running": true,
#   "last_scan": "2026-04-30T12:34:56.789Z",
#   "scan_interval_seconds": 30,
#   "agents_checked": 3,
#   "flagged": ["0xca401..."],  # Carol (unverified)
#   "actions": [
#     {"agent": "0xca401...", "action": "validate", "timestamp": "..."}
#   ]
# }
```

---

## Setup & Deployment

### Prerequisites

```bash
# 0G Compute SDK
pip install a0g-sdk

# 0G Galileo credentials
export OG_PRIVATE_KEY="0x..."  # funded account on Galileo testnet
export RPC_GALILEO="https://evmrpc-testnet.0g.ai"

# Note: All forge/cast commands require --legacy flag (EIP-1559 not supported)
```

### Build & Test

```bash
# Build contracts
cd /home/jang/Workspace/warvis-hackerton
forge build

# Deploy to Galileo (with --legacy)
forge create contracts/src/MeritCore.sol:MeritCore \
  --rpc-url https://evmrpc-testnet.0g.ai \
  --private-key $OG_PRIVATE_KEY \
  --legacy

# Run BFF service
cd python
uvicorn bff.main:app --host 0.0.0.0 --port 8000
```

### Live Demo URL

**https://meritscore.warvis.org** (Docker, port 61234)

- Click "Sword #1: Live Evaluation" → enter agent address
- Tab "Sword #2: TEE Attestation" → see real/mock TeeML output
- Tab "Sword #3: KH Workflow" → trigger autonomous validation
- Tab "Sword #4: AI Analysis" → sandwich detection results

---

## Why This Wins the 0G Prize

1. **Autonomous Loop** — MeritGuard continuously monitors agents without human intervention
2. **0G Stack Integration** — uses all three 0G products (Compute TeeML, Storage, Galileo EVM)
3. **Working Demo** — live tx evidence on Galileo + live API
4. **Proof of Work** — contract addresses, endpoint tests, curl examples all verifiable

| Requirement | Evidence |
|-------------|----------|
| **Autonomous agent** | MeritGuard loop (python/bff/agent_loop.py) |
| **Working example** | Live demo at meritscore.warvis.org |
| **README + setup** | This doc + /home/jang/Workspace/warvis-hackerton/README.md |
| **Live demo** | https://meritscore.warvis.org (port 61234) |

---

## References

- **README:** `/home/jang/Workspace/warvis-hackerton/README.md` (Architecture section, lines 182–222)
- **Attestation Code:** `python/bff/attestation.py` (lines 47–115, 126–190)
- **Agent Loop:** `python/bff/agent_loop.py`
- **EvidenceRegistry Contract:** `contracts/src/EvidenceRegistry.sol` (lines 1–42)
- **MeritCore Contract:** `contracts/src/MeritCore.sol`
- **Live API:** `python/bff/main.py` (lines 173–194, endpoint `/attestation`)

---

**Built during EthGlobal OpenAgents Hackathon 2026-04-25 to 2026-05-04**
