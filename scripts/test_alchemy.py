#!/usr/bin/env python3
"""
Quick test to verify Alchemy API key works
Note: WhaleTracker currently uses Polymarket subgraph, not Alchemy.
This script is for future Web3 integration if needed.
"""

import os
import sys

def test_alchemy_connection():
    """Test Alchemy API connection"""
    
    # Get API key
    alchemy_key = os.getenv('ALCHEMY_API_KEY', 'QC9BcNYIzvefC4dQJ_qKI')
    
    print("\n" + "="*70)
    print("  ALCHEMY API CONNECTION TEST")
    print("="*70 + "\n")
    
    print(f"API Key: {alchemy_key[:10]}...")
    
    # Build URL
    url = f"https://polygon-mainnet.g.alchemy.com/v2/{alchemy_key}"
    print(f"URL: https://polygon-mainnet.g.alchemy.com/v2/{alchemy_key[:10]}...\n")
    
    try:
        # Try to import Web3
        try:
            from web3 import Web3
        except ImportError:
            print("❌ Web3 library not installed")
            print("   Install with: pip install web3")
            return False
        
        # Connect to Polygon
        print("Connecting to Polygon network...")
        web3 = Web3(Web3.HTTPProvider(url))
        
        # Test connection
        if web3.is_connected():
            print("✅ Connected to Polygon successfully!\n")
            
            # Get current block
            block_number = web3.eth.block_number
            print(f"Current block number: {block_number:,}")
            
            # Get chain ID
            chain_id = web3.eth.chain_id
            print(f"Chain ID: {chain_id} (137 = Polygon Mainnet)")
            
            if chain_id == 137:
                print("\n✅ All checks passed! Alchemy API key is working correctly.")
                return True
            else:
                print(f"\n⚠️  Connected but chain ID is wrong (expected 137, got {chain_id})")
                return False
        else:
            print("❌ Failed to connect to Polygon")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_alchemy_connection()
    sys.exit(0 if success else 1)

