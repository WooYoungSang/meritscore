#!/bin/bash
# Deploy AgentLendingPool to Base Sepolia
# Usage: DEPLOYER_KEY=0x... BASE_RPC=https://... ./scripts/deploy_lending_pool.sh

set -e

if [ -z "$DEPLOYER_KEY" ]; then
    echo "Error: DEPLOYER_KEY not set"
    exit 1
fi

MERIT_VAULT_ADDR="${MERIT_VAULT_ADDR:-0x3ef2818dD26F4B2e73D8fAb65F6aEA6bc1A2F5E2}"
ASSET_ADDR="${ASSET_ADDR:-0x0000000000000000000000000000000000000000}"  # Set to actual ERC20 token
BASE_RPC="${BASE_RPC:-https://sepolia.base.org}"
CHAIN_ID=84532

echo "Deploying AgentLendingPool..."
echo "MeritVault: $MERIT_VAULT_ADDR"
echo "Asset: $ASSET_ADDR"

forge create contracts/examples/AgentLendingPool.sol:AgentLendingPool \
    --constructor-args "$MERIT_VAULT_ADDR" "$ASSET_ADDR" \
    --rpc-url "$BASE_RPC" \
    --private-key "$DEPLOYER_KEY" \
    --chain-id "$CHAIN_ID"

echo "Deployment complete!"
