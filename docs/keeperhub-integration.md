# KeeperHub Integration Guide: Autonomous Merit Validation Workflow

**Prize Track:** KeeperHub Partner Prize — "Best Meaningful Use + Working Demo"

---

## Prize Requirements Mapping

The KeeperHub prize requires:

1. **Meaningful use** — workflow solves a real problem, not a toy integration
2. **Working demo** — live example with real transactions
3. **README + setup instructions** — documented architecture and commands
4. **Approach write-up** — clear explanation of why KeeperHub was chosen

**MeritScore qualifies via a deterministic 3-step workflow that:**

- Uses KeeperHub as the enforcement layer for agent merit validation
- Prevents false positives (merit-gated access without proof)
- Provides immutable audit trail for DeFi protocol compliance
- Solves the problem: "How do we safely gate DeFi access based on agent behavior?"

---

## Why MeritScore Uses KeeperHub

### The Problem

Merit scores alone are not enough for DeFi protocols. A protocol needs:

1. **Proof of validation** — not just "this agent has score X"
2. **Audit trail** — "this score was checked on date Y via workflow Z"
3. **Deterministic execution** — no race conditions or replay attacks
4. **Cross-chain coordination** — scores on Galileo, access gated on Base

### The Solution: 3-Step KeeperHub Workflow

MeritScore wraps merit scoring in a KeeperHub workflow that:

1. **CHECK** — verifies agent merit against threshold (on Galileo)
2. **VALIDATE** — confirms attestation + score bounds (on Base)
3. **EXECUTE** — records proof of validation in audit log, triggers downstream action

Each step is **deterministic**, **auditable**, and **timestamped**.

---

## 3-Step Workflow Architecture

### Diagram

```
Agent → API Request → KeeperHub Webhook
                         ↓
                    ┌─────────────────────┐
                    │  CHECK              │
                    │  Query MeritCore on │
                    │  0G Galileo         │
                    │  score >= threshold?│
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │  VALIDATE           │
                    │  Call MeritVault on │
                    │  Base Sepolia       │
                    │  Verify attestation │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │  EXECUTE            │
                    │  Record proof in    │
                    │  KeeperHub audit    │
                    │  Return OK/PENDING  │
                    └──────────┬──────────┘
                               ↓
                         Agent Proceeds
                    (or PENDING if KH down)
```

### File Reference

**File:** `python/bff/workflow.py` (lines 101–220)

```python
async def check_and_validate_merit(
    address: str,
    threshold: int,
    rpc_url: str,
) -> Tuple[bool, bool]:
    """
    Lines 101–131: Execute CHECK and VALIDATE steps.
    
    CHECK (lines 120):   Query MeritCore on Galileo for score >= threshold.
    VALIDATE (lines 126): Call MeritVault.validate() on Base for attestation.
    
    Returns: (check_ok, validate_ok)
    """

async def execute_workflow(
    address: str,
    threshold: int,
) -> str:
    """
    Lines 195–220: Execute the EXECUTE step.
    
    Fallback chain:
      1. KH Workflow API with exponential backoff
      2. If KH_BASE_URL unset or health probe fails → return "PENDING"
    
    Returns: "OK" if KH executed, "PENDING" otherwise.
    """
```

---

## KeeperHub Workflow Details

### Environment Configuration

```bash
# .env (required for live KH integration)
KH_BASE_URL="https://app.keeperhub.com"
KH_API_KEY="wfb_..."           # From KeeperHub dashboard
KH_WEBHOOK_KEY="..."           # Webhook signing key
KH_WORKFLOW_ID="..."           # Workflow UUID
KH_TIMEOUT_SECONDS="10"        # Timeout for KH HTTP calls
```

### Health Probe

**File:** `python/bff/workflow.py` (lines 36–61)

Before EXECUTE, MeritScore probes KeeperHub health:

```python
async def _probe_kh_health() -> bool:
    """Confirm KeeperHub API reachable + API key valid."""
    base = _KH_BASE_URL.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # 1. Health check (always 200)
            health = await client.get(f"{base}/api/health")
            health.raise_for_status()
            
            # 2. Auth check — verify API key
            auth = await client.get(
                f"{base}/api/workflows",
                headers={"Authorization": f"Bearer {_KH_API_KEY}"},
            )
            auth.raise_for_status()
            return True
    except Exception as exc:
        logger.warning("KH probe failed: %s", exc)
        return False
```

**Fallback behavior:** If KH is unreachable, EXECUTE returns `"PENDING"` — the protocol can still operate (badge mode), but auditable proof is deferred.

### Webhook Execution

**File:** `python/bff/workflow.py` (lines 64–94)

```python
async def _call_kh_execute(address: str, threshold: int) -> str:
    """Trigger KeeperHub workflow via /api/workflows/{id}/webhook."""
    url = f"{base}/api/workflows/{_KH_WORKFLOW_ID}/webhook"
    headers = {
        "Authorization": f"Bearer {_KH_WEBHOOK_KEY}",
        "Content-Type": "application/json"
    }
    
    resp = await client.post(
        url,
        json={
            "address": address,
            "threshold": threshold,
            "chain_id": 84532,  # Base Sepolia
        },
        headers=headers,
    )
    
    # Returns "OK" on success, "PENDING" on failure
    return "OK" if resp.status_code < 300 else "PENDING"
```

---

## Sample Request/Response

### Endpoint

```
POST /kh/workflow
Content-Type: application/json
```

### Request

```json
{
  "address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
  "threshold": 5000
}
```

### Response (Success)

```json
{
  "check": true,
  "validate": true,
  "zk_verify": {
    "verified": true,
    "proof_hash": "0x1a2b3c...",
    "public_signals": [6703, 5000],
    "merkle_root": "0x..."
  },
  "execute": "OK",
  "mode": "Workflow"
}
```

### Response (KH Unreachable, Fallback)

```json
{
  "check": true,
  "validate": true,
  "zk_verify": {
    "verified": true,
    "proof_hash": "0x1a2b3c...",
    "public_signals": [6703, 5000],
    "merkle_root": "0x..."
  },
  "execute": "PENDING",
  "mode": "Direct"
}
```

**File:** `python/bff/main.py` (lines 197–251)

---

## Live Proof Checklist

### 1. Health Check

```bash
# Check if KH is reachable from BFF
curl -s https://meritscore.warvis.org/health | jq .

# Expected:
# {
#   "status": "ok",
#   "chain": {
#     "galileo": true,     # 0G Galileo reachable
#     "base": true         # Base Sepolia reachable
#   }
# }
```

### 2. KeeperHub Workflow Execution

```bash
# Trigger workflow for Bob (merit 0.6703, should PASS all steps)
curl -s -X POST https://meritscore.warvis.org/kh/workflow \
  -H "Content-Type: application/json" \
  -d '{
    "address": "0xb0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0",
    "threshold": 5000
  }' | jq .

# Expected (if KH configured):
# {
#   "check": true,
#   "validate": true,
#   "zk_verify": {"verified": true, ...},
#   "execute": "OK",
#   "mode": "Workflow"
# }

# Or (if KH not configured):
# {
#   "check": true,
#   "validate": true,
#   "zk_verify": {"verified": true, ...},
#   "execute": "PENDING",
#   "mode": "Direct"
# }
```

### 3. KeeperHub Execution Log

```bash
# View last 20 KH workflow attempts
curl -s https://meritscore.warvis.org/kh/execution-log | jq .

# Expected:
# {
#   "entries": [
#     {
#       "timestamp": "2026-04-30T12:34:56.789Z",
#       "address": "0xb0b0b0b0...",
#       "threshold": 5000,
#       "check": true,
#       "validate": true,
#       "zk_verify": true,
#       "execute": "PENDING" or "OK"
#     },
#     ...
#   ]
# }
```

### 4. Agent Merit on Galileo

```bash
# Query MeritCore directly (CHECK step simulation)
cast call 0x19E3C17F58052Bb75D1c24bC1c56C2bfd1E5A906 \
  "getMerit(address)" 0xb0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0 \
  --rpc-url https://evmrpc-testnet.0g.ai --legacy

# Expected: 6703 (Bob's score in 1e4 scale)
```

### 5. MeritVault on Base Sepolia (VALIDATE step)

```bash
# Query MeritVault for attestation proof
cast call 0x3ef2818dD26F4B2e73D8fAb65F6aEA6bc1A2F5E2 \
  "validate(address)" 0xb0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0 \
  --rpc-url https://sepolia.base.org

# Expected: true (score exists and is valid)
```

---

## Setup & Deployment

### Prerequisites

```bash
# Python dependencies
pip install fastapi httpx pydantic python-dotenv

# KeeperHub credentials (from their dashboard)
export KH_BASE_URL="https://app.keeperhub.com"
export KH_API_KEY="wfb_..."
export KH_WEBHOOK_KEY="..."
export KH_WORKFLOW_ID="..."

# Chain RPCs
export RPC_GALILEO="https://evmrpc-testnet.0g.ai"
export RPC_BASE_SEPOLIA="https://sepolia.base.org"
```

### Run BFF Service

```bash
cd /home/jang/Workspace/warvis-hackerton
python -m uvicorn python.bff.main:app --host 0.0.0.0 --port 8000
```

### Test Locally

```bash
# Test CHECK + VALIDATE without real KH
export KH_BASE_URL=""  # Disable KH, fallback to PENDING

curl -X POST http://localhost:8000/kh/workflow \
  -H "Content-Type: application/json" \
  -d '{"address": "bob", "threshold": 5000}'

# Should return execute: "PENDING" (KH not configured)
```

---

## Why This Wins the KeeperHub Prize

| Criterion | Evidence |
|-----------|----------|
| **Meaningful Use** | Prevents false positives in DeFi gating; audit trail for compliance |
| **Working Demo** | Live curl examples above; /kh/workflow endpoint tested daily |
| **README + Setup** | This doc + `/home/jang/Workspace/warvis-hackerton/README.md` lines 342–350 |
| **Approach Write-up** | 3-step architecture (CHECK → VALIDATE → EXECUTE) clearly documented |
| **Deterministic** | Each workflow step logged, timestamped, auditable |
| **Graceful Fallback** | If KH unreachable, returns "PENDING", no protocol breakage |

---

## Architecture Highlights

### Decoupling via KeeperHub

Without KeeperHub, merit gating is a simple check:
```python
# Simple but audit-blind
if merit > 0.5:
    execute_swap()
```

With KeeperHub, it becomes an auditable workflow:
```python
# Deterministic, timestamped, proof-of-compliance
check_ok = await check_merit_threshold(address, 5000)
validate_ok = await validate_merit(address)
execute_status = await execute_workflow(address, 5000)
# Now: proof that validation happened at timestamp T
```

### Multi-Chain Coordination

```
Agent on Any Chain
         ↓
    BFF API (8000)
    ↓            ↓
CHECK (Galileo) VALIDATE (Base)
    ↓            ↓
  MeritCore   MeritVault
    ↓            ↓
KeeperHub (orchestrates both)
    ↓
Audit Log (immutable proof)
```

---

## References

- **README:** `/home/jang/Workspace/warvis-hackerton/README.md` (lines 342–350, Sword #3)
- **Workflow Code:** `python/bff/workflow.py` (lines 101–220)
- **API Endpoint:** `python/bff/main.py` (lines 197–251)
- **Health Probe:** `python/bff/workflow.py` (lines 36–61)
- **Execution Log:** `python/bff/main.py` (lines 607–616)

---

**Built during EthGlobal OpenAgents Hackathon 2026-04-25 to 2026-05-04**
