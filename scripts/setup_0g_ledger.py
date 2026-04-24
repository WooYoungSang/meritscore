"""One-shot script: create 0G Compute ledger account after topping up wallet.

Usage:
    python scripts/setup_0g_ledger.py

Requirements:
    - OG_PRIVATE_KEY in .env
    - Wallet balance >= 0.1 A0GI (faucet: https://faucet.0g.ai)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from a0g import A0G
from web3 import Web3


def main() -> int:
    pk = os.getenv("OG_PRIVATE_KEY")
    if not pk:
        print("ERROR: OG_PRIVATE_KEY not set in .env")
        return 1

    client = A0G(private_key=pk, network="testnet")
    w3 = client.w3
    account = client.account

    balance = float(client.get_balance())
    print(f"Account : {account.address}")
    print(f"Balance : {balance:.6f} A0GI")

    # Check if ledger already exists
    ledger = client.get_ledger()
    if ledger is not None:
        print("✅ Ledger already exists — no action needed")
        return 0

    min_bal = float(Web3.from_wei(client.ledger_contract.functions.MIN_ACCOUNT_BALANCE().call(), "ether"))
    deposit = min_bal + 0.01  # small buffer above minimum

    if balance < deposit:
        print(f"❌ Insufficient balance: have {balance:.4f} A0GI, need {deposit:.4f} A0GI")
        print(f"   Faucet: https://faucet.0g.ai  →  {account.address}")
        return 1

    print(f"Creating ledger (depositing {deposit:.4f} A0GI)…")
    nonce = w3.eth.get_transaction_count(account.address)
    tx = client.ledger_contract.functions.addLedger("proof-of-merit-hackathon").build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gasPrice": w3.eth.gas_price,
        "gas": 300_000,
        "value": Web3.to_wei(deposit, "ether"),
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"TX sent: {tx_hash.hex()}")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status == 1:
        print(f"✅ Ledger created! TX: {tx_hash.hex()}")
        print("   Set MOCK_MODE=false in .env to enable real 0G Compute attestation")
        return 0
    else:
        print(f"❌ TX reverted — check balance and retry")
        return 1


if __name__ == "__main__":
    sys.exit(main())
