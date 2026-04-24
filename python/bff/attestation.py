"""0G Compute Attestation Card (Sword #2).

Real call flow (MOCK_MODE=false):
  1. A0G(private_key, network='testnet') — connect to 0G Galileo
  2. get_all_services() — enumerate TeeML chatbot providers
  3. get_openai_client(provider.provider) — OpenAI-compatible endpoint
  4. chat.completions.create(...) — TEE-attested inference
  5. sha256(response) — compute_hash  |  EvidenceRegistry.latest() — storage_root
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os

logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────
MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"
ORACLE_COMMIT_HASH = os.getenv(
    "ORACLE_COMMIT_HASH",
    "0x09d34df4fd5c9c75b9970e4fbe0820c2b982466532d5413e1ae3b75fe7a1b4c1",
)
RPC_GALILEO = os.getenv("RPC_GALILEO", "https://evmrpc-testnet.0g.ai")
OG_PRIVATE_KEY = os.getenv("OG_PRIVATE_KEY")


# ── Mock helpers ────────────────────────────────────────────────────────────

def _mock_compute_hash() -> str:
    return "0x" + hashlib.sha256(b"proof-of-merit-bff-attestation").hexdigest()


def _mock_storage_root() -> str:
    return "0x" + hashlib.sha256(b"proof-of-merit-storage-root").hexdigest()


# ── Real 0G Compute call ───────────────────────────────────────────────────

def _invoke_0g_compute() -> tuple[str, bool]:
    """Try a real TeeML inference via 0G Compute SDK.

    Returns:
        (compute_hash, success)
        compute_hash: sha256 of inference response content, 0x-prefixed
        success: True if 0G call completed, False if fallback used
    """
    if not OG_PRIVATE_KEY:
        logger.warning("OG_PRIVATE_KEY not set — using mock compute_hash")
        return _mock_compute_hash(), False

    try:
        from a0g import A0G

        client = A0G(private_key=OG_PRIVATE_KEY, network="testnet")
        logger.info("0G client init: account=%s", client.account.address)

        # Check ledger exists (MIN_ACCOUNT_BALANCE = 0.1 A0GI required)
        ledger = client.get_ledger()
        if ledger is None:
            balance = float(client.get_balance())
            logger.warning(
                "0G Compute ledger not created — need 0.1 A0GI, have %.4f. "
                "Run addLedger() after topping up via faucet. Using mock.",
                balance,
            )
            return _mock_compute_hash(), False

        # Find TeeML chatbot provider
        services = client.get_all_services()
        tee_provider = next(
            (s for s in services if s.verifiability == "TeeML" and s.serviceType == "chatbot"),
            None,
        )
        if tee_provider is None:
            logger.warning("No TeeML chatbot service available — using mock")
            return _mock_compute_hash(), False

        logger.info("Using TeeML provider=%s model=%s", tee_provider.provider[:12], tee_provider.model)

        # OpenAI-compatible inference against TeeML endpoint
        oai = client.get_openai_client(tee_provider.provider)
        resp = oai.chat.completions.create(
            model=tee_provider.model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "You are a TEE attestation oracle. "
                        "Respond with exactly one line: proof-of-merit-attestation-ok"
                    ),
                }
            ],
            max_tokens=32,
        )
        content = resp.choices[0].message.content or str(resp.id)
        compute_hash = "0x" + hashlib.sha256(content.encode()).hexdigest()
        logger.info("0G TeeML inference OK — compute_hash=%s…", compute_hash[:18])
        return compute_hash, True

    except Exception as exc:
        logger.error("0G Compute call failed: %s — using mock", exc)
        return _mock_compute_hash(), False


async def _get_compute_hash_from_0g() -> tuple[str, bool]:
    """Async wrapper around the sync 0G SDK call."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _invoke_0g_compute)


# ── Public API ─────────────────────────────────────────────────────────────

async def get_attestation_data() -> dict:
    """Get 0G Compute Attestation Card.

    AC1: Returns {compute_hash, storage_root, oracle_commit, mode}
    AC2: MOCK_MODE=false → real 0G Compute call with graceful fallback
    AC3: oracle_commit from ORACLE_COMMIT_HASH env / default
    AC4: storage_root from EvidenceRegistry.latest() on 0G Galileo
    AC5: mode="Workflow" if 0G succeeded, "Direct" if fallback

    Returns:
        dict with compute_hash, storage_root, oracle_commit, mode
    """
    from .chain import get_storage_root

    if MOCK_MODE:
        logger.info("MOCK_MODE=true — returning deterministic mock hashes")
        return {
            "compute_hash": _mock_compute_hash(),
            "storage_root": _mock_storage_root(),
            "oracle_commit": ORACLE_COMMIT_HASH,
            "mode": "Workflow",
        }

    # MOCK_MODE=false: attempt real 0G calls
    logger.info("MOCK_MODE=false — invoking 0G Compute + EvidenceRegistry")

    compute_hash, compute_ok = await _get_compute_hash_from_0g()

    try:
        storage_root = await get_storage_root(RPC_GALILEO)
        logger.info("EvidenceRegistry.latest() OK: %s…", storage_root[:18])
    except Exception as exc:
        logger.error("EvidenceRegistry fetch failed: %s — using mock storage_root", exc)
        storage_root = _mock_storage_root()
        compute_ok = False

    mode = "Workflow" if compute_ok else "Direct"
    logger.info("Attestation complete: mode=%s compute_ok=%s", mode, compute_ok)

    return {
        "compute_hash": compute_hash,
        "storage_root": storage_root,
        "oracle_commit": ORACLE_COMMIT_HASH,
        "mode": mode,
    }
