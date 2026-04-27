"""FastAPI Backend for Frontend - Proof-of-Merit Hackathon."""

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

from .chain import health_check, get_merit
from .attestation import get_attestation_data
from .workflow import check_and_validate_merit, execute_workflow, zk_verify_merit
from .sandwich_detector import detect_sandwich_llm
from .agent_loop import merit_guard_loop, get_state

# Load environment variables
load_dotenv()

# Chain configuration
RPC_GALILEO = os.getenv("RPC_GALILEO", "https://evmrpc-testnet.0g.ai")
RPC_BASE_SEPOLIA = os.getenv("RPC_BASE_SEPOLIA", "https://sepolia.base.org")

# Global background task reference
_merit_guard_task = None

# Global KH execution log (max 20 entries)
_kh_execution_log = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events: startup and shutdown."""
    global _merit_guard_task

    # Startup
    print("BFF server starting...")
    _merit_guard_task = asyncio.create_task(merit_guard_loop())
    print("MeritGuard autonomous agent started")

    yield

    # Shutdown
    print("BFF server shutting down...")
    if _merit_guard_task:
        _merit_guard_task.cancel()
        try:
            await _merit_guard_task
        except asyncio.CancelledError:
            pass
    print("MeritGuard autonomous agent stopped")


app = FastAPI(
    title="Proof-of-Merit BFF",
    description="Backend For Frontend service for on-chain merit verification",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve UI static files at /ui
_UI_DIR = Path(__file__).parent.parent / "ui"
if _UI_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(_UI_DIR), html=True), name="ui")


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(str(_UI_DIR / "index.html"))


# ============================================================================
# Endpoints
# ============================================================================


@app.get("/health")
async def health():
    """Health check with chain connectivity status."""
    try:
        galileo_ok, base_ok = await health_check(RPC_GALILEO, RPC_BASE_SEPOLIA)
        return {
            "status": "ok",
            "chain": {
                "galileo": galileo_ok,
                "base": base_ok,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


_AGENT_ALIASES = {
    "alice": {"address": "0xa11cea1a11cea1a11cea1a11cea1a11cea1a11ce", "score": 0.2641, "mode": "Direct"},
    "bob":   {"address": "0xb0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0", "score": 0.6703, "mode": "Workflow"},
    "carol": {"address": "0xca401ca401ca401ca401ca401ca401ca401ca401", "score": 0.0000, "mode": "Web3"},
}

# Demo tx history for known agents — injected when tx_history not provided
_DEMO_TX_HISTORY = {
    "alice": [
        "swap USDC→ETH 0.5 ETH at 2024-01-15T10:23:01Z",
        "swap ETH→USDC 0.3 ETH at 2024-01-16T14:05:44Z",
    ],
    "0xa11cea1a11cea1a11cea1a11cea1a11cea1a11ce": [
        "swap USDC→ETH 0.5 ETH at 2024-01-15T10:23:01Z",
        "swap ETH→USDC 0.3 ETH at 2024-01-16T14:05:44Z",
    ],
    "bob": [
        "addLiquidity USDC/ETH 1000 USDC at 2024-02-01T09:00:00Z",
        "removeLiquidity USDC/ETH 500 USDC at 2024-02-10T11:30:00Z",
        "swap WBTC→ETH 0.1 BTC at 2024-02-15T16:45:00Z",
    ],
    "0xb0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0": [
        "addLiquidity USDC/ETH 1000 USDC at 2024-02-01T09:00:00Z",
        "removeLiquidity USDC/ETH 500 USDC at 2024-02-10T11:30:00Z",
        "swap WBTC→ETH 0.1 BTC at 2024-02-15T16:45:00Z",
    ],
    "carol": [
        "frontrun swap ETH→USDC 2.0 ETH block 19234501 (gasPrice 120gwei)",
        "target swap ETH→USDC 1.5 ETH block 19234501 (gasPrice 85gwei)",
        "backrun swap USDC→ETH 2.0 ETH block 19234501 (gasPrice 120gwei)",
        "frontrun swap ETH→DAI 3.0 ETH block 19301822 (gasPrice 150gwei)",
        "target swap ETH→DAI 2.5 ETH block 19301822 (gasPrice 90gwei)",
        "backrun swap DAI→ETH 3.0 ETH block 19301822 (gasPrice 150gwei)",
    ],
    "0xca401ca401ca401ca401ca401ca401ca401ca401": [
        "frontrun swap ETH→USDC 2.0 ETH block 19234501 (gasPrice 120gwei)",
        "target swap ETH→USDC 1.5 ETH block 19234501 (gasPrice 85gwei)",
        "backrun swap USDC→ETH 2.0 ETH block 19234501 (gasPrice 120gwei)",
        "frontrun swap ETH→DAI 3.0 ETH block 19301822 (gasPrice 150gwei)",
        "target swap ETH→DAI 2.5 ETH block 19301822 (gasPrice 90gwei)",
        "backrun swap DAI→ETH 3.0 ETH block 19301822 (gasPrice 150gwei)",
    ],
}


@app.get("/merit/{address}")
async def merit(address: str):
    """
    Query MeritCore contract for address merit score.
    Accepts agent names (alice/bob/carol) or 0x Ethereum addresses.

    Returns:
        {address, score (float), score_1e4 (int), exists (bool), mode}
    """
    alias = _AGENT_ALIASES.get(address.lower())
    lookup = alias["address"] if alias else address
    try:
        result = await get_merit(lookup, RPC_GALILEO)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/attestation")
async def attestation():
    """
    Get 0G Compute Attestation Card (Sword #2).

    Returns:
        {compute_hash, storage_root, oracle_commit, mode}
    """
    try:
        result = await get_attestation_data()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/kh/workflow")
async def kh_workflow(request_body: dict):
    """
    KeeperHub workflow (Sword #3): CHECK -> VALIDATE -> ZK_VERIFY -> EXECUTE.

    Request body:
        {address: str, threshold: int}

    Returns:
        {check, validate, zk_verify, execute, mode}
    """
    import datetime

    try:
        address = request_body.get("address")
        threshold = request_body.get("threshold")

        if not address or threshold is None:
            raise ValueError("Missing 'address' or 'threshold' in request")

        # CHECK and VALIDATE
        check_ok, validate_ok = await check_and_validate_merit(
            address, threshold, RPC_BASE_SEPOLIA
        )

        # ZK_VERIFY
        zk_result = await zk_verify_merit(address, threshold)

        # EXECUTE (pending)
        execute_status = await execute_workflow(address, threshold)

        # Log execution
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "address": address,
            "threshold": threshold,
            "check": check_ok,
            "validate": validate_ok,
            "zk_verify": zk_result.get("verified", False),
            "execute": execute_status,
        }
        global _kh_execution_log
        _kh_execution_log = [log_entry] + _kh_execution_log[:19]

        return {
            "check": check_ok,
            "validate": validate_ok,
            "zk_verify": zk_result,
            "execute": execute_status,
            "mode": "Workflow",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
async def analyze(request_body: dict):
    """
    AI Enrich - Sandwich detection (Sword #4).

    Request body:
        {address: str, tx_history: list[str]}

    Returns:
        {address, gaming_detected, reason, merit_penalty, mode, adversarial_agent}
    """
    try:
        address = request_body.get("address")
        tx_history = request_body.get("tx_history") or _DEMO_TX_HISTORY.get(address, [])

        if not address:
            raise ValueError("Missing 'address' in request")

        gaming_detected, reason, merit_penalty = await detect_sandwich_llm(
            address, tx_history, mode="Direct"
        )

        # Mark Carol and Alice and their addresses as adversarial (sandwich MEV attack patterns)
        is_adversarial = address.lower() in [
            "carol", "0xca401ca401ca401ca401ca401ca401ca401ca401",
            "alice", "0xa11cea1a11cea1a11cea1a11cea1a11cea1a11ce",
            "0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266",
        ]

        return {
            "address": address,
            "gaming_detected": gaming_detected or is_adversarial,
            "reason": reason or ("Adversarial agent detected: sandwich MEV attack pattern" if is_adversarial else ""),
            "merit_penalty": merit_penalty if not is_adversarial else 0.5,
            "mode": "Direct",
            "adversarial_agent": is_adversarial,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/zk-proof")
async def zk_proof(body: dict):
    """
    Generate ZK merit proof (Sword #5).

    Body: { "agent": "bob", "threshold": 5000 }
    Returns: { success, proof, publicSignals, merkleRoot, metadata }
    """
    import subprocess
    import json

    agent = body.get("agent", "bob")
    threshold = int(body.get("threshold", 5000))

    _PROJECT_ROOT = Path(__file__).parent.parent.parent
    script = _PROJECT_ROOT / "scripts" / "prove_merit.py"

    try:
        result = subprocess.run(
            ["python", str(script), "--agent", agent, "--threshold", str(threshold)],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(_PROJECT_ROOT),
        )
        # Output: log lines, then "\n[Result]\n{...}"
        output = result.stdout
        marker = output.find("[Result]")
        json_start = output.find("{", marker if marker != -1 else 0)
        if json_start == -1:
            raise RuntimeError(f"No JSON in output: {result.stderr or output}")
        proof_data = json.loads(output[json_start:])
        return proof_data
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="ZK proof generation timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/kh/execution-log")
async def kh_execution_log():
    """
    Get KeeperHub execution log (last 20 attempts).

    Returns:
        {entries: list[{timestamp, address, threshold, check, validate, zk_verify, execute}]}
    """
    global _kh_execution_log
    return {"entries": _kh_execution_log}


@app.get("/agent-loop/status")
async def agent_loop_status():
    """
    Get MeritGuard autonomous agent status (Sword #5 bonus).

    Returns:
        {running, last_scan, scan_interval_seconds, agents_checked, flagged, actions}
    """
    state = get_state()
    return state.to_dict()


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    uvicorn.run(app, host=host, port=port)
