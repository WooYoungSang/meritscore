# KeeperHub Feedback — MeritScore Integration

**Project**: MeritScore (EthGlobal OpenAgents 2026)  
**Date**: 2026-04-25  
**Track**: KeeperHub Partner Prize  
**Contact**: silence1442@gmail.com  

---

## Overview

MeritScore is a dual-chain merit scoring system for AI agents.  
We implemented a 3-step KeeperHub workflow: **CHECK → VALIDATE → EXECUTE**  
targeting two chains: **0G Galileo (chainId 16602)** and **Base Sepolia (chainId 84532)**.

---

## Issue 1: 0G Galileo (chainId 16602) Not Supported

### What We Tried

```python
# python/bff/workflow.py — execute_workflow()
payload = {
    "chain_id": 16602,          # 0G Galileo testnet
    "address": agent_address,
    "action": "distribute_merit",
    "contract": "0x19E3C17F58052Bb75D1c24bC1c56C2bfd1E5A906",  # MeritCore
}
response = await client.post(f"{KH_BASE_URL}/v1/workflows/execute", json=payload)
```

### Error Evidence

```
POST /v1/workflows/execute HTTP/1.1
Authorization: Bearer kh_bqAlPd3oFkJErq4s6FFw90jm6YVn8ZFP

{
  "chain_id": 16602,
  "address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
  "action": "distribute_merit"
}

→ HTTP 422 Unprocessable Entity
{
  "error": "unsupported_chain",
  "message": "chain_id 16602 is not in the supported chains list",
  "supported_chains": [1, 10, 137, 8453, 84532, 42161, 11155111]
}
```

### Impact on Our Architecture

Our scoring logic lives on **0G Galileo** (MeritCore.sol) and capital allocation
on **Base Sepolia** (MeritVault.sol). KeeperHub can only automate the Base side.

The cross-chain relay step (0G score → Base execution) required us to implement
a manual oracle commit on 0G and then trigger KeeperHub only on Base Sepolia.

---

## Issue 2: Workflow Schema Discovery

`list_action_schemas` returned an empty array for cross-chain workflows:

```json
GET /v1/schemas/actions?chain_id=16602
→ { "schemas": [] }

GET /v1/schemas/actions?chain_id=84532
→ { "schemas": ["execute_contract_call", "transfer_erc20", "monitor_event"] }
```

No `cross_chain_relay` schema exists, making oracle bridging unautomated.

---

## Specific Improvement Suggestions

### 1. Add 0G Galileo (chainId 16602) to Supported Chains

```python
# Proposed KH chain registry addition
SUPPORTED_CHAINS = {
    ...existing chains...,
    16602: {
        "name": "0G Galileo",
        "rpc": "https://evmrpc-testnet.0g.ai",
        "explorer": "https://explorer.0g.ai",
        "type": "testnet",
        "eip1559": False,  # requires --legacy flag
    }
}
```

Required flag: all transactions must use legacy gas pricing (EIP-1559 not supported).

### 2. `cross_chain_relay` Action Schema

```json
{
  "action": "cross_chain_relay",
  "source_chain_id": 16602,
  "destination_chain_id": 84532,
  "oracle_commit_hash": "0x09d34df4...",
  "execute_on_destination": {
    "contract": "0x3ef2818d...",
    "function": "allocate(address,uint256)",
    "args": ["0xf39Fd6e5...", 2641]
  }
}
```

This would enable our full pipeline to run as a single KeeperHub workflow
instead of splitting across a manual oracle + KH Workflow.

### 3. `execute_contract_call` Cross-Chain Extension

Extend the existing `execute_contract_call` action with optional `source_chain_read`:

```json
{
  "action": "execute_contract_call",
  "chain_id": 84532,
  "pre_check": {
    "chain_id": 16602,
    "contract": "0x19E3C17F...",
    "function": "epochFinalized(uint256)",
    "args": [42],
    "expected": true
  },
  "contract": "0x3ef2818d...",
  "function": "allocate(address,uint256)"
}
```

---

## What Did Work Well ✅

- **Base Sepolia (84532)**: `execute_contract_call` worked first try.
- **3-step workflow** (CHECK → VALIDATE → EXECUTE): clean API design, easy to reason about.
- **Monitoring logs** (`get_execution_logs`): excellent for audit trails.
- **API key auth**: simple, no OAuth friction.

---

## Workaround We Implemented

Since KH doesn't support 0G Galileo, we split the workflow:

```
0G Galileo:    MeritCore.batchSetMerit() + EvidenceRegistry.anchor()
               ↓ (manual oracle commit, no KH)
Oracle Relay:  Read score from 0G → sign → post to Base
               ↓
Base Sepolia:  KeeperHub CHECK → VALIDATE → EXECUTE (MeritVault.allocate())
```

Oracle commit tx: `0xd492f5714656eb1199c307c1c67902906a0f946a9113f697e25f05a8e4917b61`  
Evidence anchor tx: `0x5feb7bc4d3c7c0dbf64726f0cca751fda4735378fa80cf78af42316b8ef6394e`

---

## Conclusion

KeeperHub's 3-step workflow is a clean primitive for autonomous capital allocation.  
Adding 0G Galileo support would unlock AI agent use cases where TEE-attested  
computations on 0G need to be **enforced** by autonomous execution on EVM chains.

We believe the `cross_chain_relay` schema, if implemented, would make KeeperHub  
the de-facto infrastructure layer for cross-chain AI agent coordination.

**→ Happy to contribute a PR for 0G chain support if the team is interested.**
