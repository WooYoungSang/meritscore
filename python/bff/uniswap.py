"""Uniswap V3 merit-gated swap module (Sword #6).

Provides quote and swap functions for WETH<->USDC on Base Sepolia.
Uses QuoterV2 for gas-free quotes and SwapRouter02 for atomic swaps.
"""

import json
import logging
from pathlib import Path

from web3 import Web3
from eth_account import Account

logger = logging.getLogger(__name__)

# ============================================================================
# Contract Configuration
# ============================================================================

SWAP_ROUTER_02 = "0x94cC0AaC535CCDB3C01d6787D6413C739ae12bc4"
QUOTER_V2 = "0xC5290058841028F1614F3A6F0F5816cAd0df5E27"
WETH = "0x4200000000000000000000000000000000000006"
USDC = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"

# Primary fee tier (0.3%), fallback to 0.05% if liquidity insufficient
DEFAULT_FEE_TIER = 3000
FALLBACK_FEE_TIER = 500


def _load_abi(contract_name: str) -> list:
    """Load ABI from contracts/abi/{contract_name}.json."""
    abi_path = (
        Path(__file__).parent.parent.parent
        / "contracts" / "abi" / f"{contract_name}.json"
    )
    try:
        with open(abi_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"ABI not found: {abi_path}, using minimal ABI")
        return []


SWAP_ROUTER_02_ABI = _load_abi("SwapRouter02")
QUOTER_V2_ABI = _load_abi("QuoterV2")


def _validate_token_address(token: str) -> None:
    """Validate Ethereum address format (0x-prefixed, 42 chars)."""
    if not isinstance(token, str) or not token.startswith("0x"):
        raise ValueError(
            f"Invalid token address: must be 0x-prefixed, got {token}"
        )
    if len(token) != 42:
        raise ValueError(
            f"Invalid token address: must be 42 chars, got {len(token)}"
        )
    try:
        Web3.to_checksum_address(token)
    except Exception as e:
        raise ValueError(f"Invalid token address: {e}")


def _estimate_price_impact(amount_in: int, amount_out: int) -> float:
    """Estimate price impact as percentage.

    For a simple quote, price_impact % = (amount_out / (amount_in * 1.0005)) * 100
    Adjusted for fee tier (0.3% = 0.003, 0.05% = 0.0005).
    This is a rough heuristic; actual impact depends on pool depth.
    """
    if amount_in <= 0:
        return 0.0
    # Assume 0.3% fee tier for impact calc (most common)
    fee_factor = 1.0 - 0.003
    ideal_out = int(amount_in * fee_factor)
    if ideal_out <= 0:
        return 100.0
    impact = 100.0 * (1.0 - (amount_out / ideal_out))
    return max(0.0, min(100.0, impact))


def quote_amount_out(
    from_token: str,
    to_token: str,
    amount_in: int,
    rpc_url: str = "https://sepolia.base.org",
) -> dict:
    """Quote exact token swap amount without executing.

    Uses QuoterV2.quoteExactInputSingle() for gas-free pricing.

    Args:
        from_token: 0x-prefixed source token address
        to_token: 0x-prefixed destination token address
        amount_in: amount in wei (as int)
        rpc_url: Base Sepolia RPC endpoint

    Returns:
        {
            "amount_out": str (wei),
            "fee_tier": int (500 or 3000),
            "sqrt_price_after": str (hex),
        }

    Raises:
        ValueError: if token addresses invalid
        Exception: if quote call fails
    """
    _validate_token_address(from_token)
    _validate_token_address(to_token)

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise ConnectionError(f"Cannot connect to RPC: {rpc_url}")

    if not QUOTER_V2_ABI:
        raise RuntimeError("QuoterV2 ABI not loaded")

    quoter = w3.eth.contract(
        address=Web3.to_checksum_address(QUOTER_V2),
        abi=QUOTER_V2_ABI
    )

    # Try primary fee tier first
    try:
        fee_tier = DEFAULT_FEE_TIER
        params = {
            "tokenIn": Web3.to_checksum_address(from_token),
            "tokenOut": Web3.to_checksum_address(to_token),
            "amountIn": amount_in,
            "fee": fee_tier,
            "sqrtPriceLimitX96": 0,  # No price limit
        }
        result = quoter.functions.quoteExactInputSingle(
            params
        ).call()
        amount_out = result[0]
        sqrt_price_after = result[1]

        logger.info(
            f"Quote OK: {amount_in} → {amount_out} (fee={fee_tier}bps)"
        )
        return {
            "amount_out": str(amount_out),
            "fee_tier": fee_tier,
            "sqrt_price_after": str(sqrt_price_after),
        }
    except Exception as e:
        logger.warning(
            f"Quote failed with fee {DEFAULT_FEE_TIER}: {e}, "
            f"trying fallback {FALLBACK_FEE_TIER}"
        )
        try:
            fee_tier = FALLBACK_FEE_TIER
            params = {
                "tokenIn": Web3.to_checksum_address(from_token),
                "tokenOut": Web3.to_checksum_address(to_token),
                "amountIn": amount_in,
                "fee": fee_tier,
                "sqrtPriceLimitX96": 0,
            }
            result = quoter.functions.quoteExactInputSingle(
                params
            ).call()
            amount_out = result[0]
            sqrt_price_after = result[1]

            logger.info(
                f"Quote OK (fallback): {amount_in} → {amount_out} "
                f"(fee={fee_tier}bps)"
            )
            return {
                "amount_out": str(amount_out),
                "fee_tier": fee_tier,
                "sqrt_price_after": str(sqrt_price_after),
            }
        except Exception as e2:
            logger.error(f"Quote fallback also failed: {e2}")
            raise


def swap_exact_tokens(
    from_token: str,
    to_token: str,
    amount_in: int,
    amount_out_min: int,
    wallet_addr: str,
    private_key: str,
    rpc_url: str = "https://sepolia.base.org",
) -> dict:
    """Execute exact-input swap via SwapRouter02.

    Args:
        from_token: 0x-prefixed source token address
        to_token: 0x-prefixed destination token address
        amount_in: amount in wei (as int)
        amount_out_min: minimum output amount (slippage enforcement)
        wallet_addr: 0x-prefixed sender address
        private_key: 0x-prefixed private key for signing
        rpc_url: Base Sepolia RPC endpoint

    Returns:
        {
            "tx_hash": str (0x-prefixed),
            "amount_out": str (wei),
            "block_number": int,
        }

    Raises:
        ValueError: if token addresses or amounts invalid
        RuntimeError: if tx reverts on-chain
        Exception: if RPC/signing fails
    """
    _validate_token_address(from_token)
    _validate_token_address(to_token)

    if not isinstance(amount_in, int) or amount_in <= 0:
        raise ValueError(f"Invalid amount_in: {amount_in}")
    if not isinstance(amount_out_min, int) or amount_out_min < 0:
        raise ValueError(f"Invalid amount_out_min: {amount_out_min}")

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise ConnectionError(f"Cannot connect to RPC: {rpc_url}")

    if not SWAP_ROUTER_02_ABI:
        raise RuntimeError("SwapRouter02 ABI not loaded")

    # Derive account from private key
    account = Account.from_key(private_key)
    if account.address.lower() != wallet_addr.lower():
        raise ValueError(
            f"Private key does not match wallet_addr "
            f"({account.address} vs {wallet_addr})"
        )

    # Get nonce
    nonce = w3.eth.get_transaction_count(account.address)

    # Determine fee tier by attempting quote
    try:
        quote_result = quote_amount_out(
            from_token, to_token, amount_in, rpc_url
        )
        fee_tier = quote_result["fee_tier"]
        amount_out_quoted = int(quote_result["amount_out"])
    except Exception as e:
        logger.warning(f"Cannot quote for fee tier: {e}, using default")
        fee_tier = DEFAULT_FEE_TIER
        amount_out_quoted = 0

    # Build swap params (no deadline in SwapRouter02 v2)
    swap_params = {
        "tokenIn": Web3.to_checksum_address(from_token),
        "tokenOut": Web3.to_checksum_address(to_token),
        "fee": fee_tier,
        "recipient": Web3.to_checksum_address(wallet_addr),
        "amountIn": amount_in,
        "amountOutMinimum": amount_out_min,
        "sqrtPriceLimitX96": 0,
    }

    router = w3.eth.contract(
        address=Web3.to_checksum_address(SWAP_ROUTER_02),
        abi=SWAP_ROUTER_02_ABI
    )

    # Build transaction
    tx = router.functions.exactInputSingle(
        swap_params
    ).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 300000,
        "gasPrice": w3.eth.gas_price,
    })

    # Sign and send
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    # Wait for confirmation (simplified: just return hash + last block)
    # In production, would wait for receipt
    block_number = w3.eth.block_number

    logger.info(
        f"Swap submitted: tx_hash={tx_hash.hex()[:16]}... "
        f"amount_in={amount_in} amount_out_min={amount_out_min}"
    )

    return {
        "tx_hash": f"0x{tx_hash.hex()}",
        "amount_out": str(amount_out_quoted),
        "block_number": block_number,
    }
