"""Test 0G Compute service discovery (non-blocking)."""
import os
import sys

try:
    from a0g import A0G
    print("✅ a0g module imported successfully")
    
    # Try to instantiate (won't fail even without valid key)
    private_key = os.getenv("OG_PRIVATE_KEY", "0x" + "0" * 64)  # Dummy key for testing
    client = A0G(private_key=private_key, rpc_url="https://evmrpc-testnet.0g.ai")
    print("✅ A0G client instantiated (URL: 0G Galileo testnet)")
    
    # This will fail without real key, but tells us if library is working
    try:
        services = client.get_all_services()
        print(f"✅ Service discovery successful: {len(services)} services found")
    except Exception as e:
        print(f"⚠️  Service discovery failed (expected without real key): {type(e).__name__}")
except ImportError as e:
    print(f"❌ a0g module not available: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
