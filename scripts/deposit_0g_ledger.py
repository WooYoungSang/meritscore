"""Deposit A0GI into existing 0G Compute ledger and run one inference.

Usage:
    python scripts/deposit_0g_ledger.py

Requirements:
    - OG_PRIVATE_KEY in .env
    - Wallet balance >= 1.05 A0GI (faucet: https://faucet.0g.ai)
    - Existing ledger (run setup_0g_ledger.py first)
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from a0g import A0G
from web3 import Web3

DEPOSIT_AMOUNT = 1.05  # A0GI — covers addAccount(1.0) + gas buffer


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

    if balance < DEPOSIT_AMOUNT:
        print(f"❌ Need {DEPOSIT_AMOUNT} A0GI, have {balance:.4f}")
        print(f"   Faucet: https://faucet.0g.ai  →  {account.address}")
        return 1

    # depositFund into existing ledger
    print(f"Depositing {DEPOSIT_AMOUNT} A0GI into ledger…")
    nonce = w3.eth.get_transaction_count(account.address)
    tx = client.ledger_contract.functions.depositFund().build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gasPrice": w3.eth.gas_price,
        "gas": 200_000,
        "value": Web3.to_wei(DEPOSIT_AMOUNT, "ether"),
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"depositFund TX: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status != 1:
        print("❌ depositFund reverted")
        return 1
    print("✅ Deposit confirmed")

    # Find TeeML chatbot provider
    services = client.get_all_services()
    provider = next(
        (s for s in services if s.verifiability == "TeeML" and s.serviceType == "chatbot"),
        None,
    )
    if not provider:
        print("❌ No TeeML chatbot service found")
        return 1

    print(f"Using provider: {provider.provider}")
    print(f"Model: {provider.model}")

    # Run TeeML inference
    try:
        oai = client.get_openai_client(provider.provider)
        resp = oai.chat.completions.create(
            model=provider.model,
            messages=[{
                "role": "user",
                "content": "You are a TEE attestation oracle. Reply with exactly: proof-of-merit-attestation-ok",
            }],
            max_tokens=20,
        )
        content = resp.choices[0].message.content
        compute_hash = "0x" + hashlib.sha256(content.encode()).hexdigest()
        print(f"\n✅ 0G TeeML Inference SUCCESS")
        print(f"   Response  : {content}")
        print(f"   compute_hash: {compute_hash}")
        print(f"\nCP5 DONE — set MOCK_MODE=false in .env to use real attestation")
        return 0
    except Exception as e:
        print(f"❌ Inference failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
