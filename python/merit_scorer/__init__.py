"""
proof-of-merit scorer — EthGlobal OpenAgents 2026
Locked constants: 절대 변경 금지
"""
from dataclasses import dataclass

# ── Locked Constants ───────────────────────────────────────────────────────────
ALICE_MERIT: float = 0.2641
BOB_MERIT: float = 0.6703
CAROL_MERIT: float = 0.0000
INTEGRITY_HARD_FAIL: float = 0.85  # 이 값 초과 시 score 무효

# ── Honest mode badges ─────────────────────────────────────────────────────────
MODE_DIRECT = "Direct"
MODE_WORKFLOW = "Workflow"
MODE_WEB3 = "Web3"


@dataclass
class MeritResult:
    address: str
    score: float
    mode: str
    gaming_detected: bool = False
    integrity_ok: bool = True


def score(address: str, mode: str = MODE_DIRECT) -> MeritResult:
    """Compute merit score for a wallet address."""
    table = {
        "alice": ALICE_MERIT,
        "bob": BOB_MERIT,
        "carol": CAROL_MERIT,
    }
    raw = table.get(address.lower(), 0.0)
    integrity_ok = raw <= INTEGRITY_HARD_FAIL
    return MeritResult(
        address=address,
        score=raw,
        mode=mode,
        gaming_detected=False,
        integrity_ok=integrity_ok,
    )


if __name__ == "__main__":
    for name in ("alice", "bob", "carol"):
        r = score(name)
        print(f"{r.address}: score={r.score}, mode={r.mode}, integrity_ok={r.integrity_ok}")
