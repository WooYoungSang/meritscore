# KeeperHub Integration Feedback — MeritScore Team

**Hackathon**: EthGlobal OpenAgents 2026  
**Project**: MeritScore — Experian for AI Agents  
**Team**: WoopsFactory  
**Date**: 2026-04-27

---

## Summary

We integrated KeeperHub as the automation layer for our 3-step merit verification workflow (CHECK → VALIDATE → EXECUTE). After significant debugging, we achieved a working end-to-end integration. This document captures our findings to help improve the KeeperHub developer experience.

---

## What We Built

A 3-step KeeperHub workflow triggered by our BFF API:

1. **CHECK** — Query MeritCore (0G Galileo) for agent score ≥ threshold
2. **VALIDATE** — Attest via MeritVault (Base Sepolia)
3. **EXECUTE** — Trigger KeeperHub workflow via webhook

Live endpoint: `POST https://meritscore.warvis.org/kh/workflow`  
Response: `{"check": true, "validate": true, "execute": "OK", "mode": "Workflow"}`

---

## API Discoveries (Undocumented)

### Working Endpoint
```
POST /api/workflows/{workflowId}/webhook
Authorization: Bearer wfb_<workflow-bearer-token>
Content-Type: application/json
```

### Key Findings

| Finding | Detail |
|---------|--------|
| **Webhook endpoint** | `/api/workflows/{id}/webhook` — not `/execute` |
| **Auth key type** | `wfb_` prefixed key (Workflow Bearer), not `kh_` API key |
| **`kh_` key scope** | Read-only: `GET /api/workflows` returns `[]`, POST returns 401 |
| **Workflow creation** | UI-only — no REST API for programmatic workflow creation |
| **Docs availability** | `docs.keeperhub.com` returns 403 without auth |

---

## Pain Points & Suggestions

### 1. API Documentation (Critical)
- **Issue**: `docs.keeperhub.com` is access-restricted. No public REST API docs available.
- **Time lost**: ~4 hours debugging undocumented endpoints
- **Suggestion**: Publish a public API reference page, at minimum covering authentication and workflow trigger endpoints.

### 2. Authentication Confusion (High)
- **Issue**: Two different key types (`kh_` vs `wfb_`) serve different purposes with no documentation explaining the difference.
- `kh_` API key: Read access to workflow list (but returns `[]` even when workflows exist)
- `wfb_` Workflow Bearer key: Required to trigger webhook — only shown in workflow UI settings
- **Suggestion**: Add a clear authentication guide explaining key types, scopes, and which key to use for which operation.

### 3. GET /api/workflows Returns Empty Array (Medium)
- **Issue**: `GET /api/workflows` returns `[]` even when workflows exist in the account. The `kh_` API key cannot see workflows created via browser session.
- **Suggestion**: Either fix the API to return the authenticated user's workflows, or document that workflow discovery requires the `wfb_` key per workflow.

### 4. No Programmatic Workflow Creation (Medium)
- **Issue**: `POST /api/workflows/create` returns 401 for all key types. Workflows can only be created via the visual UI.
- **Suggestion**: Expose a REST endpoint for creating simple workflows programmatically, or provide a CLI/SDK for hackathon use cases.

### 5. Workflow Node Types (Low)
- **Issue**: No "Contract Call" node available in the visual editor. We expected on-chain call capability but had to use an HTTP node instead.
- **Suggestion**: Add a native EVM Contract Call node with ABI import support.

---

## What Worked Well

- The visual workflow builder (React Flow-based) is intuitive once you know the correct auth flow
- `GET /api/health` is reliable for connectivity checks
- Response format `{"executionId": "...", "status": "running"}` is clean and actionable
- The `wfb_` webhook token is a good security model once understood

---

## Integration Code

```python
# python/bff/workflow.py — working KH integration
async def _call_kh_execute(address: str, threshold: int) -> str:
    url = f"{KH_BASE_URL}/api/workflows/{KH_WORKFLOW_ID}/webhook"
    headers = {
        "Authorization": f"Bearer {KH_WEBHOOK_KEY}",
        "Content-Type": "application/json"
    }
    resp = await client.post(url, json={
        "address": address,
        "threshold": threshold,
        "chain_id": 84532
    }, headers=headers)
    # Returns {"executionId": "...", "status": "running"} on success
    return "OK" if resp.status_code < 300 else "PENDING"
```

---

## Environment Variables Required

```env
KH_BASE_URL=https://app.keeperhub.com
KH_API_KEY=kh_<read-only-api-key>         # From Settings → API Keys
KH_WEBHOOK_KEY=wfb_<workflow-bearer-key>   # From workflow UI → Webhook trigger node
KH_WORKFLOW_ID=<workflow-id-from-url>      # From URL: /workflows/{id}
```

---

## Conclusion

Despite the documentation gaps, KeeperHub's webhook trigger model is solid and works well as an automation layer for on-chain agent workflows. With public API docs and a few UX improvements, KeeperHub could become the go-to automation tool for blockchain developers.

We're happy to provide more detailed feedback or hop on a call with the KeeperHub team.

**Contact**: WoopsFactory team — EthGlobal OpenAgents 2026
