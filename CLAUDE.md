# Project Harness

This CLAUDE.md was rendered by `devos_harness_install` (Ignis Harness Registry).
It pins the agent manifest at install time; update via `devos_harness_propagate`.


## Stack

- Language: Python (merit_scorer) + Solidity (MeritCore / MeritVault) + TypeScript (Oracle relay)
- Build system: Foundry (contracts) + pnpm (frontend/scripts)
- Frameworks: Streamlit (UI), 0G Compute SDK, KeeperHub API

## Commands

- Build: `forge build && pnpm build`
- Test: `forge test && pytest python/ -q`
- Lint: `forge fmt --check && ruff check python/`

## Locked Constants (절대 변경 금지)

```
HACKATHON_START      = 2026-04-24 14:00 KST
SUBMISSION_DEADLINE  = 2026-05-04 01:00 KST
ALICE_MERIT          = 0.2641
BOB_MERIT            = 0.6703
CAROL_MERIT          = 0.0000
INTEGRITY_HARD_FAIL  = 0.85
```

## Chain Config

| Chain | ID | RPC | 비고 |
|-------|----|-----|------|
| 0G Galileo | 16602 | `https://evmrpc-testnet.0g.ai` | **`--legacy` 필수** (EIP-1559 미지원) |
| Base Sepolia | 84532 | `https://sepolia.base.org` | — |

## Context & Sync Protocol

### Single Source of Truth (SSoT)
- **Obsidian vault**: `WARVIS`
- **Dashboard (중앙 앵커)**: `obsidian://open?vault=WARVIS&file=01-dashboard%2Fhackathon-ethglobal-openagents`
- **Obsidian note path**: `01-dashboard/hackathon-ethglobal-openagents.md`

### 3-Way Sync 원칙
```
Obsidian (SSoT)  ←→  warvis-mcp (인덱스)  ←→  로컬 코드
```
1. **컨텍스트 조회 우선순위**: warvis-mcp (`devos_search_context`) → Obsidian MCP (`obsidian_read_note`)
2. **Obsidian 업데이트 후**: `devos_index_project(project_id="warvis-hackerton")` 실행
3. **코드 구현 완료 후**: Obsidian 해당 UoW/Sword 상태 패치 (`obsidian_patch_note_section`)
4. **세션 시작 시**: `devos_get_project_state` + `devos_get_bet_progress` 로 현황 확인

### warvis-mcp Project
- `project_id`: `warvis-hackerton`
- 인덱싱 대상: Dashboard에 연결된 모든 ADR / NFR / FR / UoW / Bet / Pitch

### 인덱싱 커버리지 (Dashboard 기준)
| 타입 | 수량 | 위치 |
|------|:----:|------|
| ADR | 10건 | `20-projects/warvis-hackerton--adr-*.md` |
| FR | 16건 | `20-projects/warvis-hackerton--fr-*.md` |
| NFR | 9건 | `20-projects/warvis-hackerton--nfr-*.md` |
| UoW | 20건 | `20-projects/warvis-hackerton--uow-*.md` |
| Bet | 1건 | `20-projects/warvis-hackerton--bet-*.md` |
| Pitch | 5건 | `20-projects/warvis-hackerton--pitch-*.md` |

## Live Deployment

| 항목 | 값 |
|------|-----|
| **URL** | `https://meritscore.warvis.org` |
| **Port** | `61234` (docker-compose) |
| **Mode** | `MOCK_MODE=true` (default) |

### Deployed Contracts

| Contract | Chain | Address |
|----------|-------|---------|
| `MeritCore` | 0G Galileo (16602) | `0x19E3C17F58052Bb75D1c24bC1c56C2bfd1E5A906` |
| `MeritVault` | Base Sepolia (84532) | `0x3ef2818dD26F4B2e73D8fAb65F6aEA6bc1A2F5E2` |
| `EvidenceRegistry` | 0G Galileo (16602) | `0x4DE88763BfcBd799376c4715c245F656D518e43B` |

### BFF API Endpoints (FastAPI, port 61234)

| Method | Path | Sword | Description |
|--------|------|:-----:|-------------|
| GET | `/health` | — | Chain connectivity (galileo + base) |
| GET | `/merit/{address}` | — | Merit score (alias: alice/bob/carol or 0x addr) |
| GET | `/attestation` | #2 | TEE attestation card (0G Compute) |
| POST | `/kh/workflow` | #3 | KeeperHub CHECK→VALIDATE→EXECUTE |
| POST | `/analyze` | #4 | AI sandwich detection (Gemma4 26B / Ollama) |

### Sword Implementation Status

| # | Sword | Status |
|:-:|-------|:------:|
| 1 | Live Evaluation Button | ⬜ D3 AM 예정 |
| 2 | TEE Attestation Card | ✅ DONE |
| 3 | KH 3-Step Workflow + Log | ✅ DONE |
| 4 | AI Enriches Formula | ✅ DONE |
| 5 | ZK Merit Proof | ⬜ 선택적 |

## Spike Learnings (D-2, 2026-04-22)

- **0G Galileo**: forge/cast 모든 명령에 `--legacy` 플래그 필수
- **0G Compute**: `from a0g import A0G`, `get_all_services()` sync. 레저 계정 A0G 추가 필요
- **0G Storage**: SDK `from contracts import FlowContract`. 킥오프 시 인프라 재확인
- **KeeperHub**: 킥오프 시 endpoint 공개 예정. `KH_API_KEY`는 `.env` 전용
- **Wallet**: `0x0bb64a3ec3B1c3Fc818A384D580Cc7E61f4c352E`


## Agent Delegation

| Agent | Applies to | Capabilities |
|-------|------------|--------------|
| `rules-guardian` | hackathon, compliance, submission-gate | rule-enforcement, submission-veto |  <!-- Read-only EthGlobal 룰 심판. 8 Rules + AI 정책 전역 감시. 위반 1건 → VETO. commit 전 preflight / 제출 전 최종 게이트 두 시점 호출. -->
| `hackathon-conductor` | hackathon, proof-of-merit, implementation | 4-sword, cp-tracking, kill-switch |  <!-- proof-of-merit 특화 지휘관. 4 Sword 구현, CP1~CP9 Hill 추적, Kill Switch 실행. commit 전 rules-guardian 의무 호출. -->
| `bet-reviewer` | review, ship-gate | gate-review, evidence-validation |  <!-- Read-only Build Completion Report reviewer. Validates acceptance criteria, Hill Chart position, and kill conditions. Outputs SHIP / BLOCK / SCOPE_HAMMER verdict. -->
| `contract-auditor` | contract-audit, verification | contract-analysis, code-review |  <!-- Read-only interface conformance auditor. Verifies implementation matches contract definitions. -->
| `python-generic-engineer` | python | — |  <!-- Python domain library engineer for any project's libs/ or src/ domain code. Stdlib-first, type-annotated dataclasses. Use for pure Python domain modeling, data structures, algorithms, and library code with no project-specific external dependencies. -->
| `python-reviewer` | any | — |  <!-- Universal Python code reviewer. Resolves project conventions at runtime via a 4-stage fallback (caller arg → CLAUDE.md → pyproject.toml → PEP8 defaults). Emits CRITICAL/WARN/INFO findings with file:line anchors. Read-only. -->
| `silent-failure-hunter` | any | — |  <!-- Lightweight scanner for stubs, TODO/FIXME/XXX markers, bare excepts, pass-only bodies, NotImplementedError, and docstring-only functions. Returns a JSON-structured list of detections with file:line and ±2-line snippets. Read-only. -->
| `small-diff-implementer` | tdd, orchestration | tdd-orchestration, phase-management |  <!-- TDD cycle coordinator — gates and sequences tdd-red → tdd-green → tdd-refactor. Determines current TDD phase and delegates to the appropriate specialist. -->
| `spec-auditor` | spec-audit, verification | contract-analysis, spec-review |  <!-- Read-only spec/contract gap auditor. Reviews spec files (ADR/FR/NFR) against contract definitions and reports structural gaps. -->
| `tdd-green` | tdd, implementation | implementation, minimal-coding |  <!-- TDD Green phase — implement the absolute minimum code to make the red test pass. No refactoring. No extra features. -->
| `tdd-red` | tdd, test-writing | test-writing, verification |  <!-- TDD Red phase — write exactly one failing test that proves a missing or broken behavior. Stops after confirming failure. -->
| `tdd-refactor` | tdd, refactoring | refactoring, code-quality |  <!-- TDD Refactor phase — improve code structure while keeping all tests green. No behavior changes. -->
| `warvis-finisher` | warvis | — |  <!-- WARVIS stage 5 — Finalize verified session. -->
| `warvis-initiator` | warvis | — |  <!-- WARVIS stage 1 — Start dev session, preflight checks. -->
| `warvis-maker` | warvis | — |  <!-- WARVIS stage 3 — TDD implementation (red→green→refactor). -->
| `warvis-orchestrator` | warvis | — |  <!-- Universal UoW lifecycle orchestrator. Runs devos_* MCP lifecycle. -->
| `warvis-planner` | warvis | — |  <!-- WARVIS stage 2 — Generate implementation plan. -->
| `warvis-setup` | warvis | — |  <!-- WARVIS project onboarding agent. -->
| `warvis-verifier` | warvis | — |  <!-- WARVIS stage 4 — Quality gates (Lint→Test→Security→Integration). -->
| `work-reporter` | reporting, status | report-generation, metrics-analysis |  <!-- Read-only work status reporter. Generates structured Daily Status, Bet Progress, Period Summary, or Ad-hoc reports based on trigger. -->

## Skills

| Skill | Trigger | Description |
|-------|---------|-------------|
| `preflight-compli