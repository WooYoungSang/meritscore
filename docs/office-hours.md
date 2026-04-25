# Sponsor Office Hours Logs — MeritScore

## 0G Sponsor Session (2026-04-24)

### Questions & Answers

**Q: forge/cast 명령어 실행 시 EIP-1559 관련 오류 발생**
- A: 0G Galileo (16602)는 EIP-1559를 미지원합니다. 모든 forge/cast 명령에 `--legacy` 플래그를 추가하세요.
- Example: `forge deploy --network 0g-galileo --legacy`

**Q: 0G Compute SDK에서 fund transfer 시 service name 확인**
- A: `ledger.transferFund(provider, "inference-v1.0", amount)`
- **Critical**: service name은 정확히 `"inference-v1.0"` (not `"inference"` or `"inference-v1"`)

**Q: User balance 조회 방법**
- A: `inference_contract.getAccount(user, provider)` returns tuple — index[3] = balance in wei
- Example: `balance_wei = result[3]`

**Q: EvidenceRegistry 저장소 쿼리**
- A: `EvidenceRegistry.latest()` returns `(bytes32, string, uint256)`
  - bytes32: evidence hash
  - string: evidence metadata
  - uint256: timestamp

### Action Items

- [x] Update forge scripts with `--legacy` flag
- [x] Validate service name in 0G Compute calls
- [x] Test balance queries against testnet
- [x] Document storage proof format

### Learnings

- 0G Galileo is a legacy-only chain; plan migration if EIP-1559 support arrives
- Service names are case-sensitive; use exact string match
- Balance queries return wei; convert to A0GI for display (divide by 10^18)
- Evidence metadata is arbitrary string; use structured format (JSON) for parsing

---

## KeeperHub Sponsor Session (2026-04-25)

### Questions & Answers

**Q: KeeperHub 3-Step Workflow 구현**
- A: KH workflow supports CHECK → VALIDATE → EXECUTE pipeline
- Implementation: `POST /kh/workflow` with payload:
  ```json
  {
    "action": "CHECK|VALIDATE|EXECUTE",
    "evidence": {...},
    "merkle_root": "0x...",
    "proof": [...]
  }
  ```

**Q: KH API endpoint 확인**
- A: **PENDING** — Discord `#keeperhub` 채널에서 최종 확인 필요
- Tentative endpoint: `https://api.keeperhub.io/workflow` (unconfirmed)
- **DO NOT HARDCODE** — use environment variable `KH_API_ENDPOINT` from `.env`

**Q: KH_API_KEY 관리**
- A: `KH_API_KEY` must be in `.env` (never in code or CLAUDE.md)
- Example `.env`: `KH_API_KEY=sk-...`
- Load via: `os.getenv("KH_API_KEY")`

**Q: Workflow logging & state tracking**
- A: Log each state transition (CHECK → VALIDATE → EXECUTE) with timestamp
- Store workflow state in persistent storage (contract or database)
- Example log entry:
  ```json
  {
    "workflow_id": "0x...",
    "timestamp": 1714041600,
    "state": "VALIDATE",
    "status": "in_progress",
    "evidence_hash": "0x..."
  }
  ```

### Action Items

- [ ] Confirm KH API endpoint with Discord #keeperhub
- [ ] Set up KH_API_KEY in .env (local testing only)
- [ ] Implement workflow state machine (CHECK → VALIDATE → EXECUTE)
- [ ] Add comprehensive workflow logging
- [ ] Test workflow on testnet with dummy merkle proofs
- [ ] Create KH integration test suite

### Learnings

- KH workflow is 3-phase; each phase is independent POST call
- API endpoint discovery required — check Discord before production deployment
- State transitions must be logged for audit trail
- Proof format depends on KH spec (merkle tree assumed, confirm)
- Error handling must cover network failures, timeout, and validation failures

---

## Integration Notes

### Deployed Contracts Reference

| Contract | Chain | Address |
|----------|-------|---------|
| `MeritCore` | 0G Galileo (16602) | `0x19E3C17F58052Bb75D1c24bC1c56C2bfd1E5A906` |
| `MeritVault` | Base Sepolia (84532) | `0x3ef2818dD26F4B2e73D8fAb65F6aEA6bc1A2F5E2` |
| `EvidenceRegistry` | 0G Galileo (16602) | `0x4DE88763BfcBd799376c4715c245F656D518e43B` |

### Demo Wallet

- Address: `0x0bb64a3ec3B1c3Fc818A384D580Cc7E61f4c352E`
- Balance: ~3.0 A0GI (as of 2026-04-25)

### Test Coverage

- [ ] 0G Compute fund transfer with correct service name
- [ ] Balance query and conversion to human-readable units
- [ ] Evidence registry storage and retrieval
- [ ] KH workflow state machine transitions
- [ ] Error handling for network failures

---

## Blockers & Resolutions

| Blocker | Status | Resolution |
|---------|:------:|-----------|
| 0G EIP-1559 support | ✅ RESOLVED | Use `--legacy` flag |
| KH API endpoint | ⏳ PENDING | Discord confirmation needed |
| KH proof format spec | ⏳ PENDING | Clarify merkle tree structure |
| Service name case sensitivity | ✅ RESOLVED | Always use exact `"inference-v1.0"` |

---

## Next Steps

1. **Confirm KH endpoint** — Post in Discord `#keeperhub` or reach out to sponsor directly
2. **Finalize proof format** — Request KH documentation on merkle proof structure
3. **Integration testing** — Test full CHECK→VALIDATE→EXECUTE pipeline
4. **Production readiness** — Validate all learnings on testnet before final submission

---

*Last updated: 2026-04-26*
*Session conducted by: WoopsFactory*
