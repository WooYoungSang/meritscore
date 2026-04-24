# MeritScore API Documentation

**Base URL**: `http://localhost:61234`  
**Version**: 1.0  
**Status**: ✅ LIVE

## Endpoints

### 1. Health Check

```http
GET /health
```

**Response** (200 OK):
```json
{
  "status": "ok",
  "chain": {
    "galileo": true,
    "base": true
  }
}
```

### 2. Merit Lookup

```http
GET /merit/{address}
```

**Parameters**:
- `address` (string): Wallet address or alias (alice/bob/carol)

**Examples**:
```bash
curl http://localhost:61234/merit/alice
curl http://localhost:61234/merit/0x0bb64a3ec3B1c3Fc818A384D580Cc7E61f4c352E
```

**Response** (200 OK):
```json
{
  "address": "0xa11cea1a11cea1a11cea1a11cea1a11cea1a11ce",
  "score": 0.2641,
  "score_1e4": 2641,
  "exists": true,
  "mode": "Direct"
}
```

### 3. Attestation Card

```http
GET /attestation
```

**Response** (200 OK):
```json
{
  "compute_hash": "0x...",
  "storage_root": "0x...",
  "oracle_commit": "0x09d34df4...",
  "mode": "Direct"
}
```

**Modes**:
- `Direct`: MOCK_MODE=true or 0G Compute unavailable
- `Workflow`: MOCK_MODE=false + 0G Compute successful

### 4. AI Analysis

```http
POST /analyze
Content-Type: application/json

{
  "address": "0x..."
}
```

**Response** (200 OK):
```json
{
  "address": "0xa11cea...",
  "gaming_detected": false,
  "reason": "No transaction history provided",
  "merit_penalty": 0,
  "mode": "Direct"
}
```

### 5. KeeperHub Workflow

```http
POST /kh/workflow
Content-Type: application/json

{
  "agent_address": "0x...",
  "attestation": "0x...",
  "storage_root": "0x..."
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "tx_hash": "0x...",
  "merit_score": 0.6703
}
```

**Status Codes**:
- `200`: Success
- `400`: Invalid input
- `503`: Service unavailable (fallback mode)

## Rate Limits

No rate limiting applied (MOCK_MODE).  
Production deployment will use token bucket (10 req/sec per IP).

## Authentication

No authentication required for MOCK_MODE.  
Production: API key via `Authorization: Bearer <key>` header.
