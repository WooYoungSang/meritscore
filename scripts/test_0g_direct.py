"""Direct TeeML provider access via app-sk session token (no addAccount needed).

Reverse-engineered from 0G Compute frontend bundle.js generateSessionToken():
  token = {address, provider, timestamp, expiresAt, nonce}
  message = JSON.stringify(token)          # compact, insertion-order
  msgHash = keccak256(message.encode())    # raw keccak, no prefix
  sig = signMessage(msgHash_bytes)         # eth prefixed sign
  auth = "app-sk-" + b64(message + "|" + sig.hex())
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3

load_dotenv(Path(__file__).parent.parent / ".env")

PROVIDER_ADDR = "0xa48f01287233509FD694a22Bf840225062E67836"
PROVIDER_URL = "https://compute-network-6.integratenetwork.work"
MODEL = "qwen/qwen-2.5-7b-instruct"


def generate_session_token(account: Account, provider: str) -> str:  # type: ignore[name-defined]
    ts = int(time.time() * 1000)
    token = {
        "address": account.address,
        "provider": provider,
        "timestamp": ts,
        "expiresAt": ts + 3_600_000,
        "nonce": secrets.token_hex(8),
    }
    message = json.dumps(token, separators=(",", ":"))
    msg_hash = Web3.keccak(text=message)              # keccak256(utf8(message))
    signable = encode_defunct(primitive=bytes(msg_hash))  # adds eth prefix
    signed = Account.sign_message(signable, private_key=account.key)
    raw = message + "|" + "0x" + signed.signature.hex()
    return "Bearer app-sk-" + base64.b64encode(raw.encode()).decode()


def main() -> int:
    pk = os.getenv("OG_PRIVATE_KEY")
    if not pk:
        print("ERROR: OG_PRIVATE_KEY not set")
        return 1

    account = Account.from_key(pk)
    print(f"Account : {account.address}")

    token = generate_session_token(account, PROVIDER_ADDR)
    print(f"Token   : {token[:60]}…")

    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": (
                    "You are a TEE attestation oracle. "
                    "Reply with exactly one line: proof-of-merit-attestation-ok"
                ),
            }
        ],
        "max_tokens": 32,
    }

    print(f"\nPOST {PROVIDER_URL}/v1/proxy/chat/completions …")
    try:
        resp = requests.post(
            f"{PROVIDER_URL}/v1/proxy/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        print(f"Status  : {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            compute_hash = "0x" + hashlib.sha256(content.encode()).hexdigest()
            print(f"\n✅ 0G TeeML Inference SUCCESS (direct session token)")
            print(f"   Response    : {content}")
            print(f"   compute_hash: {compute_hash}")
            print(f"\nCP5 DONE — set MOCK_MODE=false in .env to use real attestation")
            return 0
        else:
            print(f"Body    : {resp.text[:400]}")
            return 1
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
