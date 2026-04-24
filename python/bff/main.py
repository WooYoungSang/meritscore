"""FastAPI Backend for Frontend - Proof-of-Merit Hackathon."""

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
from .workflow import check_and_validate_merit, execute_workflow
from .sandwich_detector import detect_sandwich_llm

# Load environment variables
load_dotenv()

# Chain configuration
RPC_GALILEO = os.getenv("RPC_GALILEO", "https://evmrpc-testnet.0g.ai")
RPC_BASE_SEPOLIA = os.getenv("RPC_BASE_SEPOLIA", "https://sepolia.base.org")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events: startup and shutdown."""
    # Startup
    print("BFF server starting...")
    yield
    # Shutdown
    print("BFF server shutting down...")


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
    if alias:
        score = alias["score"]
        return {
            "address": alias["address"],
            "score": score,
            "score_1e4": int(score * 10000),
            "exists": True,
            "mode": alias["mode"],
        }
    try:
        result = await get_merit(address, RPC_GALILEO)
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
    KeeperHub workflow (Sword #3): CHECK -> VALIDATE -> EXECUTE.

    Request body:
        {address: str, threshold: int}

    Returns:
        {check, validate, execute, mode}
    """
    try:
        address = request_body.get("address")
        threshold = request_body.get("threshold")

        if not address or threshold is None:
            raise ValueError("Missing 'address' or 'threshold' in request")

        # CHECK and VALIDATE
        check_ok, validate_ok = await check_and_validate_merit(
            address, threshold, RPC_BASE_SEPOLIA
        )

        # EXECUTE (pending)
        execute_status = await execute_workflow(address, threshold)

        return {
            "check": check_ok,
            "validate": validate_ok,
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
        {address, gaming_detected, reason, merit_penalty, mode}
    """
    try:
        address = request_body.get("address")
        tx_history = request_body.get("tx_history") or _DEMO_TX_HISTORY.get(address, [])

        if not address:
            raise ValueError("Missing 'address' in request")

        gaming_detected, reason, merit_penalty = await detect_sandwich_llm(
            address, tx_history, mode="Direct"
        )

        return {
            "address": address,
            "gaming_detected": gaming_detected,
            "reason": reason,
            "merit_penalty": merit_penalty,
            "mode": "Direct",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    uvicorn.run(app, host=host, port=port)
